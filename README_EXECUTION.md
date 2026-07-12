# 🚀 Guide d'Exécution Rapide

## Méthodes d'Exécution

### Option 1: Scripts Batch (Recommandé - Double-clic)
```
run.bat           → Extraction principale (pages cibles + extraction)
run_specs.bat     → Extraction spécifications uniquement (colonne 2)
```

### Option 2: Ligne de Commande
```bash
# Extraction complète
python src/pdf_extraction/main.py

# Extraction spécifications
python src/pdf_extraction/main_specifications.py
```

### Option 3: Module Python (après pip install -e .)
```bash
pdf-extract         # Extraction principale
pdf-extract-specs   # Extraction spécifications
```

## Fichiers d'Entrée
- Place tes PDFs dans: `data/input/`
- Le script prend automatiquement le premier PDF trouvé

## Fichiers de Sortie
- `data/output/pages_cibles.pdf` - Pages sélectionnées
- `data/output/extraction.json` - Résultats extraction

## Résolution Problèmes

### Erreur Poppler
Si tu vois "PDFInfoNotInstalledError":
- Poppler n'est pas dans le PATH
- Le script fonctionne, mais ne peut pas faire l'OCR
- Solution: Ajouter `tools/poppler-26.02.0/Library/bin` au PATH Windows

### Erreur Tesseract  
Si tu vois "Tesseract not found":
- Exécute: `scripts/setup/INSTALL_TESSERACT.bat`
- Puis: `scripts/setup/INSTALL_FRA.bat`

## Structure du Projet

```
AI_AGENT_GCT/
├── run.bat                      ← Double-clic pour lancer
├── run_specs.bat                ← Double-clic pour specs
├── src/pdf_extraction/          ← Code source
│   ├── main.py                  ← Script principal
│   └── main_specifications.py   ← Script specs
├── data/
│   ├── input/                   ← Place tes PDFs ici
│   └── output/                  ← Résultats ici
└── docs/
    ├── QUICK_START.md           ← Guide détaillé
    └── CHANGELOG.md             ← Historique
```

## Support

Consulte:
- `docs/QUICK_START.md` - Guide complet
- `docs/INDEX_DOCUMENTATION.md` - Index documentation
- `docs/CHANGELOG.md` - Historique des versions
