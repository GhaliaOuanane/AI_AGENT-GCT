# 📋 DÉCISIONS FINALES DE REFACTORING

**Date:** 2026-07-12  
**Status:** EN ATTENTE DE VALIDATION UTILISATEUR

---

## ✅ STRUCTURE VALIDÉE

```
AI_AGENT_GCT/
├── src/pdf_extraction/              ← Package Python
│   ├── __init__.py
│   ├── core/                        ← Modules de base
│   ├── extractors/                  ← Extracteurs
│   └── utils/                       ← Utilitaires
├── tests/
│   ├── unit/                        ← Tests unitaires
│   └── integration/                 ← Tests d'intégration
├── scripts/
│   ├── production/                  ← Scripts opérationnels
│   ├── debug/                       ← Outils debug actifs (pas historique)
│   └── setup/                       ← Installation
├── docs/
│   ├── technical/                   ← Documentation technique
│   └── CHANGELOG.md                 ← UN SEUL fichier consolidé
├── data/
├── tools/
├── README.md
├── pyproject.toml
├── requirements.txt
└── .gitignore
```

**archive/** sera HORS GIT (ou branche séparée après validation)

---

## 📊 ANALYSE AUTOMATIQUE DES SCRIPTS

### Résultat de l'analyse d'utilisation:

**✅ Scripts avec références (utilisés):** 25/26 (96%)
**⚠️ Scripts sans référence (obsolètes):** 1/26 (4%)

### Scripts Production (3 - documentés, réutilisables)

| Script | Références | Lignes | Décision |
|--------|------------|--------|----------|
| generate_extraction_report.py | 6 | 84 | ✅ **scripts/production/** |
| show_specifications.py | 7 | 91 | ✅ **scripts/production/** |
| inspect_selection.py | 3 | 37 | ✅ **scripts/production/** |

### Scripts Debug Actifs (2 - encore utilisés pour debug)

| Script | Fonction | Décision |
|--------|----------|----------|
| detect_table_grid.py | Détecte grille tableau | ✅ **scripts/debug/** (ACTIF) |
| visualize_table_structure.py | Visualise structure | ✅ **scripts/debug/** (ACTIF) |

### Scripts à Archiver (21 - historiques/ponctuels)

**Tous les autres scripts** (analyze_*, debug_*, test_*, etc.) → **archive/abandoned/scripts/**

Raison: Utilisés ponctuellement pendant développement, pas de valeur opérationnelle continue.

---

## 📝 DÉCISIONS PAR GROUPE

### GROUPE 1: Extracteurs Racine

| Fichier | Décision | Justification |
|---------|----------|---------------|
| extract_specifications_production.py | ✅ **Symlink racine** → src/pdf_extraction/extractors/ | Version production, créer symlink pour compatibilité |
| extract_specifications_v2_strict.py | 🔄 **archive/abandoned/** | Doublon de production.py |
| extract_specifications_v3_generalized.py | 🔄 **archive/abandoned/** | Approche abandonnée (V3_DIAGNOSIS_FINAL.md) |

### GROUPE 2: Extracteurs src/ (11 fichiers)

**GARDER (2):**
- ✅ `column_extractor.py` → `src/pdf_extraction/extractors/`
- ✅ `second_column_extractor.py` → `src/pdf_extraction/extractors/`

**ARCHIVER (9):**
- 🔄 `column2_extractor_*.py` (3 fichiers) → `archive/abandoned/extractors/`
- 🔄 `extract_column2_*.py` (5 fichiers) → `archive/abandoned/extractors/`
- 🔄 `extract_specifications_*.py` (3 fichiers sauf main) → `archive/abandoned/extractors/`

### GROUPE 3: Page Selectors (3 fichiers)

**GARDER (1):**
- ✅ `page_selector.py` → `src/pdf_extraction/core/`

**ARCHIVER (2):**
- 🔄 `page_selector_debug.py` → `archive/abandoned/`
- 🔄 `page_selector_robust.py` → `archive/abandoned/`

### GROUPE 4: Scripts Vérification Racine (6 fichiers)

**GARDER (1 - outil actif):**
- ✅ `check_extraction.py` → `scripts/debug/` (OUTIL ACTIF)

**ARCHIVER (5 - historiques):**
- 🔄 `compare_alignment.py` → `archive/abandoned/`
- 🔄 `debug_alignment.py` → `archive/abandoned/`
- 🔄 `validate_specifications_extraction.py` → `archive/abandoned/`
- 🔄 `verify_output.py` → `archive/abandoned/`
- 🔄 `verify_v3_output.py` → `archive/abandoned/`

### GROUPE 5: Scripts Installation (11 fichiers)

**GARDER (5):**
- ✅ `setup_tesseract.py` → `scripts/setup/`
- ✅ `INSTALL_TESSERACT.bat` → `scripts/setup/`
- ✅ `INSTALL_FRA.bat` → `scripts/setup/`
- ✅ `COPY_FRA_TRAINEDDATA.bat` → `scripts/setup/` (fusionner avec MOVE)
- ✅ `move_fra_traineddata.py` → `scripts/setup/`

**SUPPRIMER (6 - doublons .ps1/.vbs):**
- ❌ `install_tesseract.ps1` (doublon .bat)
- ❌ `install_fra.ps1` (doublon .bat)
- ❌ `install_fra.vbs` (complexe inutile)
- ❌ `copy_fra_traineddata.ps1` (doublon .bat)
- ❌ `MOVE_FRA_TRAINEDDATA.bat` (fusionner dans COPY)
- ❌ `RUN_INSTALL_FRA_AS_ADMIN.bat` (complexe inutile)

### GROUPE 6: Documentation (35 fichiers)

**GARDER (8):**
- ✅ README.md (racine)
- ✅ CHANGELOG.md (à créer, fusion de 27 rapports)
- ✅ QUICK_START.md → `docs/`
- ✅ INDEX_DOCUMENTATION.md → `docs/`
- ✅ ALIGNMENT_FIX_REPORT.md → `docs/technical/`
- ✅ SIMPLIFICATION_OUTPUTS.md → `docs/technical/`
- ✅ SIMPLIFICATION_COMPLETE.md → `docs/technical/`
- ✅ CLEANUP_RECOMMENDATIONS.md → `docs/technical/`

**FUSIONNER dans CHANGELOG.md puis ARCHIVER (27 fichiers):**

Tous les rapports de status/summary/completion/plan/diagnosis → Extraire infos importantes → CHANGELOG.md chronologique → Archiver sources

**CAS SPÉCIAL: SECOND_COLUMN_EXTRACTION.md (30+ pages)**

⚠️ **DÉCISION REQUISE:** Ce rapport est une documentation technique complète, pas un rapport de status.

**Options:**
1. **Garder séparément** dans `docs/technical/` (recommandé si utilisé comme référence)
2. **Fusionner sections pertinentes** dans CHANGELOG + garder version complète dans `docs/technical/`
3. **Archiver** si obsolète

**Recommandation:** Garder dans `docs/technical/` car c'est une documentation fonctionnelle, pas un rapport historique.

### GROUPE 7: Fichiers Temporaires

**SUPPRIMER:**
- ❌ `debug_column2_visual_page1.png`
- ❌ `debug_pages.txt` (déjà dans .gitignore, auto-généré)

---

## 🎯 COMPTAGE FINAL

| Action | Python | Markdown | Batch/PS1 | Images | Total |
|--------|--------|----------|-----------|--------|-------|
| **GARDER (réorganiser)** | 15 | 9 | 5 | 0 | **29** |
| **ARCHIVER (git mv)** | 35 | 26 | 0 | 0 | **61** |
| **SUPPRIMER (immédiat)** | 0 | 0 | 6 | 2 | **8** |
| **CRÉER (nouveau)** | 7 __init__.py | 1 CHANGELOG | 1 pyproject.toml | 0 | **9** |

---

## ⚙️ FICHIERS À CRÉER

### 1. pyproject.toml (racine)

Package Python installable avec `pip install -e .`

### 2. CHANGELOG.md (docs/)

Fusion chronologique de:
- AGENT_MISSION_COMPLETE.md
- COLUMN_EXTRACTION_PLAN.md
- COLUMN2_EXTRACTION_FINAL.md
- STATUS_COLUMN2_COMPLETE.md
- V3_DIAGNOSIS_FINAL.md
- ALIGNMENT_FIX_REPORT.md (référence, pas fusion)
- SIMPLIFICATION_OUTPUTS.md (référence)
- Tous les autres rapports status/summary

**Structure proposée:**
```markdown
# CHANGELOG

## [1.0.0] - 2026-07-12 - Refactoring Structurel
- Réorganisation complète du projet en package Python
- ...

## [0.9.0] - 2026-07-11 - Simplification des Sorties
- Suppression de tous les fichiers de sortie sauf extraction.json
- ...

## [0.8.0] - 2026-07-XX - Correction Alignement Y-based
- Fix bug alignement colonnes (ALIGNMENT_FIX_REPORT.md)
- ...

## [0.7.0] - 2026-07-XX - Extraction V3 (abandonnée)
- Tentative approche multi-tables (V3_DIAGNOSIS_FINAL.md)
- ...

## [0.6.0] - 2026-XX-XX - Extraction 2e Colonne
- Implémentation second_column_extractor.py
- ...

## [0.5.0] - 2026-XX-XX - Extraction V2 Production
- Version finale ratio-based extraction
- ...
```

### 3. __init__.py (7 fichiers)

- `src/pdf_extraction/__init__.py`
- `src/pdf_extraction/core/__init__.py`
- `src/pdf_extraction/extractors/__init__.py`
- `src/pdf_extraction/utils/__init__.py`
- `tests/__init__.py`
- `tests/unit/__init__.py`
- `tests/integration/__init__.py`

### 4. scripts/setup/README.md

Documentation des scripts d'installation avec instructions claires.

### 5. .gitignore (mise à jour)

Ajouter:
```gitignore
# Archive (temporaire, à purger après validation)
archive/

# Fichiers temporaires
debug_pages.txt
debug_*.png
```

---

## 🚀 ORDRE D'EXÉCUTION (après validation)

### Étape 1: Backup et Branche
```bash
git add -A
git commit -m "Backup complet avant refactoring structurel"
git checkout -b refactoring-structural
```

### Étape 2: Créer Structure (SANS toucher à l'ancienne)
```bash
mkdir -p src/pdf_extraction/{core,extractors,utils}
mkdir -p tests/{unit,integration}
mkdir -p scripts/{production,debug,setup}
mkdir -p docs/technical
mkdir -p archive/abandoned/{extractors,scripts,selectors}

# Créer __init__.py
for dir in src/pdf_extraction{,/core,/extractors,/utils} tests{,/unit,/integration}; do
    touch $dir/__init__.py
done
```

### Étape 3: Déplacements avec git mv (conservation historique)
```bash
# Exemple: déplacer les fichiers principaux
git mv src/main.py src/pdf_extraction/
git mv src/pdf_reader.py src/pdf_extraction/core/
# ... (liste complète après validation)
```

### Étape 4: Archivage (git mv vers archive/)
```bash
# Archiver code obsolète
git mv src/column2_extractor_fixed.py archive/abandoned/extractors/
# ... (tous les fichiers listés dans GROUPE 2-4)
```

### Étape 5: Suppressions (APRÈS validation période test)
```bash
# Supprimer uniquement fichiers temporaires et doublons .ps1
rm debug_column2_visual_page1.png
rm install_tesseract.ps1
rm install_fra.ps1
rm install_fra.vbs
rm copy_fra_traineddata.ps1
rm RUN_INSTALL_FRA_AS_ADMIN.bat
```

### Étape 6: Créer Fichiers Config
```bash
# Créer pyproject.toml
# Créer docs/CHANGELOG.md
# Créer scripts/setup/README.md
# Mettre à jour .gitignore
```

### Étape 7: Mise à Jour Imports
```bash
# Script automatique de mise à jour des imports
python scripts/setup/migrate_imports.py
```

### Étape 8: Symlinks Compatibilité
```bash
# Créer symlink pour extract_specifications_production.py
ln -s src/pdf_extraction/extractors/extract_specifications_production.py extract_specifications_production.py
```

### Étape 9: Tests
```bash
# Installer en mode dev
pip install -e .

# Tester extraction
python -m pdf_extraction.main

# Tests unitaires
pytest tests/

# Vérifier sortie
cat data/output/extraction.json
```

### Étape 10: Commit et Merge
```bash
git add -A
git commit -m "Refactoring structurel: package Python + organisation claire"
git checkout main
git merge refactoring-structural
```

### Étape 11: Nettoyage Final (après 2 semaines validation)
```bash
# Supprimer archive/ ou la déplacer vers branche séparée
git checkout -b archive-historique
git mv archive/ .
git add -A
git commit -m "Archive historique du code obsolète"
git checkout main
git rm -rf archive/
git commit -m "Suppression archive après période de validation"
```

---

## ⚠️ VALIDATION FINALE REQUISE

### Questions restantes:

1. **SECOND_COLUMN_EXTRACTION.md:** Garder dans `docs/technical/` ou fusionner dans CHANGELOG?
   - ✅ Recommandation: **GARDER séparément** (documentation fonctionnelle)

2. **archive/abandoned/:** Dans repo temporairement (2 semaines) ou branche séparée immédiatement?
   - ✅ Recommandation: **Dans repo 2 semaines** puis branche séparée

3. **pyproject.toml:** Créer ou rester avec requirements.txt seul?
   - ✅ Recommandation: **CRÉER** (norme PEP 621, installable)

4. **Migration imports:** Automatique ou manuelle?
   - ✅ Recommandation: **Script automatique** puis validation manuelle

### Checklist validation:

- [ ] Structure `src/pdf_extraction/` avec __init__.py validée
- [ ] Séparation `tests/unit/` et `tests/integration/` validée
- [ ] Liste des 29 fichiers à garder validée
- [ ] Liste des 8 fichiers à supprimer validée
- [ ] Plan des 61 fichiers à archiver validé
- [ ] Décision sur SECOND_COLUMN_EXTRACTION.md prise
- [ ] Décision sur archive/ prise
- [ ] Ordre d'exécution validé

---

## 📞 PRÊT À EXÉCUTER

Une fois toutes les validations ci-dessus confirmées, je peux:

1. ✅ Créer la structure complète
2. ✅ Effectuer tous les déplacements (git mv)
3. ✅ Créer les fichiers de configuration
4. ✅ Mettre à jour les imports
5. ✅ Tester le projet
6. ✅ Générer le rapport final

**Attendant vos confirmations finales avant de procéder.**

---

**Fin des décisions finales**
