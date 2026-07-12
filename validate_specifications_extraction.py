"""
✅ VALIDATION - SPECIFICATIONS EXTRACTION
Rapport d'analyse complète du fichier JSON généré
"""

import json
from pathlib import Path
from collections import Counter

def analyze_extraction():
    """Analyse complète de l'extraction."""
    json_path = Path("data/output/specifications_source_of_truth.json")
    
    if not json_path.exists():
        print(f"❌ Fichier non trouvé: {json_path}")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n{'='*70}")
    print("VALIDATION - SPECIFICATIONS EXTRACTION")
    print(f"{'='*70}\n")
    
    # Métadonnées
    print(f"Document source: {data.get('document')}")
    print(f"Colonne source: {data.get('colonne_source')}")
    print(f"Date extraction: {data.get('extraction_date')}\n")
    
    # Statistiques globales
    pages = data.get('pages', [])
    total_pages = len(pages)
    total_entries = sum(len(p['entries']) for p in pages)
    
    print(f"{'STATISTIQUES GLOBALES'}")
    print(f"-" * 70)
    print(f"Pages traitées: {total_pages}")
    print(f"Entrées totales: {total_entries}")
    print(f"Moyenne entrées/page: {total_entries / total_pages:.1f}\n")
    
    # Analyse des entrées
    all_entries = []
    for page in pages:
        all_entries.extend(page['entries'])
    
    entries_to_verify = [e for e in all_entries if e['a_verifier']]
    entries_ok = [e for e in all_entries if not e['a_verifier']]
    
    print(f"{'QUALITE OCR'}")
    print(f"-" * 70)
    print(f"Entrées OK (confiance ≥ 70): {len(entries_ok)} ({100*len(entries_ok)/total_entries:.0f}%)")
    print(f"À vérifier (confiance < 70): {len(entries_to_verify)} ({100*len(entries_to_verify)/total_entries:.0f}%)\n")
    
    # Distribution confiance
    confidences = [e['confiance_ocr'] for e in all_entries]
    if confidences:
        min_conf = min(confidences)
        max_conf = max(confidences)
        avg_conf = sum(confidences) / len(confidences)
        
        print(f"{'CONFIANCE OCR'}")
        print(f"-" * 70)
        print(f"Minimum: {min_conf:.1f}%")
        print(f"Maximum: {max_conf:.1f}%")
        print(f"Moyenne: {avg_conf:.1f}%\n")
        
        # Histogramme
        bins = [0, 30, 50, 70, 85, 100]
        hist = {}
        for conf in confidences:
            for i in range(len(bins)-1):
                if bins[i] <= conf < bins[i+1]:
                    key = f"{bins[i]}-{bins[i+1]}"
                    hist[key] = hist.get(key, 0) + 1
                    break
            else:
                key = f"{bins[-2]}-{bins[-1]}"
                hist[key] = hist.get(key, 0) + 1
        
        print(f"Distribution par intervalle:")
        for key in sorted(hist.keys()):
            pct = 100 * hist[key] / len(confidences)
            bar = '█' * int(pct / 2)
            print(f"  {key:8}%: {bar} {hist[key]:3d} ({pct:5.1f}%)")
    
    print(f"\n{'RAISONS DE VERIFICATION'}")
    print(f"-" * 70)
    
    reasons = Counter()
    for entry in entries_to_verify:
        reason = entry.get('raison_verification', 'non_specifie')
        if reason:
            reasons[reason] += 1
    
    if reasons:
        for reason, count in reasons.most_common():
            print(f"  • {reason}: {count}")
    else:
        print("  Aucune raison spécifiée")
    
    print(f"\n{'DONNEES EXTRACTION'}")
    print(f"-" * 70)
    
    # Vérifier colonnes
    has_designation = sum(1 for e in all_entries if e.get('designation', '').strip())
    has_valeur = sum(1 for e in all_entries if e.get('valeur', '').strip())
    
    print(f"Entrées avec Designation: {has_designation} ({100*has_designation/total_entries:.0f}%)")
    print(f"Entrées avec Valeur: {has_valeur} ({100*has_valeur/total_entries:.0f}%)")
    print(f"Entrées complètes (both): {sum(1 for e in all_entries if e.get('designation', '').strip() and e.get('valeur', '').strip())}")
    
    print(f"\n{'EXEMPLES'}")
    print(f"-" * 70)
    
    # Exemples OK
    print(f"\nTop 3 entrées avec meilleure confiance:")
    top_ok = sorted(all_entries, key=lambda e: e['confiance_ocr'], reverse=True)[:3]
    for i, entry in enumerate(top_ok, 1):
        print(f"  {i}. [{entry['confiance_ocr']:.0f}%] {entry['designation'][:25]} → {entry['valeur'][:35]}")
    
    # Exemples à vérifier
    print(f"\nTop 3 entrées à vérifier (confiance faible):")
    to_verify_sorted = sorted(entries_to_verify, key=lambda e: e['confiance_ocr'])[:3]
    for i, entry in enumerate(to_verify_sorted, 1):
        print(f"  {i}. [{entry['confiance_ocr']:.0f}%] {entry['designation'][:25]} → {entry['valeur'][:35]}")
    
    print(f"\n{'FICHIERS GENERES'}")
    print(f"-" * 70)
    json_file = Path("data/output/specifications_source_of_truth.json")
    xlsx_file = Path("data/output/specifications_source_of_truth.xlsx")
    
    print(f"✓ JSON: {json_file} ({json_file.stat().st_size / 1024:.1f} KB)")
    
    if xlsx_file.exists():
        print(f"✓ Excel: {xlsx_file} ({xlsx_file.stat().st_size / 1024:.1f} KB)")
    
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    analyze_extraction()
