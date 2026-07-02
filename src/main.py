from pathlib import Path

from pdf_reader import open_pdf
from page_selector import select_target_pages
from pdf_writer import write_selected_pages


def _find_input_pdf() -> Path:
    """Recherche automatiquement le premier PDF dans data/input."""

    input_dir = Path("data/input")

    if not input_dir.exists():
        raise FileNotFoundError(f"Dossier introuvable : {input_dir}")

    pdf_files = sorted(input_dir.glob("*.pdf")) + sorted(input_dir.glob("*.PDF"))

    if not pdf_files:
        raise FileNotFoundError(f"Aucun PDF trouvé dans : {input_dir}")

    return pdf_files[0]


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

    poppler_path = r"D:\AI_AGENT GCT\tools\poppler-26.02.0\Library\bin"

    selected_pages = select_target_pages(
        reader=reader,
        pdf_path=input_path,
        use_ocr=True,
        poppler_path=poppler_path,
    )

    print(f"\nNombre de pages sélectionnées : {len(selected_pages)}")

    if not selected_pages:
        print("\nAucune page cible trouvée.")
        return

    write_selected_pages(selected_pages, output_path)

    print("\nPDF créé avec succès.")
    print(f"Fichier enregistré : {output_path}")


if __name__ == "__main__":
    main()