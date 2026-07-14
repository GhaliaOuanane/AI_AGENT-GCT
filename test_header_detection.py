"""
Script de test pour vérifier la détection des headers "Exigé ou à préciser"
"""

from src.pdf_extraction.extractors.column_extractor import (
    match_header,
    normalize,
    extract_structured_rows,
    to_json
)

def test_header_matching():
    """Test les différentes variantes de headers"""
    
    test_cases = [
        # (input, expected_role, expected_detected_label)
        ("Spécification", "specification", "Spécification"),
        ("Exigé ou à préciser", "specification", "Exigé ou à préciser"),
        ("Exigé", "specification", "Exigé"),
        ("À préciser", "specification", "À préciser"),
        ("EXIGE OU A PRECISER", "specification", "EXIGE OU A PRECISER"),
        ("Désignation", "designation", "Désignation"),
        ("Proposition", "proposition", "Proposition"),
    ]
    
    print("="*70)
    print("TEST: Détection de headers")
    print("="*70)
    
    for input_text, expected_role, expected_label in test_cases:
        role, score, method, detected_label = match_header(input_text)
        
        status = "✓" if role == expected_role else "✗"
        print(f"{status} Input: '{input_text}'")
        print(f"   → Role: {role} (expected: {expected_role})")
        print(f"   → Detected label: '{detected_label}'")
        print(f"   → Score: {score}%, Method: {method}")
        print()

if __name__ == "__main__":
    test_header_matching()
    
    print("\n" + "="*70)
    print("Pour tester avec un PDF réel, utilisez:")
    print("  python test_header_detection.py --pdf data/input/BRAIN_INFORMATIQUE_16052025101905.PDF")
    print("="*70)
