"""
Module de validation d'entrée basé sur la qualité d'image.

Stratégie:
- Évaluation de la lisibilité (résolution, netteté, contraste) plutôt que présence de texte
- Acceptation des scans nets haute résolution
- Rejet uniquement des scans de mauvaise qualité
- 2 chemins: "numerique" (pas d'OCR) et "scanne_net" (OCR activé)
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, Literal
import fitz  # PyMuPDF
import json
from datetime import datetime
import numpy as np
import cv2


# Configuration - Seuils de qualité image
MINIMUM_DPI = 200  # DPI minimum pour considérer une image exploitable
IDEAL_DPI = 300  # DPI idéal
MINIMUM_SHARPNESS = 100  # Variance Laplacien minimum (netteté)
MINIMUM_CONTRAST_STD = 15  # Écart-type minimum des niveaux de gris
TEXT_COVERAGE_THRESHOLD = 5  # % pour détecter si c'est un PDF numérique


@dataclass
class ImageQualityMetrics:
    """Métriques de qualité d'image pour un scan."""
    avg_dpi: float
    min_dpi: float
    max_dpi: float
    sharpness_score: float  # Variance Laplacien
    contrast_std: float  # Écart-type niveaux de gris
    is_sharp: bool
    is_high_resolution: bool
    has_good_contrast: bool


@dataclass
class ValidationResult:
    """Résultat de validation d'un PDF."""
    is_valid: bool
    document_type: Literal["numerique", "scanne_net", "scanne_mauvaise_qualite", "invalide"]
    reason: str
    metrics: Dict[str, Any]
    image_quality: Optional[ImageQualityMetrics] = None
    
    def to_dict(self) -> dict:
        """Convertit en dictionnaire pour JSON."""
        result = {
            "is_valid": self.is_valid,
            "document_type": self.document_type,
            "reason": self.reason,
            "metrics": self.metrics
        }
        if self.image_quality:
            result["image_quality"] = {
                "avg_dpi": self.image_quality.avg_dpi,
                "min_dpi": self.image_quality.min_dpi,
                "sharpness_score": self.image_quality.sharpness_score,
                "contrast_std": self.image_quality.contrast_std,
                "is_sharp": self.image_quality.is_sharp,
                "is_high_resolution": self.image_quality.is_high_resolution,
                "has_good_contrast": self.image_quality.has_good_contrast
            }
        return result


def _calculate_sharpness(img_array: np.ndarray) -> float:
    """
    Calcule la netteté d'une image via variance du Laplacien.
    
    Args:
        img_array: Image numpy array (RGB ou grayscale)
    
    Returns:
        Score de netteté (plus élevé = plus net)
    """
    # Convertir en niveaux de gris si nécessaire
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    # Calculer variance du Laplacien
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = laplacian.var()
    
    return float(variance)


def _calculate_contrast(img_array: np.ndarray) -> float:
    """
    Calcule le contraste d'une image via écart-type des niveaux de gris.
    
    Args:
        img_array: Image numpy array (RGB ou grayscale)
    
    Returns:
        Écart-type des niveaux de gris
    """
    # Convertir en niveaux de gris si nécessaire
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    return float(gray.std())


def _extract_image_quality_metrics(page, pdf_path: Path, page_num: int) -> Optional[ImageQualityMetrics]:
    """
    Extrait les métriques de qualité d'image d'une page.
    
    Args:
        page: Page PyMuPDF
        pdf_path: Chemin du PDF
        page_num: Numéro de page
    
    Returns:
        ImageQualityMetrics ou None si pas d'image
    """
    images = page.get_images(full=True)
    
    if not images:
        return None
    
    # Analyser toutes les images de la page
    dpis = []
    sharpness_scores = []
    contrast_scores = []
    
    for img_info in images:
        xref = img_info[0]
        
        try:
            # Extraire DPI via les rectangles d'image
            img_rects = page.get_image_rects(xref)
            if img_rects:
                # Estimer DPI basé sur la taille affichée vs taille réelle
                base_image = page.parent.extract_image(xref)
                img_width = base_image["width"]
                img_height = base_image["height"]
                
                for rect in img_rects:
                    # DPI = pixels / (taille_affichée_en_points / 72)
                    dpi_x = img_width / (rect.width / 72) if rect.width > 0 else 0
                    dpi_y = img_height / (rect.height / 72) if rect.height > 0 else 0
                    avg_dpi = (dpi_x + dpi_y) / 2
                    dpis.append(avg_dpi)
        except Exception:
            pass
    
    # Rendre la page pour analyse de netteté/contraste
    try:
        mat = fitz.Matrix(2.0, 2.0)  # 144 DPI pour analyse
        pix = page.get_pixmap(matrix=mat)
        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        
        if pix.n == 4:  # RGBA
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
        
        # Calculer netteté et contraste
        sharpness = _calculate_sharpness(img_array)
        contrast = _calculate_contrast(img_array)
        
        sharpness_scores.append(sharpness)
        contrast_scores.append(contrast)
    except Exception:
        pass
    
    if not dpis and not sharpness_scores:
        return None
    
    # Agréger les métriques
    avg_dpi = np.mean(dpis) if dpis else 0
    min_dpi = np.min(dpis) if dpis else 0
    max_dpi = np.max(dpis) if dpis else 0
    avg_sharpness = np.mean(sharpness_scores) if sharpness_scores else 0
    avg_contrast = np.mean(contrast_scores) if contrast_scores else 0
    
    return ImageQualityMetrics(
        avg_dpi=round(avg_dpi, 2),
        min_dpi=round(min_dpi, 2),
        max_dpi=round(max_dpi, 2),
        sharpness_score=round(avg_sharpness, 2),
        contrast_std=round(avg_contrast, 2),
        is_sharp=avg_sharpness >= MINIMUM_SHARPNESS,
        is_high_resolution=min_dpi >= MINIMUM_DPI,
        has_good_contrast=avg_contrast >= MINIMUM_CONTRAST_STD
    )


def validate_input_pdf(pdf_path: Path) -> ValidationResult:
    """
    Valide un PDF selon la qualité de lisibilité.
    
    Logique:
    1. Si PDF numérique (texte natif) → accepté, type "numerique"
    2. Si scan net + haute résolution + bon contraste → accepté, type "scanne_net"
    3. Si scan flou/basse résolution/faible contraste → rejeté
    
    Args:
        pdf_path: Chemin du fichier PDF à valider
    
    Returns:
        ValidationResult avec is_valid, document_type, reason, metrics
    """
    if not pdf_path.exists():
        return ValidationResult(
            is_valid=False,
            document_type="invalide",
            reason="fichier_introuvable",
            metrics={"error": f"File not found: {pdf_path}"}
        )
    
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        return ValidationResult(
            is_valid=False,
            document_type="invalide",
            reason="fichier_corrompu",
            metrics={"error": str(e)}
        )
    
    total_pages = len(doc)
    pages_with_text = 0
    total_text_length = 0
    
    # Métriques d'image (pour scans)
    all_image_metrics = []
    
    # Analyser les premières pages (échantillon)
    sample_size = min(3, total_pages)
    
    for page_num in range(sample_size):
        page = doc[page_num]
        
        # Extraction de texte
        text = page.get_text()
        text_length = len(text.strip())
        total_text_length += text_length
        
        if text_length >= 50:
            pages_with_text += 1
        
        # Métriques d'image
        img_metrics = _extract_image_quality_metrics(page, pdf_path, page_num)
        if img_metrics:
            all_image_metrics.append(img_metrics)
    
    doc.close()
    
    # Calculer la couverture texte
    text_coverage_percent = (pages_with_text / sample_size * 100) if sample_size > 0 else 0
    avg_chars_per_page = total_text_length / sample_size if sample_size > 0 else 0
    
    metrics = {
        "total_pages": total_pages,
        "sampled_pages": sample_size,
        "pages_with_text": pages_with_text,
        "text_coverage_percent": round(text_coverage_percent, 2),
        "avg_chars_per_page": round(avg_chars_per_page, 2)
    }
    
    # DÉCISION 1: PDF numérique natif (présence de texte exploitable)
    if text_coverage_percent >= TEXT_COVERAGE_THRESHOLD:
        return ValidationResult(
            is_valid=True,
            document_type="numerique",
            reason="document_numerique_natif",
            metrics=metrics
        )
    
    # DÉCISION 2: PDF scan - évaluer qualité image
    if not all_image_metrics:
        # Pas de texte ET pas d'images détectables
        return ValidationResult(
            is_valid=False,
            document_type="invalide",
            reason="document_vide_ou_corrompu",
            metrics=metrics
        )
    
    # Agréger les métriques d'image
    avg_image_quality = ImageQualityMetrics(
        avg_dpi=np.mean([m.avg_dpi for m in all_image_metrics]),
        min_dpi=np.min([m.min_dpi for m in all_image_metrics]),
        max_dpi=np.max([m.max_dpi for m in all_image_metrics]),
        sharpness_score=np.mean([m.sharpness_score for m in all_image_metrics]),
        contrast_std=np.mean([m.contrast_std for m in all_image_metrics]),
        is_sharp=np.mean([m.is_sharp for m in all_image_metrics]) >= 0.7,  # 70% pages nettes
        is_high_resolution=np.mean([m.is_high_resolution for m in all_image_metrics]) >= 0.7,
        has_good_contrast=np.mean([m.has_good_contrast for m in all_image_metrics]) >= 0.7
    )
    
    # Vérifier qualité
    quality_checks = [
        avg_image_quality.is_sharp,
        avg_image_quality.is_high_resolution,
        avg_image_quality.has_good_contrast
    ]
    
    quality_score = sum(quality_checks)
    
    # DÉCISION 2a: Scan de bonne qualité (au moins 2/3 critères OK)
    if quality_score >= 2:
        return ValidationResult(
            is_valid=True,
            document_type="scanne_net",
            reason="scan_haute_qualite_accepte",
            metrics=metrics,
            image_quality=avg_image_quality
        )
    
    # DÉCISION 2b: Scan de mauvaise qualité (rejet)
    rejection_reasons = []
    if not avg_image_quality.is_sharp:
        rejection_reasons.append(f"flou (nettete={avg_image_quality.sharpness_score:.0f}, seuil={MINIMUM_SHARPNESS})")
    if not avg_image_quality.is_high_resolution:
        rejection_reasons.append(f"basse resolution (min_dpi={avg_image_quality.min_dpi:.0f}, seuil={MINIMUM_DPI})")
    if not avg_image_quality.has_good_contrast:
        rejection_reasons.append(f"faible contraste (std={avg_image_quality.contrast_std:.0f}, seuil={MINIMUM_CONTRAST_STD})")
    
    return ValidationResult(
        is_valid=False,
        document_type="scanne_mauvaise_qualite",
        reason="scan_qualite_insuffisante: " + ", ".join(rejection_reasons),
        metrics=metrics,
        image_quality=avg_image_quality
    )


def log_rejected_file(pdf_path: Path, validation: ValidationResult, output_dir: Path = None) -> None:
    """
    Journalise un PDF rejeté dans rejected_files.json.
    
    Args:
        pdf_path: Chemin du fichier rejeté
        validation: Résultat de validation
        output_dir: Dossier de sortie (défaut: data/output)
    """
    if output_dir is None:
        output_dir = Path("data/output")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    rejected_file = output_dir / "rejected_files.json"
    
    # Charger les rejets existants
    if rejected_file.exists():
        try:
            with open(rejected_file, 'r', encoding='utf-8') as f:
                rejected_list = json.load(f)
        except Exception:
            rejected_list = []
    else:
        rejected_list = []
    
    # Ajouter le nouveau rejet
    rejection_entry = {
        "filename": pdf_path.name,
        "filepath": str(pdf_path),
        "rejected_at": datetime.now().isoformat(),
        "reason": validation.reason,
        "metrics": validation.metrics
    }
    
    rejected_list.append(rejection_entry)
    
    # Sauvegarder
    with open(rejected_file, 'w', encoding='utf-8') as f:
        json.dump(rejected_list, f, ensure_ascii=False, indent=2)


def get_rejection_message(pdf_path: Path, validation: ValidationResult) -> str:
    """
    Génère un message de rejet actionnable pour l'utilisateur.
    
    Args:
        pdf_path: Chemin du fichier rejeté
        validation: Résultat de validation
    
    Returns:
        Message formaté pour la console
    """
    metrics = validation.metrics
    
    if validation.document_type == "scanne_mauvaise_qualite":
        # Message spécifique pour scan de mauvaise qualité
        quality_info = ""
        if validation.image_quality:
            quality_info = f"""
Metriques detectees:
  - Resolution: {validation.image_quality.min_dpi:.0f} DPI (minimum requis: {MINIMUM_DPI})
  - Nettete: {validation.image_quality.sharpness_score:.0f} (minimum requis: {MINIMUM_SHARPNESS})
  - Contraste: {validation.image_quality.contrast_std:.0f} (minimum requis: {MINIMUM_CONTRAST_STD})"""
        
        message = f"""[REJET] "{pdf_path.name}" : scan de mauvaise qualite.
Raison: {validation.reason}{quality_info}

> Le document est illisible en l'etat.
> Merci de fournir:
  - Un scan haute resolution (300 DPI minimum)
  - Une image nette (pas floue)
  - Un bon contraste (pas delavee/pale)
  OU
  - La version numerique native (export PDF depuis le logiciel source)"""
    
    elif validation.document_type == "invalide":
        if "corrompu" in validation.reason:
            message = f"""[REJET] "{pdf_path.name}" : fichier corrompu ou illisible.
Erreur: {metrics.get('error', 'erreur inconnue')}

> Verifiez l'integrite du fichier PDF."""
        else:
            message = f"""[REJET] "{pdf_path.name}" : {validation.reason}.

> Verifiez que le fichier est un PDF valide."""
    
    else:
        message = f"""[REJET] "{pdf_path.name}" : {validation.reason}."""
    
    return message
