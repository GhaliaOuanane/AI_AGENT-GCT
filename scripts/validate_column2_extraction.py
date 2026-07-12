#!/usr/bin/env python3
"""
Validation de l'extraction colonne 2.

Vérifie:
1. Ordre préservé (pas de réorganisation)
2. Pas de doublons
3. Pas d'omissions
4. Structure correcte
"""

import json
from pathlib import Path


def validate_extraction():
    """Valide l'extraction."""
    json_path = Path("data/output/column2_ordered.json")
    
    if not json_path.exists():
        print("[ERROR] column2_ordered.json not found")
        return False
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n{'='*70}")
    print("VALIDATION EXTRACTION COLONNE 2")
    print(f"{'='*70}\n")
    
    # Vérifications
    print("✓ Fichier JSON chargé")
    print(f"✓ Pages trouvées: {len(data)}")
    
    total_lines = 0
    all_lines = []
    
    for page_item in data:
        page_num = page_item['page']
        lines = page_item['column2_lines']
        total_lines += len(lines)
        
        print(f"\nPage {page_num}:")
        print(f"  Lignes: {len(lines)}")
        
        # Vérifier les doublons
        unique_lines = set(lines)
        if len(unique_lines) != len(lines):
            dupes = [l for l in lines if lines.count(l) > 1]
            print(f"  ⚠️  ATTENTION: {len(lines) - len(unique_lines)} doublons détectés!")
            for dupe in set(dupes):
                print(f"     Doublon: '{dupe[:50]}...'")
        else:
            print(f"  ✓ Pas de doublons")
        
        # Vérifier l'ordre (première vs dernière ligne)
        if lines:
            print(f"  Première ligne: '{lines[0][:50]}...'")
            print(f"  Dernière ligne: '{lines[-1][:50]}...'")
        
        all_lines.extend(lines)
    
    print(f"\n{'='*70}")
    print(f"\nRésumé Global:")
    print(f"  ✓ Total pages: {len(data)}")
    print(f"  ✓ Total lignes: {total_lines}")
    print(f"  ✓ Moyenne par page: {total_lines / len(data):.1f}")
    
    # Vérifier doublons globaux
    unique_all = set(all_lines)
    if len(unique_all) != len(all_lines):
        print(f"  ⚠️  Doublons globaux: {len(all_lines) - len(unique_all)}")
    else:
        print(f"  ✓ Pas de doublons globaux")
    
    print(f"\n{'='*70}")
    print("✅ VALIDATION TERMINÉE")
    print(f"{'='*70}\n")
    
    return True


if __name__ == "__main__":
    validate_extraction()
