from pathlib import Path
import sys
import re

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from page_selector_robust import _normalize, _analyze_line_structure

page3_text = """
lot 1 acquisition d une imprimante laser reseau grand quantite 5
specification proposition
marque et modele a preciser
technologie d impression laser monochrome
resolution de l impression 1200 1200 dpi
vitesse d impression jusqu a 55 pages par minute en a4
"""

normalized = _normalize(page3_text)
structure = _analyze_line_structure(normalized)

print("=== PROSE DETECTION DEBUG ===")
print(f"Normalized text:\n{normalized}\n")
print(f"Line count: {structure['line_count']}")
print(f"Lines with numbers: {structure['lines_with_numbers']}")
print(f"Ratio: {structure['lines_with_numbers'] / structure['line_count']:.2f}")

# Test critère 1
crit1 = structure['avg_words_per_line'] > 15 and structure['numeric_density'] < 0.1
print(f"\nCritère 1 (mots>15 ET density<0.1): {crit1}")
print(f"  avg_words={structure['avg_words_per_line']:.2f}, density={structure['numeric_density']:.3f}")

# Test critère 2
lines_with_numbers_ratio = structure['lines_with_numbers'] / structure['line_count']
crit2 = lines_with_numbers_ratio < 0.3 and structure['line_count'] > 5
print(f"\nCritère 2 (lines_ratio<0.3 ET count>5): {crit2}")
print(f"  ratio={lines_with_numbers_ratio:.2f}, count={structure['line_count']}")

# Test critère 3
prose_sequences = len(re.findall(r'\b\w+\s+\w+\s+\w+\s+\w+\b(?!\s*\d)', normalized))
threshold = structure['line_count'] * 0.6
crit3 = prose_sequences > threshold
print(f"\nCritère 3 (prose_seq > count*0.6): {crit3}")
print(f"  prose_sequences={prose_sequences}, threshold={threshold:.1f}")

matches = re.findall(r'\b\w+\s+\w+\s+\w+\s+\w+\b(?!\s*\d)', normalized)
print(f"  Matches found: {len(matches)}")
for i, match in enumerate(matches[:5], 1):
    print(f"    {i}. '{match}'")
