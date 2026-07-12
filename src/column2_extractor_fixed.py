"""
Extraction de la 2e colonne - Version CORRIGÉE

✅ À PARTIR DES PAGES CIBLES
✅ VALIDE LES EN-TÊTES (Modèle 1 ou 2)
✅ EXTRAIT TOUT LE CONTENU
"""

import fitz
import cv2
import pytesseract
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np
import re


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


def normalize_text(text: str) -> str:
    """Normalise pour comparaison (minuscules, sans accents)."""
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


def detect_header_model(header_texts: List[str]) -> Optional[Tuple[str, int]]:
    """
    Détecte si l'en-tête correspond à Modèle 1 ou 2.
    
    Returns:
        ('model1' ou 'model2', col2_index)
        ou None si pas de match
    """
    if len(header_texts) < 3:
        return None
    
    # Prendre les 3 premiers (colonnes principales)
    headers = header_texts[:3]
    norm_headers = [normalize_text(h) for h in headers]
    
    # Vérifier MODÈLE 1: Désignation / Spécification / Proposition
    model1_checks = [
        any(kw in norm_headers[0] for kw in MODEL_1_KEYWORDS['col1']),
        any(kw in norm_headers[1] for kw in MODEL_1_KEYWORDS['col2']),
        any(kw in norm_headers[2] for kw in MODEL_1_KEYWORDS['col3'])
    ]
    
    if all(model1_checks):
        return ('model1', 1)  # Colonne 2 est à l'index 1
    
    # Vérifier MODÈLE 2: Composants / Caractéristiques / Proposition
    model2_checks = [
        any(kw in norm_headers[0] for kw in MODEL_2_KEYWORDS['col1']),
        any(kw in norm_headers[1] for kw in MODEL_2_KEYWORDS['col2']),
        any(kw in norm_headers[2] for kw in MODEL_2_KEYWORDS['col3'])
    ]
    
    if all(model2_checks):
        return ('model2', 1)  # Colonne 2 est à l'index 1
    
    return None


# ============================================================================
# EXTRACTION OCR
# ============================================================================

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
    """OCR + extraction coordonnées."""
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
        if not text or len(text) < 1:
            continue
        
        word = {
            'text': text,
            'x': int(data['left'][i]),
            'y': int(data['top'][i]),
            'width': int(data['width'][i]),
            'height': int(data['height'][i]),
            'conf': int(data['conf'][i])
        }
        words.append(word)
    
    return words


def extract_header_line(words: List[Dict], threshold_y=100) -> Optional[Tuple[List[str], List[Tuple]]]:
    """
    Extrait les 3 en-têtes de la première ligne.
    
    Returns:
        (liste de 3 textes, liste de 3 bounding boxes)
    """
    if not words:
        return None
    
    # Prendre les mots dans les premiers pixels (en-têtes)
    header_words = [w for w in words if w['y'] < threshold_y]
    
    if len(header_words) < 5:  # Au minimum quelques mots
        return None
    
    # Diviser en 3 colonnes par tiers
    img_width = max(w['x'] + w['width'] for w in words)
    third = img_width / 3
    
    # Mots de chaque colonne
    col1_w = [w for w in header_words if w['x'] < third]
    col2_w = [w for w in header_words if third <= w['x'] < 2*third]
    col3_w = [w for w in header_words if w['x'] >= 2*third]
    
    headers = []
    boxes = []
    
    for col_words in [col1_w, col2_w, col3_w]:
        if col_words:
            text = ' '.join([w['text'] for w in col_words])
            x1 = min(w['x'] for w in col_words)
            y1 = min(w['y'] for w in col_words)
            x2 = max(w['x'] + w['width'] for w in col_words)
            y2 = max(w['y'] + w['height'] for w in col_words)
            headers.append(text)
            boxes.append((x1, y1, x2, y2))
        else:
            headers.append("")
            boxes.append((0, 0, 0, 0))
    
    return (headers, boxes)


def extract_column_by_position(
    words: List[Dict],
    col_x_min: int,
    col_x_max: int,
    skip_y: float
) -> List[str]:
    """
    Extrait tout le contenu d'une colonne.
    
    Parameters:
        words: liste des mots OCR
        col_x_min, col_x_max: position X de la colonne
        skip_y: Y à partir de laquelle commencer
    """
    col_center = (col_x_min + col_x_max) / 2
    col_width = col_x_max - col_x_min
    tolerance = col_width * 0.5  # ±50% pour robustesse
    
    # Mots dans cette colonne et après en-têtes
    col_words = [
        w for w in words
        if abs(w['x'] + w['width']/2 - col_center) <= tolerance
        and w['y'] >= skip_y
    ]
    
    if not col_words:
        return []
    
    # Grouper par ligne (Y)
    col_words = sorted(col_words, key=lambda w: w['y'])
    
    rows = []
    row_threshold = 35
    current_row = [col_words[0]]
    
    for word in col_words[1:]:
        if abs(word['y'] - current_row[0]['y']) <= row_threshold:
            current_row.append(word)
        else:
            rows.append(current_row)
            current_row = [word]
    
    if current_row:
        rows.append(current_row)
    
    # Joindre mots de chaque ligne
    result = []
    for row in rows:
        row_sorted = sorted(row, key=lambda w: w['x'])
        line_text = ' '.join([w['text'] for w in row_sorted])
        if line_text.strip():
            result.append(line_text)
    
    return result


def is_table_page_by_text(raw_text: str) -> bool:
    """
    Vérifie rapidement si une page contient un tableau.
    (utilise texte brut du PDF)
    """
    norm = normalize_text(raw_text)
    
    # Mots-clés qui indiquent un tableau
    table_keywords = [
        'designation', 'specification', 'proposition',
        'composants', 'caracteristiques', 'technique',
        'modele', 'lot', 'quantite'
    ]
    
    return any(kw in norm for kw in table_keywords)


# ============================================================================
# EXTRACTION PRINCIPALE
# ============================================================================

def extract_column2_from_tables(pdf_path: str) -> List[Dict]:
    """
    ✅ Extrait colonne 2 à partir des PAGES AVEC TABLEAUX VALIDES.
    
    Processus:
    1. Identifier pages avec en-têtes valides (Modèle 1 ou 2)
    2. Extraire en-têtes
    3. Mapper et extraire colonne 2
    4. Retourner TOUT le contenu
    """
    doc = fitz.open(pdf_path)
    results = []
    pages_with_tables_detected = 0
    pages_with_valid_headers = 0
    
    print(f"\n[INFO] Traitement: {Path(pdf_path).name}")
    print(f"[INFO] Total pages: {doc.page_count}")
    print("=" * 70)
    
    for page_num in range(doc.page_count):
        try:
            # Étape 1: Essayer directement OCR (PDF peut être image/scanné)
            # Pas de pré-filtrage textuel, on teste chaque page
            
            # Étape 2: Rendu HD + OCR
            img_rgb = render_page_hd(pdf_path, page_num, dpi=300)
            img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
            
            words = ocr_page(img_gray)
            
            if not words:
                continue
            
            pages_with_tables_detected += 1
            
            # Étape 3: Extraire et valider en-têtes
            header_info = extract_header_line(words, threshold_y=120)
            
            if not header_info:
                continue
            
            headers, boxes = header_info
            
            # Valider que c'est Modèle 1 ou 2
            model_match = detect_header_model(headers)
            
            if not model_match:
                # En-têtes ne correspondent à aucun modèle
                print(f"[SKIP] Page {page_num + 1}: En-têtes trouvés mais invalides")
                print(f"       '{headers[0]}' / '{headers[1]}' / '{headers[2]}'")
                continue
            
            pages_with_valid_headers += 1
            
            model_name, col2_idx = model_match
            col2_box = boxes[col2_idx]
            
            # Étape 4: Déterminer Y après en-têtes
            header_y_max = max(b[3] for b in boxes if b != (0, 0, 0, 0))
            skip_y = header_y_max + 15
            
            # Étape 5: Extraire colonne 2 COMPLÈTEMENT
            col2_content = extract_column_by_position(
                words,
                col2_box[0],
                col2_box[2],
                skip_y
            )
            
            if not col2_content:
                print(f"[SKIP] Page {page_num + 1}: Pas de contenu en colonne 2")
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
                'column2': col2_content
            }
            
            results.append(result_item)
            
            print(f"[OK] Page {page_num + 1}: {len(col2_content)} lignes (Model: {model_name})")
            
        except Exception as e:
            print(f"[ERROR] Page {page_num + 1}: {e}")
            continue
    
    doc.close()
    
    print(f"\n[DEBUG] Pages avec potentiel tableau: {pages_with_tables_detected}")
    print(f"[DEBUG] Pages avec en-têtes détectés: {pages_with_valid_headers}")
    print(f"[DEBUG] Pages avec extraction réussie: {len(results)}")
    
    return results


# ============================================================================
# EXPORT
# ============================================================================

def save_results_json(results: List[Dict], output_path: str):
    """Sauvegarde en JSON."""
    import json
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Résultats sauvegardés: {output_path}")


def print_summary(results: List[Dict]):
    """Affiche un résumé."""
    print("\n" + "=" * 70)
    print("RÉSUMÉ DE L'EXTRACTION")
    print("=" * 70)
    
    if not results:
        print("Aucune page avec tableau valide trouvée.")
        return
    
    print(f"\nTotal pages traitées: {len(results)}")
    
    total_lines = sum(len(r['column2']) for r in results)
    print(f"Total lignes extraites: {total_lines}")
    print(f"Moyenne par page: {total_lines / len(results):.1f}")
    
    model_counts = {}
    for r in results:
        model = r['model']
        model_counts[model] = model_counts.get(model, 0) + 1
    
    print(f"\nParDistribution des modèles:")
    for model, count in model_counts.items():
        print(f"  {model}: {count} page(s)")
    
    print("\n" + "=" * 70)
    print("Aperçu (3 premières pages):")
    print("=" * 70)
    
    for item in results[:3]:
        print(f"\nPage {item['page']} ({item['model']})")
        print(f"  En-têtes: {item['headers']['col1']} | {item['headers']['col2']} | {item['headers']['col3']}")
        print(f"  Colonne 2 ({len(item['column2'])} lignes):")
        for i, line in enumerate(item['column2'][:7], 1):
            display = line[:70] + "..." if len(line) > 70 else line
            print(f"    {i}. {display}")
        if len(item['column2']) > 7:
            print(f"    ... et {len(item['column2']) - 7} autres")


if __name__ == "__main__":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    # Test
    pdf_path = "data/input/BRAIN INFORMATIQUE_16052025101905.PDF"
    output_json = "data/output/column2_extraction.json"
    
    # Exécuter
    results = extract_column2_from_tables(pdf_path)
    
    # Sauvegarder
    if results:
        save_results_json(results, output_json)
        print_summary(results)
    else:
        print("\n[WARN] Aucun résultat à sauvegarder")
