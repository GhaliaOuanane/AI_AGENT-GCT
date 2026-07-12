from pathlib import Path
import pytesseract

from pdf_extraction.core.pdf_reader import open_pdf
from pdf_extraction.core.pdf_writer import write_selected_pages
from pdf_extraction.core.page_selector import select_target_pages
from pdf_extraction.extractors.column_extractor import verify_tesseract_setup, to_json

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
    print("EXTRACTION STRUCTURÉE DES LIGNES (V2 PROVEN)")
    print("=" * 60)
    
    # CORRECTION: Utiliser l'extraction V2 qui marche (ratio-based, page-level)
    print(f"\nExtraction depuis : {output_path} (pages cibles uniquement)")
    print("Utilisation de l'algorithme V2 (ratio-based, prouvé avec 132 entries)\n")
    
    # Import V2 extraction
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from extract_specifications_production import extract_all_specifications as extract_v2
    
    # Temporairement pointer vers pages_cibles.pdf
    import shutil
    temp_backup = None
    pages_cibles_in_output = Path(output_path)
    
    # V2 cherche pages_cibles.pdf dans data/output (déjà là)
    v2_result = extract_v2()
    
    if v2_result:
        # Convertir format V2 vers format extraction.json
        results = []
        for page_data in v2_result['pages']:
            for entry in page_data['entries']:
                results.append({
                    "fichier": v2_result['document'],
                    "page": page_data['page'],
                    "lot": None,
                    "modele_detecte": "v2_ratio_based",
                    "designation": entry['designation'],
                    "specification": entry['valeur'],
                    "proposition": "",
                    "confiance_ocr": {
                        "designation": 0,
                        "specification": entry['confiance_ocr'],
                        "proposition": 0
                    },
                    "methode_mapping_headers": "ratio_based"
                })
        
        # Export JSON uniquement
        to_json(results, "data/output/extraction.json")
        
        # Résumé
        print(f"\n[OK] Extraction completee:")
        print(f"   Total entries: {len(results)}")
        print(f"   Source: {output_path}")
        print(f"   Output: data/output/extraction.json")
    else:
        print("[WARN] Aucune ligne extraite")


if __name__ == "__main__":
    main()
