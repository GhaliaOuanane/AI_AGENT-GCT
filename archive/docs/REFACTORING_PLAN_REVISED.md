# 📋 PLAN DE REFACTORING RÉVISÉ - VERSION VALIDÉE

**Date:** 2026-07-12  
**Version:** 2.0 (corrigée selon feedback professionnel)

---

## ✅ STRUCTURE CIBLE FINALE

```
AI_AGENT_GCT/
│
├── 📁 src/
│   └── pdf_extraction/
│       ├── __init__.py                    ← AJOUTÉ (obligatoire)
│       ├── main.py
│       ├── main_specifications.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── pdf_reader.py
│       │   ├── pdf_writer.py
│       │   ├── page_selector.py
│       │   ├── text_extractor.py
│       │   └── ocr_reader.py
│       ├── extractors/
│       │   ├── __init__.py
│       │   ├── column_extractor.py
│       │   ├── second_column_extractor.py
│       │   └── extract_specifications_main.py
│       └── utils/
│           ├── __init__.py
│           ├── clean_ocr.py
│           └── cleanup_competing_files.py
│
├── 📁 tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── __init__.py
│   │   └── (tests unitaires à venir)
│   └── integration/
│       ├── __init__.py
│       ├── test_page_selection.py         ← Renommé
│       ├── test_direct_detection.py
│       └── test_robustness.py
│
├── 📁 scripts/
│   ├── production/                        ← Scripts opérationnels réutilisables
│   │   ├── generate_extraction_report.py
│   │   ├── show_specifications.py
│   │   └── inspect_selection.py
│   ├── debug/                             ← OUTILS DEBUG ACTIFS (pas d'historique)
│   │   ├── visualize_table_structure.py  ← Utile pour debug
│   │   ├── detect_table_grid.py          ← Utile pour debug
│   │   └── (uniquement outils encore utilisés)
│   └── setup/                             ← Scripts installation/configuration
│       ├── setup_tesseract.py
│       ├── install_tesseract.bat
│       ├── install_fra.bat
│       ├── move_fra_traineddata.py
│       └── README.md                      ← Instructions setup
│
├── 📁 docs/
│   ├── README.md                          ← Symlink vers ../README.md
│   ├── QUICK_START.md
│   ├── INDEX_DOCUMENTATION.md
│   ├── CHANGELOG.md                       ← UN SEUL fichier consolidé
│   └── technical/
│       ├── ALIGNMENT_FIX_REPORT.md
│       ├── SIMPLIFICATION_OUTPUTS.md
│       └── REFACTORING_PLAN_REVISED.md
│
├── 📁 data/
│   ├── input/
│   └── output/
│
├── 📁 tools/
│   └── poppler-26.02.0/
│
├── 📄 .gitignore                          ← Mis à jour
├── 📄 README.md                           ← Documentation principale
├── 📄 pyproject.toml                      ← NOUVEAU (PEP 621)
├── 📄 requirements.txt                    ← Conservé pour compatibilité
└── 📄 extract_specifications_production.py ← Symlink vers src/pdf_extraction/

📁 archive/                                ← HORS GIT (ou branche séparée)
└── abandoned/
    └── (code obsolète, à purger après validation)
```

---

## 📊 LISTE DÉTAILLÉE DES FICHIERS À TRAITER

### 🔵 GROUPE 1: EXTRACTEURS DE SPÉCIFICATIONS (RACINE)

| Fichier | Fonction | Décision | Justification |
|---------|----------|----------|---------------|
| **extract_specifications_production.py** | Extraction V2 Y-based (UTILISÉ par src/main.py) | ✅ **GARDER** (symlink) | Version production active, utilisée par main.py |
| extract_specifications_v2_strict.py | Version V2 stricte | 🔄 **ARCHIVER** | Doublon de production.py, même algorithme |
| extract_specifications_v3_generalized.py | V3 multi-tables (ÉCHOUE sur tableaux continus) | 🔄 **ARCHIVER** | Approche abandonnée, documentée comme non fonctionnelle dans V3_DIAGNOSIS_FINAL.md |

**Action:** 
- `extract_specifications_production.py` → Créer symlink à la racine vers `src/pdf_extraction/extractors/specifications_production.py`
- Les 2 autres → `archive/abandoned/extractors/`

---

### 🔵 GROUPE 2: EXTRACTEURS COLONNE 2 (src/) - **10 FICHIERS**

| Fichier | Date dernier commit | Utilisé? | Décision |
|---------|---------------------|----------|----------|
| **second_column_extractor.py** | Récent | ✅ Oui (main_specifications.py) | ✅ **GARDER** |
| column2_extractor_fixed.py | Ancien | ❌ Non | 🔄 **ARCHIVER** |
| column2_extractor_v2.py | Ancien | ❌ Non | 🔄 **ARCHIVER** |
| column2_final.py | Ancien | ❌ Non | 🔄 **ARCHIVER** |
| extract_column2_final_v3.py | Ancien | ❌ Non | 🔄 **ARCHIVER** |
| extract_column2_from_cibles.py | Ancien | ❌ Non | 🔄 **ARCHIVER** |
| extract_column2_improved.py | Ancien | ❌ Non | 🔄 **ARCHIVER** |
| extract_column2_simple.py | Ancien | ❌ Non | 🔄 **ARCHIVER** |
| extract_specifications_final.py | Ancien | ❌ Non | 🔄 **ARCHIVER** |
| extract_specifications_grid_based.py | Ancien | ❌ Non | 🔄 **ARCHIVER** |
| extract_specifications_robust.py | Ancien | ❌ Non | 🔄 **ARCHIVER** |

**Action:** 
- `second_column_extractor.py` → `src/pdf_extraction/extractors/`
- Les 10 autres → `archive/abandoned/extractors/column2_iterations/`

**Justification:** Ces fichiers représentent des itérations de développement. Le seul fonctionnel est `second_column_extractor.py` (utilisé par `main_specifications.py`).

---

### 🔵 GROUPE 3: EXTRACTEURS GRID-BASED (src/)

| Fichier | Fonction | Utilisé? | Décision |
|---------|----------|----------|----------|
| **column_extractor.py** | Grid-based + utilitaires (to_json, verify_tesseract) | ✅ Oui (main.py) | ✅ **GARDER** |

**Action:** `column_extractor.py` → `src/pdf_extraction/extractors/`

**Justification:** Utilisé activement par `main.py`, contient fonctions utilitaires critiques.

---

### 🔵 GROUPE 4: PAGE SELECTORS (src/)

| Fichier | Fonction | Utilisé? | Décision |
|---------|----------|----------|----------|
| **page_selector.py** | Sélection pages (PRODUCTION) | ✅ Oui | ✅ **GARDER** |
| page_selector_debug.py | Version debug avec logs détaillés | ❌ Non | 🔄 **ARCHIVER** |
| page_selector_robust.py | Version robuste (fusionnée dans page_selector.py) | ❌ Non | 🔄 **ARCHIVER** |

**Action:**
- `page_selector.py` → `src/pdf_extraction/core/`
- Les 2 autres → `archive/abandoned/selectors/`

---

### 🔵 GROUPE 5: SCRIPTS DE VÉRIFICATION (RACINE) - **6 FICHIERS**

| Fichier | Fonction | Utile? | Décision |
|---------|----------|--------|----------|
| check_extraction.py | Vérifie extraction.json | ✅ Utile debug | 🔄 **DÉPLACER** → `scripts/debug/` |
| compare_alignment.py | Compare avant/après fix alignement | ❌ Historique | 🔄 **ARCHIVER** |
| debug_alignment.py | Debug Y-based pairing | ❌ Historique | 🔄 **ARCHIVER** |
| validate_specifications_extraction.py | Validation manuelle | ❌ Redondant | 🔄 **ARCHIVER** |
| verify_output.py | Vérification sortie (racine) | ❌ Doublon scripts/ | 🔄 **ARCHIVER** |
| verify_v3_output.py | Vérification V3 | ❌ V3 abandonnée | 🔄 **ARCHIVER** |

**Action:**
- `check_extraction.py` → `scripts/debug/` (OUTIL ACTIF)
- Les 5 autres → `archive/abandoned/verification/` (HISTORIQUE)

---

### 🔵 GROUPE 6: SCRIPTS DANS scripts/ - **25 FICHIERS**

#### 6A: Scripts Production (GARDER)

| Fichier | Fonction | Décision |
|---------|----------|----------|
| generate_extraction_report.py | Génère rapports | ✅ **GARDER** → `scripts/production/` |
| show_specifications.py | Affiche spécifications | ✅ **GARDER** → `scripts/production/` |
| inspect_selection.py | Inspecte sélection pages | ✅ **GARDER** → `scripts/production/` |

#### 6B: Scripts Debug Actifs (GARDER dans scripts/debug/)

| Fichier | Fonction | Encore utilisé? | Décision |
|---------|----------|-----------------|----------|
| visualize_table_structure.py | Visualise structure tableau | ✅ Oui | ✅ **GARDER** → `scripts/debug/` |
| detect_table_grid.py | Détecte grille tableau | ✅ Oui | ✅ **GARDER** → `scripts/debug/` |
| debug_column_detection.py | Debug détection colonnes | ⚠️ Peut-être | ⚠️ **À VALIDER** |

**QUESTION CRITIQUE:** Parmi les 22 autres scripts debug/test/analyze dans `scripts/`, lesquels utilisez-vous encore régulièrement? Je dois voir le contenu pour décider.

#### 6C: Scripts Historiques (ARCHIVER)

Tous les scripts `scripts/` non listés en 6A/6B qui sont :
- Des explorations ponctuelles (test_on_first_pdf.py)
- Des analyses one-shot (analyze_*.py historiques)
- Des tests manuels non formalisés (test_*.py sans assertions)

→ `archive/abandoned/scripts/`

---

### 🔵 GROUPE 7: SCRIPTS D'INSTALLATION - **11 FICHIERS**

| Fichier | Plateforme | Redondant? | Décision |
|---------|-----------|------------|----------|
| setup_tesseract.py | Cross-platform | Non | ✅ **GARDER** → `scripts/setup/` |
| INSTALL_TESSERACT.bat | Windows | Non | ✅ **GARDER** → `scripts/setup/` |
| install_tesseract.ps1 | Windows | ✅ Doublon .bat | ❌ **SUPPRIMER** |
| INSTALL_FRA.bat | Windows | Non | ✅ **GARDER** → `scripts/setup/` |
| install_fra.ps1 | Windows | ✅ Doublon .bat | ❌ **SUPPRIMER** |
| install_fra.vbs | Windows | ✅ Complexe inutile | ❌ **SUPPRIMER** |
| COPY_FRA_TRAINEDDATA.bat | Windows | Non | ✅ **GARDER** → `scripts/setup/` |
| copy_fra_traineddata.ps1 | Windows | ✅ Doublon .bat | ❌ **SUPPRIMER** |
| MOVE_FRA_TRAINEDDATA.bat | Windows | Non | 🔄 **FUSIONNER** avec COPY |
| move_fra_traineddata.py | Cross-platform | Non | ✅ **GARDER** → `scripts/setup/` |
| RUN_INSTALL_FRA_AS_ADMIN.bat | Windows | ✅ Complexe inutile | ❌ **SUPPRIMER** |

**Action:**
- Garder: 5 fichiers (setup_tesseract.py, INSTALL_*.bat, move_fra_traineddata.py, COPY_FRA.bat fusionné)
- Supprimer: 6 fichiers (tous les .ps1, .vbs, RUN_INSTALL)

---

### 🔵 GROUPE 8: DOCUMENTATION - **35 FICHIERS MARKDOWN**

#### 8A: Documentation Principale (GARDER à la racine ou docs/)

| Fichier | Emplacement | Décision |
|---------|-------------|----------|
| README.md | Racine | ✅ **GARDER** racine |
| CHANGELOG.md | À créer | ✅ **CRÉER** dans docs/ |
| QUICK_START.md | → docs/ | ✅ **DÉPLACER** |
| INDEX_DOCUMENTATION.md | → docs/ | ✅ **DÉPLACER** |

#### 8B: Documentation Technique (GARDER dans docs/technical/)

| Fichier | Raison | Décision |
|---------|--------|----------|
| ALIGNMENT_FIX_REPORT.md | Explique bug majeur corrigé | ✅ **GARDER** → `docs/technical/` |
| SIMPLIFICATION_OUTPUTS.md | Explique simplification récente | ✅ **GARDER** → `docs/technical/` |
| SIMPLIFICATION_COMPLETE.md | Confirmation simplification | ✅ **GARDER** → `docs/technical/` |
| CLEANUP_RECOMMENDATIONS.md | Guide nettoyage | ✅ **GARDER** → `docs/technical/` |
| REFACTORING_PLAN_REVISED.md | Ce document | ✅ **GARDER** → `docs/technical/` |

#### 8C: Rapports à FUSIONNER dans CHANGELOG.md (27 fichiers)

**Rapports d'implémentation (chronologique):**
1. AGENT_MISSION_COMPLETE.md
2. COLUMN_EXTRACTION_PLAN.md
3. COLUMN2_EXTRACTION_FINAL.md
4. COLUMN2_EXTRACTION_v3_FINAL.md
5. DELIVERABLE_SUMMARY.md
6. DELIVERABLES.md
7. EXTRACTION_SPECIFICATIONS_FINAL_REPORT.md
8. EXTRACTION_SPECIFICATIONS_PRODUCTION.md
9. EXTRACTION_SPECIFICATIONS_V2_STRICT_REPORT.md
10. FINAL_DELIVERY_SUMMARY.md
11. IMPLEMENTATION_SUMMARY_COLUMN2.md
12. IMPLEMENTATION_SUMMARY.md
13. SESSION_STATUS_V3_START.md
14. STATUS_COLUMN2_COMPLETE.md
15. TASK_5_COMPLETION_SUMMARY.md
16. SIMPLIFICATION_SUMMARY.md

**Rapports techniques:**
17. REFACTORING_DETECTION_DIRECTE.md
18. REFACTORING_REPORT.md
19. REGRESSION_ANALYSIS.md
20. REQUIREMENTS_CHECKLIST.md
21. SECOND_COLUMN_EXTRACTION.md (⚠️ Peut-être à garder séparément? Vérifier utilité)
22. V3_ARCHITECTURE_PLAN.md
23. V3_DIAGNOSIS_FINAL.md

**Fichiers git/config:**
24. .gitignore_changes.md
25. GITIGNORE_SUMMARY.md
26. README_SPECIFICATIONS_EXTRACTION.md

**Action:** Extraire les informations importantes de ces 27 fichiers, créer un CHANGELOG.md chronologique structuré, puis ARCHIVER les sources.

---

### 🔵 GROUPE 9: FICHIERS TEMPORAIRES/DEBUG

| Fichier | Type | Décision |
|---------|------|----------|
| debug_column2_visual_page1.png | Image debug | ❌ **SUPPRIMER** |
| debug_pages.txt | Log auto-généré | ❌ **SUPPRIMER** (déjà dans .gitignore) |

---

### 🔵 GROUPE 10: TESTS

| Fichier | Type | Décision |
|---------|------|----------|
| tests/test_local_page_selection.py | Test intégration | ✅ **RENOMMER** → `test_page_selection.py` + déplacer `tests/integration/` |
| tests/test_direct_detection.py | Test intégration | ✅ **GARDER** → `tests/integration/` |
| tests/test_robustness.py | Test intégration | ✅ **GARDER** → `tests/integration/` |

---

## 📋 RÉSUMÉ DES ACTIONS

### Comptage par Action

| Action | Python | Markdown | Batch/PS1 | Images | Total |
|--------|--------|----------|-----------|--------|-------|
| ✅ **GARDER (réorganiser)** | 15 | 8 | 5 | 0 | **28** |
| 🔄 **ARCHIVER (git mv)** | 30 | 27 | 0 | 0 | **57** |
| ❌ **SUPPRIMER (immédiat)** | 0 | 0 | 6 | 2 | **8** |
| ⚠️ **À VALIDER** | 20 | 0 | 0 | 0 | **20** |

### Fichiers Nécessitant Validation (scripts/)

Les **20 scripts** dans `scripts/` non classés dans les catégories ci-dessus nécessitent votre validation :

```
scripts/analyze_detection.py
scripts/analyze_separators_detailed.py
scripts/analyze_vertical_lines.py
scripts/check_pages.py
scripts/compare_selectors.py
scripts/debug_column2_structure.py
scripts/debug_detection.py
scripts/debug_page4.py
scripts/debug_prose.py
scripts/debug_regex.py
scripts/detailed_analysis.py
scripts/detailed_new_analysis.py
scripts/find_missing_pages.py
scripts/test_column_extraction.py
scripts/test_column2_debug.py
scripts/test_on_first_pdf.py
scripts/test_second_column.py
scripts/validate_column2_extraction.py
scripts/verify_output.py (doublon racine)
```

**QUESTION:** Lesquels de ces scripts utilisez-vous encore régulièrement pour le debug? Les autres seront archivés.

---

## 🔧 AJOUTS AU PLAN

### 1. Créer pyproject.toml (PEP 621)

```toml
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
authors = [
    {name = "GCT - Division Informatique"}
]
keywords = ["pdf", "ocr", "extraction", "tesseract"]

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
dev = [
    "pytest>=7.4.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.5.0",
]

[project.scripts]
pdf-extract = "pdf_extraction.main:main"
pdf-extract-specs = "pdf_extraction.main_specifications:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

[tool.black]
line-length = 100
target-version = ["py310"]

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
```

### 2. Mise à jour .gitignore

Ajouter:
```gitignore
# Archive (ne pas versionner après validation)
archive/

# Fichiers temporaires générés
debug_pages.txt
debug_*.png
*.tmp
```

### 3. Créer scripts/setup/README.md

Documentation pour les scripts d'installation avec instructions claires.

---

## ⚠️ POINTS DE VALIDATION CRITIQUE

### ❓ Questions avant exécution:

1. **Scripts dans scripts/ (20 fichiers):** Lesquels utilisez-vous encore? → Liste ci-dessus
2. **SECOND_COLUMN_EXTRACTION.md:** Ce rapport fait 30+ pages. Le garder séparément dans `docs/` ou fusionner dans CHANGELOG?
3. **archive/abandoned/:** Voulez-vous le garder dans le repo (temporairement) ou créer une branche séparée `archive` immédiatement?
4. **Symlink extract_specifications_production.py:** Garder à la racine pour compatibilité ou forcer mise à jour des imports?

### ✅ Confirmations nécessaires:

- [ ] Structure `src/pdf_extraction/` validée
- [ ] Séparation `tests/unit/` et `tests/integration/` validée
- [ ] Liste des 28 fichiers à garder validée
- [ ] Liste des 8 fichiers à supprimer validée
- [ ] Plan pour les 57 fichiers à archiver validé
- [ ] Validation des 20 scripts `scripts/` en attente

---

## 🎯 PLAN D'EXÉCUTION (après validation)

### Phase 0: Préparation
```bash
git add -A
git commit -m "Backup complet avant refactoring structurel"
git checkout -b refactoring-structural
```

### Phase 1: Créer structure
```bash
# Créer arborescence (sans supprimer l'ancienne)
mkdir -p src/pdf_extraction/{core,extractors,utils}
mkdir -p tests/{unit,integration}
mkdir -p scripts/{production,debug,setup}
mkdir -p docs/{technical,archive}
mkdir -p archive/abandoned

# Créer __init__.py
touch src/pdf_extraction/__init__.py
touch src/pdf_extraction/{core,extractors,utils}/__init__.py
touch tests/__init__.py
touch tests/{unit,integration}/__init__.py
```

### Phase 2: Déplacements (git mv)
```bash
# src/ → src/pdf_extraction/
git mv src/main.py src/pdf_extraction/
git mv src/pdf_reader.py src/pdf_extraction/core/
# ... (liste complète après validation)

# Créer symlink pour compatibilité
ln -s src/pdf_extraction/extractors/extract_specifications_production.py extract_specifications_production.py
```

### Phase 3: Archivage (git mv, PAS rm)
```bash
# Archiver code obsolète
git mv src/column2_extractor_fixed.py archive/abandoned/extractors/
# ... (tous les fichiers à archiver)
```

### Phase 4: Suppressions (après validation période test)
```bash
# Supprimer fichiers temporaires/doublons uniquement
rm debug_column2_visual_page1.png
rm *.ps1  # Doublons des .bat
# ... (liste validée uniquement)
```

### Phase 5: Documentation
```bash
# Créer CHANGELOG.md (fusion manuelle)
# Déplacer docs
git mv QUICK_START.md docs/
git mv ALIGNMENT_FIX_REPORT.md docs/technical/
# ...
```

### Phase 6: Configuration
```bash
# Créer pyproject.toml
# Mettre à jour .gitignore
# Créer scripts/setup/README.md
```

### Phase 7: Tests
```bash
# Installer en mode dev
pip install -e .

# Tester
python -m pdf_extraction.main
pytest tests/

# Vérifier extraction
cat data/output/extraction.json
```

---

## 📝 NOTES FINALES

1. **Toutes les actions utilisent `git mv`** pour conserver l'historique
2. **Aucune suppression avant validation** de la période de test (2 semaines recommandées)
3. **archive/abandoned/ sera purgé** après validation que rien ne casse
4. **Les imports seront mis à jour** automatiquement avec un script de migration
5. **pyproject.toml rend le package installable** avec `pip install -e .`

---

## ✋ EN ATTENTE DE VOTRE VALIDATION

**Avant de continuer, j'ai besoin de:**

1. ✅ Validation de la structure finale ci-dessus
2. ⚠️ **Liste des 20 scripts `scripts/` que vous utilisez encore** (voir section Groupe 6)
3. ⚠️ **Décision sur SECOND_COLUMN_EXTRACTION.md** (garder séparé ou fusionner?)
4. ⚠️ **Décision sur archive/abandoned/** (dans repo temporairement ou branche séparée?)

**Merci de me donner ces validations avant que je procède aux déplacements.**

---

**Fin du plan révisé - En attente de validation**
