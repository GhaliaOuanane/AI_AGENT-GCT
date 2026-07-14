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
                # Retourner le label original nettoyé
                detected_label = ocr_text.strip()
                return role, 100, "exact", detected_label
    
    # Niveau 1bis : match tolérant à une petite erreur OCR
    for template in KNOWN_TEMPLATES:
        for role, exact_label in template.items():
            score = fuzz.ratio(norm, exact_label)
            if score >= 90:
                detected_label = ocr_text.strip()
                return role, score, "exact_tolerant", detected_label
    
    # Niveau 2 : fuzzy fallback (3e template inconnu)
    best_role, best_score, best_label = None, 0, ""
    for role, aliases in FUZZY_ALIASES.items():
        for alias in aliases:
            score = fuzz.partial_ratio(norm, alias)
            if score > best_score:
                best_role, best_score, best_label = role, score, ocr_text.strip()
    
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


def extract_structured_rows(pdf_path: str | Path) -> List[Dict]:
    """
    Extrait toutes les lignes structurées du PDF avec alignement des 3 colonnes.
    
    Args:
        pdf_path: Chemin du fichier PDF
    
    Returns:
        Liste de dictionnaires structurés par ligne
    """
    doc = fitz.open(pdf_path)
    results = []
    
    for page_num in range(doc.page_count):
        # Étape 1: Rendu HD
        try:
            img_rgb = render_page(pdf_path, page_num, dpi=300)
            img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        except Exception as e:
            print(f"[ERROR] Page {page_num}: Render failed - {e}")
            continue
        
        # Étape 2: Détection de grille
        col_bounds, row_bounds = detect_table_grid(img_gray)
        
        if len(col_bounds) < 4 or len(row_bounds) < 2:
            print(f"[WARN] Page {page_num}: Grid not detected, using fallback")
            # Fallback K-means
            ocr_data = pytesseract.image_to_data(img_gray, output_type=pytesseract.Output.DICT)
            ocr_words = [{'left': int(ocr_data['left'][i]), 'width': int(ocr_data['width'][i])}
                         for i in range(len(ocr_data['text'])) if ocr_data['text'][i].strip()]
            if ocr_words:
                col_centers = fallback_column_detection(ocr_words)
                col_bounds = sorted(col_centers)
                row_bounds = [0, img_gray.shape[0]]
            else:
                print(f"[ERROR] Page {page_num}: No OCR words for fallback")
                continue
        
        # Étape 3: OCR de la ligne d'en-tête
        header_row_idx = 0
        header_cells = []
        for col_idx in range(len(col_bounds) - 1):
            cell_bbox = (col_bounds[col_idx] + 5, col_bounds[col_idx + 1] - 5,
                         row_bounds[header_row_idx] + 5, row_bounds[header_row_idx + 1] - 5)
            cell_img = extract_cell_from_image(img_gray, cell_bbox)
            header_text = ocr_cell(cell_img)
            header_cells.append(header_text)
        
        # Étape 4: Mapping sémantique des en-têtes
        role_to_col_idx = {}
        detected_headers = {}  # Stocker les noms détectés {role: detected_label}
        modele_detecte = "unknown"
        for idx, cell_text in enumerate(header_cells):
            role, score, method, detected_label = match_header(cell_text)
            if role:
                role_to_col_idx[role] = idx
                detected_headers[role] = detected_label
                if method in ["exact", "exact_tolerant"]:
                    # Déterminer le modèle basé sur le premier match exact
                    norm_text = normalize(cell_text)
                    if role == "designation":
                        if norm_text == "designation":
                            modele_detecte = "modele_1"
                        elif norm_text == "composants de l offre":
                            modele_detecte = "modele_2"
                    elif role == "specification":
                        if "exige" in norm_text or "preciser" in norm_text:
                            modele_detecte = "modele_1_variant"
        
        # Étape 5: OCR des cellules de données pour les 3 colonnes
        for row_idx in range(1, len(row_bounds) - 1):
            row_data = {
                "fichier": Path(pdf_path).name,
                "page": page_num + 1,
                "lot": None,  # À détecter si possible
                "modele_detecte": modele_detecte,
                "designation": "",
                "specification": "",
                "proposition": "",
                "confiance_ocr": {
                    "designation": 0,
                    "specification": 0,
                    "proposition": 0
                },
                "methode_mapping_headers": "unknown",
                "detected_headers": detected_headers  # Ajouter les noms détectés
            }
            
            # OCRiser chaque colonne si elle est mappée
            for role in ["designation", "specification", "proposition"]:
                if role in role_to_col_idx:
                    col_idx = role_to_col_idx[role]
                    cell_bbox = (col_bounds[col_idx] + 5, col_bounds[col_idx + 1] - 5,
                                 row_bounds[row_idx] + 5, row_bounds[row_idx + 1] - 5)
                    cell_img = extract_cell_from_image(img_gray, cell_bbox)
                    cell_text = ocr_cell(cell_img)
                    
                    if cell_text:
                        # Nettoyage OCR
                        cleaned_text = clean_ocr_text(cell_text, enable_regex=True, enable_confusion=False)
                        row_data[role] = cleaned_text
                        # Score de confiance simplifié (longueur du texte)
                        row_data["confiance_ocr"][role] = min(100, len(cleaned_text) * 5)
            
            # Déterminer la méthode de mapping
            for idx, cell_text in enumerate(header_cells):
                role, score, method, detected_label = match_header(cell_text)
                if role and method in ["exact", "exact_tolerant"]:
                    row_data["methode_mapping_headers"] = method
                    break
            
            # Ajouter la ligne si elle a du contenu
            if any(row_data[col] for col in ["designation", "specification", "proposition"]):
                results.append(row_data)
        
        status = "OK" if results else "WARN"
        print(f"[{status}] Page {page_num + 1}/{doc.page_count}: {len([r for r in results if r['page'] == page_num + 1])} lignes extraites")
    
    doc.close()
    return results


def to_json(results: List[Dict], output_path: str | Path = "data/output/extraction.json", use_detected_headers: bool = True) -> None:
    """
    Sauvegarde les résultats en JSON structuré.
    
    Args:
        results: Liste de dictionnaires structurés
        output_path: Chemin du fichier de sortie
        use_detected_headers: Si True, REMPLACE les clés génériques par les noms de headers détectés
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Si demandé, REMPLACER les noms génériques par les noms détectés
    if use_detected_headers:
        processed_results = []
        for row in results:
            new_row = {}
            
            # Copier d'abord tous les champs qui ne sont pas des colonnes
            for key, value in row.items():
                if key not in ["designation", "specification", "proposition"]:
                    new_row[key] = value
            
            # Si detected_headers existe, utiliser les noms détectés
            if "detected_headers" in row and row["detected_headers"]:
                detected = row["detected_headers"]
                
                # REMPLACER "designation" par le nom détecté
                if "designation" in detected and detected["designation"]:
                    header_name = detected["designation"]
                    new_row[header_name] = row.get("designation", "")
                else:
                    new_row["designation"] = row.get("designation", "")
                
                # REMPLACER "specification" par le nom détecté
                if "specification" in detected and detected["specification"]:
                    header_name = detected["specification"]
                    new_row[header_name] = row.get("specification", "")
                else:
                    new_row["specification"] = row.get("specification", "")
                
                # REMPLACER "proposition" par le nom détecté
                if "proposition" in detected and detected["proposition"]:
                    header_name = detected["proposition"]
                    new_row[header_name] = row.get("proposition", "")
                else:
                    new_row["proposition"] = row.get("proposition", "")
            else:
                # Pas de detected_headers, garder les noms génériques
                new_row["designation"] = row.get("designation", "")
                new_row["specification"] = row.get("specification", "")
                new_row["proposition"] = row.get("proposition", "")
            
            processed_results.append(new_row)
        
        results = processed_results
    
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
