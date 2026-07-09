"""
Analyse détaillée du nouveau PDF pour identifier toutes les pages cibles manquées.
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
)

# Chercher le PDF
input_dir = Path('data/input')
pdfs = list(input_dir.glob('*.PDF')) + list(input_dir.glob('*.pdf'))
if not pdfs:
    print("Aucun PDF trouvé")
    sys.exit(1)

pdf_path = pdfs[0]
print(f"Analyse de : {pdf_path.name}")

reader = open_pdf(pdf_path)
poppler_path = r'D:\AI_AGENT GCT\tools\poppler-26.02.0\Library\bin'

# Extraire les textes
page_texts = extract_page_texts(
    reader=reader,
    pdf_path=pdf_path,
    use_ocr=True,
    poppler_path=poppler_path
)

# Analyser les pages intéressantes
interesting_pages = [3, 6, 7, 8, 44]

for i in interesting_pages:
    text = page_texts[i-1]
    normalized = _normalize(text)
    
    print(f"\n{'='*80}")
    print(f"PAGE {i}")
    print(f"{'='*80}")
    print(f"Model 1 Match: {_matches_header_model_1(normalized)}")
    print(f"Model 2 Match: {_matches_header_model_2(normalized)}")
    print(f"Has Header: {_has_table_header(normalized)}")
    print(f"Is Content: {_looks_like_table_content(normalized)}")
    print(f"\nText (first 1500 chars):\n")
    print(normalized[:1500])
    if len(normalized) > 1500:
        print(f"\n[...]\n")
        print(normalized[-500:])

# Vérifier TOUTES les pages pour chercher les en-têtes
print(f"\n{'='*80}")
print("RÉSUMÉ: Pages avec en-têtes détectés")
print(f"{'='*80}")

for i in range(1, len(page_texts) + 1):
    text = page_texts[i-1]
    normalized = _normalize(text)
    
    model1 = _matches_header_model_1(normalized)
    model2 = _matches_header_model_2(normalized)
    
    if model1 or model2:
        print(f"PAGE {i}: Model1={model1}, Model2={model2}")
