"""
✅ EXTRACTION SPECIFICATIONS PRODUCTION - VERSION FINALE

Combinaison des meilleures approches:
1. Extraction COLONNES 1 + 2 (Designation + Specification)
2. DPI 400 + CLAHE pour meilleure qualité
3. OCR confiance >30
4. Segmentation Y ±30px (regroupement éprouvé)
5. Confiance = moyenne Tesseract par cellule
6. Flag "a_verifier" basé sur confiance < 70 OU patterns suspects
7. Format JSON structuré avec métadonnées complètes
"""

import fitz
import cv2
import pytesseract
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
import json
import re
from datetime import datetime

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


MINIMAL_STOP_WORDS = {
    ':', '—', '–', '…', '"', ''', ''',
}

# Patterns OCR suspects (indicateurs de confiance faible)
SUSPICIOUS_PATTERNS = [
    r'^[^a-zA-Z0-9]*$',  # Caractères non-alphanumériques
    r'[0OIl]{5,}',  # Répétitions de caractères confondus
    r'[\/\\]{3,}',  # Slashes répétés
    r'^[\s\-_\.]+$',  # Uniquement espaces/tirets/underscores
]


def ocr_page_hd(pdf_path, page_num, dpi=400) -> List[Dict]:
    """OCR 400 DPI + CLAHE."""
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
    
    img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    
    # CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img_gray = clahe.apply(img_gray)
    
    doc.close()
    
    try:
        data = pytesseract.image_to_data(
            img_gray,
            output_type=pytesseract.Output.DICT,
            lang='fra'
        )
    except:
        return []
    
    words = []
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        conf = int(data['conf'][i])
        
        # Critère: confiance >30
        if text and len(text) > 0 and conf > 30:
            words.append({
                'text': text,
                'x': int(data['left'][i]),
                'y': int(data['top'][i]),
                'width': int(data['width'][i]),
                'height': int(data['height'][i]),
                'conf': conf
            })
    
    return words


def clean_ocr_text(text: str) -> str:
    """Nettoyage minimal."""
    replacements = {
        'ñ': 'n', 'ü': 'u', 'ö': 'o', 'ä': 'a',
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'â': 'a', 'ê': 'e', 'î': 'i', 'ô': 'o', 'û': 'u',
        'à': 'a', 'è': 'e', 'ì': 'i', 'ò': 'o', 'ù': 'u',
        'ł': 'l', 'ø': 'o', 'ß': 'ss', 'æ': 'ae', 'œ': 'oe',
        '—': '-', '–': '-', '…': '...',
        'ï': 'i', 'ﬂ': 'fl', 'ﬁ': 'fi', 'ŷ': 'y',
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    text = re.sub(r'[^a-zA-Z0-9\s\-.,():%/\'"°]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def is_valid_word(word: str) -> bool:
    """Validation très permissive."""
    if len(word) < 1:
        return False
    
    if word.lower() in MINIMAL_STOP_WORDS:
        return False
    
    if not any(c.isalnum() for c in word):
        return False
    
    return True


def is_suspicious_ocr(text: str) -> bool:
    """Détecte patterns OCR suspects."""
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def extract_column_cells(words: List[Dict], col_start_ratio: float, col_end_ratio: float) -> List[Tuple[str, float, bool, str]]:
    """
    Extrait une colonne et retourne liste de tuples:
    (texte, confiance_moyenne, a_verifier, raison_verification)
    
    Args:
        words: Liste des mots OCR avec positions
        col_start_ratio: Début de la colonne (ratio 0-1)
        col_end_ratio: Fin de la colonne (ratio 0-1)
    
    Returns:
        Liste de tuples (text, confidence, needs_review, reason)
    """
    if not words:
        return []
    
    # Déterminer largeur image
    img_width = max(w['x'] + w['width'] for w in words) if words else 0
    if img_width == 0:
        return []
    
    # Filtrer les mots de la colonne
    col_start = img_width * col_start_ratio
    col_end = img_width * col_end_ratio
    
    col_words = [w for w in words if col_start <= w['x'] + w['width']/2 <= col_end]
    
    if not col_words:
        return []
    
    # Trier par Y (hauteur)
    col_words = sorted(col_words, key=lambda w: w['y'])
    
    # Grouper par ligne (Y ±30px)
    rows = []
    if col_words:
        current_row = [col_words[0]]
        
        for word in col_words[1:]:
            if abs(word['y'] - current_row[0]['y']) <= 30:
                current_row.append(word)
            else:
                rows.append(current_row)
                current_row = [word]
        
        if current_row:
            rows.append(current_row)
    
    # Traiter chaque ligne
    result = []
    for row in rows:
        row_sorted = sorted(row, key=lambda w: w['x'])
        
        # Nettoyer et valider
        cleaned_words = []
        confidences = []
        
        for w in row_sorted:
            cleaned = clean_ocr_text(w['text'])
            if is_valid_word(cleaned):
                cleaned_words.append(cleaned)
                confidences.append(w['conf'])
        
        if cleaned_words:
            line_text = ' '.join(cleaned_words)
            if len(line_text.strip()) > 0:
                # Calculer confiance moyenne
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                
                # Déterminer si à vérifier
                suspicious = is_suspicious_ocr(line_text)
                needs_review = avg_confidence < 70 or suspicious
                
                # Raison de vérification
                reason = ""
                if avg_confidence < 70:
                    reason = f"confiance_faible_{avg_confidence:.0f}"
                if suspicious:
                    reason = (reason + "_pattern_suspect") if reason else "pattern_suspect"
                
                result.append((line_text, avg_confidence, needs_review, reason))
    
    return result


def extract_specifications_page(pdf_path: str, page_num: int) -> Dict:
    """
    Extrait les spécifications d'une page.
    Retourne dict avec structure complète.
    """
    # OCR
    words = ocr_page_hd(pdf_path, page_num, dpi=400)
    
    if not words:
        return None
    
    # NOUVEAU: Identifier et exclure les premières lignes (titre + en-tête) par Y position
    # Grouper mots par ligne Y (±30px)
    words_sorted_by_y = sorted(words, key=lambda w: w['y'])
    
    lines_y = []
    if words_sorted_by_y:
        current_line_y = [words_sorted_by_y[0]['y']]
        for w in words_sorted_by_y[1:]:
            if abs(w['y'] - current_line_y[0]) <= 30:
                current_line_y.append(w['y'])
            else:
                avg_y = sum(current_line_y) / len(current_line_y)
                lines_y.append(avg_y)
                current_line_y = [w['y']]
        if current_line_y:
            avg_y = sum(current_line_y) / len(current_line_y)
            lines_y.append(avg_y)
    
    # Exclure les 2 premières lignes (titre + en-tête)
    if len(lines_y) >= 2:
        y_threshold = lines_y[1] + 50  # Tout ce qui est en-dessous de la 2ème ligne
        words_filtered = [w for w in words if w['y'] > y_threshold]
    else:
        words_filtered = words  # Pas assez de lignes pour filtrer
    
    # Déterminer si en-tête détecté
    header_detected = "Spécification"  # En-tête fixe
    
    # Créer entries en appairant les colonnes PAR POSITION Y (pas par index)
    # Chaque tuple dans col1_cells et col2_cells contient: (text, confidence, needs_review, reason)
    # Nous devons maintenant les apparier par position Y, pas par index
    
    # D'abord, reconstruire les lignes avec leur position Y moyenne
    def extract_column_cells_with_y(words: List[Dict], col_start_ratio: float, col_end_ratio: float) -> List[Tuple[str, float, bool, str, float]]:
        """Version modifiée qui retourne aussi la position Y moyenne."""
        if not words:
            return []
        
        img_width = max(w['x'] + w['width'] for w in words) if words else 0
        if img_width == 0:
            return []
        
        col_start = img_width * col_start_ratio
        col_end = img_width * col_end_ratio
        
        col_words = [w for w in words if col_start <= w['x'] + w['width']/2 <= col_end]
        if not col_words:
            return []
        
        col_words = sorted(col_words, key=lambda w: w['y'])
        
        rows = []
        if col_words:
            current_row = [col_words[0]]
            for word in col_words[1:]:
                if abs(word['y'] - current_row[0]['y']) <= 30:
                    current_row.append(word)
                else:
                    rows.append(current_row)
                    current_row = [word]
            if current_row:
                rows.append(current_row)
        
        result = []
        for row in rows:
            row_sorted = sorted(row, key=lambda w: w['x'])
            cleaned_words = []
            confidences = []
            
            for w in row_sorted:
                cleaned = clean_ocr_text(w['text'])
                if is_valid_word(cleaned):
                    cleaned_words.append(cleaned)
                    confidences.append(w['conf'])
            
            if cleaned_words:
                line_text = ' '.join(cleaned_words)
                if len(line_text.strip()) > 0:
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                    suspicious = is_suspicious_ocr(line_text)
                    needs_review = avg_confidence < 70 or suspicious
                    
                    reason = ""
                    if avg_confidence < 70:
                        reason = f"confiance_faible_{avg_confidence:.0f}"
                    if suspicious:
                        reason = (reason + "_pattern_suspect") if reason else "pattern_suspect"
                    
                    # Calculer Y moyen de la ligne
                    avg_y = sum(w['y'] for w in row) / len(row)
                    
                    result.append((line_text, avg_confidence, needs_review, reason, avg_y))
        
        return result
    
    # Re-extraire avec position Y
    col1_cells_with_y = extract_column_cells_with_y(words_filtered, 0, 1/3)
    col2_cells_with_y = extract_column_cells_with_y(words_filtered, 1/3, 2/3)
    
    # Apparier par position Y (tolérance ±50px)
    entries = []
    used_col2 = set()
    
    for designation, conf1, verify1, reason1, y1 in col1_cells_with_y:
        # Trouver la ligne col2 la plus proche en Y
        best_match_idx = None
        best_y_diff = float('inf')
        
        for idx, (valeur, conf2, verify2, reason2, y2) in enumerate(col2_cells_with_y):
            if idx in used_col2:
                continue
            y_diff = abs(y1 - y2)
            if y_diff < 50 and y_diff < best_y_diff:  # Tolérance ±50px
                best_match_idx = idx
                best_y_diff = y_diff
        
        if best_match_idx is not None:
            valeur, conf2, verify2, reason2, y2 = col2_cells_with_y[best_match_idx]
            used_col2.add(best_match_idx)
        else:
            valeur, conf2, verify2, reason2 = "", 0.0, False, ""
        
        # Utiliser confiance colonne 2 pour l'entrée
        entries.append({
            "designation": designation,
            "valeur": valeur,
            "confiance_ocr": round(conf2, 1),
            "a_verifier": verify2,
            "raison_verification": reason2
        })
    
    # Ajouter les lignes col2 non appariées (lignes sans designation)
    for idx, (valeur, conf2, verify2, reason2, y2) in enumerate(col2_cells_with_y):
        if idx not in used_col2:
            entries.append({
                "designation": "",
                "valeur": valeur,
                "confiance_ocr": round(conf2, 1),
                "a_verifier": verify2,
                "raison_verification": reason2
            })
    
    if not entries:
        return None
    
    return {
        "page": page_num + 1,
        "entete_detecte": header_detected,
        "entries": entries
    }


def extract_all_specifications() -> Dict:
    """Extraction complète."""
    pages_cibles_path = Path("data/output/pages_cibles.pdf")
    
    if not pages_cibles_path.exists():
        print(f"ERREUR: {pages_cibles_path} non trouvé")
        return None
    
    print(f"\n{'='*70}")
    print(f"EXTRACTION SPECIFICATIONS - PRODUCTION VERSION")
    print(f"{'='*70}\n")
    print(f"Source: {pages_cibles_path}")
    print(f"Approche: Colonnes 1+2 + DPI 400 + Confiance >30")
    print(f"Segmentation: Y ±30px\n")
    
    doc = fitz.open(str(pages_cibles_path))
    print(f"Pages PDF: {doc.page_count}\n")
    
    pages_data = []
    
    for page_num in range(doc.page_count):
        try:
            print(f"Page {page_num + 1}...", end=" ")
            
            page_result = extract_specifications_page(str(pages_cibles_path), page_num)
            
            if page_result is None:
                print("X Aucun contenu")
                continue
            
            pages_data.append(page_result)
            print(f"OK {len(page_result['entries'])} entrees")
            
        except Exception as e:
            print(f"X Erreur: {str(e)[:40]}")
            continue
    
    doc.close()
    
    if not pages_data:
        print("\nERREUR: Aucune page extraite")
        return None
    
    # Construire structure JSON finale
    extraction_result = {
        "document": "pages_cibles.pdf",
        "colonne_source": "Spécification",
        "extraction_date": datetime.utcnow().isoformat() + "Z",
        "pages": pages_data
    }
    
    return extraction_result


if __name__ == "__main__":
    result = extract_all_specifications()
    
    if result:
        print(f"\n[OK] Extraction completee: {len(result.get('pages', []))} pages")
    else:
        print("\n[ERROR] Extraction echouee")
