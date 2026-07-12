"""
Test de la détection sur le PREMIER PDF (ETS BOUATTOUR) pour vérifier pas de régression.
"""

from pathlib import Path
import sys

# Renommer temporairement le PDF actuel
input_dir = Path('data/input')
current_pdf = input_dir / 'BRAIN INFORMATIQUE_16052025101905.PDF'
first_pdf_backup = input_dir / 'BRAIN INFORMATIQUE_16052025101905_BACKUP.PDF'

if current_pdf.exists() and not first_pdf_backup.exists():
    current_pdf.rename(first_pdf_backup)
    print(f"Sauvegardé : {current_pdf.name} -> {first_pdf_backup.name}")

# Chercher le PREMIER PDF
pdfs = list(input_dir.glob('*.PDF')) + list(input_dir.glob('*.pdf'))
if not pdfs:
    print("Aucun PDF trouvé dans data/input")
    sys.exit(1)

pdf_path = pdfs[0]
print(f"Testé : {pdf_path.name}")
print("="*80)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from pdf_reader import open_pdf
from text_extractor import extract_page_texts
from page_selector import select_target_pages

reader = open_pdf(pdf_path)
poppler_path = r'D:\AI_AGENT GCT\tools\poppler-26.02.0\Library\bin'

# Sélectionner les pages
selected_pages = select_target_pages(
    reader=reader,
    pdf_path=pdf_path,
    use_ocr=True,
    poppler_path=poppler_path
)

selected_indices = [i + 1 for i, p in enumerate(reader.pages) if p in selected_pages]

print(f"Pages sélectionnées: {selected_indices}")
print(f"Total: {len(selected_indices)} pages")

# Restaurer le fichier
if first_pdf_backup.exists():
    first_pdf_backup.rename(current_pdf)
    print(f"\nRestauré : {first_pdf_backup.name} -> {current_pdf.name}")
