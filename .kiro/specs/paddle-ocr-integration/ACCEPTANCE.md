# ✅ Critères d'Acceptation et Validation

## 1. Critères de Succès Globaux

### 1.1 Fonctionnalité

- [ ] **Tesseract marche sans PaddleOCR**
  - Mode `--ocr-mode tesseract` fonctionne
  - Pas de crash si PaddleOCR manquant
  - Performance identique à avant

- [ ] **PaddleOCR fallback marche**
  - Mode `--ocr-mode hybrid` utilise Tesseract d'abord
  - En cas d'erreur Tesseract → bascule PaddleOCR
  - Texte extrait correctement

- [ ] **GPU optionnel marche**
  - Flag `--gpu` détecte GPU automatiquement
  - Pas de crash si GPU absent
  - Performance améliorée si GPU présent

### 1.2 Qualité Code

- [ ] **Couverture tests ≥ 80%**
  - OCREngine.py couvert à 80%+
  - Toutes les classes couvertes
  - Chemins fallback testés

- [ ] **Pas de dégradation de performance**
  - Mode "tesseract" : 100% de perf avant
  - Mode "hybrid" : +5% temps max (sur cas nominal)
  - Mode "paddle" : acceptable même si lent

- [ ] **Backward compatibility 100%**
  - Code existant fonctionne sans modification
  - Ancien JSON compatible (ocr_details optionnel)
  - Ancien CLI compatible

### 1.3 Documentation

- [ ] **README updated**
  - Section OCR Engines
  - Options CLI expliquées
  - Exemples d'utilisation

- [ ] **Docstrings complètes**
  - Toutes les classes documentées
  - Tous les paramètres typés
  - Exemples dans docstrings

- [ ] **Guide PADDLE_OCR_GUIDE.md créé**
  - Installation
  - Troubleshooting
  - Benchmarks

---

## 2. Critères d'Acceptation par Component

### 2.1 src/ocr_engine.py

**Doit contenir :**

```python
# Classes
✓ OCREngine (ABC)
✓ TesseractOCR(OCREngine)
✓ PaddleOCREngine(OCREngine)
✓ OCREngineRouter
✓ OCRError(Exception)

# Fonctions
✓ verify_all_engines(use_gpu) → Dict
✓ detect_gpu_availability() → bool
✓ create_ocr_router(...) → OCREngineRouter

# Signatures
✓ recognize(image, lang="fra") → (text, conf, meta)
✓ verify_setup() → bool
✓ get_stats() → Dict
✓ print_stats() → None
```

**Tests unitaires :**
- [ ] `test_tesseract_recognize()` - OK
- [ ] `test_tesseract_verify_setup()` - OK
- [ ] `test_paddle_recognize()` - OK
- [ ] `test_paddle_verify_setup()` - OK
- [ ] `test_router_tesseract_mode()` - OK
- [ ] `test_router_paddle_mode()` - OK
- [ ] `test_router_hybrid_fallback()` - OK
- [ ] `test_router_confidence_fallback()` - OK
- [ ] `test_stats_tracking()` - OK

**Critère d'acceptation :**
```bash
pytest tests/test_ocr_engines.py -v --cov=src/ocr_engine
# Doit afficher : >=8 tests passed, coverage >= 80%
```

---

### 2.2 src/column_extractor.py (modifications)

**Modifications attendues :**
- [ ] Import `OCREngineRouter, OCRError, verify_all_engines`
- [ ] `extract_structured_rows()` accepte `ocr_router` optionnel
- [ ] `ocr_cell()` utilise router au lieu de pytesseract direct
- [ ] JSON enrichi avec `ocr_details` par colonne
- [ ] `print_summary()` affiche stats OCR
- [ ] Gestion d'erreur gracieuse (fallback à texte vide)

**Pas de:**
- [ ] Appel pytesseract direct dans ocr_cell()
- [ ] Casse du format JSON existant (backward compat)
- [ ] Dépendance forcée à PaddleOCR

**Tests :**
- [ ] `test_extract_with_tesseract_router()` - OK
- [ ] `test_extract_with_hybrid_router()` - OK
- [ ] `test_ocr_details_in_json()` - OK

---

### 2.3 src/main.py (modifications)

**CLI arguments ajoutés :**
```bash
✓ --ocr-mode {tesseract,paddle,hybrid}
✓ --gpu
✓ --ocr-stats
```

**Comportement :**
- [ ] `python src/main.py` → Mode hybrid (défaut)
- [ ] `python src/main.py --ocr-mode tesseract` → Tesseract seul
- [ ] `python src/main.py --gpu` → GPU auto-détecté
- [ ] `python src/main.py --ocr-stats` → Stats affichées

**Verification au démarrage :**
```bash
[CHECK] Verifying OCR setup...
  ✓ Tesseract 5.3.1 (fra available)
  ✓ PaddleOCR 2.7.2
[OK] All engines ready
```

**Tests :**
- [ ] `test_cli_default_mode()` - OK
- [ ] `test_cli_ocr_mode_arg()` - OK
- [ ] `test_cli_gpu_flag()` - OK

---

### 2.4 requirements.txt

**Ajouts :**
- [ ] `paddleocr>=2.7.0`
- [ ] `paddlepaddle>=2.5.0`

**Pas de :**
- [ ] `paddlepaddle-gpu` (optionnel, utilisateur installe)
- [ ] Pins de version trop restrictifs

---

### 2.5 Tests

**Fichiers à créer :**
- [ ] `tests/test_ocr_engines.py` - Unitaires
- [ ] `tests/test_integration_paddle.py` - Intégration
- [ ] `scripts/benchmark_ocr.py` - Perf
- [ ] `scripts/compare_precision.py` - Précision

**Coverage :**
```bash
pytest --cov=src --cov-report=html
# Afficher : coverage >= 80%
```

---

## 3. Scénarios de Test

### 3.1 Happy Path (mode hybride)

```
Input: Page du PDF réel (6-10 cellules)
1. Tesseract OCR page
2. Tout réussit ? → Return (text, 90+%, tesseract)
3. Confiance < 70% ? → Fallback Paddle
4. Output: JSON with ocr_details
Expected: ≥2 cellules en Tesseract, ≤1 en Paddle
Status: ✓ PASS si JSON correct et stats OK
```

---

### 3.2 Fallback sur erreur

```
Input: Image dégradée volontairement
1. Tesseract crash
2. Router appelle Paddle
3. Paddle réussit
Expected: text ≠ empty, fallback_reason="tesseract_error"
Status: ✓ PASS si fallback_reason correctement set
```

---

### 3.3 Mode Tesseract seul

```
Input: Mode --ocr-mode tesseract
1. Appel router.recognize()
2. Tesseract réussit → return
3. Tesseract échoue → OCRError (pas de fallback)
Expected: 0 appel Paddle
Status: ✓ PASS si stats['paddle_success'] == 0
```

---

### 3.4 Mode Paddle seul

```
Input: Mode --ocr-mode paddle
1. Appel router.recognize()
2. Paddle réussit
Expected: engine="paddle", pas d'appel Tesseract
Status: ✓ PASS si stats['tesseract_success'] == 0
```

---

### 3.5 GPU Detection

```
Input: --gpu flag avec GPU indisponible
1. Vérifier detect_gpu_availability()
2. Afficher [WARN] GPU not available, using CPU
3. Initialiser PaddleOCR avec gpu=False
Expected: Pas de crash, fonctionne en CPU
Status: ✓ PASS si execution sans crash
```

---

## 4. Performance Benchmarks

### 4.1 Acceptation Performance

**Tesseract (mode par défaut) :**
- [ ] ≤ 200ms/cell
- [ ] RAM pic ≤ 60MB
- [ ] Pas d'augmentation par rapport à avant

**PaddleOCR (CPU) :**
- [ ] ≤ 500ms/cell
- [ ] RAM pic ≤ 400MB
- [ ] Acceptable pour fallback rare

**PaddleOCR (GPU) :**
- [ ] ≤ 300ms/cell
- [ ] RAM pic ≤ 700MB
- [ ] Significativement plus rapide que CPU

**Hybrid :**
- [ ] ≤ 250ms/cell avg (sur 100 cells, mostly Tesseract)
- [ ] RAM pic ≤ 400MB (Tesseract + Paddle en mémoire)

---

### 4.2 Précision Benchmarks

**Sur 10 cellules du PDF réel :**

- [ ] Tesseract WER ≤ 5%
- [ ] PaddleOCR WER ≤ 3%
- [ ] Paddle améliore ≥2 cas sur 10

**F1-score :**
- [ ] Tesseract ≥ 0.90
- [ ] PaddleOCR ≥ 0.93

---

## 5. Validation Finale

### 5.1 Checklist Avant Merge

```
Code Quality
  ✓ Linting passe (flake8, black)
  ✓ Type checking passe (mypy)
  ✓ Aucun TODO/FIXME laissé

Testing
  ✓ Tous les tests passent
  ✓ Coverage >= 80%
  ✓ Pas de tests flaky

Functionality
  ✓ Mode tesseract marche (backward compat)
  ✓ Mode hybrid marche
  ✓ Mode paddle marche
  ✓ GPU optional, pas forcé

Performance
  ✓ Pas de dégradation vs avant
  ✓ Benchmarks documentés
  ✓ Perf acceptable pour fallback

Documentation
  ✓ README updated
  ✓ Docstrings complets
  ✓ CLI help clear
  ✓ Exemples dans guides

Integration
  ✓ JSON backward compatible
  ✓ Aucune regression sur extraction existante
  ✓ Rollback possible (git revert)
```

---

### 5.2 Sign-off Criteria

**Condition 1 : Tests**
```bash
pytest tests/ -v --cov=src --cov-threshold=80
# MUST: all pass, coverage >= 80%
```

**Condition 2 : Integration**
```bash
python src/main.py --ocr-mode hybrid --ocr-stats
# MUST: extract 6 pages without error, stats printed
```

**Condition 3 : Backward Compat**
```bash
python src/main.py  # No args
# MUST: work identically to before (mode tesseract)
```

---

## 6. Known Limitations (à documenter)

- [ ] PaddleOCR modèles = ~500MB téléchargement au 1er run
- [ ] GPU optional, pas tous les types supportés
- [ ] Hybrid mode = plus de RAM utilisée (2 engines loaded)
- [ ] Tesseract meilleur sur texte très fin imprimé
- [ ] Paddle meilleur sur images bruitées/inclinées

---

## 7. Sign-Off

**Validé par :** [À remplir]  
**Date :** [À remplir]  
**Build :** [À remplir - hash Git]  

**Notes :** [Libre]

