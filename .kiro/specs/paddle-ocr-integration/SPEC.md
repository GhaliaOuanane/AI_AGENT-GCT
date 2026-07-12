# 🚀 SPEC : Intégration PaddleOCR comme Fallback

## 📌 Vue d'ensemble

Ajouter **PaddleOCR** comme moteur OCR secondaire au pipeline d'extraction, avec fallback automatique depuis Tesseract en cas d'erreur ou de faible confiance. Le système reste hybride : Tesseract par défaut (rapide, léger), PaddleOCR comme secours (robuste, deep learning).

**Objectif final :** Améliorer la robustesse de l'OCR sur des PDFs scannés bruyants sans sacrifier les performances sur les cas nominaux.

---

## 🎯 Objectifs

1. ✅ Créer une interface OCR polymorphe (`OCREngine`)
2. ✅ Implémenter `TesseractOCR` (engine par défaut)
3. ✅ Implémenter `PaddleOCREngine` (fallback)
4. ✅ Router automatique : Tesseract → PaddleOCR en cas d'erreur
5. ✅ Ajouter scores de confiance réels (PaddleOCR native)
6. ✅ Logger la raison du fallback (tracabilité)
7. ✅ Ajouter options CLI (`--hybrid`, `--paddle-only`, `--gpu`)
8. ✅ Benchmarking : timing, RAM, précision

---

## 📐 Architecture

### Hiérarchie des modules

```
src/
├── ocr_engine.py          [NEW] Interface polymorphe + factory
│   ├── OCREngine (abstract)
│   ├── TesseractOCR (impl)
│   ├── PaddleOCREngine (impl)
│   └── OCREngineFactory
│
├── column_extractor.py    [MODIFIÉ] Intégration du router OCR
│   └── extract_cell() utilise OCREngine au lieu de pytesseract direct
│
└── main.py                [MODIFIÉ] CLI + options engines
    └── --hybrid / --paddle-only / --gpu
```

### Flux décisionnel

```
ocr_cell(image) 
  ↓
TesseractOCR.recognize(image)
  ├─ [SUCCESS + conf >= 70%] → Return
  ├─ [ERROR] → Log + Fallback
  └─ [conf < 70%] → Soft-fallback
         ↓
    PaddleOCREngine.recognize(image)
      ├─ [SUCCESS] → Return + Log "PADDLE_FALLBACK"
      ├─ [FAILED] → Raise + Log "DUAL_FAILURE"
      └─ Return (text, engine, confidence)
```

### Score de confiance

- **Tesseract** : Estimation via longueur + regex validity
  - Formule : `min(100, len(text) * 5 + regex_bonus)`
  - Seuil soft-fallback : 70%

- **PaddleOCR** : Score natif (0-1 par mot)
  - Moyenne des scores par mot
  - Convertis en 0-100

---

## 🔧 Design détaillé

### 1. Interface abstraite `OCREngine`

```python
class OCREngine(ABC):
    @abstractmethod
    def recognize(self, image: np.ndarray, lang: str = "fra") 
        → Tuple[str, float, Dict[str, Any]]:
        """
        Returns: (text, confidence_score, metadata)
        metadata: {
            "engine": "tesseract"|"paddle",
            "execution_time": float,
            "words_count": int,
            "error": None|str
        }
        """
        pass
    
    @abstractmethod
    def verify_setup(self) → bool:
        """Vérifie la config au démarrage."""
        pass
```

### 2. Implémentation Tesseract

```python
class TesseractOCR(OCREngine):
    def __init__(self, tesseract_cmd: Optional[str] = None):
        self.tesseract_cmd = tesseract_cmd or self._find_tesseract()
        self.confidence_threshold = 70
    
    def recognize(self, image, lang="fra"):
        # PSM 6 : bloc texte uniforme
        # Output DICT pour confiance par mot
        data = pytesseract.image_to_data(image, lang=lang, 
                                         config="--psm 6",
                                         output_type=pytesseract.Output.DICT)
        
        text = " ".join(data['text']).strip()
        confidence = self._compute_confidence(data)
        
        return text, confidence, {
            "engine": "tesseract",
            "execution_time": ...,
            "words_count": len([w for w in data['text'] if w.strip()])
        }
    
    def _compute_confidence(self, ocr_data: Dict) -> float:
        # Moyenne des confiances tesseract
        # Si < 70%, ready pour fallback
        pass
```

### 3. Implémentation PaddleOCR

```python
class PaddleOCREngine(OCREngine):
    def __init__(self, use_gpu: bool = False, 
                 model_dir: Optional[Path] = None):
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang=['ch', 'en', 'fr'],  # Support FR natif
            gpu=use_gpu,
            model_storage_directory=model_dir,
            enable_mkldnn=not use_gpu
        )
    
    def recognize(self, image, lang="fra"):
        results = self.ocr.ocr(image, cls=True)
        text = self._extract_text(results)
        confidence = self._extract_confidence(results)
        
        return text, confidence, {
            "engine": "paddle",
            "execution_time": ...,
            "words_count": len(results[0]) if results else 0
        }
    
    def _extract_text(self, results) → str:
        # results[0] = list of ([x,y], text, conf)
        pass
    
    def _extract_confidence(self, results) → float:
        # Moyenne des confiances paddle (0-1) → 0-100
        pass
```

### 4. Factory + Router

```python
class OCREngineRouter:
    def __init__(self, mode: str = "hybrid", use_gpu: bool = False):
        """
        mode: "tesseract" | "paddle" | "hybrid"
        """
        self.mode = mode
        self.primary = TesseractOCR()
        self.fallback = PaddleOCREngine(use_gpu=use_gpu) if mode != "tesseract" else None
        self.stats = {
            "primary_success": 0,
            "primary_fallback": 0,
            "dual_failure": 0,
            "confidence_fallback": 0
        }
    
    def recognize(self, image: np.ndarray, lang: str = "fra") 
        → Tuple[str, float, Dict]:
        """
        Route vers primary/fallback selon mode et résultat.
        """
        if self.mode == "paddle":
            return self.fallback.recognize(image, lang)
        
        # Mode tesseract ou hybrid
        try:
            text, conf, meta = self.primary.recognize(image, lang)
            
            if self.mode == "hybrid" and conf < 70:
                # Soft fallback : confiance faible
                self.stats["confidence_fallback"] += 1
                text, conf, meta = self._fallback_recognize(image, lang)
            else:
                self.stats["primary_success"] += 1
            
            return text, conf, meta
        
        except Exception as e:
            self.stats["primary_fallback"] += 1
            if self.fallback:
                return self._fallback_recognize(image, lang)
            else:
                raise OCRError(f"Primary OCR failed: {e}")
    
    def _fallback_recognize(self, image, lang):
        try:
            text, conf, meta = self.fallback.recognize(image, lang)
            meta["fallback_reason"] = "tesseract_error"
            return text, conf, meta
        except Exception as e:
            self.stats["dual_failure"] += 1
            raise OCRError(f"Both OCR engines failed: {e}")
```

---

## 📊 Données et Formats

### Modifications du JSON structuré

```json
{
  "fichier": "BRAIN INFORMATIQUE_16052025101905.PDF",
  "page": 1,
  "designation": "Résolution de l'impression",
  "specification": "1200*1200 dpi",
  "proposition": "1200*1200 dpi",
  "ocr_details": {
    "designation": {
      "engine": "tesseract",
      "confidence": 95,
      "execution_time_ms": 145,
      "fallback_reason": null
    },
    "specification": {
      "engine": "paddle",
      "confidence": 87,
      "execution_time_ms": 280,
      "fallback_reason": "tesseract_low_confidence"
    },
    "proposition": {
      "engine": "tesseract",
      "confidence": 92,
      "execution_time_ms": 138,
      "fallback_reason": null
    }
  }
}
```

### Résumé global (après extraction)

```
[SUMMARY] Pages: 6, Lignes: 42
[OCR_STATS] Primary success: 126/128 (98%)
[OCR_STATS] Confidence fallback: 2/128 (1.6%)
[OCR_STATS] Dual failure: 0
[OCR_STATS] Avg confidence: 93.2%
[PERFORMANCE] Tesseract: 0.142s/cell, RAM: 52MB
[PERFORMANCE] PaddleOCR: 0.285s/cell, RAM: 385MB (GPU: 620MB)
[GPU_INFO] GPU available: True, GPU used: True
```

---

## 🧪 Tests et Validation

### Test 1 : Fallback automatique
- OCRiser cellule volontairement dégradée → Tesseract échoue → Paddle réussit
- Vérifier `fallback_reason` dans JSON

### Test 2 : Soft fallback (confiance faible)
- OCRiser cellule avec 50% de confiance Tesseract → Paddle appelé
- Vérifier amélioration de confiance

### Test 3 : Performance
- Mode "tesseract" : < 200ms/cell
- Mode "hybrid" : < 350ms/cell (fallback rare)
- Mode "paddle" : < 400ms/cell (GPU) ou < 1s (CPU)

### Test 4 : Précision
- Comparer Tesseract vs Paddle sur 10 cellules du PDF réel
- F1-score, WER (Word Error Rate)

---

