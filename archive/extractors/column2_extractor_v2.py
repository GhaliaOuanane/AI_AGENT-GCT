"""
Extraction de la 2e colonne - Version 2 (CORRIGÉE)

Processus:
1. Identifier pages cibles (avec en-têtes valides)
2. Valider que l'en-tête correspond Modèle 1 ou 2
3. Mapper colonne 2 basée sur en-tête
4. Extraire TOUT le contenu (pas de filtrage strict)
"""

import fitz
import cv2
import pytesseract
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np
import re
from page_selector import select_target_pages
from pdf_reader import open_pdf


# ============================================================================
# DÉTECTION D'EN-TÊTES (Modèle 1 ou 2)
# ============================================================================

MODEL_1_KEYWORDS = {
    'col1': ['désignation', 'designation'],
    'col2': ['spécification', 'specification'],
    'col3': ['proposition']
}

MODEL_2_KEYWORDS = {
    'col1': ['composants', 'composant', 'offre'],
    'col2': ['caractéristiques', 'caracteristiques', 'technique', 'minimales', 'minimum'],
    'col3': ['proposition']
}


def normalize_header_text(text: str) -> str:
    """Normalise le texte pour comparaison."""
    text = text.lower().strip()
    text = text.replace('é', 'e')
    text = text.replace('è', 'e')
    text = text.replace('ê', 'e')
    text = text.replace('ç', 'c')
    text = text.replace('à', 'a')
    return text


def detect_header_model(header_texts: List[str]) -> Optional[Tuple[str, Dict]]:
    """
    Détecte si l'en-tête correspond à Modèle 1 ou 2.
    
    Returns:
        ('model1' ou 'model2', {'col1_idx': 0, 'col2_idx': 1, 'col3_idx': 2})
        ou None si pas de match
    """
    if len(header_texts) < 3:
        return None
    
    # Normaliser les 3 en-têtes
    norm_headers = [normalize_header_text(h) for h in header_texts[:3]]
    
    # Vérifier Modèle 1
    model1_match = True
    col_mapping_m1 = {'col1': 0, 'col2': 1, 'col3': 2}
    
    for col, keywords in MODEL_1_KEYWORDS.items():
        col_idx = col_mapping_m1[col]
        if not any(kw in norm_headers[col_idx] for kw in keywords):
            model1_match = False
            break
    
    if model1_match:
        return ('model1', col_mapping_m1)
    
    # Vérifier Modèle 2
    model2_match = True
    col_mapping_m2 = {'col1': 0, 'col2': 1, 'col3': 2}
    
    for col, keywords in MODEL_2_KEYWORDS.items():
        col_idx = col_mapping_m2[col]
        if not any(kw in norm_headers[col_idx] for kw in keywords):
            model2_match = False
            break
    
    if model2_match:
        return ('model2', col_mapping_m2)
    
    return None


# ============================================================================
# EXTRACTION D'OCR AVEC VALIDATION
# ============================================================================

def render_page(pdf_path, page_num, dpi=300):
    """Rendu haute résolution d'une page PDF."""
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


def extract_ocr_words_with_coords(img_gray) -> List[Dict]:
    """
    Récupère les mots OCR avec coordonnées X/Y.
    Retourne liste de {'text', 'x', 'y', 'width', 'height', 'x_end', 'y_end', 'conf'}
    """
    data = pytesseract.image_to_data(img_gray, output_type=pytesseract.Output.DICT, lang='fra')
    
    words = []
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        if not text or len(text) < 1:
            continue
        
        word = {
            'text': text,
            'x': int(data['left'][i]),
            'y': int(data['top'][i]),
            'width': int(data['width'][i]),
            'height': int(data['height'][i]),
            'x_end': int(data['left'][i]) + int(data['width'][i]),
            'y_end': int(data['top'][i]) + int(data['height'][i]),
            'conf': int(data['conf'][i])
        }
        words.append(word)
    
    return words


def extract_header_line(img_gray, row_height_threshold=80) -> Tuple[List[str], List[Tuple[int, int, int, int]]]:
    """
    Extrait les 3 en-têtes de la première ligne du tableau.
    Retourne: (liste de 3 textes d'en-tête, liste de bounding boxes)
    """
    words = extract_ocr_words_with_coords(img_gray)
    
    if not words:
        return [], []
    
    # Prendre les mots dans les ~80 premiers pixels (hauteur en-tête)
    header_words = [w for w in words if w['y'] < row_height_threshold]
    
    if not header_words:
        return [], []
    
    # Trier par X pour avoir ordre gauche → droite
    header_words = sorted(header_words, key=lambda w: w['x'])
    
    # Diviser en 3 groupes (colonnes) par tiers de la largeur
    img_width = img_gray.shape[1]
    third_width = img_width / 3
    
    col1_words = [w for w in header_words if w['x'] < third_width]
    col2_words = [w for w in header_words if third_width <= w['x'] < 2 * third_width]
    col3_words = [w for w in header_words if w['x'] >= 2 * third_width]
    
    headers = []
    header_boxes = []
    
    for col_words in [col1_words, col2_words, col3_words]:
        if col_words:
            text = ' '.join([w['text'] for w in col_words])
            x_min = min(w['x'] for w in col_words)
            y_min = min(w['y'] for w in col_words)
            x_max = max(w['x_end'] for w in col_words)
            y_max = max(w['y_end'] for w in col_words)
            headers.append(text)
            header_boxes.append((x_min, y_min, x_max, y_max))
        else:
            headers.append("")
            header_boxes.append((0, 0, 0, 0))
    
    return headers, header_boxes


def group_words_by_row(words: List[Dict], row_height_threshold=30, skip_first_rows=1) -> List[List[Dict]]:
    """
    Groupe les mots par ligne (Y similaire).
    skip_first_rows: nombre de lignes à ignorer (en-têtes)
    """
    if not words:
        return []
    
    # Trier par Y
    sorted_words = sorted(words, key=lambda w: w['y'])
    
    # Passer les premières lignes (en-têtes)
    rows_to_skip = skip_first_rows * row_height_threshold * 1.5  # Approximation
    filtered_words = [w for w in sorted_words if w['y'] > rows_to_skip]
    
    if not filtered_words:
        return []
    
    rows = []
    current_row = [filtered_words[0]]
    
    for word in filtered_words[1:]:
        if abs(word['y'] - current_row[0]['y']) <= row_height_threshold:
            current_row.append(word)
        else:
            rows.append(current_row)
            current_row = [word]
    
    rows.append(current_row)
    return rows


def extract_column_from_header_box(
    words: List[Dict],
    header_box: Tuple[int, int, int, int],
    skip_header_y: float
) -> List[str]:
    """
    Extrait le contenu d'une colonne basée sur la position de l'en-tête.
    
    header_box: (x_min, y_min, x_max, y_max) de l'en-tête
    skip_header_y: Position Y à partir de laquelle les données commencent
    """
    x_min, _, x_max, _ = header_box
    col_center_x = (x_min + x_max) / 2
    col_width = x_max - x_min
    
    # Prendre les mots dont X est proche du centre de la colonne (±30% de largeur)
    col_tolerance = col_width * 0.4
    col_words = [
        w for w in words
        if abs(w['x'] + w['width']/2 - col_center_x) <= col_tolerance
        and w['y'] > skip_header_y
    ]
    
    if not col_words:
        return []
    
    # Grouper par ligne
    col_words = sorted(col_words, key=lambda w: w['y'])
    rows = []
    current_row = [col_words[0]]
    row_height_threshold = 30
    
    for word in col_words[1:]:
        if abs(word['y'] - current_row[0]['y']) <= row_height_threshold:
            current_row.append(word)
        else:
            rows.append(current_row)
            current_row = [word]
    
    rows.append(current_row)
    
    # Joindre mots de chaque ligne
    result = []
    for row in rows:
        row_sorted = sorted(row, key=lambda w: w['x'])
        row_text = ' '.join([w['text'] for w in row_sorted])
        if row_text.strip():
            result.append(row_text)
    
    return result


# ============================================================================
# EXTRACTION PRINCIPALE (À PARTIR DES PAGES CIBLES)
# ============================================================================

def extract_column2_from_target_pages(pdf_path: str) -> List[Dict]:
    """
    Extrait la colonne 2 UNIQUEMENT à partir des pages cibles.
    
    Processus:
    1. Identifier pages cibles (via page_selector)
    2. Valider en-tête (Modèle 1 ou 2)
    3. Extraire colonne 2 basée sur en-tête
    
    Returns:
        [
            {
                'page': num_page,
                'header_model': 'model1' ou 'model2',
                'header_text': '... / ... / ...',
                'column2_data': [textes extraits]
            }
        ]
    """
    # Étape 1: Identifier pages cibles
    reader = open_pdf(pdf_path)
    target_pages = select_target_pages(
        reader=reader,
        pdf_path=pdf_path,
        use_ocr=True
    )
    
    results = []
    
    # Étape 2: Pour chaque page cible
    for target_page in target_pages:
        page_num = reader.pages.index(target_page)
        
        try:
            # Rendu haute résolution
            img_rgb = render_page(pdf_path, page_num, dpi=300)
            img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        except Exception as e:
            print(f"[ERROR] Page {page_num}: Render failed - {e}")
            continue
        
        # Extraire en-têtes
        header_texts, header_boxes = extract_header_line(img_gray)
        
        if len(header_texts) < 3:
            print(f"[WARN] Page {page_num}: Could not extract 3 headers")
            continue
        
        # Valider modèle
        model_info = detect_header_model(header_texts)
        
        if not model_info:
            print(f"[WARN] Page {page_num}: Headers don't match Model 1 or 2")
            continue
        
        model_name, col_mapping = model_info
        col2_idx = col_mapping['col2']  # Index de colonne 2
        col2_header_box = header_boxes[col2_idx]
        
        # Extraire tous les mots de la page
        all_words = extract_ocr_words_with_coords(img_gray)
        
        if not all_words:
            print(f"[WARN] Page {page_num}: No OCR words detected")
            continue
        
        # Déterminer Y après les en-têtes
        header_y_max = max(box[3] for box in header_boxes if box != (0, 0, 0, 0))
        skip_y = header_y_max + 10
        
        # Extraire colonne 2
        col2_data = extract_column_from_header_box(all_words, col2_header_box, skip_y)
        
        # Résultat
        header_full = ' / '.join(header_texts)
        
        results.append({
            'page': page_num + 1,
            'header_model': model_name,
            'header_text': header_full,
            'column2_data': col2_data
        })
        
        print(f"[OK] Page {page_num + 1}: {len(col2_data)} lignes extraites (Model: {model_name})")
    
    return results


def export_to_json(results: List[Dict], output_path: str):
    """Exporte les résultats en JSON."""
    import json
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import json
    
    # Test
    pdf_path = "data/input/BRAIN INFORMATIQUE_16052025101905.PDF"
    
    print("Extraction de la colonne 2 (à partir des pages cibles)")
    print("=" * 70)
    
    results = extract_column2_from_target_pages(pdf_path)
    
    # Sauvegarder
    export_to_json(results, "data/output/column2_corrected.json")
    
    print("\n" + "=" * 70)
    print(f"[OK] {len(results)} pages traitées")
    print(f"Résultats: data/output/column2_corrected.json")
    
    # Aperçu
    if results:
        print("\nAperçu première page:")
        item = results[0]
        print(f"  Page: {item['page']}")
        print(f"  Modèle: {item['header_model']}")
        print(f"  En-tête: {item['header_text'][:80]}...")
        print(f"  Données (col 2): {len(item['column2_data'])} lignes")
        for i, line in enumerate(item['column2_data'][:5], 1):
            print(f"    {i}. {line[:60]}...")
