"""
Identifier les pages manquantes et comprendre pourquoi elles ne sont pas détectées.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from pdf_reader import open_pdf
from text_extractor import extract_page_texts
from page_selector import (
    _normalize,
    _matches_header_model_1,
    _matches_header_model_2,
    _has_table_header,
    _looks_like_table_content,
    _looks_like_note_page,
    _looks_like_end_of_table,
)

# Chercher le PDF
input_dir = Path('data/input')
pdfs = list(input_dir.glob('*.PDF')) + list(input_dir.glob('*.pdf'))
pdf_path = pdfs[0]

reader = open_pdf(pdf_path)
poppler_path = r'D:\AI_AGENT GCT\tools\poppler-26.02.0\Library\bin'

# Extraire les textes
page_texts = extract_page_texts(
    reader=reader,
    pdf_path=pdf_path,
    use_ocr=True,
    poppler_path=poppler_path
)

# Analyser les pages autour des pages détectées
# Détectées: 3, 6, 7, 8
# Potentiellement manquées: 2, 4, 5, 9+

print("ANALYSE DES PAGES MANQUÉES")
print("="*80)

for page_num in [2, 4, 5, 9]:
    text = page_texts[page_num-1]
    normalized = _normalize(text)
    
    line_count = len([line for line in text.splitlines() if line.strip()])
    
    print(f"\nPAGE {page_num}:")
    print(f"  Line count: {line_count}")
    print(f"  Model 1 Header: {_matches_header_model_1(normalized)}")
    print(f"  Model 2 Header: {_matches_header_model_2(normalized)}")
    print(f"  Has Header: {_has_table_header(normalized)}")
    print(f"  Is Table Content: {_looks_like_table_content(normalized)}")
    print(f"  Is Note Page: {_looks_like_note_page(normalized)}")
    print(f"  Is End Page: {_looks_like_end_of_table(normalized)}")
    print(f"  Text preview:\n{normalized[:500]}")
    print()
