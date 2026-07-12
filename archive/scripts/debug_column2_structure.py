"""
Debug: Analyser la structure des colonnes dans pages_cibles.pdf
Pour comprendre comment les colonnes sont réellement disposées
"""

import fitz
import cv2
import pytesseract
from pathlib import Path
import numpy as np
from collections import defaultdict

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def ocr_page_debug(pdf_path, page_num, dpi=400):
    """OCR avec debug info."""
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
    elif pix.n == 1:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    
    img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
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
        
        if text and len(text) > 0 and conf > 40:
            words.append({
                'text': text,
                'x': int(data['left'][i]),
                'y': int(data['top'][i]),
                'width': int(data['width'][i]),
                'height': int(data['height'][i]),
                'conf': conf
            })
    
    return words


def analyze_structure(words):
    """Analyser la structure des colonnes."""
    if not words:
        print("  ❌ Aucun mot détecté")
        return
    
    print(f"  Total mots: {len(words)}")
    
    # Statistiques X
    x_coords = [w['x'] for w in words]
    print(f"  X min: {min(x_coords)}, max: {max(x_coords)}")
    print(f"  X range: {max(x_coords) - min(x_coords)}")
    
    # Grouper par Y (lignes)
    y_lines = defaultdict(list)
    for w in words:
        y_key = round(w['y'] / 25) * 25  # Grouper par 25px
        y_lines[y_key].append(w)
    
    print(f"  Lignes détectées: {len(y_lines)}")
    
    # Afficher les X positions pour chaque ligne (top 3)
    for i, (y_key, line_words) in enumerate(sorted(y_lines.items())[:3]):
        x_positions = sorted([w['x'] for w in line_words])
        print(f"    Ligne {i+1} (Y~{y_key}): {len(line_words)} mots, X positions: {x_positions}")
        print(f"      Texte: {' '.join([w['text'] for w in sorted(line_words, key=lambda w: w['x'])])}")


# Main
pdf_path = "data/output/pages_cibles.pdf"
doc = fitz.open(pdf_path)

print(f"\n{'='*70}")
print(f"DEBUG: STRUCTURE COLONNES - pages_cibles.pdf")
print(f"{'='*70}\n")

for page_num in range(min(doc.page_count, 3)):  # Analyser les 3 premières pages
    print(f"Page {page_num + 1}:")
    words = ocr_page_debug(pdf_path, page_num, dpi=400)
    analyze_structure(words)
    print()

doc.close()
