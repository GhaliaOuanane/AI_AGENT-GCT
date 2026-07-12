# 🚀 PLAN D'EXÉCUTION REFACTORING - VERSION CORRIGÉE

**Date:** 2026-07-12  
**Version:** 3.0 (corrections appliquées)  
**Status:** PRÊT POUR EXÉCUTION

---

## ✅ CORRECTIONS APPLIQUÉES

### 1. ❌ Suppression Symlink extract_specifications_production.py
**Avant:** Créer symlink à la racine  
**Après:** Mise à jour directe de l'import dans main.py

```python
# Dans src/pdf_extraction/main.py
from pdf_extraction.extractors.extract_specifications_production import extract_all_specifications
```

### 2. ✅ archive/ Suivi par Git (période validation)
**Avant:** Ajout immédiat à .gitignore  
**Après:** Suivi Git pendant validation, commit distinct pour purge finale

```bash
# Après 2 semaines de validation
git add archive/
git commit -m "chore: add archive for validation period"

# Puis après validation
git rm -rf archive/
git commit -m "chore: purge archive/ after validation period"
```

### 3. 🗂️ Structure Archive Simplifiée
**Avant:** `docs/archive/` séparée  
**Après:** Une seule zone d'archive

```
archive/
├── docs/           ← Tous les rapports historiques
├── scripts/        ← Scripts obsolètes
├── extractors/     ← Extracteurs obsolètes
└── selectors/      ← Sélecteurs obsolètes
```

### 4. 🔍 Analyse Scripts Corrigée
**Avant:** 96% scripts "utilisés" (références depuis .md à archiver)  
**Après:** **Nouveau filtre** - exclusion Groupe 8C

**Résultat:** 96% scripts ACTIFS (25/26) - 1 seul obsolète

---

## 📊 NOUVELLE STRUCTURE CIBLE

```
AI_AGENT_GCT/
├── src/pdf_extraction/              ← Package Python
│   ├── __init__.py                  ✅ Obligatoire
│   ├── main.py
│   ├── main_specifications.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── pdf_reader.py
│   │   ├── pdf_writer.py
│   │   ├── page_selector.py
│   │   ├── text_extractor.py
│   │   └── ocr_reader.py
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── column_extractor.py
│   │   ├── second_column_extractor.py
│   │   ├── extract_specifications_main.py
│   │   └── extract_specifications_production.py
│   └── utils/
│       ├── __init__.py
│       ├── clean_ocr.py
│       └── cleanup_competing_files.py
│
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   └── __init__.py
│   └── integration/
│       ├── __init__.py
│       ├── test_page_selection.py
│       ├── test_direct_detection.py
│       └── test_robustness.py
│
├── scripts/
│   ├── production/                  ← 3 scripts opérationnels
│   │   ├── generate_extraction_report.py
│   │   ├── show_specifications.py
│   │   └── inspect_selection.py
│   ├── debug/                       ← 2 outils debug ACTIFS
│   │   ├── detect_table_grid.py
│   │   └── visualize_table_structure.py
│   └── setup/                       ← 5 scripts installation
│       ├── setup_tesseract.py
│       ├── INSTALL_TESSERACT.bat
│       ├── INSTALL_FRA.bat
│       ├── COPY_FRA_TRAINEDDATA.bat
│       ├── move_fra_traineddata.py
│       └── README.md
│
├── docs/
│   ├── QUICK_START.md
│   ├── INDEX_DOCUMENTATION.md
│   ├── CHANGELOG.md                 ← UN SEUL fichier (fusion)
│   └── technical/
│       ├── ALIGNMENT_FIX_REPORT.md
│       ├── SIMPLIFICATION_OUTPUTS.md
│       ├── SECOND_COLUMN_EXTRACTION.md  ← Version condensée
│       └── REFACTORING_EXECUTION_PLAN.md
│
├── archive/                         ← Suivi Git pendant validation
│   ├── docs/                        ← 27 rapports historiques
│   ├── scripts/                     ← 1 script obsolète
│   ├── extractors/                  ← 13 extracteurs obsolètes
│   └── selectors/                   ← 2 sélecteurs obsolètes
│
├── data/
├── tools/
├── README.md
├── pyproject.toml                   ← NOUVEAU
├── requirements.txt
└── .gitignore                       ← Mis à jour
```

---

## 📋 DÉCISIONS FINALES

### Scripts (26 fichiers analysés)

| Catégorie | Nombre | Destination |
|-----------|--------|-------------|
| **Production** | 3 | `scripts/production/` |
| **Debug actifs** | 2 | `scripts/debug/` |
| **Setup** | 5 | `scripts/setup/` |
| **Obsolète** | 1 | `archive/scripts/` |
| **Historiques** | 15 | `archive/scripts/` (référencés uniquement dans .md archivés) |

**Scripts Production (3):**
- generate_extraction_report.py
- show_specifications.py  
- inspect_selection.py

**Scripts Debug Actifs (2):**
- detect_table_grid.py
- visualize_table_structure.py

**Scripts à Archiver (16):**
- visual_debug_column2.py (0 référence)
- Tous les autres scripts debug/test/analyze (15 - référencés uniquement dans .md archivés)

### Documentation (35 fichiers)

| Action | Nombre | Détail |
|--------|--------|--------|
| **GARDER** | 8 | README.md + 7 docs essentielles |
| **CRÉER** | 2 | CHANGELOG.md + SECOND_COLUMN_EXTRACTION.md (condensée) |
| **ARCHIVER** | 27 | Rapports historiques → `archive/docs/` |

### Code Source

| Action | Nombre | Détail |
|--------|--------|--------|
| **RÉORGANISER** | 13 | src/ → src/pdf_extraction/ |
| **ARCHIVER** | 13 | Extracteurs obsolètes |
| **SUPPRIMER** | 8 | Doublons .ps1 + images debug |

---

## 🚀 PLAN D'EXÉCUTION (11 ÉTAPES)

### ÉTAPE 0: Préparation
```bash
# Backup complet
git add -A
git commit -m "backup: état avant refactoring structurel"

# Créer branche de travail
git checkout -b refactoring-structural

# Créer branche validation (pour archive)
git checkout -b validation-archive
git checkout refactoring-structural
```

### ÉTAPE 1: Créer Structure (SANS toucher existant)
```bash
# Créer dossiers
mkdir -p src/pdf_extraction/{core,extractors,utils}
mkdir -p tests/{unit,integration}
mkdir -p scripts/{production,debug,setup}
mkdir -p docs/technical
mkdir -p archive/{docs,scripts,extractors,selectors}

# Créer __init__.py
touch src/pdf_extraction/__init__.py
touch src/pdf_extraction/core/__init__.py
touch src/pdf_extraction/extractors/__init__.py
touch src/pdf_extraction/utils/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py

# Créer scripts/setup/README.md
cat > scripts/setup/README.md << 'EOF'
# Scripts d'Installation

## Tesseract OCR

### Windows
```bash
# Option 1: Script automatique
python setup_tesseract.py

# Option 2: Manuel
INSTALL_TESSERACT.bat
INSTALL_FRA.bat
```

### Vérification
```bash
tesseract --version
tesseract --list-langs  # Doit contenir 'fra'
```
EOF
```

### ÉTAPE 2: Déplacements Code Source (git mv)
```bash
# Main scripts
git mv src/main.py src/pdf_extraction/
git mv src/main_specifications.py src/pdf_extraction/

# Core modules
git mv src/pdf_reader.py src/pdf_extraction/core/
git mv src/pdf_writer.py src/pdf_extraction/core/
git mv src/page_selector.py src/pdf_extraction/core/
git mv src/text_extractor.py src/pdf_extraction/core/
git mv src/ocr_reader.py src/pdf_extraction/core/

# Extractors
git mv src/column_extractor.py src/pdf_extraction/extractors/
git mv src/second_column_extractor.py src/pdf_extraction/extractors/
git mv src/extract_specifications_main.py src/pdf_extraction/extractors/
git mv extract_specifications_production.py src/pdf_extraction/extractors/

# Utils
git mv src/clean_ocr.py src/pdf_extraction/utils/
git mv src/cleanup_competing_files.py src/pdf_extraction/utils/

# Commit
git add -A
git commit -m "refactor: reorganize code into pdf_extraction package"
```

### ÉTAPE 3: Déplacements Tests (git mv)
```bash
git mv tests/test_local_page_selection.py tests/integration/test_page_selection.py
git mv tests/test_direct_detection.py tests/integration/
git mv tests/test_robustness.py tests/integration/

git add -A
git commit -m "refactor: organize tests into unit/integration"
```

### ÉTAPE 4: Déplacements Scripts (git mv)
```bash
# Production
git mv scripts/generate_extraction_report.py scripts/production/
git mv scripts/show_specifications.py scripts/production/
git mv scripts/inspect_selection.py scripts/production/

# Debug actifs
git mv scripts/detect_table_grid.py scripts/debug/
git mv scripts/visualize_table_structure.py scripts/debug/

# Setup
git mv setup_tesseract.py scripts/setup/
git mv INSTALL_TESSERACT.bat scripts/setup/
git mv INSTALL_FRA.bat scripts/setup/
git mv COPY_FRA_TRAINEDDATA.bat scripts/setup/
git mv move_fra_traineddata.py scripts/setup/

git add -A
git commit -m "refactor: organize scripts into production/debug/setup"
```

### ÉTAPE 5: Déplacements Documentation (git mv)
```bash
# Docs essentielles
git mv QUICK_START.md docs/
git mv INDEX_DOCUMENTATION.md docs/
git mv ALIGNMENT_FIX_REPORT.md docs/technical/
git mv SIMPLIFICATION_OUTPUTS.md docs/technical/
git mv SIMPLIFICATION_COMPLETE.md docs/technical/
git mv CLEANUP_RECOMMENDATIONS.md docs/technical/

# Version condensée SECOND_COLUMN
git mv SECOND_COLUMN_EXTRACTION_CONDENSED.md docs/technical/SECOND_COLUMN_EXTRACTION.md

git add -A
git commit -m "refactor: organize documentation"
```

### ÉTAPE 6: Créer Fichiers Config
```bash
# Créer pyproject.toml
cat > pyproject.toml << 'EOF'
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "pdf-extraction"
version = "1.0.0"
description = "Extraction intelligente de spécifications techniques depuis PDFs"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "Proprietary"}
authors = [{name = "GCT - Division Informatique"}]

dependencies = [
    "pypdf>=3.0.0",
    "pdf2image>=1.16.0",
    "Pillow>=10.0.0",
    "opencv-python>=4.8.0",
    "pytesseract>=0.3.10",
    "pymupdf>=1.23.0",
    "rapidfuzz>=3.0.0",
    "scikit-learn>=1.3.0",
    "numpy>=1.24.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.4.0", "black>=23.0.0", "flake8>=6.0.0"]

[project.scripts]
pdf-extract = "pdf_extraction.main:main"
pdf-extract-specs = "pdf_extraction.main_specifications:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]

[tool.black]
line-length = 100
target-version = ["py310"]
EOF

git add pyproject.toml
git commit -m "feat: add pyproject.toml for package installation"
```

### ÉTAPE 7: Mise à Jour Imports (AUTOMATIQUE)
```bash
# Script de migration automatique des imports
cat > scripts/setup/migrate_imports.py << 'EOF'
"""Script de migration automatique des imports."""
import re
from pathlib import Path

IMPORT_MAPPINGS = {
    r'from pdf_reader import': 'from pdf_extraction.core.pdf_reader import',
    r'from pdf_writer import': 'from pdf_extraction.core.pdf_writer import',
    r'from page_selector import': 'from pdf_extraction.core.page_selector import',
    r'from text_extractor import': 'from pdf_extraction.core.text_extractor import',
    r'from ocr_reader import': 'from pdf_extraction.core.ocr_reader import',
    r'from column_extractor import': 'from pdf_extraction.extractors.column_extractor import',
    r'from second_column_extractor import': 'from pdf_extraction.extractors.second_column_extractor import',
    r'from extract_specifications_main import': 'from pdf_extraction.extractors.extract_specifications_main import',
    r'from extract_specifications_production import': 'from pdf_extraction.extractors.extract_specifications_production import',
    r'from clean_ocr import': 'from pdf_extraction.utils.clean_ocr import',
}

def migrate_file(filepath: Path):
    """Migre les imports d'un fichier."""
    content = filepath.read_text(encoding='utf-8')
    original = content
    
    for old, new in IMPORT_MAPPINGS.items():
        content = re.sub(old, new, content)
    
    if content != original:
        filepath.write_text(content, encoding='utf-8')
        print(f"✅ Migré: {filepath}")
        return True
    return False

def main():
    root = Path('.')
    migrated = 0
    
    # Migrer tous les fichiers Python
    for py_file in root.rglob('*.py'):
        if 'archive' in str(py_file) or '.venv' in str(py_file):
            continue
        if migrate_file(py_file):
            migrated += 1
    
    print(f"\n✅ {migrated} fichiers migrés")

if __name__ == "__main__":
    main()
EOF

python scripts/setup/migrate_imports.py

git add -A
git commit -m "refactor: migrate imports to pdf_extraction package"
```

### ÉTAPE 8: ⚠️ VALIDATION OBLIGATOIRE - Tests
```bash
# Installer en mode dev
pip install -e .

# TESTS OBLIGATOIRES
echo "Running tests..."
pytest tests/ -v

# Si tests échouent → ROLLBACK IMMÉDIAT
if [ $? -ne 0 ]; then
    echo "❌ TESTS FAILED - ROLLBACK"
    git reset --hard HEAD~1
    exit 1
fi

echo "✅ Tests passed"
```

### ÉTAPE 9: Test Extraction Principale
```bash
# Test extraction principale
python -m pdf_extraction.main

# Vérifier sortie
if [ -f "data/output/extraction.json" ]; then
    echo "✅ extraction.json generated"
    cat data/output/extraction.json | python -m json.tool > /dev/null
    if [ $? -eq 0 ]; then
        echo "✅ extraction.json is valid JSON"
    else
        echo "❌ extraction.json is INVALID"
        git reset --hard
        exit 1
    fi
else
    echo "❌ extraction.json NOT generated"
    git reset --hard
    exit 1
fi
```

### ÉTAPE 10: Archivage Code Obsolète (git mv)
```bash
# Archiver extracteurs obsolètes
git mv src/column2_extractor_fixed.py archive/extractors/
git mv src/column2_extractor_v2.py archive/extractors/
git mv src/column2_final.py archive/extractors/
git mv src/extract_column2_final_v3.py archive/extractors/
git mv src/extract_column2_from_cibles.py archive/extractors/
git mv src/extract_column2_improved.py archive/extractors/
git mv src/extract_column2_simple.py archive/extractors/
git mv src/extract_specifications_final.py archive/extractors/
git mv src/extract_specifications_grid_based.py archive/extractors/
git mv src/extract_specifications_robust.py archive/extractors/
git mv extract_specifications_v2_strict.py archive/extractors/
git mv extract_specifications_v3_generalized.py archive/extractors/

# Archiver sélecteurs obsolètes
git mv src/page_selector_debug.py archive/selectors/
git mv src/page_selector_robust.py archive/selectors/

# Archiver scripts vérification
git mv check_extraction.py scripts/debug/  # GARDER (actif)
git mv compare_alignment.py archive/scripts/
git mv debug_alignment.py archive/scripts/
git mv validate_specifications_extraction.py archive/scripts/
git mv verify_output.py archive/scripts/
git mv verify_v3_output.py archive/scripts/

# Archiver scripts obsolètes (les 16 scripts)
git mv scripts/visual_debug_column2.py archive/scripts/
# ... (tous les scripts référencés uniquement dans .md archivés)
git mv scripts/analyze_detection.py archive/scripts/
git mv scripts/analyze_separators_detailed.py archive/scripts/
git mv scripts/analyze_vertical_lines.py archive/scripts/
git mv scripts/check_pages.py archive/scripts/
git mv scripts/compare_selectors.py archive/scripts/
git mv scripts/debug_column2_structure.py archive/scripts/
git mv scripts/debug_column_detection.py archive/scripts/
git mv scripts/debug_detection.py archive/scripts/
git mv scripts/debug_page4.py archive/scripts/
git mv scripts/debug_prose.py archive/scripts/
git mv scripts/debug_regex.py archive/scripts/
git mv scripts/detailed_analysis.py archive/scripts/
git mv scripts/detailed_new_analysis.py archive/scripts/
git mv scripts/find_missing_pages.py archive/scripts/
git mv scripts/test_column2_debug.py archive/scripts/
git mv scripts/test_column_extraction.py archive/scripts/
git mv scripts/test_on_first_pdf.py archive/scripts/
git mv scripts/test_second_column.py archive/scripts/
git mv scripts/validate_column2_extraction.py archive/scripts/

# Archiver documentation historique (27 fichiers)
git mv AGENT_MISSION_COMPLETE.md archive/docs/
git mv COLUMN_EXTRACTION_PLAN.md archive/docs/
git mv COLUMN2_EXTRACTION_FINAL.md archive/docs/
git mv COLUMN2_EXTRACTION_v3_FINAL.md archive/docs/
git mv DELIVERABLE_SUMMARY.md archive/docs/
git mv DELIVERABLES.md archive/docs/
git mv EXTRACTION_SPECIFICATIONS_FINAL_REPORT.md archive/docs/
git mv EXTRACTION_SPECIFICATIONS_PRODUCTION.md archive/docs/
git mv EXTRACTION_SPECIFICATIONS_V2_STRICT_REPORT.md archive/docs/
git mv FINAL_DELIVERY_SUMMARY.md archive/docs/
git mv IMPLEMENTATION_SUMMARY_COLUMN2.md archive/docs/
git mv IMPLEMENTATION_SUMMARY.md archive/docs/
git mv SESSION_STATUS_V3_START.md archive/docs/
git mv STATUS_COLUMN2_COMPLETE.md archive/docs/
git mv TASK_5_COMPLETION_SUMMARY.md archive/docs/
git mv SIMPLIFICATION_SUMMARY.md archive/docs/
git mv REFACTORING_DETECTION_DIRECTE.md archive/docs/
git mv REFACTORING_REPORT.md archive/docs/
git mv REGRESSION_ANALYSIS.md archive/docs/
git mv REQUIREMENTS_CHECKLIST.md archive/docs/
git mv SECOND_COLUMN_EXTRACTION.md archive/docs/SECOND_COLUMN_EXTRACTION_FULL.md
git mv V3_ARCHITECTURE_PLAN.md archive/docs/
git mv V3_DIAGNOSIS_FINAL.md archive/docs/
git mv .gitignore_changes.md archive/docs/
git mv GITIGNORE_SUMMARY.md archive/docs/
git mv README_SPECIFICATIONS_EXTRACTION.md archive/docs/
git mv REFACTORING_ANALYSIS_REPORT.md archive/docs/
git mv REFACTORING_PLAN_REVISED.md archive/docs/
git mv REFACTORING_FINAL_DECISIONS.md archive/docs/

git add -A
git commit -m "chore: archive obsolete code and historical documentation"
```

### ÉTAPE 11: Suppressions Finales (doublons)
```bash
# Supprimer doublons PowerShell/VBScript
rm install_tesseract.ps1
rm install_fra.ps1
rm install_fra.vbs
rm copy_fra_traineddata.ps1
rm RUN_INSTALL_FRA_AS_ADMIN.bat
rm MOVE_FRA_TRAINEDDATA.bat  # Fusionné dans COPY

# Supprimer fichiers temporaires
rm debug_column2_visual_page1.png
rm debug_pages.txt  # Si existe

# Supprimer dossier src/ vide
rmdir src/

git add -A
git commit -m "chore: remove duplicate install scripts and temporary files"
```

---

## 📊 RÉSULTATS ATTENDUS

### Avant Refactoring
```
Racine: 60+ fichiers désordonnés
src/: 24 fichiers Python sans structure
scripts/: 26 scripts mélangés
docs: 35 .md éparpillés
```

### Après Refactoring
```
Racine: 3 fichiers (README, pyproject, requirements)
src/pdf_extraction/: 13 fichiers organisés
tests/: Structure claire unit/integration
scripts/: 10 scripts (3 prod + 2 debug + 5 setup)
docs/: 8 fichiers essentiels
archive/: 57 fichiers (validation temporaire)
```

### Gains
- **-94%** fichiers à la racine
- **Package Python installable** avec pip
- **Tests validés** automatiquement
- **Structure professionnelle** maintenable
- **Archive temporaire** pour sécurité

---

## ⚠️ POINTS DE SÉCURITÉ

### 1. Validation Tests OBLIGATOIRE
```bash
pytest tests/ -v
# Si échec → git reset --hard (rollback automatique)
```

### 2. Archive Suivi Git (2 semaines)
```bash
# archive/ reste dans Git pendant validation
# Purge après 2 semaines avec commit distinct
git rm -rf archive/
git commit -m "chore: purge archive/ after validation period"
```

### 3. Backups Multiples
- ✅ Commit backup avant refactoring
- ✅ Branche refactoring-structural
- ✅ Branche validation-archive
- ✅ Tests automatiques avant archivage

---

## ✅ CHECKLIST FINALE

### Avant Exécution
- [ ] Backup Git complet
- [ ] Branche refactoring-structural créée
- [ ] Ce plan lu entièrement

### Pendant Exécution
- [ ] Étape 1: Structure créée
- [ ] Étape 2-5: Déplacements git mv effectués
- [ ] Étape 6: pyproject.toml créé
- [ ] Étape 7: Imports migrés automatiquement
- [ ] Étape 8: **Tests validés (OBLIGATOIRE)**
- [ ] Étape 9: Extraction testée
- [ ] Étape 10: Code obsolète archivé
- [ ] Étape 11: Doublons supprimés

### Après Exécution
- [ ] `python -m pdf_extraction.main` fonctionne
- [ ] `pytest tests/ -v` passe
- [ ] `extraction.json` généré correctement
- [ ] Structure propre vérifiée
- [ ] Documentation mise à jour

### Validation (2 semaines)
- [ ] Projet fonctionne normalement
- [ ] Aucune régression détectée
- [ ] Archive peut être purgée

---

## 🚀 COMMANDE D'EXÉCUTION FINALE

```bash
# Lancer le refactoring complet
bash REFACTORING_EXECUTION_PLAN.md  # Suivre étapes 0-11

# Ou exécuter étape par étape manuellement
```

**PRÊT POUR EXÉCUTION** ✅

---

**Version 3.0 - Corrections appliquées** | 2026-07-12
