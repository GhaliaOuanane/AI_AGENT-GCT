#!/usr/bin/env python3
"""
Visualise les spécifications extraites dans un format lisible.
"""

import json
import sys
from pathlib import Path

def show_json(filepath, limit_pages=5):
    """Affiche le JSON des spécifications de manière lisible."""
    
    if not Path(filepath).exists():
        print(f"[ERROR] Fichier non trouvé: {filepath}")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n{'='*80}")
    print(f"SPÉCIFICATIONS - {Path(filepath).name}")
    print(f"{'='*80}\n")
    
    print(f"Total pages: {len(data)}")
    total_specs = sum(len(item['specifications']) for item in data)
    print(f"Total spécifications: {total_specs}")
    print(f"Moyenne par page: {total_specs/len(data) if data else 0:.1f}\n")
    
    print(f"{'='*80}\n")
    
    # Afficher les premières pages
    for idx, item in enumerate(data[:limit_pages], 1):
        page_num = item['page']
        specs = item['specifications']
        
        print(f"\n[PAGE {page_num}] ({len(specs)} spécifications)")
        print("-" * 80)
        
        for i, spec in enumerate(specs, 1):
            # Formater avec numérotation
            marker = f"{i:3d}."
            # Afficher avec retour à la ligne si trop long
            if len(spec) > 70:
                print(f"{marker} {spec[:70]}")
                remaining = spec[70:]
                while remaining:
                    chunk = remaining[:70]
                    print(f"     {chunk}")
                    remaining = remaining[70:]
            else:
                print(f"{marker} {spec}")
        
        if idx < limit_pages:
            print()
    
    remaining_pages = len(data) - limit_pages
    if remaining_pages > 0:
        print(f"\n... et {remaining_pages} page(s) non affichées")
    
    print(f"\n{'='*80}\n")

def main():
    print("Visualiseur de Spécifications Extraites\n")
    
    # Options
    print("Choisissez le fichier à visualiser:")
    print("  1. specifications.json (complet)")
    print("  2. specifications_strict.json (haute qualité)")
    
    choice = input("\nVotre choix [1 ou 2] (default: 2): ").strip() or "2"
    
    files = {
        "1": "data/output/specifications.json",
        "2": "data/output/specifications_strict.json"
    }
    
    if choice not in files:
        print("[ERROR] Choix invalide")
        return
    
    filepath = files[choice]
    
    # Nombre de pages à afficher
    limit = input("Nombre de pages à afficher [5]: ").strip()
    limit = int(limit) if limit.isdigit() else 5
    
    show_json(filepath, limit_pages=limit)

if __name__ == "__main__":
    main()
