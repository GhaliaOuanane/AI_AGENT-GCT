#!/usr/bin/env python3
"""
Génère un rapport complet d'extraction de spécifications.
Crée un fichier Markdown avec statistiques et aperçu.
"""

import json
from pathlib import Path
from datetime import datetime


def generate_report(json_file, output_report):
    """Génère un rapport Markdown à partir du JSON des spécifications."""
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_pages = len(data)
    total_specs = sum(len(item['specifications']) for item in data)
    avg_specs = total_specs / total_pages if total_pages > 0 else 0
    
    # Trouver les pages avec le plus et le moins de spécifications
    if data:
        max_page = max(data, key=lambda x: len(x['specifications']))
        min_page = min(data, key=lambda x: len(x['specifications']))
    
    report = f"""# Rapport d'Extraction de Spécifications

**Généré:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}  
**Fichier source:** {Path(json_file).name}

---

## 📊 Statistiques Globales

| Métrique | Valeur |
|----------|--------|
| **Total pages** | {total_pages} |
| **Total spécifications** | {total_specs} |
| **Moyenne par page** | {avg_specs:.1f} |
| **Spécifications min** | {len(min_page['specifications']) if data else 0} (Page {min_page['page'] if data else 0}) |
| **Spécifications max** | {len(max_page['specifications']) if data else 0} (Page {max_page['page'] if data else 0}) |

---

## 📋 Détail par Page

"""
    
    for item in data:
        page_num = item['page']
        specs = item['specifications']
        
        report += f"### Page {page_num}\n"
        report += f"**{len(specs)} spécifications**\n\n"
        
        for i, spec in enumerate(specs, 1):
            report += f"{i}. {spec}\n"
        
        report += "\n"
    
    # Écriture du rapport
    with open(output_report, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"[OK] Rapport généré: {output_report}")
    print(f"     {total_pages} pages, {total_specs} spécifications")


def main():
    # Fichiers à traiter
    json_file = Path("data/output/specifications_strict.json")
    output_report = Path("data/output/RAPPORT_SPECIFICATIONS.md")
    
    if not json_file.exists():
        print(f"[ERROR] {json_file} non trouvé")
        return
    
    generate_report(json_file, output_report)


if __name__ == "__main__":
    main()
