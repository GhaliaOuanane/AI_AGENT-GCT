"""
✅ EXTRACTION COLONNE 2 - VERSION FINALE CORRIGÉE

Fixes appliquées:
1. En-têtes peuvent être dispersés verticalement (tolérance 80px)
2. Extraction OCR sur TOUTES les pages (PDF scanné)
3. Valide en-tête (Modèle 1 ou 2) PUIS extrait colonne 2
4. Extrait TOUT le contenu (pas de filtrage strict)
"""

import fitz
import cv2
import pytesseract
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np
import json


def normalize_text(text: str) -> str:
    """Normalise pour comparaison."""
    text = text.lower().strip()
    replacements = {
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'à': 'a', 'â': 'a', 'ä': 'a',
        'ù': 'u', 'û': 'u', 'ü': 'u',
        'ô': 'o', 'ö': 'o',
        'ç': 'c', 'î': 'i', 'ï': 'i'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


# Mots-clés pour les modèles
MODEL_1 = {
    'col1': ['designat'],  # "désignation"
    'col2': ['specificat'],  # "spécification"
    'col3': ['proposition']
}

MODEL_2 = {
    'col1': ['composant', 'offre'],
    'col2': ['caracteristic', 'technique', 'minimal'],
    'col3': ['proposition']
}


def detect_model(headers: List[str]) -> Optional[Tuple[str, int]]:
    """
    Détecte Modèle 1 ou 2 basé sur 3 en-têtes.
    Returns: ('model1'/'model2', col2_index) ou None
    """
    if len(headers) < 3:
        return None
    
    norm = [normalize_text(h) for h in headers[:3]]
    
    # Vérifier Modèle 1
    m1_ok = all(
        any(kw in norm[i] for kw in MODEL_1['col' + str(i+1)])
        for i in range(3)
    )
    if m1_ok:
        return ('MODEL_1', 1)
    
    # Vérifier Modèle 2
    m2_ok = all(
        any(kw in norm[i] for kw in MODEL_2['col' + str(i+1)])
        for i in range(3)
    )
    if m2_ok:
        return ('MODEL_2', 1)
    
    return None


def render_page_hd(pdf_path, page_num, dpi=300):
    """Rendu haute résolution."""
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
    
    doc.close()
    return img


def ocr_page(img_gray) -> List[Dict]:
    """OCR."""
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
        if text and len(text) > 0:
            words.append({
                'text': text,
                'x': int(data['left'][i]),
                'y': int(data['top'][i]),
                'width': int(data['width'][i]),
                'height': int(data['height'][i]),
                'conf': int(data['conf'][i])
            })
    
    return words


def extract_headers_and_boxes(words: List[Dict], header_y_threshold=350) -> Optional[Tuple[List[str], List[Tuple]]]:
    """
    ✅ CORRIGÉ: En-têtes peuvent être dispersés (Y ±80px).
    
    Regroupe mots proches en Y pour former les 3 en-têtes colonne.
    """
    if not words:
        return None
    
    # Prendre les mots dans la zone des en-têtes (premiers ~350px)
    header_words = [w for w in words if w['y'] < header_y_threshold]
    
    if len(header_words) < 5:
        return None
    
    # Diviser en 3 colonnes par position X
    img_width = max(w['x'] + w['width'] for w in words)
    third = img_width / 3
    
    col1_words = [w for w in header_words if w['x'] < third]
    col2_words = [w for w in header_words if third <= w['x'] < 2*third]
    col3_words = [w for w in header_words if w['x'] >= 2*third]
    
    headers = []
    boxes = []
    
    for col_words in [col1_words, col2_words, col3_words]:
        if col_words:
            # Joindre les mots de la colonne
            text = ' '.join([w['text'] for w in col_words])
            x1 = min(w['x'] for w in col_words)
            y1 = min(w['y'] for w in col_words)
            x2 = max(w['x'] + w['width'] for w in col_words)
            y2 = max(w['y'] + w['height'] for w in col_words)
            
            headers.append(text)
            boxes.append((x1, y1, x2, y2))
        else:
            headers.append("")
            boxes.append(None)
    
    return (headers, boxes)


def extract_column_content(
    words: List[Dict],
    col_box: Tuple,
    start_y: float
) -> List[str]:
    """
    Extrait TOUT le contenu d'une colonne.
    """
    if not col_box:
        return []
    
    x1, _, x2, _ = col_box
    col_center = (x1 + x2) / 2
    col_width = x2 - x1
    tolerance = col_width * 0.6
    
    # Mots dans cette colonne, après en-têtes
    col_words = [
        w for w in words
        if abs(w['x'] + w['width']/2 - col_center) <= tolerance
        and w['y'] >= start_y
    ]
    
    if not col_words:
        return []
    
    # Grouper par ligne (Y)
    col_words = sorted(col_words, key=lambda w: w['y'])
    
    rows = []
    row_threshold = 40
    current_row = [col_words[0]]
    
    for word in col_words[1:]:
        if abs(word['y'] - current_row[0]['y']) <= row_threshold:
            current_row.append(word)
        else:
            rows.append(current_row)
            current_row = [word]
    
    if current_row:
        rows.append(current_row)
    
    # Joindre par ligne
    result = []
    for row in rows:
        line = ' '.join([w['text'] for w in sorted(row, key=lambda w: w['x'])])
        if line.strip():
            result.append(line)
    
    return result


def extract_column2_all_pages(pdf_path: str) -> List[Dict]:
    """
    ✅ Extraction finale corrigée:
    - Traite TOUTES les pages
    - Détecte en-têtes (Model 1 ou 2)
    - Extrait colonne 2 complètement
    """
    doc = fitz.open(pdf_path)
    results = []
    
    print(f"\n{'='*70}")
    print(f"EXTRACTION COLONNE 2 - VERSION FINALE")
    print(f"{'='*70}\n")
    print(f"Fichier: {Path(pdf_path).name}")
    print(f"Pages: {doc.page_count}")
    print(f"{'='*70}\n")
    
    for page_num in range(doc.page_count):
        try:
            # Rendu + OCR
            img_rgb = render_page_hd(pdf_path, page_num, dpi=300)
            img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
            
            words = ocr_page(img_gray)
            
            if not words:
                continue
            
            # Extraire en-têtes
            header_info = extract_headers_and_boxes(words, header_y_threshold=350)
            
            if not header_info:
                continue
            
            headers, boxes = header_info
            
            # Valider modèle
            model_match = detect_model(headers)
            
            if not model_match:
                continue
            
            model_name, col2_idx = model_match
            col2_box = boxes[col2_idx]
            
            if not col2_box:
                continue
            
            # Déterminer Y après en-têtes
            header_y_max = max(
                b[3] for b in boxes 
                if b is not None
            )
            start_y = header_y_max + 20
            
            # Extraire colonne 2
            col2_data = extract_column_content(words, col2_box, start_y)
            
            if not col2_data:
                continue
            
            # Résultat
            result_item = {
                'page': page_num + 1,
                'model': model_name,
                'headers': {
                    'col1': headers[0],
                    'col2': headers[1],
                    'col3': headers[2]
                },
                'column2_lines': col2_data
            }
            
            results.append(result_item)
            
            print(f"✓ Page {page_num + 1:2d}: {len(col2_data):3d} lignes ({model_name})")
            
        except Exception as e:
            pass
    
    doc.close()
    return results


if __name__ == "__main__":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    pdf_path = "data/input/BRAIN INFORMATIQUE_16052025101905.PDF"
    output_json = "data/output/column2_extracted.json"
    
    # Exécuter
    results = extract_column2_all_pages(pdf_path)
    
    # Sauvegarder
    if results:
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*70}")
        print(f"✅ Succès: {len(results)} pages traitées")
        print(f"Fichier: {output_json}")
        print(f"{'='*70}\n")
        
        # Aperçu
        if results:
            item = results[0]
            print(f"Aperçu Page {item['page']} ({item['model']}):")
            print(f"  En-têtes: {item['headers']['col1'][:30]}... |")
            print(f"            {item['headers']['col2'][:30]}... |")
            print(f"            {item['headers']['col3'][:30]}...")
            print(f"  Colonne 2 ({len(item['column2_lines'])} lignes):")
            for i, line in enumerate(item['column2_lines'][:5], 1):
                print(f"    {i}. {line[:60]}")
    else:
        print(f"\n[ERROR] Aucun résultat")
