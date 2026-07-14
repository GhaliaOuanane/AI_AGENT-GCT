"""
Test l'extraction complète avec détection de headers personnalisés
"""

import json
from pathlib import Path
from src.pdf_extraction.extractors.column_extractor import extract_structured_rows, to_json

def test_extraction_with_detected_headers():
    """Test l'extraction avec le PDF qui a "Exigé ou à préciser" """
    
    pdf_path = Path("data/output/pages_cibles.pdf")
    
    if not pdf_path.exists():
        print(f"[ERROR] PDF not found: {pdf_path}")
        print("Please run the main extraction first to generate pages_cibles.pdf")
        return
    
    print("="*70)
    print("TEST: Extraction avec detected_headers")
    print("="*70)
    print(f"PDF: {pdf_path}")
    print()
    
    # Extraire les données
    print("[INFO] Extraction en cours...")
    results = extract_structured_rows(pdf_path)
    
    if not results:
        print("[WARN] Aucun résultat extrait")
        return
    
    print(f"[OK] {len(results)} lignes extraites\n")
    
    # Analyser le premier résultat
    first_result = results[0]
    print("Premier résultat:")
    print(json.dumps(first_result, ensure_ascii=False, indent=2))
    print()
    
    # Vérifier si detected_headers est présent
    if "detected_headers" in first_result:
        print("[✓] detected_headers présent!")
        print(f"    Headers détectés: {first_result['detected_headers']}")
    else:
        print("[✗] detected_headers MANQUANT!")
    
    # Sauvegarder avec noms détectés
    output_path = "data/output/extraction_test_detected.json"
    print(f"\n[INFO] Sauvegarde avec use_detected_headers=True...")
    to_json(results, output_path, use_detected_headers=True)
    
    # Lire et afficher le résultat
    with open(output_path, 'r', encoding='utf-8') as f:
        saved_data = json.load(f)
    
    print("\nPremier élément sauvegardé:")
    print(json.dumps(saved_data[0], ensure_ascii=False, indent=2))
    
    # Chercher la clé "Exigé ou à préciser"
    for key in saved_data[0].keys():
        if "exig" in key.lower() or "precis" in key.lower():
            print(f"\n[✓] Clé personnalisée trouvée: '{key}'")
            print(f"    Valeur: '{saved_data[0][key]}'")

if __name__ == "__main__":
    test_extraction_with_detected_headers()
