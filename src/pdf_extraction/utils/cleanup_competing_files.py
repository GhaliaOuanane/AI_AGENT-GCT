"""
Nettoyage des fichiers concurrents d'extraction.

Après validation de la nouvelle extraction (specifications_source_of_truth.json),
supprime TOUS les anciens fichiers concurrents:
- column2_improved.json/.xlsx
- column2_ordered.json/.xlsx
- extraction.json/.xlsx
- specifications.json
- specifications_strict.json

Log: liste des fichiers supprimés pour traçabilité.
"""

from pathlib import Path
import json
from datetime import datetime


COMPETING_FILES = [
    "column2_improved.json",
    "column2_improved.xlsx",
    "column2_ordered.json",
    "column2_ordered.xlsx",
    "extraction.json",
    "extraction.xlsx",
    "specifications.json",
    "specifications_strict.json",
]

SOURCE_OF_TRUTH_FILE = "specifications_source_of_truth.json"


def cleanup_competing_files(output_dir: str = "data/output", dry_run: bool = False) -> dict:
    """
    Supprime fichiers concurrents.
    
    Args:
        output_dir: Dossier contenant les fichiers
        dry_run: Si True, liste seulement sans supprimer
    
    Returns:
        Dict avec statistiques (supprimés, erreurs, conservé)
    """
    
    output_path = Path(output_dir)
    
    # Vérifier que source de vérité existe
    truth_file = output_path / SOURCE_OF_TRUTH_FILE
    if not truth_file.exists():
        raise FileNotFoundError(
            f"ERREUR: {SOURCE_OF_TRUTH_FILE} n'existe pas. "
            "Exécute d'abord extract_specifications_grid_based.py"
        )
    
    print(f"\n{'='*70}")
    print("NETTOYAGE FICHIERS CONCURRENTS")
    print(f"{'='*70}\n")
    
    if dry_run:
        print("[DRY RUN - Aucun fichier ne sera supprimé]\n")
    
    deleted_files = []
    errors = []
    
    for filename in COMPETING_FILES:
        filepath = output_path / filename
        
        if filepath.exists():
            try:
                if dry_run:
                    print(f"[WOULD DELETE] {filename}")
                else:
                    filepath.unlink()
                    print(f"[DELETED] {filename}")
                    deleted_files.append(filename)
            except Exception as e:
                err_msg = f"Erreur suppression {filename}: {str(e)}"
                print(f"[ERROR] {err_msg}")
                errors.append(err_msg)
        else:
            print(f"[SKIP] {filename} (n'existe pas)")
    
    # Confirmation fichier conservé
    print(f"\n{'='*70}")
    print(f"[CONSERVE] {SOURCE_OF_TRUTH_FILE}")
    print(f"{'='*70}\n")
    
    # Vérifier contenu
    try:
        with open(truth_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        n_pages = len(data.get('pages', []))
        n_entries = sum(len(p.get('entries', [])) for p in data.get('pages', []))
        
        print(f"Contenu validé:")
        print(f"  - Pages: {n_pages}")
        print(f"  - Entrées: {n_entries}")
        print(f"  - Colonne source: {data.get('colonne_source', 'N/A')}")
        print(f"  - Date extraction: {data.get('extraction_date', 'N/A')}\n")
    except Exception as e:
        print(f"WARNING: Impossible de valider contenu: {str(e)}\n")
    
    return {
        "deleted_count": len(deleted_files),
        "deleted_files": deleted_files,
        "errors": errors,
        "source_of_truth": str(truth_file),
        "timestamp": datetime.now().isoformat()
    }


def log_cleanup_report(output_dir: str = "data/output"):
    """Log rapport de nettoyage pour audit."""
    
    report = cleanup_competing_files(output_dir, dry_run=False)
    
    log_file = Path(output_dir) / "cleanup_report.json"
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\nRapport sauvegardé: {log_file}")
    print(f"\nRESUME:")
    print(f"  - Fichiers supprimés: {report['deleted_count']}")
    print(f"  - Erreurs: {len(report['errors'])}")
    print(f"  - Source de vérité: {Path(report['source_of_truth']).name}\n")
    
    return report


if __name__ == "__main__":
    import sys
    
    dry_run = '--dry-run' in sys.argv
    
    if dry_run:
        print("Exécution en DRY RUN (simulation, aucune suppression)")
        cleanup_competing_files(dry_run=True)
    else:
        log_cleanup_report()
