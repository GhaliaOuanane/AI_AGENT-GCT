#!/usr/bin/env python3
"""
Script de configuration et installation de Tesseract OCR
Utilise des méthodes automatiques pour télécharger et configurer Tesseract
"""

import os
import sys
import subprocess
import urllib.request
import zipfile
import shutil
from pathlib import Path

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def print_step(text, status="INFO"):
    colors = {
        "INFO": "\033[94m",
        "OK": "\033[92m",
        "WARN": "\033[93m",
        "ERROR": "\033[91m"
    }
    reset = "\033[0m"
    print(f"{colors.get(status, '')}{status:6}{reset} {text}")

def check_tesseract_installed():
    """Vérifie si Tesseract est déjà installé"""
    print_step("Vérification de l'installation Tesseract...", "INFO")
    
    paths = [
        Path("C:/Program Files/Tesseract-OCR/tesseract.exe"),
        Path("C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"),
    ]
    
    for path in paths:
        if path.exists():
            print_step(f"Tesseract trouvé à: {path}", "OK")
            return str(path)
    
    print_step("Tesseract n'est pas installé", "ERROR")
    return None

def download_tesseract_portable():
    """Télécharge une version portable de Tesseract"""
    print_step("Téléchargement de Tesseract OCR (version portable)...", "INFO")
    
    # Utilise UB-Mannheim tesseract portable
    urls = [
        "https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.1/tesseract-ocr-w64-setup-v5.3.1.exe",
        "https://github.com/UB-Mannheim/tesseract/releases/download/v5.2.0/tesseract-ocr-w64-setup-v5.2.0.exe",
    ]
    
    install_dir = Path("C:/Program Files/Tesseract-OCR")
    
    print_step("ATTENTION: Installation automatique sur Windows difficile", "WARN")
    print_step("Télécharge manuellement depuis:", "WARN")
    print(f"  https://github.com/UB-Mannheim/tesseract/wiki")
    print()
    print_step("Versions recommandées:", "INFO")
    print("  • tesseract-ocr-w64-setup-v5.3.1.exe (64-bit)")
    print("  • tesseract-ocr-setup-v5.3.1.exe (32-bit)")
    print()
    print_step("Après installation, relance ce script", "INFO")
    
    return False

def download_french_pack():
    """Télécharge le pack linguistique français"""
    print_step("Configuration du pack français (fra.traineddata)...", "INFO")
    
    tessdata_path = Path("C:/Program Files/Tesseract-OCR/tessdata")
    fra_file = tessdata_path / "fra.traineddata"
    
    if not tessdata_path.exists():
        print_step("Dossier tessdata introuvable", "WARN")
        return False
    
    if fra_file.exists():
        print_step("Pack français déjà installé", "OK")
        return True
    
    print_step("Téléchargement fra.traineddata (~70MB)...", "INFO")
    url = "https://github.com/tesseract-ocr/tessdata/raw/main/fra.traineddata"
    
    try:
        urllib.request.urlretrieve(url, str(fra_file))
        print_step(f"Pack français téléchargé: {fra_file}", "OK")
        return True
    except Exception as e:
        print_step(f"Erreur: {e}", "ERROR")
        print_step("Télécharge manuellement depuis:", "WARN")
        print(f"  {url}")
        return False

def configure_environment():
    """Configure les variables d'environnement"""
    print_step("Configuration des variables d'environnement...", "INFO")
    
    tesseract_path = Path("C:/Program Files/Tesseract-OCR/tesseract.exe")
    tessdata_path = Path("C:/Program Files/Tesseract-OCR/tessdata")
    
    # Configure pour la session actuelle
    os.environ["TESSDATA_PREFIX"] = str(tessdata_path)
    os.environ["PATH"] = f"{str(tesseract_path.parent)};{os.environ.get('PATH', '')}"
    
    print_step(f"TESSDATA_PREFIX = {tessdata_path}", "OK")
    print_step(f"tesseract path = {tesseract_path.parent}", "OK")
    
    return True

def verify_tesseract():
    """Vérifie que Tesseract fonctionne"""
    print_step("Vérification de Tesseract...", "INFO")
    
    try:
        result = subprocess.run(
            ["tesseract", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print_step(version_line, "OK")
            return True
        else:
            print_step("Erreur lors de la vérification", "ERROR")
            return False
    except FileNotFoundError:
        print_step("tesseract command not found", "ERROR")
        return False
    except Exception as e:
        print_step(f"Erreur: {e}", "ERROR")
        return False

def main():
    print_header("🔧 Configuration Tesseract OCR")
    
    # Vérifie l'installation
    tesseract_exe = check_tesseract_installed()
    
    if not tesseract_exe:
        print_header("⚠️  Installation Requise")
        download_tesseract_portable()
        print_header("❌ Configuration Incomplète")
        sys.exit(1)
    
    # Configure l'environnement
    configure_environment()
    
    # Télécharge le pack français
    download_french_pack()
    
    # Vérifie
    if verify_tesseract():
        print_header("✅ Tesseract OCR Configuré avec Succès!")
        print("\n💡 Prochaines étapes:")
        print("  1. Si c'est la première installation, redémarre PowerShell")
        print("  2. Réexécute : python src/main.py")
        print()
        return 0
    else:
        print_header("❌ Erreur de Configuration")
        return 1

if __name__ == "__main__":
    sys.exit(main())
