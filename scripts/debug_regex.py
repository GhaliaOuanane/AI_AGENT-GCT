"""
Debug des regex pour identifier les patterns non détectés.
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

# Tester page 3
text_page3 = page_texts[2]  # page 3 (0-indexed)
normalized = _normalize(text_page3)

print("PAGE 3 - FULL TEXT:")
print("="*80)
print(normalized)
print("\n" + "="*80)
print("REGEX TESTS:")
print("="*80)

# Test 1: "designation"
designation_pattern = r"\bdes[il1]gnat[io0ln]+\b"
match_designation = bool(re.search(designation_pattern, normalized, re.IGNORECASE))
print(f"Designation pattern: {designation_pattern}")
print(f"Match: {match_designation}")
if not match_designation:
    # Chercher les variations
    design_like = re.findall(r"\b\w*design\w*\b", normalized, re.IGNORECASE)
    print(f"Found 'design'-like words: {design_like}")

# Test 2: "specification"
spec_pattern = r"\bspec[il1][fj][il1][cf]at[io0ln]+\b"
match_spec = bool(re.search(spec_pattern, normalized, re.IGNORECASE))
print(f"\nSpecification pattern: {spec_pattern}")
print(f"Match: {match_spec}")
if not match_spec:
    spec_like = re.findall(r"\b\w*spec\w*\b", normalized, re.IGNORECASE)
    print(f"Found 'spec'-like words: {spec_like}")

# Test 3: "proposition"
prop_pattern = r"\bpropos[il1]t[io0lnj]+s?\b"
match_prop = bool(re.search(prop_pattern, normalized, re.IGNORECASE))
print(f"\nProposition pattern: {prop_pattern}")
print(f"Match: {match_prop}")
if not match_prop:
    prop_like = re.findall(r"\b\w*propos\w*\b", normalized, re.IGNORECASE)
    print(f"Found 'propos'-like words: {prop_like}")

# Essayer un pattern plus permissif
print("\n" + "="*80)
print("PATTERNS PLUS PERMISSIFS:")
print("="*80)

# Simple search for the French words (post-normalization)
has_des = "designation" in normalized or re.search(r"\bdes[a-z]*gnat[a-z]*\b", normalized, re.IGNORECASE)
has_spec = "specification" in normalized or re.search(r"\bspec[a-z]*\b", normalized, re.IGNORECASE)
has_prop = "proposition" in normalized or re.search(r"\bpropos[a-z]*\b", normalized, re.IGNORECASE)

print(f"Has 'designation': {has_des}")
print(f"Has 'specification': {has_spec}")
print(f"Has 'proposition': {has_prop}")

# Vérifier ce qui est présent
print("\n" + "="*80)
print("MOTS TROUVÉS:")
print("="*80)
words = normalized.split()
design_words = [w for w in words if "design" in w]
spec_words = [w for w in words if "spec" in w]
prop_words = [w for w in words if "propos" in w]

print(f"Design-related: {set(design_words)}")
print(f"Spec-related: {set(spec_words)}")
print(f"Prop-related: {set(prop_words)}")
