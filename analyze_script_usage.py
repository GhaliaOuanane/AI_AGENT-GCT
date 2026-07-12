"""
Script d'analyse de l'utilisation des scripts dans scripts/
Identifie quels scripts sont encore référencés dans le code actif.

CORRECTION: Exclusion des références depuis fichiers .md marqués pour archivage.
Un script n'est "utilisé" que s'il est référencé depuis:
- Fichiers .py actifs
- Fichiers .bat/.ps1 conservés
- Fichiers .md conservés (pas ceux du Groupe 8C)
"""
import os
import re
from pathlib import Path
from collections import defaultdict

# Fichiers Markdown du Groupe 8C (à archiver) - leurs références ne comptent pas
# AJOUT: Fichiers de refactoring qui mentionnent les scripts sans les utiliser
ARCHIVED_MARKDOWN_FILES = {
    'AGENT_MISSION_COMPLETE.md',
    'COLUMN_EXTRACTION_PLAN.md',
    'COLUMN2_EXTRACTION_FINAL.md',
    'COLUMN2_EXTRACTION_v3_FINAL.md',
    'DELIVERABLE_SUMMARY.md',
    'DELIVERABLES.md',
    'EXTRACTION_SPECIFICATIONS_FINAL_REPORT.md',
    'EXTRACTION_SPECIFICATIONS_PRODUCTION.md',
    'EXTRACTION_SPECIFICATIONS_V2_STRICT_REPORT.md',
    'FINAL_DELIVERY_SUMMARY.md',
    'IMPLEMENTATION_SUMMARY_COLUMN2.md',
    'IMPLEMENTATION_SUMMARY.md',
    'SESSION_STATUS_V3_START.md',
    'STATUS_COLUMN2_COMPLETE.md',
    'TASK_5_COMPLETION_SUMMARY.md',
    'SIMPLIFICATION_SUMMARY.md',
    'REFACTORING_DETECTION_DIRECTE.md',
    'REFACTORING_REPORT.md',
    'REGRESSION_ANALYSIS.md',
    'REQUIREMENTS_CHECKLIST.md',
    'SECOND_COLUMN_EXTRACTION.md',
    'V3_ARCHITECTURE_PLAN.md',
    'V3_DIAGNOSIS_FINAL.md',
    '.gitignore_changes.md',
    'GITIGNORE_SUMMARY.md',
    'README_SPECIFICATIONS_EXTRACTION.md',
    # Fichiers de refactoring (mentionnent scripts sans les utiliser)
    'REFACTORING_ANALYSIS_REPORT.md',
    'REFACTORING_PLAN_REVISED.md',
    'REFACTORING_FINAL_DECISIONS.md',
    'REFACTORING_EXECUTION_PLAN.md',
    'REFACTORING_READY.md',
}

def find_script_references(root_dir: Path, script_name: str):
    """Trouve toutes les références à un script dans le code actif."""
    references = []
    script_basename = Path(script_name).stem
    
    # Patterns de recherche
    patterns = [
        rf'import\s+{script_basename}',
        rf'from\s+{script_basename}',
        rf'python\s+.*{script_name}',
        rf'subprocess.*{script_name}',
        rf'{script_name}',
    ]
    
    # Parcourir tous les fichiers Python, Markdown conservés, et scripts shell
    for ext in ['*.py', '*.md', '*.bat', '*.ps1']:
        for filepath in root_dir.rglob(ext):
            # Ignorer le script lui-même et les archives
            if 'archive' in str(filepath) or filepath.name == script_name:
                continue
            
            # CORRECTION: Ignorer les fichiers .md marqués pour archivage
            if filepath.suffix == '.md' and filepath.name in ARCHIVED_MARKDOWN_FILES:
                continue
            
            try:
                content = filepath.read_text(encoding='utf-8', errors='ignore')
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        references.append(str(filepath.relative_to(root_dir)))
                        break
            except Exception as e:
                pass
    
    return references

def analyze_script_metadata(script_path: Path):
    """Analyse les métadonnées d'un script."""
    metadata = {
        'size': script_path.stat().st_size,
        'lines': 0,
        'has_main': False,
        'has_docstring': False,
        'last_modified': script_path.stat().st_mtime,
    }
    
    try:
        content = script_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        metadata['lines'] = len(lines)
        metadata['has_main'] = 'def main(' in content or 'if __name__' in content
        metadata['has_docstring'] = '"""' in content or "'''" in content
    except Exception:
        pass
    
    return metadata

def main():
    root = Path('.')
    scripts_dir = root / 'scripts'
    
    if not scripts_dir.exists():
        print("Dossier scripts/ non trouvé")
        return
    
    print("=" * 80)
    print("ANALYSE D'UTILISATION DES SCRIPTS")
    print("=" * 80)
    print()
    
    # Liste tous les scripts
    scripts = sorted(scripts_dir.glob('*.py'))
    
    results = []
    
    for script in scripts:
        script_name = script.name
        references = find_script_references(root, script_name)
        metadata = analyze_script_metadata(script)
        
        results.append({
            'name': script_name,
            'references': references,
            'metadata': metadata,
        })
    
    # Trier par nombre de références (décroissant)
    results.sort(key=lambda x: len(x['references']), reverse=True)
    
    # Afficher résultats
    print("SCRIPTS AVEC RÉFÉRENCES (probablement utilisés):")
    print("-" * 80)
    for r in results:
        if len(r['references']) > 0:
            print(f"\n✅ {r['name']}")
            print(f"   Références: {len(r['references'])}")
            print(f"   Lignes: {r['metadata']['lines']}")
            print(f"   Has main: {r['metadata']['has_main']}")
            for ref in r['references']:
                print(f"      → {ref}")
    
    print("\n" + "=" * 80)
    print("SCRIPTS SANS RÉFÉRENCES (probablement obsolètes):")
    print("-" * 80)
    for r in results:
        if len(r['references']) == 0:
            print(f"\n⚠️ {r['name']}")
            print(f"   Lignes: {r['metadata']['lines']}")
            print(f"   Has main: {r['metadata']['has_main']}")
            print(f"   Taille: {r['metadata']['size']} bytes")
    
    print("\n" + "=" * 80)
    print("RÉSUMÉ:")
    print("-" * 80)
    total = len(results)
    with_refs = sum(1 for r in results if len(r['references']) > 0)
    without_refs = total - with_refs
    
    print(f"Total scripts: {total}")
    print(f"Avec références ACTIVES: {with_refs} ({100*with_refs/total:.0f}%)")
    print(f"Sans références: {without_refs} ({100*without_refs/total:.0f}%)")
    print()
    
    print("NOTE: Les références depuis fichiers .md du Groupe 8C (à archiver)")
    print("      ne sont PAS comptées. Seules comptent les références depuis:")
    print("      - Fichiers .py actifs")
    print("      - Fichiers .bat/.ps1 conservés")
    print("      - Fichiers .md conservés (README, QUICK_START, etc.)")
    print()
    
    print("RECOMMANDATIONS:")
    print("-" * 80)
    print(f"✅ GARDER (scripts/production/ ou scripts/debug/): {with_refs} scripts")
    print(f"🔄 ARCHIVER (archive/scripts/): {without_refs} scripts")
    print()

if __name__ == "__main__":
    main()
