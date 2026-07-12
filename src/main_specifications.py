#!/usr/bin/env python3
"""
Wrapper pour maintenir la compatibilité avec l'ancien chemin src/main_specifications.py
Redirige vers le nouveau chemin src/pdf_extraction/main_specifications.py
"""

import sys
from pathlib import Path

# Ajouter le parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importer et exécuter le vrai main
from pdf_extraction.main_specifications import main

if __name__ == "__main__":
    main()
