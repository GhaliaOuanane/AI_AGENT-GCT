# RECOMMANDATIONS DE NETTOYAGE

Ce document liste les fichiers qui peuvent être supprimés sans affecter le fonctionnement du projet.

---

## FICHIERS OBSOLÈTES À SUPPRIMER

### Scripts d'extraction obsolètes
Ces scripts sont des versions anciennes ou abandonnées. Le script principal est `src/main.py`.

❌ `extract_specifications_v2_strict.py` (doublon de extract_specifications_production.py)
❌ `extract_specifications_v3_generalized.py` (approche abandonnée, ne fonctionne pas pour tableaux continus)

**À conserver:**
✅ `extract_specifications_production.py` (utilisé par src/main.py)

---

### Scripts de vérification/debug
Ces scripts étaient utiles pour le développement mais ne sont plus nécessaires en production.

❌ `check_extraction.py` (script de vérification manuel)
❌ `compare_alignment.py` (script de comparaison pour debug)
❌ `debug_alignment.py` (script de debug Y-based pairing)
❌ `validate_specifications_extraction.py` (validation manuelle)
❌ `verify_output.py` (vérification manuelle)
❌ `verify_v3_output.py` (vérification V3, version abandonnée)

**Note:** Si vous voulez conserver ces scripts pour debug futur, créez un dossier `scripts/debug/` et déplacez-les là.

---

### Fichiers de débogage/images
❌ `debug_column2_visual_page1.png` (image de debug)
❌ `debug_pages.txt` (log de debug)

---

### Rapports de développement
Ces rapports documentent le processus de développement mais ne sont plus nécessaires une fois le projet stable.

**Rapports d'implémentation (historique):**
❌ `AGENT_MISSION_COMPLETE.md`
❌ `COLUMN_EXTRACTION_PLAN.md`
❌ `COLUMN2_EXTRACTION_FINAL.md`
❌ `COLUMN2_EXTRACTION_v3_FINAL.md`
❌ `DELIVERABLE_SUMMARY.md`
❌ `DELIVERABLES.md`
❌ `EXTRACTION_SPECIFICATIONS_FINAL_REPORT.md`
❌ `EXTRACTION_SPECIFICATIONS_PRODUCTION.md`
❌ `EXTRACTION_SPECIFICATIONS_V2_STRICT_REPORT.md`
❌ `FINAL_DELIVERY_SUMMARY.md`
❌ `IMPLEMENTATION_SUMMARY_COLUMN2.md`
❌ `IMPLEMENTATION_SUMMARY.md`
❌ `SESSION_STATUS_V3_START.md`
❌ `STATUS_COLUMN2_COMPLETE.md`
❌ `TASK_5_COMPLETION_SUMMARY.md`

**Rapports techniques (historique):**
❌ `REFACTORING_DETECTION_DIRECTE.md`
❌ `REFACTORING_REPORT.md`
❌ `REGRESSION_ANALYSIS.md`
❌ `REQUIREMENTS_CHECKLIST.md`
❌ `SECOND_COLUMN_EXTRACTION.md`
❌ `V3_ARCHITECTURE_PLAN.md`
❌ `V3_DIAGNOSIS_FINAL.md`

**Rapports à conserver (documentation utile):**
✅ `ALIGNMENT_FIX_REPORT.md` (explique la correction du bug d'alignement)
✅ `SIMPLIFICATION_OUTPUTS.md` (explique la simplification récente)
✅ `README.md` (documentation principale)
✅ `QUICK_START.md` (guide de démarrage rapide)
✅ `INDEX_DOCUMENTATION.md` (index de la documentation)

---

### Scripts d'installation Tesseract
Ces scripts servaient à installer Tesseract/fra.traineddata. Si Tesseract est déjà installé, ils ne sont plus nécessaires.

❌ `COPY_FRA_TRAINEDDATA.bat`
❌ `copy_fra_traineddata.ps1`
❌ `INSTALL_FRA.bat`
❌ `install_fra.ps1`
❌ `install_fra.vbs`
❌ `INSTALL_TESSERACT.bat`
❌ `install_tesseract.ps1`
❌ `MOVE_FRA_TRAINEDDATA.bat`
❌ `move_fra_traineddata.py`
❌ `RUN_INSTALL_FRA_AS_ADMIN.bat`
❌ `setup_tesseract.py`

**Note:** Si vous devez réinstaller Tesseract sur une nouvelle machine, gardez ces scripts. Sinon, supprimez-les.

---

### Fichiers git
❌ `.gitignore_changes.md` (historique de modifications du .gitignore)
❌ `GITIGNORE_SUMMARY.md` (résumé du .gitignore)

**À conserver:**
✅ `.gitignore` (configuration git)

---

### Fichiers de documentation obsolètes
❌ `README_SPECIFICATIONS_EXTRACTION.md` (documentation redondante avec README.md)

---

## STRUCTURE RECOMMANDÉE APRÈS NETTOYAGE

```
AI_AGENT GCT/
├── .git/
├── .kiro/
├── .venv/
├── .vscode/
├── data/
│   ├── input/
│   │   └── BRAIN INFORMATIQUE_16052025101905.PDF
│   └── output/
│       ├── .gitkeep
│       ├── extraction.json          ← SORTIE UNIQUE
│       └── pages_cibles.pdf
├── src/
│   ├── clean_ocr.py
│   ├── column_extractor.py
│   ├── main.py
│   ├── ocr_reader.py
│   ├── page_selector.py
│   ├── pdf_reader.py
│   └── pdf_writer.py
├── scripts/ (optionnel)
│   └── debug/ (optionnel - pour scripts de debug)
├── tests/
├── tools/
├── .gitignore
├── ALIGNMENT_FIX_REPORT.md          ← Documentation technique
├── extract_specifications_production.py
├── INDEX_DOCUMENTATION.md
├── QUICK_START.md
├── README.md
├── requirements.txt
├── SIMPLIFICATION_OUTPUTS.md
└── CLEANUP_RECOMMENDATIONS.md       ← Ce fichier
```

---

## COMMANDE DE NETTOYAGE

Si vous voulez supprimer tous les fichiers obsolètes d'un coup (⚠️ **ATTENTION: irréversible**):

```powershell
# Sauvegarder d'abord (optionnel)
git add -A
git commit -m "Backup before cleanup"

# Supprimer les scripts obsolètes
Remove-Item extract_specifications_v2_strict.py
Remove-Item extract_specifications_v3_generalized.py
Remove-Item check_extraction.py
Remove-Item compare_alignment.py
Remove-Item debug_alignment.py
Remove-Item validate_specifications_extraction.py
Remove-Item verify_output.py
Remove-Item verify_v3_output.py

# Supprimer les fichiers de debug
Remove-Item debug_column2_visual_page1.png
Remove-Item debug_pages.txt

# Supprimer les rapports obsolètes
Remove-Item AGENT_MISSION_COMPLETE.md
Remove-Item COLUMN_EXTRACTION_PLAN.md
Remove-Item COLUMN2_EXTRACTION_FINAL.md
Remove-Item COLUMN2_EXTRACTION_v3_FINAL.md
Remove-Item DELIVERABLE_SUMMARY.md
Remove-Item DELIVERABLES.md
Remove-Item EXTRACTION_SPECIFICATIONS_FINAL_REPORT.md
Remove-Item EXTRACTION_SPECIFICATIONS_PRODUCTION.md
Remove-Item EXTRACTION_SPECIFICATIONS_V2_STRICT_REPORT.md
Remove-Item FINAL_DELIVERY_SUMMARY.md
Remove-Item IMPLEMENTATION_SUMMARY_COLUMN2.md
Remove-Item IMPLEMENTATION_SUMMARY.md
Remove-Item SESSION_STATUS_V3_START.md
Remove-Item STATUS_COLUMN2_COMPLETE.md
Remove-Item TASK_5_COMPLETION_SUMMARY.md
Remove-Item REFACTORING_DETECTION_DIRECTE.md
Remove-Item REFACTORING_REPORT.md
Remove-Item REGRESSION_ANALYSIS.md
Remove-Item REQUIREMENTS_CHECKLIST.md
Remove-Item SECOND_COLUMN_EXTRACTION.md
Remove-Item V3_ARCHITECTURE_PLAN.md
Remove-Item V3_DIAGNOSIS_FINAL.md

# Supprimer les scripts d'installation (si Tesseract déjà installé)
Remove-Item COPY_FRA_TRAINEDDATA.bat
Remove-Item copy_fra_traineddata.ps1
Remove-Item INSTALL_FRA.bat
Remove-Item install_fra.ps1
Remove-Item install_fra.vbs
Remove-Item INSTALL_TESSERACT.bat
Remove-Item install_tesseract.ps1
Remove-Item MOVE_FRA_TRAINEDDATA.bat
Remove-Item move_fra_traineddata.py
Remove-Item RUN_INSTALL_FRA_AS_ADMIN.bat
Remove-Item setup_tesseract.py

# Supprimer les fichiers git obsolètes
Remove-Item .gitignore_changes.md
Remove-Item GITIGNORE_SUMMARY.md
Remove-Item README_SPECIFICATIONS_EXTRACTION.md
```

---

## APRÈS LE NETTOYAGE

1. **Vérifier que le projet fonctionne toujours:**
   ```bash
   python src/main.py
   ```

2. **Commiter les changements:**
   ```bash
   git add -A
   git commit -m "Clean up obsolete files and reports"
   ```

3. **Mettre à jour INDEX_DOCUMENTATION.md** pour refléter la nouvelle structure

---

## RÉSUMÉ

**Avant nettoyage:** ~60 fichiers à la racine
**Après nettoyage:** ~10-15 fichiers à la racine (essentiels)

**Gain de clarté:** ✅ Structure plus simple et claire
**Gain d'espace:** ✅ Moins de fichiers inutiles
**Maintenance:** ✅ Plus facile de trouver les fichiers importants
