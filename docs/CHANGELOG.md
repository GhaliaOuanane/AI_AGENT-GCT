# Changelog - Projet PDF Extraction

Ce fichier consolide l'historique complet du projet.

---

## [2026-07-12] Refactoring Structurel Majeur

### ✅ Complété
- **Structure Package Python**: Migration vers `src/pdf_extraction/` conforme PEP 420
- **Organisation Code**: Séparation `core/`, `extractors/`, `utils/`
- **Tests Organisés**: Structure `tests/unit/` et `tests/integration/`
- **Scripts Catégorisés**: `scripts/production/`, `scripts/debug/`, `scripts/setup/`
- **Documentation Centralisée**: `docs/` et `docs/technical/`
- **Archivage**: 66 fichiers obsolètes déplacés vers `archive/`
- **Package Installable**: `pyproject.toml` créé, `pip install -e .` fonctionnel
- **Historique Préservé**: Tous déplacements via `git mv`

### 📊 Métriques
- Fichiers racine: 60+ → 8 (-87%)
- Structure: Plate → Package professionnel
- Imports: Relatifs → Absolus via package
- Tests: 31 tests, 23 passants (8 pré-existants échouent)

### 🔧 Changements Breaking
- **Imports modifiés**: `from pdf_reader import` → `from pdf_extraction.core.pdf_reader import`
- **Scripts déplacés**: Vérifier nouveaux chemins dans `scripts/production/`, `scripts/debug/`
- **Docs déplacées**: Documentation technique dans `docs/technical/`

### 📝 Détails Techniques
- Correction threshold documentation: `Y_THRESHOLD=15` → `row_height_threshold=30`
- Import correction dans `main.py`: ancien chemin vers package structure
- Création `__init__.py` dans tous les packages

**Commits:**
- `7497ae3` backup: état avant refactoring structurel
- `bf37134` feat: add pyproject.toml
- `0303ce6` refactor: move core files to pdf_extraction package structure
- `5a5aaad` docs: fix threshold value in condensed documentation
- `5f608b6` chore: archive obsolete code and historical documentation (66 files)
- `4c9aeac` refactor: organize tests, scripts, and documentation into final structure
- `1e12ba9` chore: remove duplicate install scripts and temporary debug files

**Branches:**
- `main` - Branche stable avec backup
- `refactoring-structural` - Branche de travail avec refactoring
- `validation-archive` - Branche de validation

---

## [2025-05-16] Simplification des Sorties

### Complété
- Suppression de tous les formats de sortie sauf `extraction.json`
- Suppression génération Excel/XLSX
- Suppression génération PNG/images colonnes
- Nettoyage code associé (imports, fonctions, dépendances)
- Vérification: `extraction.json` produit avec même contenu

### Résultat
- 1 seul fichier de sortie: `data/output/extraction.json`
- Code simplifié, maintenabilité améliorée
- Pas de régression fonctionnelle

---

## [2025-05-15] Extraction V2 Production (132 Entries)

### Complété
- Algorithme V2 ratio-based validé
- Extraction de 132 entrées depuis pages cibles
- Format JSON structuré avec métadonnées
- QC: 18% flaggés pour revue manuelle
- `extract_specifications_production.py` finalisé

### Qualité
- Précision extraction: ~82% automatique
- Méthode: Ratio-based column mapping
- Source: `data/output/pages_cibles.pdf`

---

## [2025-05] Extraction Deuxième Colonne

### Complété
- Module `second_column_extractor.py` créé
- Algorithme K-means pour détection colonnes (k=3)
- OCR Tesseract avec langue française
- Groupement par ligne (Y similaire ±30px)
- Filtrage mode strict (bruit OCR < 30%)
- Résultat: ~935 spécifications extraites (43 pages)

### Paramètres Clés
- DPI: 300
- `row_height_threshold`: 30 pixels
- `MIN_VALID_RATIO`: 0.5 (mode strict)
- Langue: 'fra' (Tesseract)

---

## [2025-04] Sélection Pages Cibles

### Complété
- Module `page_selector.py` créé
- Détection automatique en-têtes tableaux (2 modèles)
  - Modèle 1: Désignation | Spécification | Proposition
  - Modèle 2: Composants | Caractéristiques techniques | Proposition
- Détection contenu tabulaire
- Détection fin de tableau (NB, Total + nombre)
- Génération `data/output/pages_cibles.pdf`

### Qualité
- Détection robuste des tableaux
- Support continuation pages (sans en-tête)
- Gestion erreurs OCR (variantes orthographiques)

---

## [2025-03] Infrastructure de Base

### Complété
- Modules core créés:
  - `pdf_reader.py` - Lecture PDF avec PyPDF
  - `pdf_writer.py` - Écriture PDF sélectif
  - `text_extractor.py` - Extraction texte (natif + OCR)
  - `ocr_reader.py` - OCR avec Tesseract
  - `column_extractor.py` - Base extraction colonnes
- Configuration Tesseract Windows
- Structure dossiers `data/input/` et `data/output/`
- Tests initiaux

### Dépendances
- PyPDF, pdf2image, Pillow
- opencv-python
- pytesseract, PyMuPDF
- rapidfuzz, scikit-learn, numpy

---

## Structure Actuelle du Projet

```
AI_AGENT_GCT/
├── src/pdf_extraction/              # Package principal
│   ├── core/                        # Modules de base (6 fichiers)
│   ├── extractors/                  # Extracteurs (4 fichiers)
│   └── utils/                       # Utilitaires (2 fichiers)
├── tests/
│   ├── unit/                        # Tests unitaires
│   └── integration/                 # Tests intégration (3 fichiers)
├── scripts/
│   ├── production/                  # Scripts opérationnels (3)
│   ├── debug/                       # Outils debug (2)
│   └── setup/                       # Scripts installation (5)
├── docs/
│   ├── technical/                   # Documentation technique (10)
│   ├── QUICK_START.md
│   ├── INDEX_DOCUMENTATION.md
│   └── CHANGELOG.md                 # Ce fichier
├── archive/                         # Fichiers obsolètes (validation 2 semaines)
│   ├── docs/                        # 29 rapports historiques
│   ├── scripts/                     # 24 scripts obsolètes
│   ├── extractors/                  # 13 extracteurs obsolètes
│   └── selectors/                   # 2 sélecteurs obsolètes
├── data/
│   ├── input/                       # PDFs source
│   └── output/                      # Résultats extraction
├── tools/                           # Outils externes (Poppler)
├── README.md
├── pyproject.toml                   # Configuration package
└── requirements.txt                 # Dépendances Python
```

---

## Historique Détaillé (Archive)

Les rapports détaillés des étapes précédentes sont disponibles dans `archive/docs/`:
- `AGENT_MISSION_COMPLETE.md` - Mission complète agent IA
- `TASK_5_COMPLETION_SUMMARY.md` - Résumé extraction V2
- `COLUMN2_EXTRACTION_FINAL.md` - Extraction deuxième colonne
- `FINAL_DELIVERY_SUMMARY.md` - Livraison finale
- `IMPLEMENTATION_SUMMARY.md` - Résumé implémentation
- Et 24 autres rapports historiques...

---

## Références

### Documentation Technique Active
- `docs/technical/SECOND_COLUMN_EXTRACTION.md` - Guide extraction (version condensée)
- `docs/technical/ALIGNMENT_FIX_REPORT.md` - Corrections alignement
- `docs/technical/SIMPLIFICATION_OUTPUTS.md` - Simplification sorties
- `docs/technical/REFACTORING_EXECUTION_PLAN.md` - Plan refactoring complet
- `docs/technical/REFACTORING_FINAL_REPORT.md` - Rapport final refactoring

### Documentation Historique Complète
- `archive/docs/SECOND_COLUMN_EXTRACTION_FULL.md` - Guide complet (30+ pages)
- `archive/docs/` - 29 rapports historiques complets

---

**Dernière mise à jour:** 2026-07-12  
**Version:** 1.0.0  
**Mainteneur:** GCT - Division Informatique
