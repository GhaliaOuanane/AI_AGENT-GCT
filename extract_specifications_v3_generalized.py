"""
✅ EXTRACTION SPÉCIFICATIONS - VERSION V3 GÉNÉRALISÉ

Handles MULTIPLE TABLES per document with dynamic detection:

ÉTAPE 0: Segmentation en tableaux (par région, pas par page)
- Detect lot/market titles (regex pattern, not hard-coded)
- Identify separate tables by title, column count, vertical gaps
- Each table gets table_id (table_1, table_2, ...) independent of title text

ÉTAPE 1: Grid detection per table region (multiple passes, robust)
- Pass 1: Standard adaptive thresholding + morphology
- Pass 2: Softer thresholds if line count too low
- Keep result with best coherence with text projection
- Validate: ≥3 horizontal lines AND ≥2 vertical lines

ÉTAPE 2: Header detection (large alias list, fuzzy matching)
- Column 1: ["désignation", "designation", "composants", "article", "poste", ...]
- Column 2 (TARGET): ["spécification", "caractéristiques techniques", "exigence", ...]
- Column 3: ["proposition", "propositions"]
- Fuzzy matching (edit distance, accent-tolerant, case-insensitive)

ÉTAPE 2bis: Section row detection
- Row where: Designation non-empty AND (Specification empty AND Proposition empty)
- Mark as type: "section", valeur: null (not a data row)
- Don't count in structural validation (Étape 3)

ÉTAPE 3: Structural validation (per table, not per page)
- Count data lines (exclude sections, headers)
- Requirement: nb_lignes_designation == nb_lignes_specification
- If mismatch: table_rejetee=true, motif="lignes_desalignees"

ÉTAPE 4: Multi-page continuity
- Same table continues if: same column count AND no new lot title AND no header-like line
- Inherits table_id and column index from previous page
- Don't restart line numbering

ÉTAPE 5: OCR + double confidence check (per cell)
- Upscale, denoise, adaptive thresholding, deskew
- Flag if: confidence <70% OR incoherent text OR symbols OR abnormal length

ÉTAPE 6: Output format (single JSON with all tables)
- One "tables" array per document
- Each table has: table_id, titre_detecte, pages, entries[]
- Each entry has: type (donnée/section), valeur, confiance, flags

ÉTAPE 7: Systemic failure guard
- If >50% tables rejected → stop execution (not individual failure)
- If no tables segmented at all → "segmentation_tableaux_echouee"

NO API/LLM. Tesseract + OpenCV local only.
"""

import fitz
import cv2
import pytesseract
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
import json
import re
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, asdict

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ============================================================================
# CONSTANTES
# ============================================================================

# Header alias lists (column 1, 2, 3)
HEADER_ALIASES = {
    "col1": ["désignation", "designation", "composants", "composant", "composant de l'offre", 
             "composants de l'offre", "article", "poste", "libellé", "designation du produit"],
    "col2": ["spécification", "specification", "caractéristiques techniques minimales", 
             "caractéristiques minimales", "caract techniques", "exigence", "exigences",
             "critères techniques", "requirements", "specs"],
    "col3": ["proposition", "propositions", "offre", "votre proposition"]
}

# Lot/market title pattern
LOT_TITLE_PATTERN = r'^\s*(lot|marché|n°|no|numero)\s*[\d\-a-z]*\s*[:.\-]?\s*(.+)'

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class TableRegion:
    """Region candidate for a table."""
    page_num: int
    x_min: int
    y_min: int
    x_max: int
    y_max: int
    
    @property
    def width(self) -> int:
        return self.x_max - self.x_min
    
    @property
    def height(self) -> int:
        return self.y_max - self.y_min


@dataclass
class GridInfo:
    """Detected grid structure."""
    h_lines: List[Tuple[int, int]]  # [(y_min, y_max), ...]
    v_lines: List[Tuple[int, int]]  # [(x_min, x_max), ...]
    rows: List[Tuple[int, int]]     # [(y_min, y_max), ...] derived from h_lines
    cols: List[Tuple[int, int]]     # [(x_min, x_max), ...] derived from v_lines
    valid: bool
    

@dataclass
class HeaderInfo:
    """Detected header information."""
    col1_text: Optional[str]
    col2_text: Optional[str]
    col3_text: Optional[str]
    col1_idx: int
    col2_idx: int
    col3_idx: Optional[int]
    col2_suspicious: bool


# ============================================================================
# ÉTAPE 0: SEGMENTATION EN TABLEAUX
# ============================================================================

def detect_lot_title(text: str) -> Optional[str]:
    """Détecte si texte ressemble à titre de lot."""
    match = re.search(LOT_TITLE_PATTERN, text.strip(), re.IGNORECASE)
    if match:
        return match.group(0)
    return None


def normalize_text_for_comparison(text: str) -> str:
    """Normalise texte pour comparaison."""
    text = text.lower().strip()
    text = re.sub(r'[àâäéèêëïîôöœuù]', '', text)
    return text


def segment_tables_in_document(pdf_path: str) -> Dict[int, List[TableRegion]]:
    """
    Segmente document en tableaux par région.
    Retourne: {page_num: [TableRegion, ...]}
    """
    doc = fitz.open(pdf_path)
    tables_by_page = defaultdict(list)
    
    try:
        for page_num in range(doc.page_count):
            tables_by_page[page_num] = detect_tables_on_page(doc, page_num)
    finally:
        doc.close()
    
    return dict(tables_by_page)


def detect_tables_on_page(doc, page_num: int, dpi: int = 300) -> List[TableRegion]:
    """
    Détecte régions de tableaux sur une page.
    CORRECTION: Fusionner régions adjacentes pour éviter sur-segmentation.
    """
    page = doc[page_num]
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n).copy()
    if pix.n == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
    elif pix.n == 1:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    
    # Detect candidate regions by horizontal gaps
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    
    # Horizontal projection to find gap regions
    h_proj = np.sum(gray < 200, axis=1)  # Dark pixels (text/lines)
    
    # Find transitions: gap when projection drops to near-zero
    threshold = np.max(h_proj) * 0.1
    regions = []
    in_region = False
    y_start = 0
    
    min_region_height = 150  # INCREASED from 50 to avoid micro-fragments
    
    for y in range(len(h_proj)):
        if h_proj[y] > threshold and not in_region:
            y_start = y
            in_region = True
        elif h_proj[y] <= threshold and in_region:
            # Region ended
            if y - y_start > min_region_height:
                regions.append((y_start, y))
            in_region = False
    
    if in_region and len(h_proj) - y_start > min_region_height:
        regions.append((y_start, len(h_proj)))
    
    # Merge adjacent regions (gap < 100px) to avoid over-segmentation
    merged_regions = []
    if regions:
        current_start, current_end = regions[0]
        
        for y_start, y_end in regions[1:]:
            gap = y_start - current_end
            if gap < 100:  # Merge if gap is small
                current_end = y_end
            else:
                merged_regions.append((current_start, current_end))
                current_start, current_end = y_start, y_end
        
        merged_regions.append((current_start, current_end))
    else:
        merged_regions = regions
    
    # Convert to TableRegion objects
    table_regions = []
    for y_min, y_max in merged_regions:
        # Vertical extent full width for now
        table_regions.append(TableRegion(
            page_num=page_num,
            x_min=0,
            y_min=y_min,
            x_max=img.shape[1],
            y_max=y_max
        ))
    
    return table_regions


# ============================================================================
# ÉTAPE 1: GRID DETECTION (MULTI-PASS, ROBUST)
# ============================================================================

def detect_grid_robust(img: np.ndarray, table_region: TableRegion, page_num: int) -> Tuple[Optional[GridInfo], List[str]]:
    """
    Détecte grille avec passes multiples.
    Retourne: (GridInfo or None, errors_list)
    """
    errors = []
    
    # Crop to region
    y_min, y_max = table_region.y_min, table_region.y_max
    x_min, x_max = table_region.x_min, table_region.x_max
    
    if y_max <= y_min or x_max <= x_min:
        return None, ["Region invalide"]
    
    region_img = img[y_min:y_max, x_min:x_max].copy()
    gray = cv2.cvtColor(region_img, cv2.COLOR_RGB2GRAY)
    
    # Pass 1: Standard morphology
    grid_1 = detect_grid_pass(gray, "pass1", table_region.width)
    
    # Pass 2: Softer thresholds if Pass 1 insufficient
    grid_2 = None
    if grid_1 and len(grid_1.h_lines) < 3:
        grid_2 = detect_grid_pass(gray, "pass2", table_region.width)
    
    # Choose best result
    if grid_1 and grid_1.valid:
        best_grid = grid_1
    elif grid_2 and grid_2.valid:
        best_grid = grid_2
    else:
        best_grid = None
    
    if best_grid is None:
        errors.append(f"Page {page_num}: Grille non détectée")
        return None, errors
    
    return best_grid, errors


def detect_grid_pass(gray: np.ndarray, pass_name: str, region_width: int) -> Optional[GridInfo]:
    """
    Single pass of grid detection.
    """
    try:
        # Binarization
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, blockSize=11, C=2
        )
        
        # Detect horizontal lines
        h_kernel_size = max(5, region_width // 25)
        h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h_kernel_size, 1))
        h_lines_img = cv2.erode(binary, h_kernel, iterations=1)
        h_lines_img = cv2.dilate(h_lines_img, h_kernel, iterations=1)
        
        # Detect vertical lines
        v_kernel_size = max(5, gray.shape[0] // 40)
        v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_kernel_size))
        v_lines_img = cv2.erode(binary, v_kernel, iterations=1)
        v_lines_img = cv2.dilate(v_lines_img, v_kernel, iterations=1)
        
        # Extract line positions
        h_lines = extract_line_positions_horizontal(h_lines_img)
        v_lines = extract_line_positions_vertical(v_lines_img)
        
        # Validate
        if len(h_lines) < 3 or len(v_lines) < 2:
            return None
        
        # Derive rows and cols
        rows = cluster_lines_horizontal(h_lines)
        cols = cluster_lines_vertical(v_lines)
        
        return GridInfo(
            h_lines=h_lines,
            v_lines=v_lines,
            rows=rows,
            cols=cols,
            valid=len(rows) >= 2 and len(cols) >= 2
        )
    
    except Exception as e:
        return None


def extract_line_positions_horizontal(binary: np.ndarray) -> List[Tuple[int, int]]:
    """Extract horizontal line Y positions."""
    contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    y_positions = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w > 50:  # Significant horizontal extent
            y_positions.append((y, y + h))
    
    return sorted(set(y_positions))


def extract_line_positions_vertical(binary: np.ndarray) -> List[Tuple[int, int]]:
    """Extract vertical line X positions."""
    contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    x_positions = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if h > 50:  # Significant vertical extent
            x_positions.append((x, x + w))
    
    return sorted(set(x_positions))


def cluster_lines_horizontal(y_positions: List[Tuple[int, int]], threshold: int = 15) -> List[Tuple[int, int]]:
    """Cluster nearby horizontal lines into rows."""
    if not y_positions:
        return []
    
    rows = []
    current_cluster = [y_positions[0]]
    
    for y_pos in y_positions[1:]:
        if abs(y_pos[0] - current_cluster[0][0]) <= threshold:
            current_cluster.append(y_pos)
        else:
            avg_y = (min(p[0] for p in current_cluster), max(p[1] for p in current_cluster))
            rows.append(avg_y)
            current_cluster = [y_pos]
    
    if current_cluster:
        avg_y = (min(p[0] for p in current_cluster), max(p[1] for p in current_cluster))
        rows.append(avg_y)
    
    return rows


def cluster_lines_vertical(x_positions: List[Tuple[int, int]], threshold: int = 15) -> List[Tuple[int, int]]:
    """Cluster nearby vertical lines into columns."""
    if not x_positions:
        return []
    
    cols = []
    current_cluster = [x_positions[0]]
    
    for x_pos in x_positions[1:]:
        if abs(x_pos[0] - current_cluster[0][0]) <= threshold:
            current_cluster.append(x_pos)
        else:
            avg_x = (min(p[0] for p in current_cluster), max(p[1] for p in current_cluster))
            cols.append(avg_x)
            current_cluster = [x_pos]
    
    if current_cluster:
        avg_x = (min(p[0] for p in current_cluster), max(p[1] for p in current_cluster))
        cols.append(avg_x)
    
    return cols


# ============================================================================
# ÉTAPE 2: HEADER DETECTION (FUZZY MATCHING)
# ============================================================================

def ocr_words_in_region(img: np.ndarray, region: TableRegion, dpi: int = 400) -> List[Dict]:
    """OCR words in table region."""
    y_min, y_max = region.y_min, region.y_max
    x_min, x_max = region.x_min, region.x_max
    
    region_img = img[y_min:y_max, x_min:x_max].copy()
    gray = cv2.cvtColor(region_img, cv2.COLOR_RGB2GRAY)
    
    # CLAHE for quality
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    
    try:
        data = pytesseract.image_to_data(
            gray, output_type=pytesseract.Output.DICT, lang='fra'
        )
    except:
        return []
    
    words = []
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        conf = int(data['conf'][i])
        if text and conf > 30:
            words.append({
                'text': text,
                'x': int(data['left'][i]) + x_min,
                'y': int(data['top'][i]) + y_min,
                'width': int(data['width'][i]),
                'height': int(data['height'][i]),
                'conf': conf
            })
    
    return words


def detect_headers(img: np.ndarray, region: TableRegion, grid: GridInfo) -> HeaderInfo:
    """
    Détecte en-têtes de colonnes par fuzzy matching.
    """
    # OCR first row
    if not grid.rows:
        return HeaderInfo(None, None, None, 0, 1, 2, False)
    
    first_row_y_min, first_row_y_max = grid.rows[0]
    
    # Get words in first row
    words = ocr_words_in_region(img, region)
    first_row_words = [w for w in words if first_row_y_min <= w['y'] + w['height']/2 <= first_row_y_max]
    
    if not first_row_words:
        return HeaderInfo(None, None, None, 0, 1, 2, False)
    
    # Group by column
    if len(grid.cols) < 3:
        return HeaderInfo(None, None, None, 0, 1, None, False)
    
    col1_x_min, col1_x_max = grid.cols[0]
    col2_x_min, col2_x_max = grid.cols[1]
    col3_x_min, col3_x_max = grid.cols[2] if len(grid.cols) > 2 else (None, None)
    
    # Extract text per column
    def get_column_text(x_min, x_max):
        col_words = [w for w in first_row_words if x_min <= w['x'] + w['width']/2 <= x_max]
        return ' '.join([w['text'] for w in sorted(col_words, key=lambda w: w['x'])])
    
    col1_text = get_column_text(col1_x_min, col1_x_max)
    col2_text = get_column_text(col2_x_min, col2_x_max)
    col3_text = get_column_text(col3_x_min, col3_x_max) if col3_x_max else None
    
    # Match against aliases
    col2_suspicious = not fuzzy_match_header(col2_text, HEADER_ALIASES["col2"])
    
    return HeaderInfo(
        col1_text=col1_text,
        col2_text=col2_text,
        col3_text=col3_text,
        col1_idx=0,
        col2_idx=1,
        col3_idx=2 if col3_x_max else None,
        col2_suspicious=col2_suspicious
    )


def fuzzy_match_header(text: str, aliases: List[str], threshold: float = 0.7) -> bool:
    """
    Fuzzy match text against alias list.
    Returns True if match found.
    """
    text_norm = normalize_text_for_comparison(text)
    
    for alias in aliases:
        alias_norm = normalize_text_for_comparison(alias)
        
        # Simple substring match (can be enhanced with Levenshtein)
        if alias_norm in text_norm or text_norm in alias_norm:
            return True
    
    return False


# ============================================================================
# STUB: REMAINING ÉTAPES (TO BE COMPLETED)
# ============================================================================

def ocr_cell_content(img: np.ndarray, y_min: int, y_max: int, x_min: int, x_max: int) -> Tuple[str, float]:
    """OCR contenu d'une cellule avec prétraitement."""
    try:
        margin = 2
        y_min = max(0, y_min + margin)
        y_max = min(img.shape[0], y_max - margin)
        x_min = max(0, x_min + margin)
        x_max = min(img.shape[1], x_max - margin)
        
        if y_max <= y_min or x_max <= x_min or y_min < 0 or x_min < 0:
            return "", 0.0
        
        cell = img[int(y_min):int(y_max), int(x_min):int(x_max)].copy()
        if cell.size == 0:
            return "", 0.0
        
        h, w = cell.shape[:2]
        if h < 5 or w < 5:
            return "", 0.0
        
        # Upscale if small
        if w < 150:
            scale = max(2, int(150 / w))
            cell = cv2.resize(cell, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        if len(cell.shape) == 3 and cell.shape[2] >= 3:
            gray = cv2.cvtColor(cell, cv2.COLOR_RGB2GRAY)
        elif len(cell.shape) == 3:
            gray = cv2.cvtColor(cell, cv2.COLOR_RGBA2GRAY)
        else:
            gray = cell
        
        if gray.size == 0:
            return "", 0.0
        
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Binarization
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, blockSize=11, C=2
        )
        
        # OCR
        try:
            data = pytesseract.image_to_data(
                binary, output_type=pytesseract.Output.DICT,
                lang='fra', config='--psm 6'
            )
        except:
            return "", 0.0
        
        words = []
        confs = []
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            conf = int(data['conf'][i])
            if text and conf > 30:
                words.append(text)
                confs.append(conf)
        
        if not words:
            return "", 0.0
        
        text = ' '.join(words)
        avg_conf = np.mean(confs) if confs else 0.0
        
        return text, avg_conf
    
    except Exception as e:
        return "", 0.0


def clean_ocr_text(text: str) -> str:
    """Nettoyage OCR minimal."""
    replacements = {
        'ñ': 'n', 'ü': 'u', 'ö': 'o', 'ä': 'a',
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'â': 'a', 'ê': 'e', 'î': 'i', 'ô': 'o', 'û': 'u',
        'à': 'a', 'è': 'e', 'ì': 'i', 'ò': 'o', 'ù': 'u',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def check_text_coherence(text: str) -> Optional[str]:
    """Vérifie cohérence textuelle."""
    if not text:
        return None
    
    # Séquence sans voyelle >= 4 caractères
    vowels = 'aeiouyàâäéèêëïîôöœuù'
    for word in text.split():
        word_alpha = ''.join(c.lower() for c in word if c.isalpha())
        if len(word_alpha) >= 4 and not any(v in word_alpha for v in vowels):
            return "texte_incoherent"
    
    # Symboles isolés suspects
    if re.search(r'[|\\~]', text):
        return "symbole_suspect"
    
    return None


def is_section_row(des_text: str, spec_text: str) -> bool:
    """
    ÉTAPE 2bis: Détecte ligne de section.
    Row where: Designation non-vide AND Specification vide
    """
    return (des_text.strip() != "" and spec_text.strip() == "")


def extract_entries_from_table(img: np.ndarray, region: TableRegion, grid: GridInfo, 
                               header: HeaderInfo) -> Dict:
    """
    ÉTAPE 2bis + 3 + 4 + 5: Extract entries from table.
    """
    if not grid.rows or len(grid.cols) < 2:
        return {
            "entries": [],
            "nb_lignes_designation": 0,
            "nb_lignes_specification": 0,
            "table_rejetee": True,
            "motif_rejet": "structure_insuffisante"
        }
    
    # Column boundaries (X coordinates)
    col1_x_min, col1_x_max = grid.cols[0]
    col2_x_min, col2_x_max = grid.cols[1] if len(grid.cols) > 1 else (col1_x_min, col1_x_max)
    
    # Adjust to region coordinates
    col1_x_min += region.x_min
    col1_x_max += region.x_min
    col2_x_min += region.x_min
    col2_x_max += region.x_min
    
    entries = []
    des_lines_count = 0
    spec_lines_count = 0
    
    # Skip first row (header)
    data_rows = grid.rows[1:] if len(grid.rows) > 1 else []
    
    for row_idx, (y_min, y_max) in enumerate(data_rows):
        # Adjust Y to image coordinates
        y_min += region.y_min
        y_max += region.y_min
        
        # OCR colonne 1 (Designation)
        des_text, des_conf = ocr_cell_content(img, y_min, y_max, col1_x_min, col1_x_max)
        des_text = clean_ocr_text(des_text)
        
        # OCR colonne 2 (Specification)
        spec_text, spec_conf = ocr_cell_content(img, y_min, y_max, col2_x_min, col2_x_max)
        spec_text = clean_ocr_text(spec_text)
        
        # Count non-empty lines
        if des_text.strip():
            des_lines_count += 1
        if spec_text.strip():
            spec_lines_count += 1
        
        # Skip empty rows
        if not (des_text.strip() or spec_text.strip()):
            continue
        
        # ÉTAPE 2bis: Section row detection
        if is_section_row(des_text, spec_text):
            entries.append({
                "designation": des_text,
                "type": "section",
                "valeur": None,
                "confiance_ocr": None,
                "a_verifier": False,
                "motif_verification": None
            })
            continue
        
        # Data row: validate confidence
        a_verifier = False
        motif = None
        
        if spec_conf < 70:
            a_verifier = True
            motif = "confiance_faible"
        else:
            coherence_issue = check_text_coherence(spec_text)
            if coherence_issue:
                a_verifier = True
                motif = coherence_issue
        
        entries.append({
            "designation": des_text,
            "type": "donnee",
            "valeur": spec_text,
            "confiance_ocr": round(spec_conf, 1),
            "a_verifier": a_verifier,
            "motif_verification": motif
        })
    
    # ÉTAPE 3: Validate structure (data rows only, not sections)
    data_entries = [e for e in entries if e['type'] == 'donnee']
    des_data_count = sum(1 for e in data_entries if e['designation'].strip())
    spec_data_count = sum(1 for e in data_entries if e['valeur'] and e['valeur'].strip())
    
    table_rejetee = (des_data_count != spec_data_count and des_data_count > 0)
    motif_rejet = "lignes_desalignees" if table_rejetee else None
    
    return {
        "entries": entries,
        "nb_lignes_designation": des_lines_count,
        "nb_lignes_specification": spec_lines_count,
        "table_rejetee": table_rejetee,
        "motif_rejet": motif_rejet
    }


# ============================================================================
# MAIN PIPELINE V3
# ============================================================================

def extract_specifications_v3(pdf_path: str) -> Optional[Dict]:
    """
    Full V3 generalized pipeline.
    """
    
    print(f"\n{'='*70}")
    print("EXTRACTION SPÉCIFICATIONS V3 - GÉNÉRALISÉ")
    print(f"{'='*70}\n")
    
    # Étape 0: Segmentation
    print("Étape 0: Segmentation en tableaux...")
    try:
        tables_by_page = segment_tables_in_document(pdf_path)
    except Exception as e:
        print(f"  ERREUR: {e}")
        return None
    
    total_regions = sum(len(regions) for regions in tables_by_page.values())
    print(f"  Régions détectées: {total_regions}")
    
    if total_regions == 0:
        print("  ERREUR: segmentation_tableaux_echouee")
        return None
    
    # Process each region (stub for now)
    doc = fitz.open(pdf_path)
    all_tables = []
    
    table_counter = 1
    for page_num in sorted(tables_by_page.keys()):
        for region in tables_by_page[page_num]:
            print(f"\nPage {page_num + 1}, Région {region.y_min}-{region.y_max}...", end=" ", flush=True)
            
            # Rendu image
            page = doc[page_num]
            zoom = 400 / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n).copy()
            if pix.n == 4:
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
            elif pix.n == 1:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            
            # Étape 1: Grid detection
            grid, errors = detect_grid_robust(img, region, page_num + 1)
            if grid is None:
                print(f"X Grille échouée")
                continue
            
            # Étape 2: Header detection
            header = detect_headers(img, region, grid)
            
            # Étapes 2bis-5: Extract entries
            extraction_result = extract_entries_from_table(img, region, grid, header)
            
            # Build table structure
            table_data = {
                "table_id": f"table_{table_counter}",
                "titre_detecte": "Non détecté",  # TODO: Detect from OCR
                "pages": [page_num + 1],
                "entete_colonne2_detecte": header.col2_text,
                "entete_colonne2_suspecte": header.col2_suspicious,
                "table_rejetee": extraction_result["table_rejetee"],
                "motif_rejet": extraction_result["motif_rejet"],
                "nb_lignes_designation": extraction_result["nb_lignes_designation"],
                "nb_lignes_specification": extraction_result["nb_lignes_specification"],
                "entries": extraction_result["entries"]
            }
            
            n_entries = len(extraction_result["entries"])
            n_flagged = sum(1 for e in extraction_result["entries"] if e.get("a_verifier"))
            status = "REJET" if extraction_result["table_rejetee"] else f"{n_entries} entrées"
            print(f"OK {status} ({n_flagged} flagged)")
            
            all_tables.append(table_data)
            table_counter += 1
    
    doc.close()
    
    # Check systemic failure
    rejected_count = sum(1 for t in all_tables if t['table_rejetee'])
    if rejected_count / len(all_tables) > 0.5 if all_tables else False:
        print(f"\n  ERREUR: >50% des tableaux rejetés")
        return None
    
    # Output JSON
    result = {
        "document": Path(pdf_path).name,
        "extraction_date": datetime.utcnow().isoformat() + "Z",
        "tables": all_tables
    }
    
    output_path = Path("data/output/specifications_v3.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*70}")
    print(f"✓ Extraction complétée")
    print(f"  Tables: {len(all_tables)}")
    print(f"  Rejetées: {rejected_count}")
    print(f"  JSON: {output_path}")
    print(f"{'='*70}\n")
    
    return result


if __name__ == "__main__":
    pdf_path = "data/output/pages_cibles.pdf"
    result = extract_specifications_v3(pdf_path)
    if result:
        print("✓ V3 EXTRACTION COMPLÉTÉE")
    else:
        print("✗ V3 EXTRACTION ÉCHOUÉE")
