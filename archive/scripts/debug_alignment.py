"""Debug script to visualize column alignment issue."""
import fitz
import cv2
import pytesseract
import numpy as np
from pathlib import Path

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def debug_page_columns(pdf_path, page_num=0, dpi=400):
    """Extract and display columns side by side to diagnose alignment."""
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n).copy()
    if pix.n == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
    
    img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img_gray = clahe.apply(img_gray)
    
    doc.close()
    
    # Get OCR data
    data = pytesseract.image_to_data(
        img_gray,
        output_type=pytesseract.Output.DICT,
        lang='fra'
    )
    
    words = []
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        conf = int(data['conf'][i])
        if text and conf > 30:
            words.append({
                'text': text,
                'x': int(data['left'][i]),
                'y': int(data['top'][i]),
                'width': int(data['width'][i]),
                'height': int(data['height'][i]),
                'conf': conf
            })
    
    if not words:
        print("No words found!")
        return
    
    # Get image width
    img_width = max(w['x'] + w['width'] for w in words)
    
    # Define column boundaries (same as code)
    col1_start = 0
    col1_end = img_width / 3
    col2_start = img_width / 3
    col2_end = 2 * img_width / 3
    
    # Filter words by column
    col1_words = [w for w in words if col1_start <= w['x'] + w['width']/2 <= col1_end]
    col2_words = [w for w in words if col2_start <= w['x'] + w['width']/2 <= col2_end]
    
    # Sort by Y
    col1_words = sorted(col1_words, key=lambda w: w['y'])
    col2_words = sorted(col2_words, key=lambda w: w['y'])
    
    print(f"\n{'='*80}")
    print(f"PAGE {page_num + 1} - RAW WORDS BEFORE GROUPING")
    print(f"{'='*80}\n")
    print(f"Column 1 (Designation) - {len(col1_words)} words:")
    for i, w in enumerate(col1_words[:20], 1):
        print(f"  {i:2d}. Y={w['y']:4d} | {w['text']}")
    
    print(f"\nColumn 2 (Specification) - {len(col2_words)} words:")
    for i, w in enumerate(col2_words[:20], 1):
        print(f"  {i:2d}. Y={w['y']:4d} | {w['text']}")
    
    # Now group by Y (±30px) and show lines
    def group_by_y(words, tolerance=30):
        if not words:
            return []
        rows = []
        current_row = [words[0]]
        for word in words[1:]:
            if abs(word['y'] - current_row[0]['y']) <= tolerance:
                current_row.append(word)
            else:
                rows.append(current_row)
                current_row = [word]
        if current_row:
            rows.append(current_row)
        return rows
    
    col1_rows = group_by_y(col1_words)
    col2_rows = group_by_y(col2_words)
    
    print(f"\n{'='*80}")
    print(f"AFTER GROUPING BY Y (±30px)")
    print(f"{'='*80}\n")
    
    print(f"Column 1 - {len(col1_rows)} lines:")
    for i, row in enumerate(col1_rows[:15], 1):
        text = ' '.join(w['text'] for w in sorted(row, key=lambda x: x['x']))
        avg_y = sum(w['y'] for w in row) / len(row)
        print(f"  {i:2d}. Y={avg_y:6.1f} | {text}")
    
    print(f"\nColumn 2 - {len(col2_rows)} lines:")
    for i, row in enumerate(col2_rows[:15], 1):
        text = ' '.join(w['text'] for w in sorted(row, key=lambda x: x['x']))
        avg_y = sum(w['y'] for w in row) / len(row)
        print(f"  {i:2d}. Y={avg_y:6.1f} | {text}")
    
    # Show side-by-side pairing
    print(f"\n{'='*80}")
    print(f"Y-POSITION BASED PAIRING (NEW APPROACH - ±50px tolerance)")
    print(f"{'='*80}\n")
    
    used_col2 = set()
    pairings = []
    
    for i, row1 in enumerate(col1_rows[:20]):
        col1_text = ' '.join(w['text'] for w in sorted(row1, key=lambda x: x['x']))
        y1 = sum(w['y'] for w in row1) / len(row1)
        
        # Find closest col2 by Y position
        best_match_idx = None
        best_y_diff = float('inf')
        
        for j, row2 in enumerate(col2_rows):
            if j in used_col2:
                continue
            y2 = sum(w['y'] for w in row2) / len(row2)
            y_diff = abs(y1 - y2)
            if y_diff < 50 and y_diff < best_y_diff:
                best_match_idx = j
                best_y_diff = y_diff
        
        if best_match_idx is not None:
            row2 = col2_rows[best_match_idx]
            col2_text = ' '.join(w['text'] for w in sorted(row2, key=lambda x: x['x']))
            y2 = sum(w['y'] for w in row2) / len(row2)
            used_col2.add(best_match_idx)
            
            y_diff_str = f"d{best_y_diff:.0f}px"
            print(f"{i+1:2d}. Y={y1:6.1f} {col1_text:35s} -> Y={y2:6.1f} {y_diff_str:8s} {col2_text}")
        else:
            print(f"{i+1:2d}. Y={y1:6.1f} {col1_text:35s} -> NO MATCH")
    
    # Show unmatched col2 rows
    print(f"\nUnmatched Column 2 rows (headers/titles):")
    for j, row2 in enumerate(col2_rows):
        if j not in used_col2:
            col2_text = ' '.join(w['text'] for w in sorted(row2, key=lambda x: x['x']))
            y2 = sum(w['y'] for w in row2) / len(row2)
            print(f"    Y={y2:6.1f} {col2_text}")

if __name__ == "__main__":
    debug_page_columns("data/output/pages_cibles.pdf", page_num=0)
