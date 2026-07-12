"""
Analyse détaillée pour identifier les vraies pages de tableau vs les faux positifs.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from pdf_reader import open_pdf
from text_extractor import extract_page_texts
from page_selector import _normalize

# Chercher le PDF
input_dir = Path('data/input')
pdfs = list(input_dir.glob('*.PDF')) + list(input_dir.glob('*.pdf'))
if not pdfs:
    print("Aucun PDF trouvé")
    sys.exit(1)

pdf_path = pdfs[0]
print(f"Analyse de : {pdf_path.name}")
print("=" * 80)

reader = open_pdf(pdf_path)
poppler_path = r'D:\AI_AGENT GCT\tools\poppler-26.02.0\Library\bin'

# Extraire les textes
page_texts = extract_page_texts(
    reader=reader,
    pdf_path=pdf_path,
    use_ocr=True,
    poppler_path=poppler_path
)

# Analyser les pages suspectes
suspect_pages = [2, 5, 6, 7, 8, 10, 11]

for i in suspect_pages:
    text = page_texts[i-1]
    normalized = _normalize(text)
    
    print(f"\n{'='*80}")
    print(f"PAGE {i} - CONTENU COMPLET:")
    print(f"{'='*80}")
    print(normalized[:1000])
    print("\n[...]\n")
    if len(normalized) > 1000:
        print(normalized[-500:])
    print()
