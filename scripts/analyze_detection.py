"""
Script d'analyse de la détection pour diagnostiquer la régression.
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
    select_target_pages
)

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

# Analyser chaque page
print(f"\nTotal pages: {len(page_texts)}\n")

for i, text in enumerate(page_texts, start=1):
    normalized = _normalize(text)
    
    model1 = _matches_header_model_1(normalized)
    model2 = _matches_header_model_2(normalized)
    has_header = _has_table_header(normalized)
    is_content = _looks_like_table_content(normalized)
    
    print(f"PAGE {i}:")
    print(f"  Modèle 1 (Désignation|Spécification|Proposition): {model1}")
    print(f"  Modèle 2 (Composants|Caractéristiques|Proposition): {model2}")
    print(f"  Has Header: {has_header}")
    print(f"  Is Content: {is_content}")
    
    if has_header or is_content:
        print(f"  SELECTED")
        print(f"  Preview: {normalized[:200]}...")
    
    print()

# Sélection finale
selected_pages = select_target_pages(
    reader=reader,
    pdf_path=pdf_path,
    use_ocr=True,
    poppler_path=poppler_path
)
selected_indices = [i + 1 for i, p in enumerate(reader.pages) if p in selected_pages]

print("=" * 80)
print(f"Pages sélectionnées: {selected_indices}")
print(f"Total: {len(selected_indices)} pages")
