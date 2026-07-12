#!/usr/bin/env python3
"""
Script principal - Extraction de la deuxième colonne des tableaux PDF.

Usage:
    python src/main_specifications.py

Output:
    - data/output/specifications.json : Toutes les pages
    - data/output/specifications_strict.json : Pages filtrées (haute qualité)
    - Console : Statistiques et aperçu
"""

import sys
from pathlib import Path
import json
import pytesseract

# Configurer Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

from pdf_extraction.extractors.extract_specifications_main import filter_noisy_pages
from pdf_extraction.extractors.second_column_extractor import extract_all_specifications
from pdf_extraction.extractors.column_extractor import verify_tesseract_setup


def main():
    print("=" * 70)
    print("EXTRACTION DE LA DEUXIÈME COLONNE - TABLEAUX À 3 COLONNES")
    print("=" * 70)
    
    # Vérifier Tesseract
    if not verify_tesseract_setup():
        print("[ERROR] Tesseract not configured properly")
        return
    
    # Trouver le PDF
    input_dir = Path("data/input")
    pdf_files = sorted(input_dir.glob("*.pdf")) + sorted(input_dir.glob("*.PDF"))
    
    if not pdf_files:
        print("[ERROR] Aucun PDF trouvé dans data/input")
        return
    
    pdf_path = pdf_files[0]
    print(f"\n[INFO] Traitement : {pdf_path.name}")
    print("-" * 70)
    
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
    
    # Résumé
    print("-" * 70)
    print("\n[RÉSULTATS]\n")
    print(f"Fichier complet: {output_full.name}")
    print(f"  {len(results)} pages extraites")
    
    print(f"\nFichier filtré: {output_strict.name}")
    print(f"  {len(results_strict)} pages de haute qualité")
    
    filtered_out = len(results) - len(results_strict)
    if filtered_out > 0:
        print(f"  ({filtered_out} page(s) écartées)")
    
    # Statistiques
    if results_strict:
        total_specs = sum(len(r['specifications']) for r in results_strict)
        avg_specs = total_specs / len(results_strict)
        print(f"\nSpécifications totales (strict): {total_specs}")
        print(f"Moyenne par page: {avg_specs:.1f}")
    
    print("\n" + "=" * 70)
    print("APERÇU - PAGES DE HAUTE QUALITÉ (STRICT)\n")
    
    for idx, item in enumerate(results_strict[:3], 1):
        page_num = item['page']
        specs = item['specifications']
        
        print(f"PAGE {page_num}:")
        print(f"({len(specs)} spécifications)")
        
        # Afficher les 8 premières
        for i, spec in enumerate(specs[:8], 1):
            # Tronquer si trop long
            display_spec = spec[:65] + "..." if len(spec) > 65 else spec
            print(f"  {i:2d}. {display_spec}")
        
        if len(specs) > 8:
            print(f"  ... et {len(specs) - 8} autres")
        
        if idx < 3:
            print()
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
