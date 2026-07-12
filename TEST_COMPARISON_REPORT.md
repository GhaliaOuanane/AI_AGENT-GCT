# 🔍 RAPPORT DE COMPARAISON DES TESTS - AVANT/APRÈS REFACTORING

**Date:** 2026-07-12  
**Comparaison:** `main` vs `refactoring-structural`

---

## ✅ RÉSULTAT: AUCUN NOUVEAU TEST ÉCHOUÉ

Les **8 tests** qui échouent actuellement échouaient **déjà avant le refactoring**.

**Preuve:** Les messages d'erreur et les tests échouant sont **identiques** avant et après.

---

## 📊 STATISTIQUES COMPARÉES

| Métrique | Avant (main) | Après (refactoring) | Différence |
|----------|--------------|---------------------|------------|
| **Tests découverts** | 31 | 31 | ✅ Identique |
| **Tests passants** | 23 (74%) | 23 (74%) | ✅ Identique |
| **Tests échouants** | 8 (26%) | 8 (26%) | ✅ Identique |
| **Temps d'exécution** | 0.010s | 0.030s | +0.020s (négligeable) |

---

## 📋 LISTE DES 8 TESTS ÉCHOUANTS (IDENTIQUES)

### Test 1: `test_model_1_incomplete`
**Fichier:** `test_direct_detection.py`  
**Classe:** `TestHeaderModel1Detection`

**Erreur AVANT:**
```
FAIL: test_model_1_incomplete (test_direct_detection.TestHeaderModel1Detection.test_model_1_incomplete)
Test avec en-tête incomplet (devrait échouer).
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\ghali\OneDrive\Desktop\AI_AGENT GCT\tests\test_direct_detection.py", line 57, in test_model_1_incomplete
    self.assertFalse(_matches_header_model_1(normalized))
AssertionError: True is not false
```

**Erreur APRÈS:**
```
FAIL: test_model_1_incomplete (test_direct_detection.TestHeaderModel1Detection.test_model_1_incomplete)
Test avec en-tête incomplet (devrait échouer).
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\ghali\OneDrive\Desktop\AI_AGENT GCT\tests\integration\test_direct_detection.py", line 57, in test_model_1_incomplete
    self.assertFalse(_matches_header_model_1(normalized))
AssertionError: True is not false
```

✅ **IDENTIQUE** (seul le chemin du fichier a changé: `tests/` → `tests/integration/`)

---

### Test 2: `test_single_line`
**Fichier:** `test_direct_detection.py`  
**Classe:** `TestTableContentDetection`

**Erreur AVANT:**
```
FAIL: test_single_line (test_direct_detection.TestTableContentDetection.test_single_line)
Test avec une seule ligne (devrait échouer).
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\ghali\OneDrive\Desktop\AI_AGENT GCT\tests\test_direct_detection.py", line 122, in test_single_line
    self.assertFalse(_looks_like_table_content(normalized))
AssertionError: True is not false
```

**Erreur APRÈS:**
```
FAIL: test_single_line (test_direct_detection.TestTableContentDetection.test_single_line)
Test avec une seule ligne (devrait échouer).
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\ghali\OneDrive\Desktop\AI_AGENT GCT\tests\integration\test_direct_detection.py", line 122, in test_single_line
    self.assertFalse(_looks_like_table_content(normalized))
AssertionError: True is not false
```

✅ **IDENTIQUE**

---

### Test 3: `test_excludes_supplier_datasheets_after_lot_tables`
**Fichier:** `test_page_selection.py`  
**Classe:** `PageSelectorTests`

**Erreur AVANT:**
```
FAIL: test_excludes_supplier_datasheets_after_lot_tables (test_local_page_selection.PageSelectorTests.test_excludes_supplier_datasheets_after_lot_tables)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\ghali\OneDrive\Desktop\AI_AGENT GCT\tests\test_local_page_selection.py", line 71, in test_excludes_supplier_datasheets_after_lot_tables
    self.assertEqual([1, 4], selected_indices)
AssertionError: Lists differ: [1, 4] != [1]

First list contains 1 additional elements.
First extra element 1:
4

- [1, 4]
+ [1]
```

**Erreur APRÈS:**
```
FAIL: test_excludes_supplier_datasheets_after_lot_tables (test_page_selection.PageSelectorTests.test_excludes_supplier_datasheets_after_lot_tables)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\ghali\OneDrive\Desktop\AI_AGENT GCT\tests\integration\test_page_selection.py", line 71, in test_excludes_supplier_datasheets_after_lot_tables
    self.assertEqual([1, 4], selected_indices)
AssertionError: Lists differ: [1, 4] != [1]

First list contains 1 additional elements.
First extra element 1:
4

- [1, 4]
+ [1]
```

✅ **IDENTIQUE**

---

### Test 4: `test_original_invalid_pages_still_rejected`
**Fichier:** `test_robustness.py`  
**Classe:** `TestRegressionPrevention`

**Erreur AVANT:**
```
FAIL: test_original_invalid_pages_still_rejected (test_robustness.TestRegressionPrevention.test_original_invalid_pages_still_rejected)
Test : les pages invalides du document original sont toujours rejetées.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\ghali\OneDrive\Desktop\AI_AGENT GCT\tests\test_robustness.py", line 199, in test_original_invalid_pages_still_rejected
    self.assertFalse(_has_table_header(_normalize(admin_page)),
AssertionError: True is not false : Page administrative devrait être rejetée
```

**Erreur APRÈS:**
```
FAIL: test_original_invalid_pages_still_rejected (test_robustness.TestRegressionPrevention.test_original_invalid_pages_still_rejected)
Test : les pages invalides du document original sont toujours rejetées.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\ghali\OneDrive\Desktop\AI_AGENT GCT\tests\integration\test_robustness.py", line 200, in test_original_invalid_pages_still_rejected
    self.assertFalse(_has_table_header(_normalize(admin_page)),
AssertionError: True is not false : Page administrative devrait être rejetée
```

✅ **IDENTIQUE** (ligne 199 → 200, ajout d'1 ligne d'import)

---

### Test 5: `test_administrative_prose_detection`
**Fichier:** `test_robustness.py`  
**Classe:** `TestStructuralAnalysis`

**Erreur AVANT:**
```
FAIL: test_administrative_prose_detection (test_robustness.TestStructuralAnalysis.test_administrative_prose_detection)
Test : identification de prose administrative.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\ghali\OneDrive\Desktop\AI_AGENT GCT\tests\test_robustness.py", line 83, in test_administrative_prose_detection
    self.assertTrue(_is_administrative_prose(_normalize(admin_text)))
AssertionError: False is not true
```

**Erreur APRÈS:**
```
FAIL: test_administrative_prose_detection (test_robustness.TestStructuralAnalysis.test_administrative_prose_detection)
Test : identification de prose administrative.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\ghali\OneDrive\Desktop\AI_AGENT GCT\tests\integration\test_robustness.py", line 84, in test_administrative_prose_detection
    self.assertTrue(_is_administrative_prose(_normalize(admin_text)))
AssertionError: False is not true
```

✅ **IDENTIQUE** (ligne 83 → 84)

---

### Test 6: `test_supplier_datasheet_detection`
**Fichier:** `test_robustness.py`  
**Classe:** `TestStructuralAnalysis`

**Erreur AVANT:**
```
FAIL: test_supplier_datasheet_detection (test_robustness.TestStructuralAnalysis.test_supplier_datasheet_detection)
Test : identification de fiche technique fournisseur.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\ghali\OneDrive\Desktop\AI_AGENT GCT\tests\test_robustness.py", line 97, in test_supplier_datasheet_detection
    self.assertTrue(_is_supplier_datasheet(_normalize(datasheet)))
AssertionError: False is not true
```

**Erreur APRÈS:**
```
FAIL: test_supplier_datasheet_detection (test_robustness.TestStructuralAnalysis.test_supplier_datasheet_detection)
Test : identification de fiche technique fournisseur.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\ghali\OneDrive\Desktop\AI_AGENT GCT\tests\integration\test_robustness.py", line 98, in test_supplier_datasheet_detection
    self.assertTrue(_is_supplier_datasheet(_normalize(datasheet)))
AssertionError: False is not true
```

✅ **IDENTIQUE** (ligne 97 → 98)

---

### Test 7: `test_reject_administrative_as_table_header`
**Fichier:** `test_robustness.py`  
**Classe:** `TestTableDetection`

**Erreur AVANT:**
```
FAIL: test_reject_administrative_as_table_header (test_robustness.TestTableDetection.test_reject_administrative_as_table_header)
Test : rejet de prose administrative comme en-tête.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\ghali\OneDrive\Desktop\AI_AGENT GCT\tests\test_robustness.py", line 144, in test_reject_administrative_as_table_header
    self.assertFalse(_has_table_header(_normalize(admin)))
AssertionError: True is not false
```

**Erreur APRÈS:**
```
FAIL: test_reject_administrative_as_table_header (test_robustness.TestTableDetection.test_reject_administrative_as_table_header)
Test : rejet de prose administrative comme en-tête.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\ghali\OneDrive\Desktop\AI_AGENT GCT\tests\integration\test_robustness.py", line 145, in test_reject_administrative_as_table_header
    self.assertFalse(_has_table_header(_normalize(admin)))
AssertionError: True is not false
```

✅ **IDENTIQUE** (ligne 144 → 145)

---

### Test 8: `test_reject_supplier_doc_as_table_header`
**Fichier:** `test_robustness.py`  
**Classe:** `TestTableDetection`

**Erreur AVANT:**
```
FAIL: test_reject_supplier_doc_as_table_header (test_robustness.TestTableDetection.test_reject_supplier_doc_as_table_header)
Test : rejet de doc fournisseur comme en-tête.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\ghali\OneDrive\Desktop\AI_AGENT GCT\tests\test_robustness.py", line 156, in test_reject_supplier_doc_as_table_header
    self.assertFalse(_has_table_header(_normalize(supplier)))
AssertionError: True is not false
```

**Erreur APRÈS:**
```
FAIL: test_reject_supplier_doc_as_table_header (test_robustness.TestTableDetection.test_reject_supplier_doc_as_table_header)
Test : rejet de doc fournisseur comme en-tête.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\ghali\OneDrive\Desktop\AI_AGENT GCT\tests\integration\test_robustness.py", line 157, in test_reject_supplier_doc_as_table_header
    self.assertFalse(_has_table_header(_normalize(supplier)))
AssertionError: True is not false
```

✅ **IDENTIQUE** (ligne 156 → 157)

---

## 📊 ANALYSE DÉTAILLÉE

### Différences Mineures (Non-Régressions)
Les seules différences entre AVANT et APRÈS sont:
1. **Chemin des fichiers**: `tests/` → `tests/integration/` ✅ Attendu (refactoring)
2. **Numéros de ligne**: +1 ou +2 lignes ✅ Attendu (ajout imports)
3. **Temps d'exécution**: +0.020s ✅ Négligeable

### Erreurs Identiques
Tous les **8 tests** échouent pour les **mêmes raisons**:
- Même `AssertionError`
- Même ligne de code (à +/-2 lignes près)
- Même message d'erreur
- Même comportement fonctionnel

---

## ✅ CONCLUSION

**AUCUNE RÉGRESSION CAUSÉE PAR LE REFACTORING**

Les 8 tests qui échouent sont des **échecs pré-existants**, présents avant le refactoring. Le refactoring n'a introduit **aucun nouveau test échouant**.

**Preuve:** Comparaison directe des sorties de tests montre des erreurs **identiques**.

---

## 🔧 CORRECTIONS APPORTÉES

Pour que les tests fonctionnent après refactoring, j'ai dû corriger:

1. **test_direct_detection.py**
   - Import: `from page_selector` → `from pdf_extraction.core.page_selector`
   - sys.path: `parent / 'src'` → `parent.parent / 'src'`

2. **test_page_selection.py**
   - Import: `from src.page_selector` → `from pdf_extraction.core.page_selector`

3. **test_robustness.py**
   - Import: `from page_selector_robust` (utilise module archivé)
   - sys.path: Ajout `archive/selectors` pour accéder au module archivé

**Commit:** `56af2ef` "fix: correct test imports for refactored structure"

Ces corrections sont **normales et attendues** lors d'un refactoring de structure de package.

---

## 📝 RECOMMANDATIONS

### Court Terme
1. ✅ **Merger le refactoring** - Aucune régression détectée
2. 📝 **Créer ticket séparé** pour les 8 tests échouants
3. 🔍 **Analyser causes racines** des échecs pré-existants

### Moyen Terme
4. 🐛 **Corriger les 8 tests**:
   - Tests 1-2: Ajuster `_matches_header_model_1` et `_looks_like_table_content`
   - Test 3: Corriger logique de sélection pages
   - Tests 4-8: Implémenter fonctions manquantes dans `page_selector_robust` ou ajuster tests

5. 📊 **Augmenter couverture tests** - Ajouter tests unitaires supplémentaires

---

## 📂 FICHIERS DE PREUVE

- `tests_avant.txt` - Résultats tests sur branche `main`
- `tests_apres_fixed.txt` - Résultats tests sur branche `refactoring-structural`

**Comparaison disponible:** Les deux fichiers peuvent être comparés ligne par ligne pour vérifier l'identité des erreurs.

---

**✅ VALIDATION: LE REFACTORING N'A CAUSÉ AUCUNE RÉGRESSION**

**Prêt pour merge vers `main`**

---

**Rapport généré le:** 2026-07-12 1:35 PM  
**Méthode:** Comparaison tests unitaires avant/après  
**Branche actuelle:** refactoring-structural  
**Branche de référence:** main

