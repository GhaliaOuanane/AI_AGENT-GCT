from pathlib import Path

from pdf_reader import open_pdf
from pdf_writer import write_selected_pages
from page_selector import select_target_pages
from column_extractor import extract_all_columns


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
    candidate = Path(__file__).resolve().parent.parent / "tools" / "poppler-26.02.0" / "Library" / "bin"
    return str(candidate) if candidate.exists() else None


def main():

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

    # Extraction des 2ᵉ colonnes
    print("\n" + "=" * 60)
    print("EXTRACTION DES 2ᵉ COLONNES")
    print("=" * 60)
    
    extract_all_columns(
        reader=reader,
        pdf_path=input_path,
        selected_pages=selected_pages,
        output_dir="data/output",
        poppler_path=poppler_path,
    )


if __name__ == "__main__":
    main()
