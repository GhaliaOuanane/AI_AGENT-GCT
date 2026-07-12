# 📊 RAPPORT D'ANALYSE STRUCTURELLE DU PROJET

**Date:** 2026-07-12  
**Analyste:** Ingénieur Logiciel Senior  
**Objectif:** Nettoyage et refactoring structurel sans modification fonctionnelle

---

## 📁 ÉTAT ACTUEL DU PROJET

### Structure Actuelle
```
AI_AGENT GCT/
├── Fichiers Python racine: 9 fichiers
├── Fichiers Markdown racine: 35 fichiers
├── Scripts Batch/PowerShell: 11 fichiers
├── Scripts divers: 3 fichiers
├── src/: 24 fichiers Python
├── scripts/: 25 fichiers Python
├── tests/: 3 fichiers Python
└── Total: ~110 fichiers (hors .git, .venv, tools)
```

---

## 🔍 ANALYSE DES DOUBLONS

### 1. Scripts d'Extraction (RACINE) - **3 DOUBLONS IDENTIFIÉS**

| Fichier | Taille | Fonction | Status | Justification |
|---------|--------|----------|--------|---------------|
| `extract_specifications_production.py` | Production | Extraction V2 Y-based (utilisé par src/main.py) | **✅ GARDER** | **Version finale fonctionnelle** utilisée activement |
| `extract_specifications_v2_strict.py` | Ancienne V2 | Extraction stricte (DOUBLON) | **❌ SUPPRIMER** | Doublon de extract_specifications_production.py |
| `extract_specifications_v3_generalized.py` | V3 abandonnée | Approche multi-tables (ne fonctionne pas) | **❌ SUPPRIMER** | Version abandonnée, documentée comme non fonctionnelle |

**Recommandation:** Garder uniquement `extract_specifications_production.py`, déplacer les 2 autres vers `archive/abandoned/`

---

### 2. Scripts de Vérification (RACINE) - **6 DOUBLONS IDENTIFIÉS**

| Fichier | Fonction | Status | Justification |
|---------|----------|--------|---------------|
| `check_extraction.py` | Vérifie extraction.json | **🔄 DÉPLACER** | → `scripts/debug/` (utile pour debug) |
| `compare_alignment.py` | Compare avant/après alignment fix | **🔄 DÉPLACER** | → `scripts/debug/` (historique) |
| `debug_alignment.py` | Debug Y-based pairing | **🔄 DÉPLACER** | → `scripts/debug/` (historique) |
| `validate_specifications_extraction.py` | Validation manuelle | **❌ SUPPRIMER** | Redondant avec check_extraction.py |
| `verify_output.py` | Vérification sortie | **❌ SUPPRIMER** | Doublon dans scripts/ |
| `verify_v3_output.py` | Vérification V3 | **❌ SUPPRIMER** | V3 abandonnée |

**Recommandation:** Créer `scripts/debug/` et y déplacer les 3 premiers, supprimer les 3 derniers

---

### 3. Extracteurs de Colonne (src/) - **10 DOUBLONS IDENTIFIÉS**

| Fichier | Fonction | Status | Justification |
|---------|----------|--------|---------------|
| `column_extractor.py` | Extraction grid-based (ancien) | **✅ GARDER** | Contient fonctions utilitaires (to_json, verify_tesseract) utilisées par main.py |
| `second_column_extractor.py` | Extraction 2e colonne K-means | **✅ GARDER** | Version fonctionnelle pour tableaux 3 colonnes |
| `column2_extractor_fixed.py` | Tentative fix colonne 2 | **❌ SUPPRIMER** | Obsolète |
| `column2_extractor_v2.py` | V2 colonne 2 | **❌ SUPPRIMER** | Obsolète |
| `column2_final.py` | Version "finale" colonne 2 | **❌ SUPPRIMER** | Remplacée par second_column_extractor.py |
| `extract_column2_final_v3.py` | V3 colonne 2 | **❌ SUPPRIMER** | Obsolète |
| `extract_column2_from_cibles.py` | Extraction depuis cibles | **❌ SUPPRIMER** | Obsolète |
| `extract_column2_improved.py` | Version améliorée | **❌ SUPPRIMER** | Obsolète |
| `extract_column2_simple.py` | Version simple | **❌ SUPPRIMER** | Obsolète |
| `extract_specifications_final.py` | Specs final | **❌ SUPPRIMER** | Redondant |
| `extract_specifications_grid_based.py` | Grid-based | **❌ SUPPRIMER** | Remplacé par column_extractor.py |
| `extract_specifications_robust.py` | Robust | **❌ SUPPRIMER** | Obsolète |

**Recommandation:** Garder uniquement `column_extractor.py` et `second_column_extractor.py`, supprimer les 10 autres

---

### 4. Page Selectors (src/) - **2 DOUBLONS IDENTIFIÉS**

| Fichier | Fonction | Status | Justification |
|---------|----------|--------|---------------|
| `page_selector.py` | Sélection de pages (production) | **✅ GARDER** | Version de production |
| `page_selector_debug.py` | Version debug avec logs | **🔄 DÉPLACER** | → `scripts/debug/` (historique) |
| `page_selector_robust.py` | Version robuste | **❌ SUPPRIMER** | Fusionnée dans page_selector.py |

**Recommandation:** Garder `page_selector.py`, déplacer `page_selector_debug.py`, supprimer `page_selector_robust.py`

---

### 5. Scripts Main (src/) - **1 DOUBLON IDENTIFIÉ**

| Fichier | Fonction | Status | Justification |
|---------|----------|--------|---------------|
| `main.py` | **Script principal de production** | **✅ GARDER** | Point d'entrée officiel (extraction.json) |
| `main_specifications.py` | Script extraction 2e colonne | **✅ GARDER** | Cas d'usage différent (spécifications) |
| `extract_specifications_main.py` | Utilitaires specs | **✅ GARDER** | Module utilitaire utilisé par main_specifications.py |

**Recommandation:** Garder les 3 (fonctions différentes)

---

### 6. Scripts dans scripts/ - **20+ SCRIPTS DE DEBUG**

| Type | Nombre | Status | Justification |
|------|--------|--------|---------------|
| Scripts de debug (`debug_*.py`) | 8 | **🔄 DÉPLACER** | → `scripts/debug/` |
| Scripts de test (`test_*.py`) | 5 | **🔄 DÉPLACER** | → `tests/` (si formels) ou `scripts/debug/` |
| Scripts d'analyse (`analyze_*.py`) | 3 | **🔄 DÉPLACER** | → `scripts/debug/` |
| Scripts de visualisation (`visual_*.py`) | 2 | **🔄 DÉPLACER** | → `scripts/debug/` |
| Scripts utilitaires (production) | 7 | **✅ GARDER** | Scripts réutilisables |

**Détail des scripts à garder dans scripts/ (production):**
- ✅ `generate_extraction_report.py` - Génération de rapports
- ✅ `show_specifications.py` - Affichage des spécifications
- ✅ `inspect_selection.py` - Inspection de sélection (peut-être utile)

**Tous les autres → `scripts/debug/`**

---

## 📚 DOCUMENTATION - **35 FICHIERS MARKDOWN**

### Fichiers à GARDER (8)

| Fichier | Raison |
|---------|--------|
| `README.md` | ✅ Documentation principale |
| `QUICK_START.md` | ✅ Guide démarrage rapide |
| `INDEX_DOCUMENTATION.md` | ✅ Navigation documentation |
| `ALIGNMENT_FIX_REPORT.md` | ✅ Explique correction bug majeur |
| `SIMPLIFICATION_OUTPUTS.md` | ✅ Explique simplification récente |
| `SIMPLIFICATION_COMPLETE.md` | ✅ Confirmation simplification |
| `CLEANUP_RECOMMENDATIONS.md` | ✅ Guide de nettoyage (ce fichier) |
| `CHANGELOG.md` | ⚠️ **À CRÉER** (fusion de tous les rapports) |

### Fichiers à FUSIONNER dans CHANGELOG.md (27)

**Rapports d'implémentation:**
- AGENT_MISSION_COMPLETE.md
- COLUMN_EXTRACTION_PLAN.md
- COLUMN2_EXTRACTION_FINAL.md
- COLUMN2_EXTRACTION_v3_FINAL.md
- DELIVERABLE_SUMMARY.md
- DELIVERABLES.md
- EXTRACTION_SPECIFICATIONS_FINAL_REPORT.md
- EXTRACTION_SPECIFICATIONS_PRODUCTION.md
- EXTRACTION_SPECIFICATIONS_V2_STRICT_REPORT.md
- FINAL_DELIVERY_SUMMARY.md
- IMPLEMENTATION_SUMMARY_COLUMN2.md
- IMPLEMENTATION_SUMMARY.md
- SESSION_STATUS_V3_START.md
- STATUS_COLUMN2_COMPLETE.md
- TASK_5_COMPLETION_SUMMARY.md
- SIMPLIFICATION_SUMMARY.md

**Rapports techniques:**
- REFACTORING_DETECTION_DIRECTE.md
- REFACTORING_REPORT.md
- REGRESSION_ANALYSIS.md
- REQUIREMENTS_CHECKLIST.md
- SECOND_COLUMN_EXTRACTION.md
- V3_ARCHITECTURE_PLAN.md
- V3_DIAGNOSIS_FINAL.md

**Fichiers git/config:**
- .gitignore_changes.md
- GITIGNORE_SUMMARY.md
- README_SPECIFICATIONS_EXTRACTION.md (redondant avec README.md)

---

## 🛠️ SCRIPTS D'INSTALLATION - **11 FICHIERS**

### Analyse

| Fichier | Plateforme | Status | Justification |
|---------|-----------|--------|---------------|
| `INSTALL_TESSERACT.bat` | Windows | **🔄 ARCHIVER** | Utile pour réinstallation |
| `install_tesseract.ps1` | Windows | **🔄 ARCHIVER** | Doublon |
| `INSTALL_FRA.bat` | Windows | **🔄 ARCHIVER** | Utile pour réinstallation |
| `install_fra.ps1` | Windows | **🔄 ARCHIVER** | Doublon |
| `install_fra.vbs` | Windows | **❌ SUPPRIMER** | Redondant |
| `COPY_FRA_TRAINEDDATA.bat` | Windows | **🔄 ARCHIVER** | Utile |
| `copy_fra_traineddata.ps1` | Windows | **🔄 ARCHIVER** | Doublon |
| `MOVE_FRA_TRAINEDDATA.bat` | Windows | **🔄 ARCHIVER** | Utile |
| `move_fra_traineddata.py` | Cross-platform | **🔄 ARCHIVER** | Utile |
| `RUN_INSTALL_FRA_AS_ADMIN.bat` | Windows | **❌ SUPPRIMER** | Complexe |
| `setup_tesseract.py` | Cross-platform | **🔄 ARCHIVER** | Utile |

**Recommandation:** Créer `scripts/setup/` et y déplacer tous les scripts d'installation (sans doublons .bat/.ps1)

---

## 📊 FICHIERS DIVERS

| Fichier | Type | Status | Justification |
|---------|------|--------|---------------|
| `debug_column2_visual_page1.png` | Image debug | **❌ SUPPRIMER** | Fichier temporaire |
| `debug_pages.txt` | Log debug | **❌ SUPPRIMER** | Généré automatiquement (.gitignore) |

---

## ✅ STRUCTURE CIBLE PROPOSÉE

```
AI_AGENT_GCT/
│
├── 📁 src/
│   └── pdf_extraction/                    ← NOUVEAU PACKAGE
│       ├── __init__.py
│       ├── main.py                        ← Point d'entrée principal
│       ├── main_specifications.py         ← Point d'entrée specs
│       ├── core/
│       │   ├── __init__.py
│       │   ├── pdf_reader.py
│       │   ├── pdf_writer.py
│       │   ├── page_selector.py
│       │   ├── text_extractor.py
│       │   └── ocr_reader.py
│       ├── extractors/
│       │   ├── __init__.py
│       │   ├── column_extractor.py        ← Extraction grid-based
│       │   ├── second_column_extractor.py ← Extraction 2e colonne
│       │   └── extract_specifications_main.py
│       └── utils/
│           ├── __init__.py
│           ├── clean_ocr.py
│           └── cleanup_competing_files.py
│
├── 📁 tests/
│   ├── __init__.py
│   ├── test_page_selection.py             ← Renommé
│   ├── test_direct_detection.py
│   └── test_robustness.py
│
├── 📁 scripts/
│   ├── production/                        ← Scripts réutilisables
│   │   ├── generate_extraction_report.py
│   │   ├── show_specifications.py
│   │   └── inspect_selection.py
│   ├── debug/                             ← Scripts debug/historiques
│   │   ├── check_extraction.py
│   │   ├── compare_alignment.py
│   │   ├── debug_alignment.py
│   │   ├── debug_*.py (tous)
│   │   ├── test_*.py (non formels)
│   │   ├── analyze_*.py
│   │   └── visual_*.py
│   └── setup/                             ← Scripts installation
│       ├── setup_tesseract.py
│       ├── install_tesseract.bat
│       ├── install_fra.bat
│       └── move_fra_traineddata.py
│
├── 📁 docs/
│   ├── README.md                          ← Symlink vers racine
│   ├── QUICK_START.md
│   ├── INDEX_DOCUMENTATION.md
│   ├── technical/
│   │   ├── ALIGNMENT_FIX_REPORT.md
│   │   ├── SIMPLIFICATION_OUTPUTS.md
│   │   └── REFACTORING_ANALYSIS_REPORT.md
│   └── archive/                           ← Documentation historique
│       └── (tous les rapports fusionnés)
│
├── 📁 archive/
│   └── abandoned/                         ← Code abandonné
│       ├── extract_specifications_v2_strict.py
│       ├── extract_specifications_v3_generalized.py
│       ├── column2_*.py (8 fichiers)
│       └── extract_column2_*.py (5 fichiers)
│
├── 📁 data/
│   ├── input/
│   └── output/
│
├── 📁 tools/
│   └── poppler-26.02.0/
│
├── 📄 .gitignore                          ← Mis à jour
├── 📄 README.md                           ← Principal
├── 📄 CHANGELOG.md                        ← NOUVEAU (fusion)
├── 📄 requirements.txt
├── 📄 extract_specifications_production.py ← Script racine (garder pour compatibilité)
└── 📄 pyproject.toml                      ← NOUVEAU (optionnel)
```

---

## 📋 PLAN D'ACTION DÉTAILLÉ

### Phase 1: Préparation (AUCUNE SUPPRESSION)

**1.1 Créer l'arborescence cible**
```bash
mkdir -p src/pdf_extraction/core
mkdir -p src/pdf_extraction/extractors
mkdir -p src/pdf_extraction/utils
mkdir -p scripts/production
mkdir -p scripts/debug
mkdir -p scripts/setup
mkdir -p docs/technical
mkdir -p docs/archive
mkdir -p archive/abandoned
mkdir -p tests
```

**1.2 Créer les fichiers __init__.py**
```bash
touch src/pdf_extraction/__init__.py
touch src/pdf_extraction/core/__init__.py
touch src/pdf_extraction/extractors/__init__.py
touch src/pdf_extraction/utils/__init__.py
touch tests/__init__.py
```

**1.3 Backup complet**
```bash
git add -A
git commit -m "Backup avant refactoring structurel"
```

---

### Phase 2: Réorganisation Code (PAS DE SUPPRESSION)

**2.1 Déplacer fichiers src/ vers structure package**
- ✅ `src/main.py` → `src/pdf_extraction/main.py`
- ✅ `src/main_specifications.py` → `src/pdf_extraction/main_specifications.py`
- ✅ `src/pdf_reader.py` → `src/pdf_extraction/core/pdf_reader.py`
- ✅ `src/pdf_writer.py` → `src/pdf_extraction/core/pdf_writer.py`
- ✅ `src/page_selector.py` → `src/pdf_extraction/core/page_selector.py`
- ✅ `src/text_extractor.py` → `src/pdf_extraction/core/text_extractor.py`
- ✅ `src/ocr_reader.py` → `src/pdf_extraction/core/ocr_reader.py`
- ✅ `src/column_extractor.py` → `src/pdf_extraction/extractors/column_extractor.py`
- ✅ `src/second_column_extractor.py` → `src/pdf_extraction/extractors/second_column_extractor.py`
- ✅ `src/extract_specifications_main.py` → `src/pdf_extraction/extractors/extract_specifications_main.py`
- ✅ `src/clean_ocr.py` → `src/pdf_extraction/utils/clean_ocr.py`
- ✅ `src/cleanup_competing_files.py` → `src/pdf_extraction/utils/cleanup_competing_files.py`

**2.2 Déplacer scripts vers catégories**

**Production:**
- ✅ `scripts/generate_extraction_report.py` → `scripts/production/`
- ✅ `scripts/show_specifications.py` → `scripts/production/`
- ✅ `scripts/inspect_selection.py` → `scripts/production/`

**Debug (24 fichiers):**
- ✅ `check_extraction.py` → `scripts/debug/`
- ✅ `compare_alignment.py` → `scripts/debug/`
- ✅ `debug_alignment.py` → `scripts/debug/`
- ✅ Tous les `scripts/debug_*.py` → `scripts/debug/`
- ✅ Tous les `scripts/test_*.py` → `scripts/debug/`
- ✅ Tous les `scripts/analyze_*.py` → `scripts/debug/`
- ✅ Tous les `scripts/visual_*.py` → `scripts/debug/`
- ✅ Autres scripts debug → `scripts/debug/`

**Setup:**
- ✅ `setup_tesseract.py` → `scripts/setup/`
- ✅ `INSTALL_TESSERACT.bat` → `scripts/setup/`
- ✅ `INSTALL_FRA.bat` → `scripts/setup/`
- ✅ `MOVE_FRA_TRAINEDDATA.bat` → `scripts/setup/`
- ✅ `move_fra_traineddata.py` → `scripts/setup/`

**2.3 Déplacer tests**
- ✅ `tests/test_local_page_selection.py` → `tests/test_page_selection.py` (renommer)
- ✅ Les 2 autres tests restent

**2.4 Archiver code obsolète**
- ✅ Tous les `src/column2_*.py` (8 fichiers) → `archive/abandoned/`
- ✅ Tous les `src/extract_column2_*.py` (5 fichiers) → `archive/abandoned/`
- ✅ Tous les `src/extract_specifications_*.py` sauf main → `archive/abandoned/`
- ✅ `src/page_selector_robust.py` → `archive/abandoned/`
- ✅ `src/page_selector_debug.py` → `scripts/debug/`
- ✅ `extract_specifications_v2_strict.py` (racine) → `archive/abandoned/`
- ✅ `extract_specifications_v3_generalized.py` (racine) → `archive/abandoned/`

---

### Phase 3: Réorganisation Documentation

**3.1 Garder à la racine**
- ✅ README.md
- ✅ CHANGELOG.md (à créer)
- ✅ requirements.txt
- ✅ .gitignore

**3.2 Déplacer vers docs/**
- ✅ QUICK_START.md → `docs/`
- ✅ INDEX_DOCUMENTATION.md → `docs/`
- ✅ ALIGNMENT_FIX_REPORT.md → `docs/technical/`
- ✅ SIMPLIFICATION_OUTPUTS.md → `docs/technical/`
- ✅ SIMPLIFICATION_COMPLETE.md → `docs/technical/`
- ✅ CLEANUP_RECOMMENDATIONS.md → `docs/technical/`
- ✅ Ce rapport → `docs/technical/REFACTORING_ANALYSIS_REPORT.md`

**3.3 Archiver documentation historique (27 fichiers)**
- ✅ Tous les rapports listés plus haut → `docs/archive/`

**3.4 Créer CHANGELOG.md** (fusion chronologique de tous les rapports)

---

### Phase 4: Nettoyage Fichiers Temporaires

**4.1 Supprimer fichiers debug temporaires**
- ❌ `debug_column2_visual_page1.png`
- ❌ `debug_pages.txt` (si existe)
- ❌ Tous les `.pyc`, `__pycache__` (déjà dans .gitignore)

**4.2 Supprimer scripts installation redondants**
- ❌ `install_tesseract.ps1` (garde .bat)
- ❌ `install_fra.ps1` (garde .bat)
- ❌ `install_fra.vbs`
- ❌ `copy_fra_traineddata.ps1` (garde .bat)
- ❌ `RUN_INSTALL_FRA_AS_ADMIN.bat`

**4.3 Supprimer scripts vérification obsolètes**
- ❌ `validate_specifications_extraction.py`
- ❌ `verify_output.py` (racine, doublon dans scripts/)
- ❌ `verify_v3_output.py`

---

### Phase 5: Mise à Jour Imports et Références

**5.1 Créer script de migration des imports**
```python
# scripts/setup/migrate_imports.py
# Remplacer tous les imports dans les fichiers:
# from pdf_reader import ... → from pdf_extraction.core.pdf_reader import ...
```

**5.2 Mettre à jour .gitignore**
- Ajouter `archive/` si nécessaire
- Vérifier que `data/output/*.json` (sauf extraction.json) est ignoré

**5.3 Créer pyproject.toml (optionnel mais recommandé)**
```toml
[project]
name = "pdf-extraction"
version = "1.0.0"
dependencies = [
    "pypdf",
    "pdf2image",
    "Pillow",
    "opencv-python",
    "pytesseract",
    "pymupdf",
    "rapidfuzz",
    "scikit-learn",
    "numpy",
]

[project.optional-dependencies]
dev = ["pytest", "black", "flake8"]
```

---

### Phase 6: Validation et Tests

**6.1 Vérifier que le projet fonctionne**
```bash
python src/pdf_extraction/main.py
```

**6.2 Exécuter les tests**
```bash
pytest tests/
```

**6.3 Vérifier extraction.json**
```bash
python scripts/production/show_specifications.py
```

---

## 📊 STATISTIQUES DE NETTOYAGE

### Fichiers par Action

| Action | Python | Markdown | Batch/PS1 | Images | Total |
|--------|--------|----------|-----------|--------|-------|
| **GARDER** | 15 | 8 | 0 | 0 | **23** |
| **DÉPLACER/RÉORGANISER** | 35 | 27 | 5 | 0 | **67** |
| **ARCHIVER** | 15 | 0 | 5 | 0 | **20** |
| **SUPPRIMER** | 3 | 0 | 6 | 2 | **11** |
| **TOTAL** | 68 | 35 | 16 | 2 | **121** |

### Réduction de Complexité

| Métrique | Avant | Après | Gain |
|----------|-------|-------|------|
| Fichiers .py à la racine | 9 | 1 | **-89%** |
| Fichiers .md à la racine | 35 | 2 | **-94%** |
| Scripts .bat/.ps1 à la racine | 11 | 0 | **-100%** |
| Fichiers src/ | 24 | 0 (réorganisé) | **Structure claire** |
| Fichiers scripts/ désordonné | 25 | 0 (catégorisé) | **Structure claire** |

---

## ⚠️ RISQUES ET MITIGATIONS

### Risques Identifiés

1. **Risque: Imports cassés après réorganisation**
   - **Mitigation:** Script de migration automatique + tests complets
   - **Niveau:** MOYEN

2. **Risque: Perte de compatibilité scripts existants**
   - **Mitigation:** Garder `extract_specifications_production.py` à la racine
   - **Niveau:** FAIBLE

3. **Risque: Perte d'historique Git**
   - **Mitigation:** Utiliser `git mv` au lieu de `mv` + backup complet
   - **Niveau:** FAIBLE

4. **Risque: Documentation obsolète**
   - **Mitigation:** Créer CHANGELOG.md + README.md mis à jour
   - **Niveau:** FAIBLE

---

## ✅ CHECKLIST DE VALIDATION

### Avant de commencer
- [ ] Backup Git complet
- [ ] Lire ce rapport entièrement
- [ ] Obtenir validation du client

### Pendant le refactoring
- [ ] Phase 1: Créer structure (pas de suppression)
- [ ] Phase 2: Déplacer code (utiliser git mv)
- [ ] Phase 3: Réorganiser docs
- [ ] Phase 4: Nettoyage fichiers temporaires
- [ ] Phase 5: Mise à jour imports
- [ ] Phase 6: Validation

### Après le refactoring
- [ ] `python src/pdf_extraction/main.py` fonctionne
- [ ] `pytest tests/` passe
- [ ] `extraction.json` généré correctement
- [ ] Documentation à jour
- [ ] Commit final avec message clair

---

## 🎯 BÉNÉFICES ATTENDUS

1. **Clarté:** Structure professionnelle type package Python
2. **Maintenabilité:** Code organisé par responsabilité
3. **Découvrabilité:** Facile de trouver chaque fichier
4. **Documentation:** CHANGELOG unique, documentation centralisée
5. **Tests:** Structure claire pour ajout de tests
6. **Simplicité:** Racine épurée (2 fichiers MD, 1 requirements.txt)

---

## 📝 NOTES IMPORTANTES

1. **NE PAS SUPPRIMER** avant validation de ce rapport
2. **UTILISER `git mv`** pour conserver l'historique
3. **TESTER À CHAQUE PHASE** avant de passer à la suivante
4. **CRÉER CHANGELOG.md** avec fusion chronologique des rapports
5. **GARDER `extract_specifications_production.py`** à la racine pour compatibilité

---

## 🤝 VALIDATION REQUISE

**Avant d'exécuter les actions listées dans ce rapport, je dois obtenir votre validation explicite.**

**Questions pour validation:**
1. Êtes-vous d'accord avec la structure cible proposée?
2. Y a-t-il des fichiers que vous souhaitez absolument garder à la racine?
3. Souhaitez-vous que je crée le package `pdf_extraction` ou préférez-vous garder `src/` plat?
4. Validez-vous la liste des fichiers à supprimer définitivement?
5. Dois-je créer `pyproject.toml` ou garder uniquement `requirements.txt`?

**Attendant votre validation avant toute action irréversible.**

---

**Fin du rapport d'analyse**
