"""
Debug pourquoi page 4 n'est pas détectée comme table content.
"""

from pathlib import Path
import sys
import re

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from pdf_reader import open_pdf
from text_extractor import extract_page_texts
from page_selector import _normalize

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

text_page4 = page_texts[3]  # page 4 (0-indexed)
normalized = _normalize(text_page4)

print("PAGE 4 - NORMALIZED TEXT:")
print("="*80)
print(normalized)
print("\n" + "="*80)
print("REGEX TESTS:")
print("="*80)

# Test Model 1 keywords
model1_pattern = r"\b(?:specification|designation)\b"
match_model1 = bool(re.search(model1_pattern, normalized, re.IGNORECASE))
print(f"Model 1 pattern: {model1_pattern}")
print(f"Match: {match_model1}")

# Test Model 2 keywords
model2_pattern = r"\b(?:caracteristiques?|propositions?)\b"
match_model2 = bool(re.search(model2_pattern, normalized, re.IGNORECASE))
print(f"\nModel 2 pattern: {model2_pattern}")
print(f"Match: {match_model2}")
if match_model2:
    model2_matches = re.findall(model2_pattern, normalized, re.IGNORECASE)
    print(f"Matches found: {model2_matches}")

# Test numbers
has_numbers = bool(re.search(r"\d", normalized))
print(f"\nHas numbers: {has_numbers}")

# Test exclusions
exclusion_pattern = r"\b(?:article|signature|cachet|remargue|remarque|chapitre|table\s+des\s+matieres|manuel|installation|configuration|deplacement|clavier|ecran|batterie|wifi|microphone|haut[- ]parleur)\b"
is_excluded = bool(re.search(exclusion_pattern, normalized, re.IGNORECASE))
print(f"Is excluded: {is_excluded}")
if is_excluded:
    excl_matches = re.findall(exclusion_pattern, normalized, re.IGNORECASE)
    print(f"Exclusion matches: {set(excl_matches)}")

# Check word by word
print(f"\n" + "="*80)
print("WORDS IN PAGE 4:")
print("="*80)
words = normalized.split()
for word in words[:100]:
    if "caract" in word.lower() or "propos" in word.lower():
        print(f"  >> {word}")
