"""
Debug visual: Extraire une page et visualiser les colonnes détectées
"""

import fitz
import cv2
import pytesseract
import numpy as np
from pathlib import Path

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def render_page_with_detections(pdf_path, page_num, dpi=300, output_path=None):
    """Rendre une page avec les colonnes marquées."""
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
    img = img.copy()  # Ensure writeable
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img_gray = clahe.apply(img_gray)
    
    # OCR avec détails
    data = pytesseract.image_to_data(
        img_gray,
        output_type=pytesseract.Output.DICT,
        lang='fra'
    )
    
    # Dessiner chaque mot
    for i in range(len(data['text'])):
        text = data['text'][i]
        conf = int(data['conf'][i])
        
        if text.strip() and conf > 40:
            x = int(data['left'][i])
            y = int(data['top'][i])
            w = int(data['width'][i])
            h = int(data['height'][i])
            
            # Couleur par X position
            x_center = x + w / 2
            if x_center < img.shape[1] / 3:
                color = (0, 255, 0)  # Column 1: Green
            elif x_center < 2 * img.shape[1] / 3:
                color = (0, 0, 255)  # Column 2: Red
            else:
                color = (255, 0, 0)  # Column 3: Blue
            
            cv2.rectangle(img, (x, y), (x+w, y+h), color, 1)
            cv2.putText(img, text[:10], (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)
    
    # Sauvegarder
    if output_path:
        cv2.imwrite(output_path, img)
        print(f"✓ Sauvegardé: {output_path}")
    
    doc.close()
    return img

# Tester avec page 1
print("Création debug image pour page 1...")
render_page_with_detections(
    "data/output/pages_cibles.pdf",
    0,  # Page 1
    dpi=300,
    output_path="debug_column2_visual_page1.png"
)

print("Créé: debug_column2_visual_page1.png")
print("Les boîtes montrent:")
print("  - VERT = Colonne 1 (Désignation)")
print("  - ROUGE = Colonne 2 (Spécifications)")
print("  - BLEU = Colonne 3 (Proposition)")
