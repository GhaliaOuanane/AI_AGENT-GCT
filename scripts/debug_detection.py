from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from page_selector_robust import (
    _analyze_line_structure,
    _detect_column_structure,
    _calculate_data_to_prose_ratio,
    _has_table_header,
    _is_administrative_prose,
    _is_supplier_datasheet,
    _normalize
)

# Test Page 3
page3_text = """
lot 1 acquisition d une imprimante laser reseau grand quantite 5
specification proposition
marque et modele a preciser
technologie d impression laser monochrome
resolution de l impression 1200 1200 dpi
vitesse d impression jusqu a 55 pages par minute en a4
"""

normalized = _normalize(page3_text)
print("=== PAGE 3 ANALYSIS ===")
print("Normalized text:", repr(normalized[:200]))

print(f"\nEXCLUSIONS:")
print(f"  - is_administrative_prose: {_is_administrative_prose(normalized)}")
print(f"  - is_supplier_datasheet: {_is_supplier_datasheet(normalized)}")

structure = _analyze_line_structure(normalized)
columns = _detect_column_structure(normalized)
data_ratio = _calculate_data_to_prose_ratio(normalized)

print(f"\nStructure:")
print(f"  - line_count: {structure['line_count']}")
print(f"  - avg_words_per_line: {structure['avg_words_per_line']:.2f}")
print(f"  - numeric_density: {structure['numeric_density']:.3f}")
print(f"  - lines_with_numbers: {structure['lines_with_numbers']}")
print(f"  - regular_pattern_score: {structure['regular_pattern_score']:.3f}")

print(f"\nColumns:")
print(f"  - has_column_pattern: {columns['has_column_pattern']}")
print(f"  - column_confidence: {columns['column_confidence']:.3f}")

print(f"\nData ratio: {data_ratio:.3f}")

print(f"\nChecks:")
has_enough_content = 3 <= structure['line_count'] <= 50
has_data_format = data_ratio > 0.2
has_column_structure = columns['column_confidence'] > 0.2
moderate_numeric_density = 0.05 <= structure['numeric_density'] <= 0.8
has_numbers_present = structure['lines_with_numbers'] >= 2

print(f"  - has_enough_content (3-50 lines): {has_enough_content}")
print(f"  - has_data_format (ratio > 0.2): {has_data_format}")
print(f"  - has_column_structure (conf > 0.2): {has_column_structure}")
print(f"  - moderate_numeric_density (0.05-0.8): {moderate_numeric_density}")
print(f"  - has_numbers_present (>= 2 lines): {has_numbers_present}")

positive_score = sum([
    has_enough_content,
    has_data_format,
    has_column_structure,
    moderate_numeric_density,
    has_numbers_present
])

print(f"\nPositive score: {positive_score} (need >= 3)")
print(f"Is table header: {_has_table_header(normalized)}")
