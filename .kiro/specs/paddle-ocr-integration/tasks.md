# 📋 Tasks d'Implémentation

## Phase 1 : Setup et Infrastructure

### Task 1.1 : Ajouter PaddleOCR aux dépendances
**Objectif :** Mettre à jour requirements.txt avec PaddleOCR et dépendances

```
dépendances à ajouter :
- paddleocr >= 2.7.0
- paddlepaddle >= 2.5.0 (CPU par défaut)
- paddlepaddle-gpu >= 2.5.0 (optionnel, pour GPU)
```

**Livrable :** requirements.txt mis à jour

---

### Task 1.2 : Créer module ocr_engine.py
**Objectif :** Implémenter l'interface abstraite OCREngine et ses deux implémentations

**Fichier :** `src/ocr_engine.py`

**Éléments à implémenter :**
1. Classe abstraite `OCREngine` avec méthodes :
   - `recognize(image, lang) → (text, confidence, metadata)`
   - `verify_setup() → bool`

2. Classe `TesseractOCR(OCREngine)` :
   - Constructor avec détection auto de tesseract.exe
   - Méthode `_compute_confidence()` pour score 0-100
   - Retry logic si Tesseract crash
   - Logging structuré

3. Classe `PaddleOCREngine(OCREngine)` :
   - Constructor avec paramètres GPU/CPU
   - Téléchargement automatique des modèles au 1er run
   - Extraction du texte et confiance depuis résultats Paddle
   - Gestion du contexte GPU

4. Classe `OCREngineRouter` :
   - Constructor : mode ("tesseract"/"paddle"/"hybrid"), use_gpu
   - Méthode `recognize()` avec logique fallback
   - Tracking des stats (success/fallback/failure)
   - Méthode `get_stats()` pour résumé

5. Classe personnalisée `OCRError(Exception)`

**Tests unitaires attendus :**
- Test setup Tesseract
- Test setup PaddleOCR (sans GPU requis)
- Test routing fallback
- Test stats tracking

**Livrable :** `src/ocr_engine.py` complet + tests passing

---

### Task 1.3 : Vérifier setup au démarrage
**Objectif :** Ajouter une fonction `verify_all_engines()` appelée depuis main()

**Fichier :** `src/ocr_engine.py` (ajouter fonction) + `src/main.py` (appel)

**Fonction attendue :**
```python
def verify_all_engines(use_gpu: bool = False) → Dict:
    """
    Vérifie Tesseract + PaddleOCR au démarrage.
    Retourne status par engine + warnings.
    """
    results = {
        "tesseract": {"ok": bool, "version": str, "languages": [str]},
        "paddle": {"ok": bool, "version": str, "gpu": bool},
        "gpu_available": bool,
        "warnings": [str]
    }
```

**Affichage console attendu :**
```
[CHECK] OCR Engines Setup
  ✓ Tesseract 5.3.1 (fra, eng available)
  ✓ PaddleOCR 2.7.2 (GPU: False, models in ~/.paddleocr)
  ⚠ GPU requested but not available, using CPU
[OK] All engines ready
```

**Livrable :** Vérification robuste au démarrage

---

## Phase 2 : Intégration dans column_extractor.py

### Task 2.1 : Refactoriser ocr_cell() pour utiliser OCREngine
**Objectif :** Remplacer appel `pytesseract.image_to_string()` par `OCREngineRouter`

**Fichier :** `src/column_extractor.py`

**Modifications attendues :**
1. Ajouter paramètre `ocr_router: OCREngineRouter` au constructor/factory
2. Remplacer la fonction `ocr_cell()` :
   ```python
   def ocr_cell(cell_img: np.ndarray, lang: str = "fra") 
       → Tuple[str, float, Dict]:
       """Retourne maintenant aussi confidence + metadata"""
       return ocr_router.recognize(cell_img, lang)
   ```

3. Mettre à jour `extract_structured_rows()` pour stocker :
   - `ocr_details` par colonne (engine, confidence, fallback_reason)

**Livrable :** column_extractor.py intégré avec OCRRouter

---

### Task 2.2 : Ajouter ocr_details au JSON structuré
**Objectif :** Enrichir la sortie JSON avec détails OCR (engine, confiance, fallback)

**Fichier :** `src/column_extractor.py`

**Structure JSON modifiée :**
```json
{
  "designation": "...",
  "specification": "...",
  "ocr_details": {
    "designation": {"engine": "...", "confidence": 95, "fallback_reason": null},
    "specification": {"engine": "...", "confidence": 87, "fallback_reason": "..."}
  }
}
```

**Livrable :** JSON avec ocr_details complètes

---

### Task 2.3 : Ajouter résumé OCR en fin d'exécution
**Objectif :** Afficher stats globales après extraction complète

**Fichier :** `src/column_extractor.py` (fonction `print_summary()`)

**Stats à afficher :**
```
[SUMMARY] 6 pages, 42 lignes
[OCR_STATS] Primary success: 126/128 (98%)
[OCR_STATS] Confidence fallback: 2/128 (1.6%)
[OCR_STATS] Avg confidence: 93.2%
```

**Livrable :** Résumé stats complet

---

## Phase 3 : Interface CLI et Options

### Task 3.1 : Ajouter options CLI
**Objectif :** Ajouter arguments pour choisir OCR engine et GPU

**Fichier :** `src/main.py`

**Arguments à ajouter :**
```
--ocr-mode {tesseract,paddle,hybrid}  (défaut: hybrid)
--gpu                                 (flag: use GPU si dispo)
--paddle-only                         (alias pour --ocr-mode paddle)
--ocr-stats                           (affiche stats détaillées)
```

**Livrable :** CLI avec options OCR

---

### Task 3.2 : Logger le mode OCR au démarrage
**Objectif :** Afficher le mode sélectionné et configuration

**Fichier :** `src/main.py`

**Affichage attendu :**
```
[INFO] OCR Configuration
  Mode: hybrid
  Primary: Tesseract 5.3.1
  Fallback: PaddleOCR 2.7.2 (GPU: False)
  Confidence threshold: 70%
```

**Livrable :** Configuration affichée au démarrage

---

## Phase 4 : Tests et Benchmarking

### Task 4.1 : Tests unitaires OCREngine
**Objectif :** Couvrir toutes les classes OCR

**Fichier :** `tests/test_ocr_engines.py` (NEW)

**Tests à implémenter :**
1. `test_tesseract_recognize()` - OCR basique
2. `test_paddle_recognize()` - OCR basique
3. `test_router_primary_success()` - Router sans fallback
4. `test_router_confidence_fallback()` - Soft fallback
5. `test_router_error_fallback()` - Hard fallback
6. `test_stats_tracking()` - Comptage stats

**Couverture attendue :** > 80%

**Livrable :** tests/test_ocr_engines.py avec > 80% couverture

---

### Task 4.2 : Test d'intégration sur PDF réel
**Objectif :** Valider sur 2-3 pages du PDF existant

**Fichier :** `tests/test_integration_paddle.py` (NEW)

**Scénarios :**
1. Mode "tesseract" → Tesseract uniquement
2. Mode "hybrid" → Tesseract + fallback si besoin
3. Mode "paddle" → PaddleOCR uniquement
4. Comparer résultats OCR entre les 3 modes

**Validation :**
- Pas de crash
- Texte extrait cohérent
- Confiance scores raisonnables (> 50%)

**Livrable :** Test d'intégration passing

---

### Task 4.3 : Benchmark performance
**Objectif :** Mesurer temps et RAM par engine

**Fichier :** `scripts/benchmark_ocr.py` (NEW)

**Métriques :**
- Temps/cell (ms)
- RAM pic (MB)
- Temps total/page (s)
- Throughput (cells/sec)

**Output :**
```
Benchmark OCR Engines (100 cells from PDF)

Tesseract:
  Time per cell: 142.3 ms ± 18.5
  Peak RAM: 52 MB
  Throughput: 7.0 cells/sec
  Total: 14.2 sec

PaddleOCR (CPU):
  Time per cell: 285.7 ms ± 42.1
  Peak RAM: 385 MB
  Throughput: 3.5 cells/sec
  Total: 28.6 sec

PaddleOCR (GPU):
  Time per cell: 187.4 ms ± 15.3
  Peak RAM: 620 MB
  Throughput: 5.3 cells/sec
  Total: 18.7 sec
```

**Livrable :** scripts/benchmark_ocr.py avec résultats

---

### Task 4.4 : Comparaison précision Tesseract vs Paddle
**Objectif :** F1-score et WER sur 10 cellules échantillonnées

**Fichier :** `scripts/compare_precision.py` (NEW)

**Ground truth :** Annotation manuelle de 10 cellules du PDF

**Métriques :**
- WER (Word Error Rate)
- CER (Character Error Rate)
- F1-score
- Cas où Paddle gagne vs Tesseract perd

**Output :**
```
Precision Comparison (10 cells)

Tesseract:
  WER: 2.3%
  CER: 0.8%
  F1: 0.975

PaddleOCR:
  WER: 1.8%
  CER: 0.6%
  F1: 0.981

Paddle improvement: +0.6 points F1
Cases where Paddle wins: 1/10
```

**Livrable :** scripts/compare_precision.py avec analyse

---

## Phase 5 : Documentation et Finalization

### Task 5.1 : Documenter OCREngine dans README
**Objectif :** Ajouter section "OCR Engines" au README

**Fichier :** `README.md`

**Contenu à ajouter :**
- Comparaison Tesseract vs PaddleOCR
- Options CLI (--ocr-mode, --gpu)
- Configuration par défaut
- Quand utiliser chaque mode
- Exemples d'utilisation

**Livrable :** README mis à jour

---

### Task 5.2 : Docstrings complètes
**Objectif :** Ajouter docstrings suivant format RST/Google

**Fichier :** `src/ocr_engine.py`

**Éléments :**
- Classes
- Toutes les méthodes publiques/privées
- Paramètres et retours typés
- Exemples d'utilisation

**Livrable :** ocr_engine.py entièrement documenté

---

### Task 5.3 : Créer guide d'utilisation
**Objectif :** Doc pour débuter avec PaddleOCR

**Fichier :** `docs/PADDLE_OCR_GUIDE.md` (NEW)

**Sections :**
1. Installation et setup
2. Options CLI
3. Quand utiliser hybrid vs paddle
4. Troubleshooting GPU
5. Exemples complets

**Livrable :** docs/PADDLE_OCR_GUIDE.md

---

## 📊 Checklist de Validation

Avant de merger :

- [ ] Tous les tests passent (> 80% couverture)
- [ ] Tesseract reste le mode par défaut (backward compat)
- [ ] PaddleOCR fallback marche sur ≥ 1 cas réel du PDF
- [ ] Pas de crash sur mode "tesseract-only"
- [ ] JSON structuré contient ocr_details complets
- [ ] Benchmarks montrent perf acceptable
- [ ] README et docs complètes
- [ ] Pas de dépendance GPU forcée
- [ ] GPU optionnel marche si dispo

