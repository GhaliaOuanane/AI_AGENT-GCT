#!/usr/bin/env python3
"""Test du nouvel extracteur de deuxième colonne."""

import sys
from pathlib import Path

# Ajouter src au chemin
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytesseract
from second_column_extractor import extract_all_specifications
import json


def filter_noisy_pages(results, noise_threshold=0.4):
    """
    Filtre les pages trop bruyeuses.
    Un texte est considéré bruyant s'il contient trop de caractères spéciaux.
    """
    def has_noise_ratio(text):
        """Calcule le ratio de caractères 'brisés' dans le texte."""
        if not text:
            return 0
        
        # Caractères typiquement générés par OCR brisé
        noise_chars = set('ü€Œè…àâäæçéèêëïîôœùûüÀÂÄÆÇÉÈÊËÏÎÔŒÙÛÜ_()[]{}')
        noise_count = sum(1 for c in text if c in noise_chars or ord(c) > 127)
        return noise_count / len(text) if text else 0
    
    filtered = []
    for item in results:
        # Calculer le ratio de bruit moyen pour la page
        noise_ratios = [has_noise_ratio(spec) for spec in item['specifications']]
        avg_noise = sum(noise_ratios) / len(noise_ratios) if noise_ratios else 0
        
        if avg_noise < noise_threshold:
            filtered.append(item)
    
    return filtered


def main():
    # Configurer Tesseract
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    # Trouver le PDF
    input_dir = Path("data/input")
    pdf_files = sorted(input_dir.glob("*.pdf")) + sorted(input_dir.glob("*.PDF"))
    
    if not pdf_files:
        print("[ERROR] Aucun PDF trouvé dans data/input")
        return
    
    pdf_path = pdf_files[0]
    print(f"[INFO] Traitement : {pdf_path}")
    print("=" * 60)
    
    # Extraire les spécifications
    results = extract_all_specifications(str(pdf_path))
    
    # Générer deux fichiers : complet et strict (filtré)
    output_full = Path("data/output/specifications.json")
    output_strict = Path("data/output/specifications_strict.json")
    
    # Fichier complet
    with open(output_full, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # Fichier strict (filtré des pages trop bruyeuses)
    results_strict = filter_noisy_pages(results, noise_threshold=0.3)
    with open(output_strict, 'w', encoding='utf-8') as f:
        json.dump(results_strict, f, ensure_ascii=False, indent=2)
    
    print("=" * 60)
    print(f"[OK] Résultats complets : {output_full}")
    print(f"     {len(results)} page(s) avec des spécifications")
    print(f"\n[OK] Résultats stricts (filtré) : {output_strict}")
    print(f"     {len(results_strict)} page(s) avec des spécifications de qualité")
    
    # Afficher un aperçu
    if results_strict:
        print("\nAperçu des 3 premières pages (mode strict) :")
        for item in results_strict[:3]:
            print(f"\nPage {item['page']}:")
            for i, spec in enumerate(item['specifications'][:5], 1):
                try:
                    print(f"  {i}. {spec}")
                except UnicodeEncodeError:
                    print(f"  {i}. [texte avec caractères spéciaux]")
            if len(item['specifications']) > 5:
                print(f"  ... et {len(item['specifications']) - 5} autres")


if __name__ == "__main__":
    main()

