#!/usr/bin/env python3
"""
Script simple pour déplacer fra.traineddata vers Tesseract OCR
"""

import shutil
from pathlib import Path

print("=" * 70)
print("  Déplacement de fra.traineddata vers Tesseract OCR")
print("=" * 70)
print()

# Chemins
source = Path.home() / "Downloads" / "fra.traineddata"
dest_dir = Path("C:/Program Files/Tesseract-OCR/tessdata")
dest_file = dest_dir / "fra.traineddata"

print(f"Source:      {source}")
print(f"Destination: {dest_file}")
print()

# Vérifie la source
if not source.exists():
    print(f"[ERROR] Fichier source introuvable: {source}")
    exit(1)

source_size_mb = source.stat().st_size / (1024 * 1024)
print(f"[OK] Fichier source trouvé ({source_size_mb:.1f} MB)")

# Vérifie le dossier de destination
if not dest_dir.exists():
    print(f"[ERROR] Dossier de destination introuvable: {dest_dir}")
    print()
    print("Vérifie que Tesseract OCR est installé dans:")
    print("  C:\\Program Files\\Tesseract-OCR\\")
    exit(1)

print(f"[OK] Dossier de destination trouvé")
print()

# Déplace le fichier
print("[INFO] Déplacement en cours...")
try:
    # Si le fichier existe déjà, le supprime d'abord
    if dest_file.exists():
        print(f"[INFO] Suppression du fichier existant...")
        dest_file.unlink()
    
    # Copie le fichier
    shutil.copy2(source, dest_file)
    
    # Vérifie que le fichier est bien là
    if dest_file.exists():
        dest_size_mb = dest_file.stat().st_size / (1024 * 1024)
        print()
        print("=" * 70)
        print("  ✅ Fichier déplacé avec succès!")
        print("=" * 70)
        print()
        print(f"Destination: {dest_file}")
        print(f"Taille:      {dest_size_mb:.1f} MB")
        print()
        print("Prochaines étapes:")
        print("  1. Redémarre PowerShell")
        print("  2. Vérifie: tesseract --list-langs")
        print("  3. Exécute: python src/main.py")
        print()
        exit(0)
    else:
        print(f"[ERROR] Le fichier n'a pas pu être copié")
        exit(1)

except PermissionError:
    print(f"[ERROR] Accès refusé - droits d'écriture insuffisants")
    print()
    print("Solution:")
    print("  Exécute ce script EN TANT QU'ADMINISTRATEUR:")
    print("  • Clique-droit sur l'invite PowerShell")
    print("  • Sélectionne 'Exécuter en tant qu'administrateur'")
    print("  • Réexécute le script")
    exit(1)

except Exception as e:
    print(f"[ERROR] Erreur lors du déplacement: {e}")
    exit(1)
