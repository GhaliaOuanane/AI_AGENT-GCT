"""
✅ EXTRACTION COLONNE 2 - SIMPLE ET DIRECT

1. Lire pages_cibles.pdf
2. Pour chaque page: extraire colonne 2 EN ORDRE (haut→bas)
3. Exporter JSON/Excel avec ordre préservé

✅ PAS DE TRI, PAS DE RÉORGANISATION
✅ ORDRE EXACT DU TABLEAU ORIGINAL
"""

import fitz
import cv2
import pytesseract
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np
import json

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


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
    """OCR avec coordonnées."""
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
        if text:
            words.append({
                'text': text,
                'x': int(data['left'][i]),
                'y': int(data['top'][i]),
                'width': int(data['width'][i]),
                'height': int(data['height'][i]),
            })
    
    return words


def extract_column2_order_preserved(words: List[Dict]) -> List[str]:
    """
    Extrait colonne 2 EN PRESERVANT L'ORDRE EXACT (haut→bas).
    
    Stratégie:
    1. Diviser mots en 3 colonnes par position X (tiers)
    2. Prendre colonne du milieu (col 2)
    3. Grouper par ligne Y, SANS RÉORGANISER
    4. Retourner dans l'ordre d'apparition original
    """
    if not words:
        return []
    
    # Diviser en 3 colonnes par X
    img_width = max(w['x'] + w['width'] for w in words)
    third = img_width / 3
    
    col2_words = [w for w in words if third <= w['x'] < 2 * third]
    
    if not col2_words:
        return []
    
    # ✅ IMPORTANT: Trier UNIQUEMENT par Y pour grouper les lignes
    # Mais garder l'ordre Y original (pas de réorganisation)
    col2_words = sorted(col2_words, key=lambda w: w['y'])
    
    # Grouper par ligne (Y proche)
    rows = []
    row_threshold = 40
    current_row = [col2_words[0]]
    
    for word in col2_words[1:]:
        if abs(word['y'] - current_row[0]['y']) <= row_threshold:
            # Même ligne: ajouter
            current_row.append(word)
        else:
            # Nouvelle ligne: sauvegarder l'ancienne
            rows.append(current_row)
            current_row = [word]
    
    if current_row:
        rows.append(current_row)
    
    # ✅ ORDRE PRÉSERVÉ: Pour chaque ligne (dans l'ordre Y),
    # joindre les mots de gauche à droite (par X)
    result = []
    for row in rows:
        row_sorted_x = sorted(row, key=lambda w: w['x'])
        line_text = ' '.join([w['text'] for w in row_sorted_x])
        if line_text.strip():
            result.append(line_text)
    
    return result


def extract_from_pages_cibles_pdf() -> List[Dict]:
    """
    Extrait colonne 2 de pages_cibles.pdf.
    
    Returns:
        [
            {
                'page': num_page,
                'column2': [liste de lignes EN ORDRE]
            }
        ]
    """
    pages_cibles_path = Path("data/output/pages_cibles.pdf")
    
    if not pages_cibles_path.exists():
        print(f"[ERROR] {pages_cibles_path} not found")
        return []
    
    print(f"\n{'='*70}")
    print(f"EXTRACTION COLONNE 2 - ORDRE PRÉSERVÉ")
    print(f"{'='*70}\n")
    print(f"Source: {pages_cibles_path}")
    
    doc = fitz.open(str(pages_cibles_path))
    print(f"Pages à traiter: {doc.page_count}\n")
    
    results = []
    
    # Traiter chaque page
    for page_num in range(doc.page_count):
        try:
            print(f"Page {page_num + 1}...", end=" ")
            
            # Rendu + OCR
            img_rgb = render_page_hd(str(pages_cibles_path), page_num, dpi=300)
            img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
            
            words = ocr_page(img_gray)
            
            if not words:
                print("✗ No OCR text")
                continue
            
            # Extraire colonne 2 EN ORDRE
            col2_lines = extract_column2_order_preserved(words)
            
            if not col2_lines:
                print("✗ No column 2 content")
                continue
            
            # Résultat (ORDRE PRÉSERVÉ)
            result_item = {
                'page': page_num + 1,
                'column2_lines': col2_lines
            }
            
            results.append(result_item)
            
            print(f"✓ {len(col2_lines)} lignes")
            
        except Exception as e:
            print(f"✗ Error: {str(e)[:30]}")
            continue
    
    doc.close()
    return results


def save_to_json(results: List[Dict], output_path: str = "data/output/column2_ordered.json"):
    """Sauvegarde en JSON."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    return output_path


def save_to_excel(results: List[Dict], output_path: str = "data/output/column2_ordered.xlsx"):
    """Sauvegarde en Excel."""
    try:
        import pandas as pd
    except ImportError:
        print("[WARN] pandas not installed, skipping Excel export")
        return None
    
    # Créer les données pour Excel
    excel_data = []
    
    for item in results:
        page_num = item['page']
        for line_num, line_text in enumerate(item['column2_lines'], 1):
            excel_data.append({
                'Page': page_num,
                'Line': line_num,
                'Column2_Content': line_text
            })
    
    if not excel_data:
        return None
    
    # Créer DataFrame
    df = pd.DataFrame(excel_data)
    
    # Sauvegarder
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(output_path, index=False, sheet_name='Column2')
    
    return output_path


def print_summary(results: List[Dict]):
    """Affiche résumé."""
    print(f"\n{'='*70}")
    print("RÉSUMÉ")
    print(f"{'='*70}\n")
    
    if not results:
        print("❌ Aucun résultat")
        return
    
    total_pages = len(results)
    total_lines = sum(len(r['column2_lines']) for r in results)
    
    print(f"✅ Pages traitées: {total_pages}")
    print(f"✅ Total lignes: {total_lines}")
    print(f"✅ Moyenne par page: {total_lines / total_pages:.1f}")
    
    # Aperçu
    print(f"\n{'='*70}")
    print("APERÇU (premières lignes des pages)")
    print(f"{'='*70}\n")
    
    for item in results:
        print(f"Page {item['page']} ({len(item['column2_lines'])} lignes):")
        for i, line in enumerate(item['column2_lines'][:5], 1):
            display = line if len(line) <= 70 else line[:67] + "..."
            print(f"  {i:2d}. {display}")
        if len(item['column2_lines']) > 5:
            print(f"  ... ({len(item['column2_lines']) - 5} autres)")
        print()


if __name__ == "__main__":
    # Exécuter
    results = extract_from_pages_cibles_pdf()
    
    if results:
        # Sauvegarder
        json_path = save_to_json(results)
        print(f"\n✅ JSON: {json_path}")
        
        xlsx_path = save_to_excel(results)
        if xlsx_path:
            print(f"✅ Excel: {xlsx_path}")
        
        # Résumé
        print_summary(results)
    else:
        print("\n❌ EXTRACTION ÉCHOUÉE")
