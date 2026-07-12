"""
✅ EXTRACTION SPÉCIFICATIONS - ROBUSTE

Pipeline fiable pour extraire la colonne "Spécification":
1. Détection en-têtes par OCR (première ligne)
2. Détection colonne par position X + validation
3. Extraction cellule par cellule
4. Scoring confiance + flags vérification
5. Sortie: specifications_source_of_truth.json

Approche:
- OCR en-têtes pour identifier colonne 2
- Segmentation grille simple (Y regroupement + X tiers)
- Extraction robuste cellule par cellule
- 100% local, pas d'API/LLM
"""

import fitz
import cv2
import pytesseract
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import json
import re
from datetime import datetime
from collections import defaultdict

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ============================================================================
# DÉTECTION EN-TÊTES
# ============================================================================

HEADER_ALIASES = {
    "spécification": ["specification", "specifications", "spécifications"],
    "caractéristiques": [
        "caractéristiques techniques minimales",
        "caractéristiques minimales",
        "caract techniques",
        "caract. tech",
    ]
}


def render_page_to_image(pdf_path: str, page_num: int, dpi: int = 300) -> np.ndarray:
    """Rendre page PDF en image RGB."""
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n).copy()
    if pix.n == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
    elif pix.n == 1:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    
    doc.close()
    return img


def ocr_image_region(img: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> str:
    """OCR sur région de l'image."""
    if x2 <= x1 or y2 <= y1:
        return ""
    
    region = img[y1:y2, x1:x2].copy()
    gray = cv2.cvtColor(region, cv2.COLOR_RGB2GRAY)
    
    # Binarisation
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, blockSize=11, C=2
    )
    
    try:
        text = pytesseract.image_to_string(
            binary,
            lang='fra',
            config='--psm 6'
        )
        return text.strip()
    except:
        return ""


def detect_specification_column_by_headers(img: np.ndarray, 
                                           page_height: int,
                                           header_region_height: int = 150) -> Optional[int]:
    """
    Détecte colonne "Spécification" en OCRisant la première ligne.
    Retourne index de colonne (0, 1, 2) ou None.
    """
    img_width = img.shape[1]
    
    # Première ligne (en-tête) - diviser en 3 zones
    col_width = img_width // 3
    headers = {}
    
    for col_idx in range(3):
        x1 = col_idx * col_width
        x2 = (col_idx + 1) * col_width if col_idx < 2 else img_width
        
        # OCR première région (première ~150px en hauteur)
        header_text = ocr_image_region(img, x1, 0, x2, min(header_region_height, page_height))
        headers[col_idx] = header_text.lower()
    
    # Matcher "Spécification" ou aliases
    for col_idx, header_text in headers.items():
        if not header_text:
            continue
        
        # Exact match
        if "specification" in header_text or "spécification" in header_text:
            return col_idx
        
        # Fuzzy match
        if any(alias in header_text for aliases in HEADER_ALIASES.values() 
               for alias in aliases):
            return col_idx
    
    # Pas trouvé
    return None


# ============================================================================
# EXTRACTION CELLULE
# ============================================================================

def preprocess_cell(cell_img: np.ndarray) -> np.ndarray:
    """Prétraitement cellule."""
    # Upscale si petit
    h, w = cell_img.shape[:2]
    if w < 150:
        scale = max(2, int(150 / w))
        cell_img = cv2.resize(cell_img, None, fx=scale, fy=scale,
                             interpolation=cv2.INTER_CUBIC)
    
    # Gris
    gray = cv2.cvtColor(cell_img, cv2.COLOR_RGB2GRAY)
    
    # Débruitage
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # Binarisation
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, blockSize=11, C=2
    )
    
    # Deskew
    try:
        coords = np.column_stack(np.where(binary > 0))
        if len(coords) > 4:
            angle = cv2.minAreaRect(coords)[2]
            if abs(angle) > 0.5:
                h, w = binary.shape
                center = (w // 2, h // 2)
                mat = cv2.getRotationMatrix2D(center, angle, 1.0)
                binary = cv2.warpAffine(mat, (w, h),
                                       borderMode=cv2.BORDER_REPLICATE)
    except:
        pass
    
    return binary


def extract_cell_ocr(img: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> Tuple[str, float, bool, str]:
    """
    Extrait contenu cellule avec OCR.
    Retourne: (texte, confiance, needs_review, raison)
    """
    margin = 3
    x1 = max(0, x1 + margin)
    y1 = max(0, y1 + margin)
    x2 = min(img.shape[1], x2 - margin)
    y2 = min(img.shape[0], y2 - margin)
    
    if x2 <= x1 or y2 <= y1:
        return ("", 0.0, True, "Cellule invalide")
    
    cell_img = img[y1:y2, x1:x2].copy()
    binary = preprocess_cell(cell_img)
    
    # OCR
    try:
        data = pytesseract.image_to_data(
            binary,
            output_type=pytesseract.Output.DICT,
            lang='fra',
            config='--psm 6'
        )
    except Exception as e:
        return ("", 0.0, True, f"OCR échec: {str(e)[:30]}")
    
    # Extraire mots et confiances
    words = []
    confidences = []
    
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        conf = int(data['conf'][i])
        
        if text and conf > 0:
            words.append(text)
            confidences.append(conf)
    
    if not words:
        return ("", 0.0, False, "")
    
    # Moyenne confiance
    avg_conf = np.mean(confidences)
    
    # Texte
    text = ' '.join(words)
    text = clean_ocr_text(text)
    
    # Flags
    needs_review = avg_conf < 70 or has_suspicious_patterns(text)
    reason = ""
    if avg_conf < 70:
        reason = f"Confiance basse ({avg_conf:.0f}%)"
    if has_suspicious_patterns(text):
        if reason:
            reason += "; "
        reason += "Patterns suspects"
    
    return (text, avg_conf, needs_review, reason)


def clean_ocr_text(text: str) -> str:
    """Nettoyage post-OCR minimal."""
    replacements = {
        'ñ': 'n', 'ü': 'u', 'ö': 'o', 'ä': 'a',
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'â': 'a', 'ê': 'e', 'î': 'i', 'ô': 'o', 'û': 'u',
        'à': 'a', 'è': 'e', 'ì': 'i', 'ò': 'o', 'ù': 'u',
        'ł': 'l', 'ø': 'o', 'ß': 'ss', 'æ': 'ae', 'œ': 'oe',
        'ï': 'i', 'ﬂ': 'fl', 'ﬁ': 'fi',
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Espaces multiples
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def has_suspicious_patterns(text: str) -> bool:
    """Détecte patterns suspects."""
    if not text:
        return False
    
    # Séquences sans voyelle > 4 caractères
    vowels = 'aeiouyàâäéèêëïîôöœuù'
    for word in text.split():
        word_alpha = ''.join(c.lower() for c in word if c.isalpha())
        if len(word_alpha) > 4 and not any(v in word_alpha for v in vowels):
            return True
    
    # Symboles parasites (|, \, ~) isolés ou en excès
    suspect_chars = '|\\~'
    count = sum(1 for c in text if c in suspect_chars)
    if count > 2:
        return True
    
    return False


# ============================================================================
# SEGMENTATION LIGNES
# ============================================================================

def segment_rows_by_y(img_height: int, ocr_results: List[Dict]) -> List[Tuple[int, int]]:
    """
    Segment lignes par regroupement des positions Y.
    
    Retourne liste de (y_min, y_max) pour chaque ligne.
    """
    if not ocr_results:
        return []
    
    # Collecter Y positions
    y_positions = []
    for entry in ocr_results:
        if 'top' in entry and 'height' in entry:
            y_top = entry['top']
            y_bottom = entry['top'] + entry['height']
            y_positions.append((y_top, y_bottom))
    
    if not y_positions:
        return []
    
    # Grouper par seuil Y (lignes proches = même ligne logique)
    y_positions = sorted(set(y_positions))
    
    rows = []
    current_row = [y_positions[0]]
    y_threshold = 25
    
    for y_pair in y_positions[1:]:
        if abs(y_pair[0] - current_row[-1][0]) <= y_threshold:
            current_row.append(y_pair)
        else:
            # Calculer limites row
            y_min = min(p[0] for p in current_row)
            y_max = max(p[1] for p in current_row)
            rows.append((y_min, y_max))
            current_row = [y_pair]
    
    if current_row:
        y_min = min(p[0] for p in current_row)
        y_max = max(p[1] for p in current_row)
        rows.append((y_min, y_max))
    
    return rows


# ============================================================================
# PIPELINE
# ============================================================================

def extract_specifications_page(pdf_path: str, page_num: int,
                               spec_col_idx: Optional[int] = None) -> Tuple[Dict, Optional[int]]:
    """
    Extrait spécifications d'une page.
    
    Retourne: (page_data, detected_or_inherited_col_index)
    """
    
    img = render_page_to_image(pdf_path, page_num, dpi=300)
    img_h, img_w = img.shape[:2]
    
    # Déterminer colonne Spécification
    if spec_col_idx is None:
        # Chercher en-tête
        spec_col_idx = detect_specification_column_by_headers(img, img_h)
        header_detected = "Spécification" if spec_col_idx is not None else None
    else:
        header_detected = None  # Hérité
    
    if spec_col_idx is None:
        return {"page": page_num + 1, "status": "Colonne non détectée"}, None
    
    # Coordonnées colonne
    col_width = img_w / 3
    spec_x1 = int(spec_col_idx * col_width)
    spec_x2 = int((spec_col_idx + 1) * col_width) if spec_col_idx < 2 else img_w
    des_x1 = int(0)
    des_x2 = int(col_width)
    
    # Extraire OCR colonne spécification (complet)
    spec_data = pytesseract.image_to_data(
        img[0:img_h, spec_x1:spec_x2],
        output_type=pytesseract.Output.DICT,
        lang='fra'
    )
    
    # Segmenter lignes
    row_segments = segment_rows_by_y(img_h, list(zip(
        spec_data['top'],
        spec_data['height']
    )))
    
    # Extraire cellules
    entries = []
    
    for row_idx, (y1, y2) in enumerate(row_segments):
        if row_idx == 0:  # Skip en-tête
            continue
        
        # Designation (col 0)
        des_text, des_conf, des_review, des_reason = extract_cell_ocr(
            img, des_x1, y1, des_x2, y2
        )
        
        # Specification (col spec)
        spec_text, spec_conf, spec_review, spec_reason = extract_cell_ocr(
            img, spec_x1, y1, spec_x2, y2
        )
        
        if spec_text.strip():
            entries.append({
                "designation": des_text,
                "valeur": spec_text,
                "confiance_ocr": round(spec_conf, 1),
                "a_verifier": spec_review,
                "raison_verification": spec_reason
            })
    
    page_data = {
        "page": page_num + 1,
        "entete_detecte": header_detected or f"hérité de page précédente",
        "entries": entries
    }
    
    return page_data, spec_col_idx


def extract_all_pages(pdf_path: str) -> Dict:
    """Pipeline complet extraction PDF."""
    
    doc = fitz.open(pdf_path)
    n_pages = doc.page_count
    doc.close()
    
    print(f"\n{'='*70}")
    print(f"EXTRACTION SPÉCIFICATIONS - ROBUSTE")
    print(f"{'='*70}\n")
    print(f"Source: {Path(pdf_path).name}")
    print(f"Pages: {n_pages}\n")
    
    results = {
        "document": Path(pdf_path).name,
        "colonne_source": "Spécification",
        "extraction_date": datetime.now().isoformat(),
        "pages": []
    }
    
    inherited_col_idx = None
    
    for page_num in range(n_pages):
        print(f"Page {page_num + 1}...", end=" ", flush=True)
        
        try:
            page_data, detected_col = extract_specifications_page(
                pdf_path, page_num,
                spec_col_idx=inherited_col_idx
            )
            
            if detected_col is not None:
                inherited_col_idx = detected_col
                n_entries = len(page_data.get('entries', []))
                print(f"OK {n_entries} entrées")
                results["pages"].append(page_data)
            else:
                print(f"SKIP")
        
        except Exception as e:
            print(f"X Erreur: {str(e)[:40]}")
            continue
    
    return results


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pdf_path = "data/output/pages_cibles.pdf"
    
    if not Path(pdf_path).exists():
        print(f"ERREUR: {pdf_path} non trouvé")
        exit(1)
    
    # Extraction
    results = extract_all_pages(pdf_path)
    
    # Sauvegarde
    output_path = Path("data/output/specifications_source_of_truth.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*70}")
    print(f"RESULTATS")
    print(f"{'='*70}\n")
    
    total_pages = len(results['pages'])
    total_entries = sum(len(p.get('entries', [])) for p in results['pages'])
    total_flagged = sum(
        sum(1 for e in p.get('entries', []) if e.get('a_verifier', False))
        for p in results['pages']
    )
    
    print(f"OK Pages traitées: {total_pages}")
    print(f"OK Entrées extraites: {total_entries}")
    if total_flagged > 0:
        print(f"WARNING Entrées à vérifier: {total_flagged} ({100*total_flagged//total_entries if total_entries else 0}%)")
    print(f"OK Sortie: {output_path}\n")
    
    if total_pages > 0:
        print("Aperçu (premières entrées):")
        for page_info in results['pages'][:2]:
            page_num = page_info['page']
            n_entries = len(page_info.get('entries', []))
            print(f"\nPage {page_num} ({n_entries} entrées):")
            for i, entry in enumerate(page_info.get('entries', [])[:3], 1):
                flag = " [!]" if entry.get('a_verifier') else ""
                print(f"  {i}. {entry['designation'][:25]:25s} | {entry['valeur'][:35]}{flag}")
