"""
✅ EXTRACTION COLONNE 2 - VERSION FINALE v3

Combinaison des meilleures approches:
1. Détection colonne 2 simple (tiers: 1/3 à 2/3)
2. DPI 400 + CLAHE pour meilleure qualité
3. OCR confiance >30 (moins strict que >40)
4. Nettoyage intelligent (sans sur-filtrage)
5. Ordre préservé (top à bottom)
"""

import fitz
import cv2
import pytesseract
from pathlib import Path
from typing import List, Dict
import numpy as np
import json
import re

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


MINIMAL_STOP_WORDS = {
    ':', '—', '–', '…', '"', ''', ''',
}


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
        
        # Critère moins strict: >30 au lieu de >40
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


def extract_column2_final(words: List[Dict]) -> List[str]:
    """
    Extraction SIMPLE:
    1. Diviser par tiers (colonne 2 = 1/3 à 2/3)
    2. Grouper par Y
    3. Nettoyer + retourner
    """
    if not words:
        return []
    
    # Simple tiers
    img_width = max(w['x'] + w['width'] for w in words)
    col2_start = img_width / 3
    col2_end = 2 * img_width / 3
    
    col2_words = [w for w in words if col2_start <= w['x'] + w['width']/2 <= col2_end]
    
    if not col2_words:
        return []
    
    # Trier par Y
    col2_words = sorted(col2_words, key=lambda w: w['y'])
    
    # Grouper par ligne (Y ±30px)
    rows = []
    if col2_words:
        current_row = [col2_words[0]]
        
        for word in col2_words[1:]:
            if abs(word['y'] - current_row[0]['y']) <= 30:
                current_row.append(word)
            else:
                rows.append(current_row)
                current_row = [word]
        
        if current_row:
            rows.append(current_row)
    
    # Traiter
    result = []
    for row in rows:
        row_sorted = sorted(row, key=lambda w: w['x'])
        
        cleaned_words = []
        for w in row_sorted:
            cleaned = clean_ocr_text(w['text'])
            if is_valid_word(cleaned):
                cleaned_words.append(cleaned)
        
        if cleaned_words:
            line_text = ' '.join(cleaned_words)
            if len(line_text.strip()) > 0:
                result.append(line_text)
    
    return result


def extract_from_pages_cibles_final() -> List[Dict]:
    """Extraction finale."""
    pages_cibles_path = Path("data/output/pages_cibles.pdf")
    
    if not pages_cibles_path.exists():
        return []
    
    print(f"\n{'='*70}")
    print(f"EXTRACTION COLONNE 2 - VERSION FINALE v3")
    print(f"{'='*70}\n")
    print(f"Source: {pages_cibles_path}")
    print(f"Approche: Tiers simple + DPI 400 + Confiance >30\n")
    
    doc = fitz.open(str(pages_cibles_path))
    print(f"Pages: {doc.page_count}\n")
    
    results = []
    
    for page_num in range(doc.page_count):
        try:
            print(f"Page {page_num + 1}...", end=" ")
            
            words = ocr_page_hd(str(pages_cibles_path), page_num, dpi=400)
            
            if not words:
                print("X No OCR text")
                continue
            
            col2_lines = extract_column2_final(words)
            
            if not col2_lines:
                print("X No column 2 content")
                continue
            
            results.append({
                'page': page_num + 1,
                'column2_lines': col2_lines
            })
            
            print(f"OK {len(col2_lines)} lignes")
            
        except Exception as e:
            print(f"X Error: {str(e)[:30]}")
            continue
    
    doc.close()
    return results


def save_to_json(results: List[Dict], output_path: str = "data/output/column2_improved.json"):
    """Save JSON."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    return output_path


def save_to_excel(results: List[Dict], output_path: str = "data/output/column2_improved.xlsx"):
    """Save Excel."""
    try:
        import pandas as pd
    except ImportError:
        return None
    
    excel_data = []
    
    for item in results:
        page_num = item['page']
        for line_num, line_text in enumerate(item['column2_lines'], 1):
            excel_data.append({
                'Page': page_num,
                'Line_#': line_num,
                'Specification': line_text
            })
    
    if not excel_data:
        return None
    
    df = pd.DataFrame(excel_data)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Column2')
        
        worksheet = writer.sheets['Column2']
        for col in worksheet.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 100)
            worksheet.column_dimensions[column].width = adjusted_width
    
    return output_path


def print_summary(results: List[Dict]):
    """Print summary."""
    print(f"\n{'='*70}")
    print("RESULTAT")
    print(f"{'='*70}\n")
    
    if not results:
        print("ERREUR: Aucun resultat")
        return
    
    total_pages = len(results)
    total_lines = sum(len(r['column2_lines']) for r in results)
    
    print(f"OK Pages: {total_pages}")
    print(f"OK Total lignes: {total_lines}")
    print(f"OK Moyenne: {total_lines / total_pages:.1f}\n")
    
    for item in results[:2]:
        print(f"Page {item['page']} ({len(item['column2_lines'])} lignes):")
        for i, line in enumerate(item['column2_lines'][:3], 1):
            print(f"  {i}. {line[:60]}")
        print()


if __name__ == "__main__":
    results = extract_from_pages_cibles_final()
    
    if results:
        json_path = save_to_json(results)
        print(f"\nOK JSON: {json_path}")
        
        xlsx_path = save_to_excel(results)
        if xlsx_path:
            print(f"OK Excel: {xlsx_path}")
        
        print_summary(results)
    else:
        print("\nERREUR: EXTRACTION ECHOUEE")
