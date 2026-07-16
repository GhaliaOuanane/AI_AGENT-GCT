from pathlib import Path
import pytesseract
import json
from datetime import datetime

from pdf_extraction.core.pdf_reader import open_pdf
from pdf_extraction.core.pdf_writer import write_selected_pages
from pdf_extraction.core.page_selector import select_target_pages
from pdf_extraction.extractors.column_extractor import verify_tesseract_setup, to_json, extract_structured_rows
from pdf_extraction.core.pdf_validator import validate_input_pdf, log_rejected_file, get_rejection_message

# Configure Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def _find_and_validate_input_pdfs() -> list[tuple[Path, str]]:
    """
    Recherche et valide tous les PDF dans data/input.
    
    Returns:
        Liste de tuples (pdf_path, document_type) pour les PDF valides
    """
    input_dir = Path("data/input")
    if not input_dir.exists():
        raise FileNotFoundError(f"Dossier introuvable : {input_dir}")

    pdf_files = sorted(input_dir.glob("*.pdf")) + sorted(input_dir.glob("*.PDF"))
    if not pdf_files:
        raise FileNotFoundError(f"Aucun PDF trouvé dans : {input_dir}")
    
    print(f"\n[INFO] {len(pdf_files)} PDF(s) trouvé(s) dans {input_dir}")
    print("=" * 60)
    print("VALIDATION DES FICHIERS D'ENTRÉE")
    print("=" * 60)
    
    valid_pdfs = []
    rejected_count = 0
    
    for pdf_file in pdf_files:
        print(f"\n[VALIDATION] {pdf_file.name}...", end=" ")
        validation = validate_input_pdf(pdf_file)
        
        if validation.is_valid:
            doc_type_display = {
                "numerique": "PDF numerique",
                "scanne_net": "Scan haute qualite"
            }.get(validation.document_type, validation.document_type)
            
            print(f"[OK] ACCEPTE ({doc_type_display})")
            
            if validation.document_type == "numerique":
                print(f"  |_ Couverture texte: {validation.metrics['text_coverage_percent']:.1f}%")
            elif validation.document_type == "scanne_net" and validation.image_quality:
                print(f"  |_ DPI: {validation.image_quality.avg_dpi:.0f}, Nettete: {validation.image_quality.sharpness_score:.0f}, Contraste: {validation.image_quality.contrast_std:.0f}")
            
            valid_pdfs.append((pdf_file, validation.document_type))
        else:
            print("[X] REJETE")
            rejected_count += 1
            
            # Message de rejet détaillé
            rejection_msg = get_rejection_message(pdf_file, validation)
            print(f"\n{rejection_msg}\n")
            
            # Journaliser le rejet
            log_rejected_file(pdf_file, validation)
    
    print("\n" + "=" * 60)
    print(f"RÉSULTAT VALIDATION: {len(valid_pdfs)} accepté(s), {rejected_count} rejeté(s)")
    print("=" * 60)
    
    if rejected_count > 0:
        print(f"[INFO] Détails des rejets dans: data/output/rejected_files.json")
    
    return valid_pdfs


def _resolve_poppler_path() -> str | None:
    # Chemin depuis src/pdf_extraction/main.py vers tools/
    candidate = Path(__file__).resolve().parent.parent.parent / "tools" / "poppler-26.02.0" / "Library" / "bin"
    if candidate.exists():
        return str(candidate)
    
    # Fallback: chemin absolu
    fallback = Path(r"C:\Users\ghali\OneDrive\Desktop\AI_AGENT GCT\tools\poppler-26.02.0\Library\bin")
    if fallback.exists():
        return str(fallback)
    
    return None


def _process_single_pdf(input_path: Path, document_type: str, pdf_index: int, total_pdfs: int) -> bool:
    """
    Traite un seul PDF avec gestion d'erreurs isolée.
    
    Args:
        input_path: Chemin du PDF à traiter
        document_type: "numerique" ou "scanne_net"
        pdf_index: Index du PDF courant (1-based)
        total_pdfs: Nombre total de PDFs à traiter
    
    Returns:
        True si le traitement a réussi, False sinon
    """
    output_path = f"data/output/pages_cibles_{input_path.stem}.pdf"
    extraction_output = f"data/output/extraction_{input_path.stem}.json"
    
    print(f"\n{'='*60}")
    print(f"TRAITEMENT [{pdf_index}/{total_pdfs}]: {input_path.name}")
    print(f"Type: {document_type}")
    print(f"{'='*60}")
    
    try:
        # Étape 1: Sélection des pages cibles
        print(f"\nOuverture du PDF : {input_path}")
        reader = open_pdf(input_path)
        print(f"Nombre de pages : {len(reader.pages)}")
        print("\nAnalyse du document...")

        poppler_path = _resolve_poppler_path()
        
        # Activer OCR UNIQUEMENT pour les scans nets
        use_ocr = (document_type == "scanne_net")
        
        if use_ocr:
            print("[INFO] Mode OCR active (scan haute qualite detecte)")

        selected_pages = select_target_pages(
            reader=reader,
            pdf_path=input_path,
            use_ocr=use_ocr,
            poppler_path=poppler_path,
        )
        print(f"Pages candidates detectees : {len(selected_pages)}")

        if not selected_pages:
            print(f"\n[WARN] Aucune page cible trouvee dans {input_path.name}")
            return False

        # Extraire les PageContext pour transmission à l'extracteur
        page_contexts = [context for page, context in selected_pages]
        
        write_selected_pages(selected_pages, output_path)
        print(f"\n[OK] PDF cibles cree: {output_path}")
        
        # Étape 2: Extraction structurée
        print("\n" + "=" * 60)
        print("EXTRACTION STRUCTUREE DES DONNEES")
        print("=" * 60)
        
        print(f"\nExtraction depuis : {output_path}")
        
        # Passer les contexts à l'extracteur
        results = extract_structured_rows(output_path, page_contexts=page_contexts)
        
        if results:
            # Export JSON avec les noms de headers détectés
            to_json(results, extraction_output, use_detected_headers=True)
            
            # Résumé
            print(f"\n[OK] Extraction completee:")
            print(f"   Total entrees: {len(results)}")
            print(f"   Output: {extraction_output}")
            
            # Afficher le modèle détecté
            if results and "modele_detecte" in results[0]:
                modele = results[0]["modele_detecte"]
                print(f"   Modèle détecté: {modele}")
            
            # Afficher les headers détectés
            if results and "detected_headers" in results[0]:
                headers = results[0]["detected_headers"]
                print(f"   Headers détectés:")
                for role, name in headers.items():
                    print(f"      - {role}: '{name}'")
            
            return True
        else:
            print(f"\n[WARN] Aucune ligne extraite pour {input_path.name}")
            return False
    
    except Exception as e:
        print(f"\n[ERROR] Échec du traitement de {input_path.name}")
        print(f"[ERROR] Erreur: {str(e)}")
        
        # Journaliser l'erreur
        error_log = Path("data/output/processing_errors.json")
        error_log.parent.mkdir(parents=True, exist_ok=True)
        
        error_entry = {
            "filename": input_path.name,
            "filepath": str(input_path),
            "error_at": datetime.now().isoformat(),
            "error": str(e),
            "error_type": type(e).__name__
        }
        
        # Charger les erreurs existantes
        if error_log.exists():
            try:
                with open(error_log, 'r', encoding='utf-8') as f:
                    errors = json.load(f)
            except Exception:
                errors = []
        else:
            errors = []
        
        errors.append(error_entry)
        
        with open(error_log, 'w', encoding='utf-8') as f:
            json.dump(errors, f, ensure_ascii=False, indent=2)
        
        print(f"[INFO] Erreur journalisée dans: {error_log}")
        return False


def main():
    """Point d'entrée principal avec traitement par batch."""
    
    print("=" * 60)
    print("AGENT IA - EXTRACTION DE SPÉCIFICATIONS TECHNIQUES")
    print("=" * 60)
    
    # Vérifier la configuration Tesseract
    if not verify_tesseract_setup():
        print("[ERROR] Tesseract setup failed. Please fix the configuration and try again.")
        return
    
    # Étape 1: Validation des fichiers d'entrée
    try:
        valid_pdfs = _find_and_validate_input_pdfs()
    except Exception as e:
        print(f"[ERROR] {e}")
        return
    
    if not valid_pdfs:
        print("\n[ERROR] Aucun PDF valide à traiter.")
        return
    
    # Étape 2: Traiter tous les PDF valides
    print(f"\n{'='*60}")
    print(f"DÉBUT DU TRAITEMENT - {len(valid_pdfs)} PDF(s) à traiter")
    print(f"{'='*60}")
    
    success_count = 0
    failure_count = 0
    
    for index, (pdf_path, document_type) in enumerate(valid_pdfs, start=1):
        success = _process_single_pdf(pdf_path, document_type, index, len(valid_pdfs))
        
        if success:
            success_count += 1
        else:
            failure_count += 1
    
    # Résumé final
    print(f"\n{'='*60}")
    print("RESUME DU TRAITEMENT")
    print(f"{'='*60}")
    print(f"[OK] Reussis: {success_count}/{len(valid_pdfs)}")
    if failure_count > 0:
        print(f"[X] Echecs: {failure_count}/{len(valid_pdfs)}")
        print(f"[INFO] Details des erreurs dans: data/output/processing_errors.json")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
