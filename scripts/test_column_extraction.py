"""
Test du module d'extraction de colonnes sur des pages connues.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from pdf_reader import open_pdf
from column_extractor import extract_and_save_column2

# Chercher un PDF
input_dir = Path('data/input')
pdfs = list(input_dir.glob('*.PDF')) + list(input_dir.glob('*.pdf'))

if not pdfs:
    print("Aucun PDF trouvé")
    sys.exit(1)

pdf_path = pdfs[0]
print(f"Testing on: {pdf_path.name}")
print("=" * 80)

reader = open_pdf(pdf_path)
poppler_path = r'D:\AI_AGENT GCT\tools\poppler-26.02.0\Library\bin'
output_dir = "data/output"

# Tester l'extraction sur les premières pages
for page_num in range(min(3, len(reader.pages))):
    print(f"\nTesting page {page_num}...")
    result = extract_and_save_column2(
        pdf_path,
        page_num,
        output_dir,
        poppler_path=poppler_path
    )
    if result:
        print(f"  Success: {result}")
    else:
        print(f"  Failed to extract")
