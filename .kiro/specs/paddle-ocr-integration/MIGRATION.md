# 🔄 Guide de Migration et Points d'Intégration

## 1. Backward Compatibility

### 1.1 Code existant non affecté

**Tesseract reste le mode par défaut :**
```python
# Ancien code continue de marcher
ocr_router = OCREngineRouter()  # Mode hybrid par défaut, mais Tesseract en priorité
text, conf, meta = ocr_router.recognize(image)
```

**Fallback PaddleOCR transparent :**
```python
# Si tu utilises mode="tesseract", c'est 100% compatible
ocr_router = OCREngineRouter(mode="tesseract")
```

### 1.2 API column_extractor.py inchangée

```python
# Ancien code :
results = extract_structured_rows(pdf_path)

# Nouveau code (optionnel) :
ocr_router = OCREngineRouter(mode="hybrid", use_gpu=True)
results = extract_structured_rows(pdf_path, ocr_router=ocr_router)
```

---

## 2. Points d'Intégration Clés

### 2.1 src/ocr_engine.py (NOUVEAU)

**Créer ce fichier avec :**
- `OCREngine` (abstract)
- `TesseractOCR` (impl)
- `PaddleOCREngine` (impl)
- `OCREngineRouter` (orchestration)
- `OCRError` (exception)
- Fonction utilitaire `verify_all_engines()`

**Taille anticipée :** ~400-500 lignes

**Dépendances :**
```python
import pytesseract
from paddleocr import PaddleOCR
import cv2
import numpy as np
import time
from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, Optional
from pathlib import Path
```

---

### 2.2 Modifications minimal requirements.txt

**Ajouter :**
```
paddleocr>=2.7.0
paddlepaddle>=2.5.0
```

**Note :** `paddlepaddle` par défaut = CPU. Pour GPU : installer `paddlepaddle-gpu` manuellement (optionnel).

**Ordre recommandé :**
```
# Existants
pypdf
pdf2image
Pillow
opencv-python
pytesseract
pymupdf
rapidfuzz
scikit-learn
numpy
pandas
openpyxl

# Nouveaux
paddleocr>=2.7.0
paddlepaddle>=2.5.0
```

---

### 2.3 src/column_extractor.py (MODIFICATIONS LÉGÈRES)

**Import à ajouter :**
```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from ocr_engine import OCREngineRouter, OCRError, verify_all_engines
```

**Changement dans `extract_structured_rows()` :**

```python
# AVANT :
def extract_structured_rows(pdf_path: str | Path) → List[Dict]:
    # ...
    text = ocr_cell(cell_img)  # Appel direct pytesseract

# APRÈS :
def extract_structured_rows(
    pdf_path: str | Path,
    ocr_router: Optional[OCREngineRouter] = None
) → List[Dict]:
    if ocr_router is None:
        ocr_router = OCREngineRouter(mode="hybrid")
    
    # ...
    try:
        text, conf, meta = ocr_router.recognize(cell_img)
    except OCRError as e:
        text = ""
        conf = 0
        meta = {"engine": "error", "error": str(e)}
```

**JSON enrichi :**
```json
"ocr_details": {
    "designation": {
        "engine": "tesseract",
        "confidence": 95,
        "execution_time_ms": 145,
        "fallback_reason": null
    }
}
```

**Fonction `print_summary()` enrichie :**
```python
def print_summary(results: List[Dict], ocr_router: OCREngineRouter) → None:
    # Stats existantes + nouvelles
    print(f"[OCR_STATS] Tesseract success: {ocr_router.stats['tesseract_success']}")
    print(f"[OCR_STATS] Fallback used: {ocr_router.stats['confidence_fallback']}")
    ocr_router.print_stats()
```

**Taille modifications :** ~50-100 lignes (ajouter, remplacer minimal)

---

### 2.4 src/main.py (MODIFICATIONS LÉGÈRES)

**Import :**
```python
from ocr_engine import OCREngineRouter, verify_all_engines
import argparse
```

**Ajout argparse :**
```python
parser.add_argument(
    "--ocr-mode",
    choices=["tesseract", "paddle", "hybrid"],
    default="hybrid",
    help="OCR engine mode (default: hybrid)"
)
parser.add_argument(
    "--gpu",
    action="store_true",
    help="Use GPU for PaddleOCR if available"
)
parser.add_argument(
    "--ocr-stats",
    action="store_true",
    help="Print detailed OCR statistics"
)
```

**Appel vérification au démarrage :**
```python
def main():
    args = parser.parse_args()
    
    print("[CHECK] Verifying OCR setup...")
    verify_all_engines(use_gpu=args.gpu)
    
    ocr_router = OCREngineRouter(
        mode=args.ocr_mode,
        use_gpu=args.gpu
    )
    
    results = extract_structured_rows(pdf_path, ocr_router=ocr_router)
    
    if args.ocr_stats:
        ocr_router.print_stats()
```

**Taille modifications :** ~50 lignes

---

## 3. Étapes d'Implémentation Recommandées

### Phase 1 : Foundation (1-2 jours)
1. ✅ Créer `src/ocr_engine.py` complet
2. ✅ Tests unitaires basiques (Tesseract + Paddle)
3. ✅ Ajouter dépendances requirements.txt

**Checkpoint :** Tesseract et Paddle peuvent tous les deux OCRiser une image

---

### Phase 2 : Intégration (1 jour)
4. ✅ Router + fallback logic dans ocr_engine.py
5. ✅ Modifier column_extractor.py minimal
6. ✅ Tests d'intégration

**Checkpoint :** Mode hybrid marche sur 2-3 pages du PDF réel

---

### Phase 3 : CLI & Ops (0.5 jour)
7. ✅ Argparse dans main.py
8. ✅ Vérification setup au démarrage
9. ✅ Stats OCR en sortie

**Checkpoint :** `python src/main.py --ocr-mode hybrid --gpu --ocr-stats` marche

---

### Phase 4 : Tests et Benchmarks (1-2 jours)
10. ✅ Tests complets (> 80% couverture)
11. ✅ Benchmark OCR (timing, RAM)
12. ✅ Comparaison précision

**Checkpoint :** Tous les tests passent, benchmarks documentés

---

### Phase 5 : Documentation (0.5 jour)
13. ✅ README updated
14. ✅ Docstrings complets
15. ✅ Guide PADDLE_OCR_GUIDE.md

---

## 4. Dépannage Intégration

### 4.1 Import PaddleOCR fail

**Symptôme :**
```
ImportError: No module named 'paddleocr'
```

**Solution :**
```bash
pip install paddleocr paddlepaddle
# ou pour GPU :
pip install paddleocr paddlepaddle-gpu
```

---

### 4.2 GPU non détecté

**Symptôme :**
```
[WARN] GPU requested but not available
```

**Solution :**
```bash
# Vérifier Torch/CUDA
python -c "import torch; print(torch.cuda.is_available())"

# Si false, cuda pas installé
# Sinon, PaddleOCR ne voit pas GPU (config CUDA)
```

---

### 4.3 Modèles PaddleOCR trop lourds

**Symptôme :**
```
Downloading models to ~/.paddleocr (500MB+)...
```

**Solution :**
```python
# Définir MODEL_DIR custom dans ocr_engine.py
model_dir = Path(__file__).parent.parent / "models" / "paddle"
paddle_engine = PaddleOCREngine(model_dir=model_dir)
```

---

### 4.4 Fallback jamais appelé

**Diagnostic :**
```python
# Mode hybrid mais Paddle jamais utilisé ?
router.print_stats()  # Vérifier confidence_fallback count

# Si 0, c'est normal ! Tesseract marche bien
```

---

## 5. Checklist d'Intégration

- [ ] `src/ocr_engine.py` créé et tests passent
- [ ] `requirements.txt` updated
- [ ] `src/column_extractor.py` modifié (50-100 lignes)
- [ ] `src/main.py` modifié (50 lignes, CLI OK)
- [ ] JSON structuré contient `ocr_details`
- [ ] Mode "tesseract" par défaut (backward compat)
- [ ] Mode "hybrid" fonctionne sur PDF réel
- [ ] Mode "paddle" fonctionne (CPU et GPU)
- [ ] Verification setup au démarrage
- [ ] Stats OCR en sortie
- [ ] README et docs updated
- [ ] Tests > 80% couverture
- [ ] Benchmarks documentés
- [ ] Aucun crash sur mode "tesseract-only"

---

## 6. Rollback si Problèmes

Si PaddleOCR crée des problèmes :

```bash
# Revenir à Tesseract uniquement
git checkout src/ocr_engine.py src/column_extractor.py src/main.py
pip uninstall paddleocr paddlepaddle
```

Code reste compatible car Tesseract est le fallback naturel.

