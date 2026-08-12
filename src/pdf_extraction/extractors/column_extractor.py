"""
Module d'extraction de la 2ᵉ colonne des tableaux.

Pipeline robuste basé sur la détection de grille par vision (OpenCV)
et l'OCR par cellule avec Tesseract.

Principe : localiser la colonne via la géométrie de la grille (lignes du tableau),
pas via le texte des en-têtes.
"""

from pathlib import Path
from typing import List, Optional, Dict, Tuple
import re
import json
import unicodedata
import numpy as np
import cv2
import fitz  # PyMuPDF
import pytesseract

# Configure Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

from rapidfuzz import fuzz
from sklearn.cluster import KMeans
from pypdf import PdfReader
import sys
sys.path.append(str(Path(__file__).parent))
from pdf_extraction.utils.clean_ocr import clean_ocr_text

# Import PageContext for type hints (Optional to avoid circular imports if needed)
try:
    from pdf_extraction.core.detection_rules import PageContext
except ImportError:
    PageContext = None  # Fallback if circular import


# ============================================================================
# VÉRIFICATION DE LA CONFIGURATION TESSERACT
# ============================================================================

def verify_tesseract_setup() -> bool:
    """
    Vérifie que Tesseract est correctement configuré avec la langue française.
    
    Returns:
        True si la configuration est valide, False sinon
    """
    print("[INFO] Checking Tesseract setup...")
    
    try:
        # Vérifier que le binaire Tesseract est trouvable
        version = pytesseract.get_tesseract_version()
        print(f"[OK] Tesseract version: {version}")
    except Exception as e:
        print(f"[ERROR] Tesseract binary not found: {e}")
        print("[ERROR] Please install Tesseract OCR from https://github.com/tesseract-ocr/tesseract")
        return False
    
    # Vérifier les langues disponibles
    try:
        languages = pytesseract.get_languages(config='')
        print(f"[DEBUG] Available languages: {languages}")
        
        if 'fra' not in languages and 'french' not in languages:
            print("[ERROR] French language pack not found in Tesseract")
            print("[ERROR] Please download 'fra.traineddata' from:")
            print("[ERROR] https://github.com/tesseract-ocr/tessdata/raw/main/fra.traineddata")
            print("[ERROR] And place it in the tessdata folder:")
            print("[ERROR]   - Windows: C:\\Program Files\\Tesseract-OCR\\tessdata\\")
            print("[ERROR]   - Linux: /usr/share/tesseract-ocr/4.00/tessdata/")
            print("[ERROR]   - macOS: /usr/local/share/tessdata/")
            print("[ERROR] Then set TESSDATA_PREFIX environment variable to point to this folder")
            return False
        else:
            print("[OK] French language pack available")
            return True
    
    except Exception as e:
        print(f"[ERROR] Failed to check Tesseract languages: {e}")
        return False


# ============================================================================
# ÉTAPE 1 — Rendu haute résolution avec PyMuPDF
# ============================================================================

def render_page(pdf_path: str | Path, page_num: int, dpi: int = 300) -> np.ndarray:
    """
    Convertit une page PDF en image haute résolution.
    
    Args:
        pdf_path: Chemin du fichier PDF
        page_num: Numéro de page (0-indexed)
        dpi: Résolution (300 minimum, 400 si beaucoup de manuscrit)
    
    Returns:
        Image numpy array (RGB)
    """
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    mat = fitz.Matrix(dpi/72, dpi/72)
    pix = page.get_pixmap(matrix=mat)
    img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    doc.close()
    return img_array


# ============================================================================
# ÉTAPE 2 — Détection de la grille par vision (OpenCV)
# ============================================================================

def merge_close(positions: List[int], gap: int = 10) -> List[int]:
    """
    Fusionne les positions adjacentes en une seule frontière.
    
    Args:
        positions: Liste des positions
        gap: Écart maximal pour fusionner
    
    Returns:
        Liste des positions fusionnées (moyennes)
    """
    if not positions:
        return []
    
    merged = [[positions[0]]]
    for p in positions[1:]:
        if p - merged[-1][-1] <= gap:
            merged[-1].append(p)
        else:
            merged.append([p])
    
    return [int(np.mean(g)) for g in merged]


def detect_table_grid(img_gray: np.ndarray) -> Tuple[List[int], List[int]]:
    """
    Détecte les lignes du tableau par morphologie mathématique.
    
    Args:
        img_gray: Image en niveaux de gris
    
    Returns:
        Tuple (col_bounds, row_bounds) : positions des frontières de colonnes et lignes
    """
    # Binarisation adaptative (robuste aux scans inégaux/jaunis)
    bw = cv2.adaptiveThreshold(
        ~img_gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY, 15, -2
    )
    
    horizontal = bw.copy()
    vertical = bw.copy()
    
    # Isoler les lignes horizontales
    h_size = horizontal.shape[1] // 30
    h_struct = cv2.getStructuringElement(cv2.MORPH_RECT, (h_size, 1))
    horizontal = cv2.erode(horizontal, h_struct)
    horizontal = cv2.dilate(horizontal, h_struct)
    
    # Isoler les lignes verticales
    v_size = vertical.shape[0] // 30
    v_struct = cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_size))
    vertical = cv2.erode(vertical, v_struct)
    vertical = cv2.dilate(vertical, v_struct)
    
    # Coordonnées X des colonnes = positions des lignes verticales
    col_positions = sorted(np.where(vertical.sum(axis=0) > vertical.shape[0]*0.3)[0])
    row_positions = sorted(np.where(horizontal.sum(axis=1) > horizontal.shape[1]*0.3)[0])
    
    col_bounds = merge_close(col_positions, gap=10)
    row_bounds = merge_close(row_positions, gap=10)
    
    return col_bounds, row_bounds


# ============================================================================
# ÉTAPE 3 — Segmentation en cellules
# ============================================================================

def segment_cells(col_bounds: List[int], row_bounds: List[int], margin: int = 5) -> List[Tuple[int, int, int, int]]:
    """
    Crée la grille de cellules à partir des frontières.
    
    Args:
        col_bounds: Positions X des frontières de colonnes
        row_bounds: Positions Y des frontières de lignes
        margin: Marge interne (px) pour ne pas couper les glyphes
    
    Returns:
        Liste de tuples (x_start, x_end, y_start, y_end) pour chaque cellule
    """
    cells = []
    
    for row_idx in range(len(row_bounds) - 1):
        for col_idx in range(len(col_bounds) - 1):
            x_start = col_bounds[col_idx] + margin
            x_end = col_bounds[col_idx + 1] - margin
            y_start = row_bounds[row_idx] + margin
            y_end = row_bounds[row_idx + 1] - margin
            
            if x_end > x_start and y_end > y_start:
                cells.append((x_start, x_end, y_start, y_end))
    
    return cells


# ============================================================================
# ÉTAPE 4 — OCR par cellule avec Tesseract
# ============================================================================

def ocr_cell(cell_img: np.ndarray, lang: str = "fra") -> str:
    """
    OCRise une cellule individuelle avec Tesseract.
    
    Args:
        cell_img: Image de la cellule (numpy array)
        lang: Langue OCR (fra pour français)
    
    Returns:
        Texte extrait
    """
    config = "--psm 6"  # bloc de texte uniforme
    text = pytesseract.image_to_string(cell_img, lang=lang, config=config)
    return text.strip()


def extract_cell_from_image(img: np.ndarray, cell_bbox: Tuple[int, int, int, int]) -> np.ndarray:
    """
    Extrait une cellule de l'image complète.
    
    Gère les coordonnées float en les convertissant en entiers et les bornant
    aux dimensions de l'image.
    
    Args:
        img: Image complète (shape: height, width, channels)
        cell_bbox: (x_start, x_end, y_start, y_end) - peut contenir des floats
    
    Returns:
        Image de la cellule (numpy array)
        
    Raises:
        ValueError: Si la cellule est invalide (x_end <= x_start ou y_end <= y_start)
    """
    x_start, x_end, y_start, y_end = cell_bbox
    
    # Dimensions de l'image
    img_height, img_width = img.shape[:2]
    
    # Convertir les floats en entiers avec arrondi
    x_start = int(round(x_start))
    x_end = int(round(x_end))
    y_start = int(round(y_start))
    y_end = int(round(y_end))
    
    # Borner aux dimensions de l'image
    x_start = max(0, min(x_start, img_width - 1))
    x_end = max(0, min(x_end, img_width))
    y_start = max(0, min(y_start, img_height - 1))
    y_end = max(0, min(y_end, img_height))
    
    # Vérifier que x_end > x_start et y_end > y_start
    if x_end <= x_start or y_end <= y_start:
        raise ValueError(
            f"Invalid cell bbox: x_start={x_start}, x_end={x_end}, "
            f"y_start={y_start}, y_end={y_end} (width={img_width}, height={img_height})"
        )
    
    # Extraire la cellule (indexation: [lignes, colonnes] = [y, x])
    return img[y_start:y_end, x_start:x_end]


# ============================================================================
# ÉTAPE 5 — Mapping sémantique des en-têtes
# ============================================================================

def normalize(s: str) -> str:
    """
    Normalise le texte pour la comparaison fuzzy.
    
    Args:
        s: Texte à normaliser
    
    Returns:
        Texte normalisé
    """
    s = s.lower().strip()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = " ".join(s.split())
    return s


# =====================================================================
# TEMPLATE 1 — en-têtes observés sur les Lots 1, 3, 4, 5
#   Désignation | Spécification | Proposition
# =====================================================================
MODELE_1_HEADERS = {
    "designation":   "designation",
    "specification": "specification",
    "proposition":   "proposition",
}


# =====================================================================
# TEMPLATE 1 VARIANTE — Exigé ou à préciser
#   Désignation | Exigé ou à préciser | Proposition
# =====================================================================
MODELE_1_VARIANT_HEADERS = {
    "designation":   "designation",
    "specification": "exige ou a preciser",
    "proposition":   "proposition",
}


# =====================================================================
# TEMPLATE 2 — en-têtes observés sur le Lot 2 (ordinateurs portables)
#   Composants de l'offre | Caractéristiques techniques minimales | Propositions
# =====================================================================
MODELE_2_HEADERS = {
    "designation":   "composants de l offre",
    "specification": "caracteristiques techniques minimales",
    "proposition":   "proposition",
}


KNOWN_TEMPLATES = [MODELE_1_HEADERS, MODELE_1_VARIANT_HEADERS, MODELE_2_HEADERS]


FUZZY_ALIASES = {
    "designation":   ["designation", "composants", "produit", "article"],
    "specification": ["specification", "caracteristiques techniques",
                       "caracteristiques minimales", "exigences techniques",
                       "exige ou a preciser", "exige", "a preciser"],
    "proposition":   ["proposition", "offre proposee", "reponse fournisseur"],
}

# Valeurs canoniques pour la normalisation de la 2ème colonne uniquement
CANONICAL_SPECIFICATION_VALUES = [
    "Spécification",
    "Exigé ou à préciser",
    "Caractéristiques techniques minimales"
]


def _normalize_specification_label(ocr_text: str, threshold: float = 0.6) -> str:
    """
    Normalise le texte OCR de la 2ème colonne vers une valeur canonique.
    
    Args:
        ocr_text: Texte OCR brut (ex: "Exiaé ou à préciser")
        threshold: Seuil de similarité (0.0 à 1.0)
    
    Returns:
        Valeur canonique la plus proche ou texte original si aucun match
    """
    norm_ocr = normalize(ocr_text)
    
    best_match = None
    best_score = 0.0
    
    for canonical in CANONICAL_SPECIFICATION_VALUES:
        norm_canonical = normalize(canonical)
        # Utiliser ratio pour correspondance exacte, partial_ratio pour sous-chaînes
        score = max(
            fuzz.ratio(norm_ocr, norm_canonical) / 100.0,
            fuzz.partial_ratio(norm_ocr, norm_canonical) / 100.0
        )
        
        if score > best_score:
            best_score = score
            best_match = canonical
    
    # Retourner la valeur canonique si le score dépasse le seuil
    if best_score >= threshold:
        return best_match
    
    # Sinon retourner le texte original (ne rien casser)
    return ocr_text.strip()


def match_header(ocr_text: str, fuzzy_threshold: int = 75) -> Tuple[Optional[str], int, str, str]:
    """
    Match un texte OCR contre les templates d'en-têtes connus.
    
    Args:
        ocr_text: Texte OCR de l'en-tête
        fuzzy_threshold: Seuil pour le fuzzy fallback
    
    Returns:
        Tuple (role, score, method, detected_label) où :
        - role est "specification", "designation" ou "proposition"
        - method est "exact", "exact_tolerant", "fuzzy" ou "no_match"
        - detected_label est le nom réel détecté (ex: "Exigé ou à préciser", "Spécification")
    """
    norm = normalize(ocr_text)
    
    # Niveau 1 : match exact contre un des templates connus
    for template in KNOWN_TEMPLATES:
        for role, exact_label in template.items():
            if norm == exact_label:
                # Normaliser uniquement si c'est la 2ème colonne (specification)
                if role == "specification":
                    detected_label = _normalize_specification_label(ocr_text)
                else:
                    detected_label = ocr_text.strip()
                return role, 100, "exact", detected_label
    
    # Niveau 1bis : match tolérant à une petite erreur OCR
    for template in KNOWN_TEMPLATES:
        for role, exact_label in template.items():
            score = fuzz.ratio(norm, exact_label)
            if score >= 90:
                # Normaliser uniquement si c'est la 2ème colonne (specification)
                if role == "specification":
                    detected_label = _normalize_specification_label(ocr_text)
                else:
                    detected_label = ocr_text.strip()
                return role, score, "exact_tolerant", detected_label
    
    # Niveau 2 : fuzzy fallback (3e template inconnu)
    best_role, best_score, best_label = None, 0, ""
    for role, aliases in FUZZY_ALIASES.items():
        for alias in aliases:
            score = fuzz.partial_ratio(norm, alias)
            if score > best_score:
                best_role, best_score = role, score
                # Normaliser uniquement si c'est la 2ème colonne (specification)
                if role == "specification":
                    best_label = _normalize_specification_label(ocr_text)
                else:
                    best_label = ocr_text.strip()
    
    if best_score >= fuzzy_threshold:
        return best_role, best_score, "fuzzy", best_label
    
    return None, best_score, "no_match", ""


# ============================================================================
# ÉTAPE 6 — Fallback K-means (tableaux sans lignes visibles)
# ============================================================================

def fallback_column_detection(ocr_words_with_bbox: List[Dict]) -> np.ndarray:
    """
    Fallback : clustering K-means sur les positions X des mots OCR.
    
    Args:
        ocr_words_with_bbox: Liste de mots avec bbox (sortie de pytesseract.image_to_data)
    
    Returns:
        Centres des clusters (positions X des colonnes)
    """
    x_centers = np.array([(w['left'] + w['width'] / 2) for w in ocr_words_with_bbox]).reshape(-1, 1)
    km = KMeans(n_clusters=3, n_init=10).fit(x_centers)
    return km.cluster_centers_.flatten()


# ============================================================================
# ÉTAPE 7 — Extraction principale avec score de confiance
# ============================================================================

def extract_column(pdf_path: str | Path, page_num: int, target_role: str = "specification") -> Dict:
    """
    Extrait la colonne cible d'une page avec diagnostic détaillé.
    
    Args:
        pdf_path: Chemin du fichier PDF
        page_num: Numéro de page (0-indexed)
        target_role: Rôle cible ("specification", "designation", "proposition")
    
    Returns:
        Dictionnaire avec page, role, rows, warnings
    """
    result = {
        "page": page_num + 1,
        "role": target_role,
        "rows": [],
        "warnings": []
    }
    
    # Étape 1: Rendu HD
    try:
        img_rgb = render_page(pdf_path, page_num, dpi=300)
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    except Exception as e:
        result["warnings"].append(f"CRITICAL: render_failed - {e}")
        return result
    
    # Étape 2: Détection de grille
    col_bounds, row_bounds = detect_table_grid(img_gray)
    
    if len(col_bounds) < 4 or len(row_bounds) < 2:
        result["warnings"].append("grid_not_detected_fallback_used")
        # Fallback K-means
        ocr_data = pytesseract.image_to_data(img_gray, output_type=pytesseract.Output.DICT)
        ocr_words = [{'left': int(ocr_data['left'][i]), 'width': int(ocr_data['width'][i])}
                     for i in range(len(ocr_data['text'])) if ocr_data['text'][i].strip()]
        if ocr_words:
            col_centers = fallback_column_detection(ocr_words)
            col_bounds = sorted(col_centers)
            row_bounds = [0, img_gray.shape[0]]  # Fallback simple pour les lignes
        else:
            result["warnings"].append("CRITICAL: no_ocr_words_for_fallback")
            return result
    
    print(f"[DEBUG] Page {page_num}: Grid detected - {len(col_bounds)} cols, {len(row_bounds)} rows")
    
    # Étape 3: Segmentation en cellules
    cells = segment_cells(col_bounds, row_bounds)
    
    # Étape 4: OCR de la ligne d'en-tête
    header_row_idx = 0
    header_cells = []
    for col_idx in range(len(col_bounds) - 1):
        cell_bbox = (col_bounds[col_idx] + 5, col_bounds[col_idx + 1] - 5,
                     row_bounds[header_row_idx] + 5, row_bounds[header_row_idx + 1] - 5)
        cell_img = extract_cell_from_image(img_gray, cell_bbox)
        header_text = ocr_cell(cell_img)
        header_cells.append(header_text)
    
    # Étape 5: Mapping sémantique des en-têtes
    role_to_col_idx = {}
    detected_headers = {}  # Stocker les noms détectés {role: detected_label}
    for idx, cell_text in enumerate(header_cells):
        role, score, method, detected_label = match_header(cell_text)
        if role:
            role_to_col_idx[role] = idx
            detected_headers[role] = detected_label
        result["warnings"].append(f"col{idx}: '{cell_text}' -> {role} ({score}%, {method})")
    
    if target_role not in role_to_col_idx:
        result["warnings"].append(f"CRITICAL: colonne '{target_role}' introuvable")
        return result
    
    col_idx = role_to_col_idx[target_role]
    result["detected_header_name"] = detected_headers.get(target_role, target_role)
    print(f"[DEBUG] Page {page_num}: Target column '{target_role}' at index {col_idx}")
    print(f"[DEBUG] Detected header name: {result['detected_header_name']}")
    
    # Étape 6: OCR des cellules de données
    for row_idx in range(1, len(row_bounds) - 1):
        cell_bbox = (col_bounds[col_idx] + 5, col_bounds[col_idx + 1] - 5,
                     row_bounds[row_idx] + 5, row_bounds[row_idx + 1] - 5)
        cell_img = extract_cell_from_image(img_gray, cell_bbox)
        cell_text = ocr_cell(cell_img)
        
        if cell_text:
            # Nettoyage OCR
            cleaned_text = clean_ocr_text(cell_text, enable_regex=True, enable_confusion=False)
            result["rows"].append(cleaned_text)
    
    return result


def _extract_structured_rows_legacy(pdf_path: str | Path, page_contexts: Optional[List] = None) -> List[Dict]:
    """
    Extrait les colonnes 1 et 2 du tableau (clé/valeur).
    
    FORMAT MINIMALISTE:
    - Lit seulement colonnes 1 (clé) et 2 (valeur)
    - Utilise OCR avec bounding boxes pour assignation correcte
    - Chaque valeur passe par quality_analyzer pour marquage a_verifier
    
    Args:
        pdf_path: Chemin du PDF FILTRÉ (pages_cibles.pdf)
        page_contexts: Liste de PageContext correspondant aux pages du PDF filtré
    
    Returns:
        Liste de dictionnaires {fichier, page, lot, cle, valeur, a_verifier}
    """
    from pdf_extraction.core.quality_analyzer import analyze_value_quality
    
    doc = fitz.open(pdf_path)
    results = []
    
    # CORRECTION: Itérer sur les pages du PDF filtré (0, 1, 2, ..., N-1)
    # et utiliser page_contexts[idx] pour récupérer les métadonnées
    for pdf_page_idx in range(doc.page_count):
        # Récupérer le contexte correspondant
        page_context = None
        if page_contexts and pdf_page_idx < len(page_contexts):
            page_context = page_contexts[pdf_page_idx]
        
        # Le numéro de page ORIGINAL est dans page_context.page_num
        original_page_num = page_context.page_num if page_context else pdf_page_idx
        
        # DIAGNOSTIC DÉTAILLÉ pour page Lot 3 (page 13 du document = index 12)
        is_debug_page = (original_page_num == 12)  # Page 13 du document
        
        if is_debug_page:
            print(f"\n{'='*80}")
            print(f"DIAGNOSTIC DÉTAILLÉ - PAGE LOT 3 (page {original_page_num + 1} du document)")
            print(f"{'='*80}")
        
        print(f"\n[EXTRACTION] Page {pdf_page_idx + 1}/{doc.page_count} du PDF filtré (page {original_page_num + 1} du document original)")
        
        # Étape 1: Rendu HD
        try:
            img_rgb = render_page(pdf_path, pdf_page_idx, dpi=300)
            img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        except Exception as e:
            print(f"[ERROR] Page {pdf_page_idx}: Render failed - {e}")
            continue
        
        # Étape 2: Détection de grille (pour frontières de colonnes)
        col_bounds, row_bounds = detect_table_grid(img_gray)
        
        # CORRECTION: Fusionner colonnes si sur-segmentation (plus de 4 limites = plus de 3 colonnes)
        if len(col_bounds) > 4:
            print(f"[WARN] Page {pdf_page_idx + 1}: Sur-segmentation détectée ({len(col_bounds)} limites), fusion en 3 colonnes")
            # Utiliser K-means pour regrouper en 4 clusters (= 3 colonnes + 2 bords)
            col_array = np.array(col_bounds).reshape(-1, 1)
            kmeans = KMeans(n_clusters=4, n_init=10, random_state=42).fit(col_array)
            col_bounds = sorted([int(center[0]) for center in kmeans.cluster_centers_])
        
        if len(col_bounds) < 4:
            print(f"[WARN] Page {pdf_page_idx + 1}: Grid not detected, using K-means fallback")
            ocr_data_temp = pytesseract.image_to_data(img_gray, output_type=pytesseract.Output.DICT, lang='fra')
            ocr_words_temp = [{'left': int(ocr_data_temp['left'][i]), 'width': int(ocr_data_temp['width'][i])}
                              for i in range(len(ocr_data_temp['text'])) if ocr_data_temp['text'][i].strip()]
            if ocr_words_temp:
                col_centers = fallback_column_detection(ocr_words_temp)
                col_bounds = sorted(col_centers)
            else:
                print(f"[ERROR] Page {pdf_page_idx + 1}: No OCR words for fallback")
                continue
        
        if len(col_bounds) < 3:  # Au moins 2 colonnes: 3 frontières minimum
            print(f"[ERROR] Page {pdf_page_idx + 1}: Not enough column boundaries ({len(col_bounds)})")
            continue
        
        # Étape 3: OCR de TOUTE LA PAGE avec bounding boxes
        ocr_data = pytesseract.image_to_data(img_gray, output_type=pytesseract.Output.DICT, lang='fra')
        
        words = []
        for i in range(len(ocr_data['text'])):
            text = ocr_data['text'][i].strip()
            if text:
                words.append({
                    'text': text,
                    'left': int(ocr_data['left'][i]),
                    'top': int(ocr_data['top'][i]),
                    'width': int(ocr_data['width'][i]),
                    'height': int(ocr_data['height'][i]),
                    'conf': int(ocr_data['conf'][i])
                })
        
        if not words:
            print(f"[WARN] Page {pdf_page_idx + 1}: No OCR text detected")
            continue
        
        if is_debug_page:
            print(f"\n[DEBUG] OCR BRUT: {len(words)} mots détectés")
            print(f"[DEBUG] Premiers mots: {' '.join([w['text'] for w in words[:20]])}")
            print(f"\n[DEBUG] Limites de colonnes détectées: {col_bounds}")
            print(f"[DEBUG] Nombre de colonnes: {len(col_bounds) - 1}")
        
        # Étape 4: Assigner chaque mot à sa colonne selon position X
        # col_bounds[0] = gauche, col_bounds[1] = séparateur col1|col2, col_bounds[2] = séparateur col2|col3
        def assign_column(word_x_center: float) -> int:
            """Retourne l'index de colonne pour un mot"""
            if word_x_center < col_bounds[1]:
                return 0  # Colonne 1
            elif len(col_bounds) >= 3 and word_x_center < col_bounds[2]:
                return 1  # Colonne 2
            else:
                return 2  # Colonne 3
        
        for word in words:
            x_center = word['left'] + word['width'] / 2
            word['column'] = assign_column(x_center)
        
        if is_debug_page:
            # Afficher répartition par colonne
            col_counts = {0: 0, 1: 0, 2: 0}
            for w in words:
                col_counts[w['column']] += 1
            print(f"\n[DEBUG] Répartition mots par colonne:")
            print(f"  Colonne 0 (Désignation): {col_counts[0]} mots")
            print(f"  Colonne 1 (Spécification): {col_counts[1]} mots")
            print(f"  Colonne 2 (Proposition): {col_counts[2]} mots")
        
        # Étape 5: Regrouper par ligne (tolérance Y: ±10px)
        words_sorted = sorted(words, key=lambda w: (w['top'], w['left']))
        
        lines = []
        current_line = []
        y_tolerance = 10
        
        for word in words_sorted:
            if not current_line:
                current_line.append(word)
            else:
                if abs(word['top'] - current_line[0]['top']) <= y_tolerance:
                    current_line.append(word)
                else:
                    lines.append(current_line)
                    current_line = [word]
        
        if current_line:
            lines.append(current_line)
        
        # Sauter la première ligne (en-têtes)
        data_lines = lines[1:] if len(lines) > 1 else []
        
        if is_debug_page:
            print(f"\n[DEBUG] Total lignes détectées: {len(lines)}")
            print(f"\n[DEBUG] En-tête (ligne 0): {' | '.join([w['text'] for w in lines[0]][:10]) if lines else 'N/A'}")
            print(f"\n[DEBUG] Lignes de données (après skip header): {len(data_lines)}")
            if data_lines:
                print(f"\n[DEBUG] PREVIEW DES 5 PREMIÈRES LIGNES:")
                for idx, line in enumerate(data_lines[:5], 1):
                    col0 = ' '.join([w['text'] for w in line if w['column'] == 0])
                    col1 = ' '.join([w['text'] for w in line if w['column'] == 1])
                    col2 = ' '.join([w['text'] for w in line if w['column'] == 2])
                    print(f"  Ligne {idx}:")
                    print(f"    Col0 (Désignation): {col0[:50]}")
                    print(f"    Col1 (Spécification): {col1[:50]}")
                    print(f"    Col2 (Proposition): {col2[:50]}")
        
        # Détecter le numéro de lot depuis le texte de la page
        # Utiliser le même pattern que detection_rules.py pour cohérence
        lot_match = re.search(r"\blot\s*(?:n\s*°?\s*)?:?\s*(\d+)", page_context.normalized_text if page_context else "", re.IGNORECASE)
        lot_number = int(lot_match.group(1)) if lot_match else None
        
        # Étape 6: Construire les entrées clé/valeur avec confiance OCR et détection débordement
        for line_words in data_lines:
            # Regrouper par colonne avec scores de confiance
            col_texts = {0: [], 1: [], 2: []}
            col_confidences = {0: [], 1: [], 2: []}
            col_heights = {0: [], 1: [], 2: []}  # Pour détecter débordement vertical
            
            for word in line_words:
                col_idx = word['column']
                col_texts[col_idx].append(word['text'])
                col_confidences[col_idx].append(word['conf'])
                col_heights[col_idx].append(word['height'])
            
            cle_text = ' '.join(col_texts[0])
            valeur_text = ' '.join(col_texts[1])
            proposition_text = ' '.join(col_texts[2])  # Colonne 3 (manuscrit souvent)
            
            # Nettoyage OCR
            cle_clean = clean_ocr_text(cle_text, enable_regex=True, enable_confusion=False) if cle_text else ""
            valeur_clean = clean_ocr_text(valeur_text, enable_regex=True, enable_confusion=False) if valeur_text else ""
            proposition_clean = clean_ocr_text(proposition_text, enable_regex=True, enable_confusion=False) if proposition_text else ""
            
            # Ne garder que les lignes avec clé ET valeur
            if not cle_clean or not valeur_clean:
                continue
            # Regrouper par colonne avec scores de confiance
            col_texts = {0: [], 1: [], 2: []}
            col_confidences = {0: [], 1: [], 2: []}
            col_heights = {0: [], 1: [], 2: []}  # Pour détecter débordement vertical
            
            for word in line_words:
                col_idx = word['column']
                col_texts[col_idx].append(word['text'])
                col_confidences[col_idx].append(word['conf'])
                col_heights[col_idx].append(word['height'])
            
            cle_text = ' '.join(col_texts[0])
            valeur_text = ' '.join(col_texts[1])
            proposition_text = ' '.join(col_texts[2])  # Colonne 3 (manuscrit souvent)
            
            # Nettoyage OCR
            cle_clean = clean_ocr_text(cle_text, enable_regex=True, enable_confusion=False) if cle_text else ""
            valeur_clean = clean_ocr_text(valeur_text, enable_regex=True, enable_confusion=False) if valeur_text else ""
            proposition_clean = clean_ocr_text(proposition_text, enable_regex=True, enable_confusion=False) if proposition_text else ""
            
            # Ne garder que les lignes avec clé ET valeur
            if not cle_clean or not valeur_clean:
                continue
            
            # Calcul confiance moyenne colonne 3 (proposition manuscrite)
            conf_col3 = int(np.mean(col_confidences[2])) if col_confidences[2] else 0
            
            # DÉTECTION DÉBORDEMENT: hauteur anormale ou longueur excessive
            avg_height_col3 = np.mean(col_heights[2]) if col_heights[2] else 0
            # Hauteur normale ~20-40px, débordement si >60px ou texte >200 caractères
            has_overflow = (avg_height_col3 > 60) or (len(proposition_clean) > 200)
            
            # SEUIL CONFIANCE: <60 = peu fiable (manuscrit mal OCRisé)
            LOW_CONFIDENCE_THRESHOLD = 60
            is_low_confidence = conf_col3 < LOW_CONFIDENCE_THRESHOLD
            
            # Analyse qualité de la valeur (colonne 2)
            quality = analyze_value_quality(valeur_clean)
            
            # Créer l'entrée enrichie
            entry = {
                "fichier": Path(pdf_path).stem.replace("pages_cibles_", "") + ".PDF",
                "page": original_page_num + 1,
                "lot": lot_number,
                "cle": cle_clean,
                "valeur": valeur_clean,
                "proposition": proposition_clean,  # Colonne 3
                "confiance_ocr_proposition": conf_col3,  # Score 0-100
                "debordement_detecte": has_overflow,
                "fiabilite_faible": is_low_confidence,
                "a_verifier": not quality["claire"]  # Analyse colonne 2 uniquement
            }
            
            results.append(entry)
        
        lines_extracted = len([r for r in results if r['page'] == original_page_num + 1])
        status = "OK" if lines_extracted > 0 else "WARN"
        print(f"[{status}] Page {pdf_page_idx + 1}: {lines_extracted} lignes extraites")
    
    doc.close()
    return results


def _normalise_for_match(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))


def _three_column_bounds(raw_bounds: List[int], words: List[Dict]) -> Optional[List[int]]:
    """Choisit les quatre traits qui encadrent les trois en-t?tes du tableau."""
    bounds = sorted(set(int(v) for v in raw_bounds))
    anchors = {}
    for word in words:
        text = _normalise_for_match(word["text"])
        if text.startswith("designation"):
            anchors["designation"] = word["left"]
        elif text.startswith("specification"):
            anchors["specification"] = word["left"]
        elif text.startswith("proposition"):
            anchors["proposition"] = word["left"]
    if len(anchors) == 3:
        d, s, p = anchors["designation"], anchors["specification"], anchors["proposition"]
        print(f"[DEBUG] Ancrages en-t?tes: {anchors}")
        left = [v for v in bounds if v < d]
        sep1 = [v for v in bounds if d < v < s]
        sep2 = [v for v in bounds if s < v < p]
        right = [v for v in bounds if v > p]
        if left and sep1 and sep2 and right:
            return [max(left), max(sep1), max(sep2), min(right)]
    merged = merge_close(bounds, gap=80)
    return merged[-4:] if len(merged) >= 4 else None


def _ocr_grid_cell(image: np.ndarray, cols: List[int], rows: List[int], row: int, col: int) -> str:
    margin = 8
    cell = image[rows[row] + margin:rows[row + 1] - margin, cols[col] + margin:cols[col + 1] - margin]
    return pytesseract.image_to_string(cell, lang="fra+eng", config="--psm 6").strip() if cell.size else ""


def extract_structured_rows(pdf_path: str | Path, page_contexts: Optional[List] = None) -> List[Dict]:
    """Extrait les lignes cellule par cellule, sans associer les mots selon Y."""
    from pdf_extraction.core.quality_analyzer import analyze_value_quality
    doc = fitz.open(pdf_path)
    results = []
    for filtered_idx in range(doc.page_count):
        context = page_contexts[filtered_idx] if page_contexts and filtered_idx < len(page_contexts) else None
        original_page = context.page_num if context else filtered_idx
        print(f"\n[EXTRACTION] Page {filtered_idx + 1}/{doc.page_count} du PDF filtr? (page {original_page + 1} du document original)")
        image = cv2.cvtColor(render_page(pdf_path, filtered_idx, dpi=300), cv2.COLOR_RGB2GRAY)
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, lang="fra+eng", config="--psm 6")
        words = [{"text": data["text"][i].strip(), "left": int(data["left"][i]), "top": int(data["top"][i])}
                 for i in range(len(data["text"])) if data["text"][i].strip()]
        raw_cols, rows = detect_table_grid(image)
        cols = _three_column_bounds(raw_cols, words)
        if not cols or len(rows) < 2:
            print(f"[WARN] Page {filtered_idx + 1}: grille inexploitable")
            continue

        match = re.search(r"\blot\D*(\d+)", context.normalized_text if context else "", re.I)
        lot = int(match.group(1)) if match else None
        pending = None
        for row in range(len(rows) - 1):
            cells = [_ocr_grid_cell(image, cols, rows, row, col) for col in range(3)]
            key, value, proposal = [clean_ocr_text(x, enable_regex=True, enable_confusion=False) if x else "" for x in cells]
            key_norm = _normalise_for_match(key)
            if row == 0 or not key:
                continue
            if key_norm.startswith("nb") or "fournisseurs doivent" in key_norm:
                break
            if not value:
                if pending:
                    pending["cle"] = (pending["cle"] + " " + key).strip()
                continue
            if pending:
                results.append(pending)
            quality = analyze_value_quality(value)
            pending = {"fichier": Path(pdf_path).stem.replace("pages_cibles_", "") + ".PDF", "page": original_page + 1,
                       "lot": lot, "cle": key, "valeur": value, "proposition": proposal,
                       "confiance_ocr_proposition": 100 if proposal else 0, "debordement_detecte": False,
                       "fiabilite_faible": not bool(proposal), "a_verifier": not quality["claire"]}
        if pending:
            results.append(pending)
        count = sum(item["page"] == original_page + 1 for item in results)
        print(f"[{'OK' if count else 'WARN'}] Page {filtered_idx + 1}: {count} lignes extraites")
    doc.close()
    return results


def to_json(results: List[Dict], output_path: str | Path = "data/output/extraction.json", use_detected_headers: bool = False) -> None:
    """
    Sauvegarde les résultats en JSON enrichi.
    
    FORMAT: Liste de {fichier, page, lot, cle, valeur, proposition, confiance_ocr_proposition, 
                      debordement_detecte, fiabilite_faible, a_verifier, validation_llm}
    
    Args:
        results: Liste de dictionnaires extraits
        output_path: Chemin du fichier de sortie
        use_detected_headers: Ignoré (compatibilité legacy)
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Les résultats sont déjà au format enrichi
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"[OK] JSON exporte: {output_path}")


def extract_specification_column(
    pdf_path: str | Path,
    page_number: int,
    poppler_path: Optional[str] = None,
    dpi: int = 300,
) -> List[Dict]:
    """
    Extrait le texte de la colonne "Spécification" ou "Caractéristiques techniques minimales".
    
    Utilise le nouveau pipeline basé sur la détection de grille par vision.
    
    Args:
        pdf_path: Chemin du fichier PDF
        page_number: Numéro de page (0-indexed)
        poppler_path: Non utilisé (conservé pour compatibilité)
        dpi: Résolution
    
    Returns:
        Liste de dictionnaires {"page": N, "row": N, "specification": "..."}
    """
    result = extract_column(pdf_path, page_number, target_role="specification")
    
    # Convertir au format attendu
    output = []
    for row_idx, row_text in enumerate(result["rows"], start=1):
        output.append({
            "page": result["page"],
            "row": row_idx,
            "specification": row_text
        })
    
    # Logger les warnings
    for warning in result["warnings"]:
        print(f"[{'WARN' if 'CRITICAL' in warning else 'DEBUG'}] Page {page_number}: {warning}")
    
    return output


def extract_column2_text(
    pdf_path: str | Path,
    page_number: int,
    output_dir: str | Path,
    poppler_path: Optional[str] = None,
    dpi: int = 300,
) -> Optional[Path]:
    """
    Extrait le texte de la colonne "Spécification" et l'enregistre en JSON.
    
    Args:
        pdf_path: Chemin du fichier PDF
        page_number: Numéro de page (0-indexed)
        output_dir: Dossier de sortie
        poppler_path: Non utilisé (conservé pour compatibilité)
        dpi: Résolution
    
    Returns:
        Chemin du fichier JSON créé, ou None si erreur
    """
    # Extraire le texte de la colonne
    column_data = extract_specification_column(
        pdf_path,
        page_number,
        poppler_path=poppler_path,
        dpi=dpi,
    )
    
    if not column_data:
        print(f"[WARN] Page {page_number}: No text extracted from specification column")
        return None
    
    # Créer le dossier de sortie
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Nommer le fichier
    output_path = output_dir / f"page_{page_number+1:03d}_column2.json"
    
    # Enregistrer en JSON
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(column_data, f, ensure_ascii=False, indent=2)
        print(f"[OK] Saved specification column data to: {output_path}")
        print(f"[INFO] Page {page_number}: Extracted {len(column_data)} rows")
        return output_path
    
    except Exception as e:
        print(f"[ERROR] Failed to save JSON: {e}")
        return None


def extract_all_columns(
    reader: PdfReader,
    pdf_path: str | Path,
    selected_pages: Optional[List] = None,
    output_dir: str | Path = "data/output",
    poppler_path: Optional[str] = None,
    dpi: int = 300,
) -> List[Path]:
    """
    Extrait le texte de la colonne "Spécification" pour toutes les pages sélectionnées.
    
    Args:
        reader: PdfReader ouvert
        pdf_path: Chemin du fichier PDF
        selected_pages: Liste des objets page (ou None pour traiter toutes)
        output_dir: Dossier de sortie
        poppler_path: Non utilisé (conservé pour compatibilité)
        dpi: Résolution
    
    Returns:
        Liste des chemins des fichiers JSON créés
    """
    # Si des pages sont spécifiées, trouver leurs indices
    if selected_pages is not None:
        selected_indices = []
        for page_obj in selected_pages:
            for idx, reader_page in enumerate(reader.pages):
                if reader_page is page_obj:
                    selected_indices.append(idx)
                    break
    else:
        selected_indices = list(range(len(reader.pages)))
    
    output_paths = []
    
    print(f"\n[INFO] Extracting specification column from {len(selected_indices)} pages...")
    
    for page_idx in selected_indices:
        output_path = extract_column2_text(
            pdf_path,
            page_idx,
            output_dir,
            poppler_path=poppler_path,
            dpi=dpi,
        )
        
        if output_path:
            output_paths.append(output_path)
    
    print(f"[OK] Extracted {len(output_paths)} column JSON files")
    return output_paths
