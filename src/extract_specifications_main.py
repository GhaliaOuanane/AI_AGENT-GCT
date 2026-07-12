#!/usr/bin/env python3
"""
Script principal pour extraire la deuxième colonne des tableaux.
Génère:
- specifications.json : Toutes les pages avec spécifications
- specifications_strict.json : Pages filtrées (haute qualité uniquement)
"""

import sys
from pathlib import Path
import json
import pytesseract

# Configurer Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

from second_column_extractor import extract_all_specifications


def filter_noisy_pages(results, noise_threshold=0.3):
    """Filtre les pages trop bruyeuses."""
    def get_noise_ratio(text):
        if not text:
            return 1.0
        # Caractères avec beaucoup d'accents/symboles = bruit
        noise_chars = set('ü€Œ…_()[]{}')
        noise_count = sum(1 for c in text if c in noise_chars or (ord(c) > 127 and c not in 'àâäæçéèêëïîôœùûüÀÂÄÆÇÉÈÊËÏÎÔŒÙÛÜ'))
        return noise_count / len(text)
    
    def get_page_noise_score(specs):
        if not specs:
            return 1.0
        ratios = [get_noise_ratio(s) for s in specs]
        return sum(ratios) / len(ratios)
    
    return [r for r in results if get_page_noise_score(r['specifications']) < noise_threshold]


def main():
    input_dir = Path("data/input")
    pdf_files = sorted(input_dir.glob("*.pdf")) + sorted(input_dir.glob("*.PDF"))
    
    if not pdf_files:
        print("[ERROR] Aucun PDF trouvé dans data/input")
        return
    
    pdf_path = pdf_files[0]
    print(f"[INFO] Extraction de : {pdf_path.name}")
    print("=" * 70)
    
    # Extraire les spécifications
    results = extract_all_specifications(str(pdf_path))
    
    # Filtrer les pages bruyeuses
    results_strict = filter_noisy_pages(results, noise_threshold=0.3)
    
    # Sauvegarder
    output_full = Path("data/output/specifications.json")
    output_strict = Path("data/output/specifications_strict.json")
    
    with open(output_full, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    with open(output_strict, 'w', encoding='utf-8') as f:
        json.dump(results_strict, f, ensure_ascii=False, indent=2)
    
    print("=" * 70)
    print(f"\n[OK] Résultats complets: {output_full.name}")
    print(f"     {len(results)} page(s) avec spécifications extraites")
    
    print(f"\n[OK] Résultats filtrés: {output_strict.name}")
    print(f"     {len(results_strict)} page(s) de haute qualité")
    
    filtered_out = len(results) - len(results_strict)
    if filtered_out > 0:
        print(f"     ({filtered_out} page(s) avec trop de bruit OCR écartées)")
    
    # Statistiques
    if results_strict:
        total_specs = sum(len(r['specifications']) for r in results_strict)
        avg_specs_per_page = total_specs / len(results_strict)
        print(f"\n[STATS] Total spécifications: {total_specs}")
        print(f"        Moyenne par page: {avg_specs_per_page:.1f}")
    
    print("\n" + "=" * 70)
    print("Aperçu (mode strict) - 3 premières pages :\n")
    
    for item in results_strict[:3]:
        print(f"PAGE {item['page']}:")
        for i, spec in enumerate(item['specifications'][:7], 1):
            spec_short = spec[:60] + "..." if len(spec) > 60 else spec
            print(f"  {i:2d}. {spec_short}")
        remaining = len(item['specifications']) - 7
        if remaining > 0:
            print(f"  ... et {remaining} autres\n")
        else:
            print()


if __name__ == "__main__":
    main()
