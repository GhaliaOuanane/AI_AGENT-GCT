"""
✅ EXTRACTION SPÉCIFICATIONS - GRILLE BASÉE

Pipeline robuste pour extraire la colonne "Spécification" d'un tableau à 3 colonnes:
1. Détection grille par morphologie mathématique (OpenCV)
2. Identification colonne "Spécification" par en-têtes
3. Extraction cellule par cellule avec OCR
4. Scoring confiance + flags de vérification
5. Sortie: source_of_truth.json

Approche:
- Aucun API/LLM (100% local)
- Cellule par cellule (pas colonne entière)
- Confiance tracée pour chaque entrée
- Héritage position pour pages sans en-tête
"""

import fitz
import cv2
import pytesseract
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ============================================================================
# TYPES ET STRUCTURES
# ============================================================================

@dataclass
class CellContent:
    """Contenu d'une cellule extraite"""
    text: str
    confidence: float
    needs_review: bool = False
    review_reason: str = ""


@dataclass
class GridCell:
    """Définition d'une cellule dans la grille"""
    col_idx: int
    row_idx: int
    x1: int
    y1: int
    x2: int
    y2: int


@dataclass
class TableGrid:
    """Grille de tableau détectée"""
    rows: List[Tuple[int, int]]  # [(y_top, y_bottom), ...]
    cols: List[Tuple[int, int]]  # [(x_left, x_right), ...]
    cells: List[GridCell]


@dataclass
class PageEntry:
    """Entrée d'une page"""
    designation: str
    valeur: str
    confiance_ocr: float
    a_verifier: bool = False
    raison_verification: str = ""


# ============================================================================
# DÉTECTION GRILLE
# ============================================================================

def render_page_to_image(pdf_path: str, page_num: int, dpi: int = 300) -> np.ndarray:
    """Rendre une page PDF en image."""
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


def detect_table_grid(img: np.ndarray, debug_output_dir: Optional[str] = None) -> Optional[TableGrid]:
    """
    Détecte la grille du tableau par morphologie mathématique.
    
    Étapes:
    1. Convertir en niveaux de gris
    2. Binarisation adaptative
    3. Détection lignes horizontales/verticales
    4. Reconstruit grille de cellules
    """
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    
    # Binarisation adaptative
    binary = cv2.adaptiveThreshold(
        gray, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=11, C=2
    )
    
    # Détection lignes horizontales
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
    h_lines = cv2.erode(binary, h_kernel, iterations=2)
    h_lines = cv2.dilate(h_lines, h_kernel, iterations=2)
    
    # Détection lignes verticales
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 50))
    v_lines = cv2.erode(binary, v_kernel, iterations=2)
    v_lines = cv2.dilate(v_lines, v_kernel, iterations=2)
    
    # Fusion
    grid = cv2.bitwise_or(h_lines, v_lines)
    
    # Trouver contours de cellules
    contours, _ = cv2.findContours(grid, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    if len(contours) < 3:  # Au moins 1 en-tête + 2 lignes = 3 contours
        return None
    
    # Extraire coordonnées des cellules
    cells = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w > 20 and h > 10:  # Filtrer bruit
            cells.append((x, y, x + w, y + h))
    
    if not cells:
        return None
    
    # Trier et déduire grille
    cells_sorted = sorted(cells, key=lambda c: (c[1], c[0]))  # Sort par Y, puis X
    
    # Extraire positions Y (lignes)
    y_positions = sorted(set(c[1] for c in cells_sorted) | set(c[3] for c in cells_sorted))
    rows = [(y_positions[i], y_positions[i+1]) for i in range(len(y_positions) - 1)]
    
    # Extraire positions X (colonnes)
    x_positions = sorted(set(c[0] for c in cells_sorted) | set(c[2] for c in cells_sorted))
    cols = [(x_positions[i], x_positions[i+1]) for i in range(len(x_positions) - 1)]
    
    # Construire cellules structurées
    grid_cells = []
    for row_idx, (y1, y2) in enumerate(rows):
        for col_idx, (x1, x2) in enumerate(cols):
            grid_cells.append(GridCell(
                col_idx=col_idx,
                row_idx=row_idx,
                x1=int(x1), y1=int(y1),
                x2=int(x2), y2=int(y2)
            ))
    
    # Debug: sauvegarder grille détectée
    if debug_output_dir:
        debug_grid = img.copy()
        for cell in grid_cells:
            cv2.rectangle(debug_grid, (cell.x1, cell.y1), (cell.x2, cell.y2), (0, 255, 0), 1)
        debug_path = Path(debug_output_dir) / "grid_detected.png"
        cv2.imwrite(str(debug_path), cv2.cvtColor(debug_grid, cv2.COLOR_RGB2BGR))
    
    return TableGrid(rows=rows, cols=cols, cells=grid_cells)


# ============================================================================
# OCR CELLULE
# ============================================================================

def extract_cell_content(img: np.ndarray, cell: GridCell, 
                         debug_output_dir: Optional[str] = None) -> CellContent:
    """
    Extrait contenu d'une cellule avec OCR.
    
    Prétraitement:
    1. Recadrage avec marge
    2. Upscale si petit
    3. Débruitage
    4. Binarisation adaptative
    5. Deskew si nécessaire
    """
    margin = 5
    x1 = max(0, cell.x1 + margin)
    y1 = max(0, cell.y1 + margin)
    x2 = min(img.shape[1], cell.x2 - margin)
    y2 = min(img.shape[0], cell.y2 - margin)
    
    if x2 <= x1 or y2 <= y1:
        return CellContent(text="", confidence=0.0, needs_review=True, 
                          review_reason="Cellule trop petite")
    
    cell_img = img[y1:y2, x1:x2].copy()
    cell_h, cell_w = cell_img.shape[:2]
    
    # Upscale si petit
    if cell_w < 150:
        scale_factor = max(2, int(150 / cell_w))
        cell_img = cv2.resize(cell_img, None, fx=scale_factor, fy=scale_factor, 
                             interpolation=cv2.INTER_CUBIC)
    
    # Niveaux de gris
    gray = cv2.cvtColor(cell_img, cv2.COLOR_RGB2GRAY)
    
    # Débruitage
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # Binarisation adaptative
    binary = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=11, C=2
    )
    
    # Deskew si angle significant
    try:
        coords = np.column_stack(np.where(binary > 0))
        angle = cv2.minAreaRect(coords)[2]
        if abs(angle) > 0.3:
            h, w = binary.shape
            center = (w // 2, h // 2)
            rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
            binary = cv2.warpAffine(binary, rot_mat, (w, h),
                                   borderMode=cv2.BORDER_REPLICATE)
    except:
        pass
    
    # OCR Tesseract
    try:
        data = pytesseract.image_to_data(
            binary,
            output_type=pytesseract.Output.DICT,
            lang='fra',
            config='--psm 6'
        )
    except Exception as e:
        return CellContent(text="", confidence=0.0, needs_review=True,
                          review_reason=f"OCR failed: {str(e)[:50]}")
    
    # Extraire texte et confiance
    words = [data['text'][i].strip() for i in range(len(data['text']))
             if data['text'][i].strip() and int(data['conf'][i]) > 0]
    confidences = [int(data['conf'][i]) for i in range(len(data['text']))
                  if data['text'][i].strip() and int(data['conf'][i]) > 0]
    
    if not words:
        return CellContent(text="", confidence=0.0)
    
    # Moyenne confiance
    avg_confidence = np.mean(confidences) if confidences else 0.0
    
    # Joindre texte
    text = ' '.join(words)
    
    # Nettoyer
    text = clean_ocr_text(text)
    
    # Flags
    needs_review = avg_confidence < 70 or contains_suspicious_sequences(text)
    reason = ""
    if avg_confidence < 70:
        reason += f"Confiance basse ({avg_confidence:.1f}%) "
    if contains_suspicious_sequences(text):
        reason += "Séquences suspectes détectées"
    
    return CellContent(
        text=text,
        confidence=avg_confidence,
        needs_review=needs_review,
        review_reason=reason.strip()
    )


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
    
    # Unifier espaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def contains_suspicious_sequences(text: str) -> bool:
    """Détecte séquences suspectes."""
    if not text:
        return False
    
    # Séquences sans voyelle > 4 caractères
    vowels = set('aeiouyàâäéèêëïîôöœuù')
    words = text.split()
    
    for word in words:
        word_clean = ''.join(c.lower() for c in word if c.isalpha())
        if len(word_clean) > 4:
            if not any(c in word_clean for c in vowels):
                return True
    
    # Symboles parasites
    if any(c in text for c in '|\\~`'):
        count = sum(1 for c in text if c in '|\\~`')
        if count > 2:
            return True
    
    return False


# ============================================================================
# DÉTECTION EN-TÊTES
# ============================================================================

HEADER_ALIASES = [
    "spécification",
    "specification",
    "caractéristiques techniques minimales",
    "caractéristiques minimales",
    "caract techniques",
    "caractéristiques"
]


def detect_specification_column(img: np.ndarray, grid: TableGrid, 
                               page_num: int) -> Optional[int]:
    """
    Détecte l'index de colonne "Spécification" via OCR d'en-tête.
    Retourne None si aucun en-tête trouvé.
    """
    if not grid.cells:
        return None
    
    # Première ligne (en-tête)
    header_cells = [c for c in grid.cells if c.row_idx == 0]
    
    if not header_cells:
        return None
    
    # OCR de chaque cellule d'en-tête
    for cell in sorted(header_cells, key=lambda c: c.col_idx):
        content = extract_cell_content(img, cell)
        header_text = content.text.lower()
        
        # Matcher contre aliases
        for alias in HEADER_ALIASES:
            if alias in header_text or header_text in alias:
                return cell.col_idx
    
    return None


# ============================================================================
# PIPELINE EXTRACTION
# ============================================================================

def extract_specifications_from_pdf(pdf_path: str, 
                                   debug_dir: Optional[str] = None) -> Dict:
    """Pipeline complet d'extraction."""
    
    debug_dir = Path(debug_dir) if debug_dir else None
    if debug_dir:
        debug_dir.mkdir(parents=True, exist_ok=True)
    
    doc = fitz.open(pdf_path)
    n_pages = doc.page_count
    doc.close()
    
    print(f"\n{'='*70}")
    print(f"EXTRACTION SPÉCIFICATIONS - GRILLE BASÉE")
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
    inherited_from_page = None
    
    for page_num in range(n_pages):
        print(f"Page {page_num + 1}...", end=" ", flush=True)
        
        try:
            # Rendre image
            img = render_page_to_image(pdf_path, page_num, dpi=300)
            
            # Détecter grille
            grid = detect_table_grid(img, debug_output_dir=str(debug_dir) if debug_dir else None)
            
            if not grid:
                print("X Grille non détectée")
                continue
            
            n_cols = len(grid.cols)
            
            # Déterminer colonne "Spécification"
            spec_col_idx = detect_specification_column(img, grid, page_num)
            
            if spec_col_idx is not None:
                # En-tête trouvé
                inherited_col_idx = spec_col_idx
                inherited_from_page = page_num + 1
                header_detected = "Spécification"
                print(f"OK Colonne {spec_col_idx + 1}/3 (en-tête détecté)")
            else:
                # Pas d'en-tête, tenter héritage
                if inherited_col_idx is not None:
                    spec_col_idx = inherited_col_idx
                    header_detected = f"hérité de la page {inherited_from_page}"
                    print(f"OK Colonne {spec_col_idx + 1}/3 ({header_detected})")
                else:
                    print("X Colonne non détectée et pas d'héritage")
                    continue
            
            # Extraire contenu de la colonne
            spec_cells = [c for c in grid.cells if c.col_idx == spec_col_idx]
            designation_cells = [c for c in grid.cells if c.col_idx == 0]
            
            entries = []
            for spec_cell in sorted(spec_cells, key=lambda c: c.row_idx):
                if spec_cell.row_idx == 0:  # Skip en-tête
                    continue
                
                # Trouver designation sur la même ligne
                matching_desg = [c for c in designation_cells if c.row_idx == spec_cell.row_idx]
                
                desg_content = extract_cell_content(img, matching_desg[0]) if matching_desg else None
                spec_content = extract_cell_content(img, spec_cell)
                
                if spec_content.text.strip():  # Ne garder que si contenu
                    entries.append({
                        "designation": desg_content.text if desg_content else "",
                        "valeur": spec_content.text,
                        "confiance_ocr": round(spec_content.confidence, 1),
                        "a_verifier": spec_content.needs_review,
                        "raison_verification": spec_content.review_reason
                    })
            
            if entries:
                results["pages"].append({
                    "page": page_num + 1,
                    "entete_detecte": header_detected,
                    "entries": entries
                })
        
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
    results = extract_specifications_from_pdf(
        pdf_path,
        debug_dir="data/output/debug/grid_based"
    )
    
    # Sauvegarde
    output_path = Path("data/output/specifications_source_of_truth.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*70}")
    print(f"RESULTATS")
    print(f"{'='*70}\n")
    
    total_pages = len(results['pages'])
    total_entries = sum(len(p['entries']) for p in results['pages'])
    total_flagged = sum(sum(1 for e in p['entries'] if e['a_verifier']) 
                       for p in results['pages'])
    
    print(f"OK Pages traitées: {total_pages}")
    print(f"OK Entrées extraites: {total_entries}")
    print(f"WARNING Entrées à vérifier: {total_flagged}")
    print(f"OK Sortie: {output_path}\n")
    
    print("Aperçu:")
    for page_info in results['pages'][:2]:
        print(f"\nPage {page_info['page']} ({len(page_info['entries'])} entrées)")
        for i, entry in enumerate(page_info['entries'][:3], 1):
            flag = " [A VERIFIER]" if entry['a_verifier'] else ""
            print(f"  {i}. {entry['designation'][:30]:30s} | {entry['valeur'][:40]}{flag}")
