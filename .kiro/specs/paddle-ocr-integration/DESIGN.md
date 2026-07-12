# 🏗️ Design Détaillé : Intégration PaddleOCR

## 1. Hiérarchie des classes

### 1.1 Interface abstraite `OCREngine`

```python
from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, Optional
import numpy as np

class OCREngine(ABC):
    """
    Interface commune pour tous les engines OCR.
    """
    
    @abstractmethod
    def recognize(self, image: np.ndarray, lang: str = "fra") \
            → Tuple[str, float, Dict[str, Any]]:
        """
        Reconnaît le texte dans une image.
        
        Args:
            image: Image numpy (RGB ou grayscale)
            lang: Code langue ISO (fra, eng, etc.)
        
        Returns:
            Tuple de (text, confidence, metadata)
            - text: Texte extrait
            - confidence: Score 0-100
            - metadata: {
                "engine": "tesseract"|"paddle",
                "execution_time_ms": float,
                "words_count": int,
                "error": None|str,
                "fallback_reason": None|str
              }
        """
        pass
    
    @abstractmethod
    def verify_setup(self) → bool:
        """Vérifie que l'engine est correctement configuré."""
        pass
    
    @property
    @abstractmethod
    def name(self) → str:
        """Retourne le nom de l'engine."""
        pass
```

### 1.2 Implémentation `TesseractOCR`

```python
import pytesseract
import time
from pathlib import Path
import re

class TesseractOCR(OCREngine):
    """Wrapper pour Tesseract OCR."""
    
    def __init__(self, tesseract_cmd: Optional[str] = None, 
                 confidence_threshold: int = 70):
        """
        Args:
            tesseract_cmd: Chemin vers tesseract.exe (auto-détecté si None)
            confidence_threshold: Seuil pour fallback (0-100)
        """
        self.tesseract_cmd = tesseract_cmd or self._find_tesseract()
        if self.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
        self.confidence_threshold = confidence_threshold
    
    def recognize(self, image: np.ndarray, lang: str = "fra") \
            → Tuple[str, float, Dict[str, Any]]:
        start_time = time.time()
        metadata = {"engine": "tesseract"}
        
        try:
            # Extraire avec données de confiance par mot
            data = pytesseract.image_to_data(
                image, 
                lang=lang,
                config="--psm 6",  # bloc texte uniforme
                output_type=pytesseract.Output.DICT
            )
            
            text = " ".join(data['text']).strip()
            confidence = self._compute_confidence(data)
            
            metadata.update({
                "execution_time_ms": (time.time() - start_time) * 1000,
                "words_count": len([w for w in data['text'] if w.strip()]),
                "error": None,
                "fallback_reason": None
            })
            
            return text, confidence, metadata
        
        except Exception as e:
            metadata.update({
                "execution_time_ms": (time.time() - start_time) * 1000,
                "words_count": 0,
                "error": str(e),
                "fallback_reason": None
            })
            raise OCRError(f"Tesseract recognition failed: {e}")
    
    def verify_setup(self) → bool:
        """Vérifie Tesseract et la langue française."""
        try:
            version = pytesseract.get_tesseract_version()
            languages = pytesseract.get_languages(config='')
            
            if 'fra' not in languages:
                print("[WARN] French language not available in Tesseract")
                return False
            
            return True
        except Exception as e:
            print(f"[ERROR] Tesseract verification failed: {e}")
            return False
    
    def _find_tesseract(self) → Optional[str]:
        """Détecte automatiquement le chemin tesseract.exe."""
        candidates = [
            Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
            Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
            Path("/usr/bin/tesseract"),
            Path("/usr/local/bin/tesseract"),
        ]
        
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        
        return None
    
    def _compute_confidence(self, ocr_data: Dict) → float:
        """
        Calcule la confiance globale à partir des données OCR.
        
        Formule : moyenne des confiances par mot (0-100)
        """
        confidences = []
        
        for i, conf_str in enumerate(ocr_data.get('conf', [])):
            if ocr_data['text'][i].strip():  # Ignorer les espaces
                try:
                    conf = float(conf_str)
                    confidences.append(conf)
                except (ValueError, TypeError):
                    pass
        
        if not confidences:
            # Fallback : estimation basée sur la longueur du texte
            text = " ".join(ocr_data.get('text', [])).strip()
            return min(100, max(0, len(text) * 2))
        
        return min(100, sum(confidences) / len(confidences))
    
    @property
    def name(self) → str:
        return "tesseract"
```

### 1.3 Implémentation `PaddleOCREngine`

```python
from paddleocr import PaddleOCR
import cv2

class PaddleOCREngine(OCREngine):
    """Wrapper pour PaddleOCR."""
    
    def __init__(self, use_gpu: bool = False, 
                 model_dir: Optional[Path] = None,
                 use_angle_cls: bool = True):
        """
        Args:
            use_gpu: Utiliser GPU si disponible
            model_dir: Dossier des modèles (défaut: ~/.paddleocr)
            use_angle_cls: Activer détection d'angle (améliore robustesse)
        """
        self.use_gpu = use_gpu
        
        try:
            self.ocr = PaddleOCR(
                use_angle_cls=use_angle_cls,
                lang=['ch', 'en', 'fr'],
                gpu=use_gpu,
                model_storage_directory=str(model_dir) if model_dir else None,
                enable_mkldnn=not use_gpu,  # CPU optimization
                verbose=False  # Pas de logs parasites
            )
        except Exception as e:
            raise OCRError(f"Failed to initialize PaddleOCR: {e}")
    
    def recognize(self, image: np.ndarray, lang: str = "fra") \
            → Tuple[str, float, Dict[str, Any]]:
        start_time = time.time()
        metadata = {"engine": "paddle"}
        
        try:
            # Convertir en RGB si nécessaire
            if len(image.shape) == 2:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            else:
                image_rgb = image
            
            # OCR
            results = self.ocr.ocr(image_rgb, cls=True)
            
            # Extraire texte et confiance
            text = self._extract_text(results)
            confidence = self._extract_confidence(results)
            
            metadata.update({
                "execution_time_ms": (time.time() - start_time) * 1000,
                "words_count": len(results[0]) if results else 0,
                "error": None,
                "fallback_reason": None
            })
            
            return text, confidence, metadata
        
        except Exception as e:
            metadata.update({
                "execution_time_ms": (time.time() - start_time) * 1000,
                "words_count": 0,
                "error": str(e),
                "fallback_reason": None
            })
            raise OCRError(f"PaddleOCR recognition failed: {e}")
    
    def verify_setup(self) → bool:
        """Vérifie que PaddleOCR est correctement configuré."""
        try:
            # Essayer de charger les modèles
            _ = self.ocr
            return True
        except Exception as e:
            print(f"[ERROR] PaddleOCR verification failed: {e}")
            return False
    
    def _extract_text(self, results: List) → str:
        """Extrait le texte depuis les résultats PaddleOCR."""
        if not results or not results[0]:
            return ""
        
        text_parts = []
        for line in results[0]:
            # line = ([x,y], text, confidence)
            if len(line) >= 2:
                text_parts.append(line[1])
        
        return " ".join(text_parts).strip()
    
    def _extract_confidence(self, results: List) → float:
        """Extrait la confiance moyenne depuis les résultats."""
        if not results or not results[0]:
            return 0.0
        
        confidences = []
        for line in results[0]:
            if len(line) >= 3:
                try:
                    conf = float(line[2])
                    confidences.append(conf)
                except (ValueError, TypeError):
                    pass
        
        if not confidences:
            return 50.0
        
        # Convertir 0-1 en 0-100
        avg_conf = sum(confidences) / len(confidences)
        return min(100, max(0, avg_conf * 100))
    
    @property
    def name(self) → str:
        return "paddle"
```

---

## 2. Router et Fallback

### 2.1 Classe `OCREngineRouter`

```python
class OCREngineRouter:
    """
    Routeur intelligent pour l'OCR avec fallback automatique.
    """
    
    MODE_TESSERACT = "tesseract"
    MODE_PADDLE = "paddle"
    MODE_HYBRID = "hybrid"
    
    def __init__(self, mode: str = "hybrid", use_gpu: bool = False):
        """
        Args:
            mode: "tesseract" | "paddle" | "hybrid"
            use_gpu: Utiliser GPU pour PaddleOCR
        """
        if mode not in [self.MODE_TESSERACT, self.MODE_PADDLE, self.MODE_HYBRID]:
            raise ValueError(f"Invalid OCR mode: {mode}")
        
        self.mode = mode
        self.use_gpu = use_gpu
        
        # Initialiser les engines
        self.tesseract = TesseractOCR()
        self.paddle = None
        
        if mode in [self.MODE_PADDLE, self.MODE_HYBRID]:
            self.paddle = PaddleOCREngine(use_gpu=use_gpu)
        
        # Stats
        self.stats = {
            "tesseract_success": 0,
            "tesseract_error": 0,
            "paddle_success": 0,
            "paddle_error": 0,
            "confidence_fallback": 0,
            "total_calls": 0
        }
        self.confidence_threshold = 70
    
    def recognize(self, image: np.ndarray, lang: str = "fra") \
            → Tuple[str, float, Dict[str, Any]]:
        """
        Reconnaît le texte avec fallback automatique.
        """
        self.stats["total_calls"] += 1
        
        if self.mode == self.MODE_TESSERACT:
            return self._recognize_tesseract_only(image, lang)
        
        elif self.mode == self.MODE_PADDLE:
            return self._recognize_paddle_only(image, lang)
        
        else:  # HYBRID
            return self._recognize_hybrid(image, lang)
    
    def _recognize_tesseract_only(self, image: np.ndarray, lang: str) \
            → Tuple[str, float, Dict[str, Any]]:
        """Mode Tesseract seul."""
        try:
            text, conf, meta = self.tesseract.recognize(image, lang)
            self.stats["tesseract_success"] += 1
            return text, conf, meta
        except OCRError as e:
            self.stats["tesseract_error"] += 1
            raise OCRError(f"Tesseract failed (no fallback in tesseract-only mode): {e}")
    
    def _recognize_paddle_only(self, image: np.ndarray, lang: str) \
            → Tuple[str, float, Dict[str, Any]]:
        """Mode PaddleOCR seul."""
        try:
            text, conf, meta = self.paddle.recognize(image, lang)
            self.stats["paddle_success"] += 1
            return text, conf, meta
        except OCRError as e:
            self.stats["paddle_error"] += 1
            raise OCRError(f"PaddleOCR failed (no fallback in paddle-only mode): {e}")
    
    def _recognize_hybrid(self, image: np.ndarray, lang: str) \
            → Tuple[str, float, Dict[str, Any]]:
        """Mode hybride : Tesseract d'abord, PaddleOCR si besoin."""
        
        # Essayer Tesseract
        try:
            text, conf, meta = self.tesseract.recognize(image, lang)
            self.stats["tesseract_success"] += 1
            
            # Vérifier la confiance
            if conf >= self.confidence_threshold:
                return text, conf, meta
            
            # Confiance trop basse → Fallback
            self.stats["confidence_fallback"] += 1
            return self._fallback_to_paddle(image, lang, "low_confidence")
        
        except OCRError as e:
            # Tesseract crash → Fallback
            self.stats["tesseract_error"] += 1
            return self._fallback_to_paddle(image, lang, "tesseract_error")
    
    def _fallback_to_paddle(self, image: np.ndarray, lang: str, 
                           fallback_reason: str) \
            → Tuple[str, float, Dict[str, Any]]:
        """Fallback vers PaddleOCR."""
        try:
            text, conf, meta = self.paddle.recognize(image, lang)
            meta["fallback_reason"] = fallback_reason
            self.stats["paddle_success"] += 1
            return text, conf, meta
        except OCRError as e:
            self.stats["paddle_error"] += 1
            raise OCRError(f"Both engines failed. Primary: {fallback_reason}, "
                          f"Fallback: {e}")
    
    def get_stats(self) → Dict[str, int]:
        """Retourne les stats d'utilisation."""
        return self.stats.copy()
    
    def print_stats(self) → None:
        """Affiche les stats de façon lisible."""
        print("\n[OCR_STATS] Engine Statistics")
        print(f"  Total calls: {self.stats['total_calls']}")
        print(f"  Tesseract success: {self.stats['tesseract_success']} "
              f"({100*self.stats['tesseract_success']/max(1, self.stats['total_calls']):.1f}%)")
        print(f"  Tesseract errors: {self.stats['tesseract_error']}")
        print(f"  Confidence fallback: {self.stats['confidence_fallback']}")
        print(f"  PaddleOCR success: {self.stats['paddle_success']}")
        print(f"  PaddleOCR errors: {self.stats['paddle_error']}")
        print(f"  Mode: {self.mode}")
        if self.use_gpu:
            print(f"  GPU: Enabled")
```

---

## 3. Exception personnalisée

```python
class OCRError(Exception):
    """Exception levée lors de problèmes OCR."""
    pass
```

---

## 4. Intégration dans column_extractor.py

### 4.1 Modification de `extract_structured_rows()`

```python
def extract_structured_rows(
    pdf_path: str | Path,
    ocr_router: Optional[OCREngineRouter] = None
) → List[Dict]:
    """
    Extrait toutes les lignes structurées du PDF.
    
    Args:
        pdf_path: Chemin du PDF
        ocr_router: Router OCR (créé si None)
    
    Returns:
        Liste de dictionnaires structurés
    """
    if ocr_router is None:
        ocr_router = OCREngineRouter(mode="hybrid")
    
    doc = fitz.open(pdf_path)
    results = []
    
    for page_num in range(doc.page_count):
        # ... code de détection de grille ...
        
        for role in ["designation", "specification", "proposition"]:
            if role in role_to_col_idx:
                col_idx = role_to_col_idx[role]
                cell_img = extract_cell_from_image(img_gray, cell_bbox)
                
                # Utiliser le router au lieu de pytesseract direct
                try:
                    text, confidence, ocr_meta = ocr_router.recognize(cell_img)
                except OCRError as e:
                    text = ""
                    confidence = 0
                    ocr_meta = {"error": str(e), "engine": "unknown"}
                
                row_data[role] = text
                row_data["ocr_details"][role] = {
                    "engine": ocr_meta.get("engine"),
                    "confidence": confidence,
                    "fallback_reason": ocr_meta.get("fallback_reason"),
                    "execution_time_ms": ocr_meta.get("execution_time_ms", 0)
                }
    
    return results
```

---

## 5. Détection automatique GPU

```python
def detect_gpu_availability() → bool:
    """Détecte si GPU est disponible pour PaddleOCR."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        # PaddleOCR peut avoir ses propres detecteurs GPU
        return False
    except Exception:
        return False
```

---

## 6. Factory avec options CLI

```python
def create_ocr_router(
    mode: str = "hybrid",
    use_gpu: Optional[bool] = None,
    gpu_auto_detect: bool = True
) → OCREngineRouter:
    """
    Factory pour créer un OCREngineRouter.
    
    Args:
        mode: "tesseract"|"paddle"|"hybrid"
        use_gpu: Forcer GPU on/off (None = auto-détect)
        gpu_auto_detect: Auto-détecter GPU
    """
    
    if use_gpu is None:
        use_gpu = gpu_auto_detect and detect_gpu_availability()
    
    return OCREngineRouter(mode=mode, use_gpu=use_gpu)
```

