from pathlib import Path
import pytesseract

from pdf_extraction.core.pdf_reader import open_pdf
from pdf_extraction.core.pdf_writer import write_selected_pages
from pdf_extraction.core.page_selector import select_target_pages
from pdf_extraction.extractors.column_extractor import verify_tesseract_setup, to_json, extract_structured_rows

# Configure Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def _find_input_pdf() -> Path:
    """Recherche automatiquement le premier PDF dans data/input."""
    input_dir = Path("data/input")
    if not input_dir.exists():
        raise FileNotFoundError(f"Dossier introuvable : {input_dir}")

    pdf_files = sorted(input_dir.glob("*.pdf")) + sorted(input_dir.glob("*.PDF"))
    if not pdf_files:
        raise FileNotFoundError(f"Aucun PDF trouvé dans : {input_dir}")

    return pdf_files[0]


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


def main():

    # Vérifier la configuration Tesseract avant de commencer
    if not verify_tesseract_setup():
        print("[ERROR] Tesseract setup failed. Please fix the configuration and try again.")
        return

    input_path = _find_input_pdf()
    output_path = "data/output/pages_cibles.pdf"

    print("=" * 60)
    print("AGENT IA - EXTRACTION DES PAGES CIBLES")
    print("=" * 60)

    print(f"\nOuverture du PDF : {input_path}")
    reader = open_pdf(input_path)
    print(f"Nombre de pages : {len(reader.pages)}")
    print("\nAnalyse du document...")

    poppler_path = _resolve_poppler_path()
    use_ocr = True

    selected_pages = select_target_pages(
        reader=reader,
        pdf_path=input_path,
        use_ocr=use_ocr,
        poppler_path=poppler_path,
    )
    print(f"Pages candidates initiales : {len(selected_pages)}")

    if not selected_pages:
        print("\nAucune page cible trouvée.")
        return

    write_selected_pages(selected_pages, output_path)
    print("\nPDF créé avec succès.")
    print(f"Fichier enregistré : {output_path}")

    # Extraction structurée des lignes avec alignement des 3 colonnes
    print("\n" + "=" * 60)
    print("EXTRACTION STRUCTURÉE DES LIGNES (avec détection de headers)")
    print("=" * 60)
    
    print(f"\nExtraction depuis : {output_path} (pages cibles uniquement)")
    print("Utilisation de l'algorithme avec détection automatique des headers\n")
    
    # Import du nouvel extracteur avec détection de headers
    from pdf_extraction.extractors.column_extractor import extract_structured_rows
    
    # Extraction avec détection automatique des headers
    results = extract_structured_rows(output_path)
    
    if results:
        # Export JSON avec les noms de headers détectés
        to_json(results, "data/output/extraction.json", use_detected_headers=True)
        
        # Résumé
        print(f"\n[OK] Extraction completee:")
        print(f"   Total entries: {len(results)}")
        print(f"   Source: {output_path}")
        print(f"   Output: data/output/extraction.json")
        
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
    else:
        print("[WARN] Aucune ligne extraite")


if __name__ == "__main__":
    main()
