#!/usr/bin/env python3
"""Test debug pour voir l'OCR et les en-têtes."""

import sys
sys.path.insert(0, 'src')

import fitz
import cv2
import pytesseract
import numpy as np
from pathlib import Path

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

pdf_path = "data/input/BRAIN INFORMATIQUE_16052025101905.PDF"

doc = fitz.open(pdf_path)

# Tester sur page 2 (devrait contenir un tableau)
test_page_num = 2

print(f"Test sur page {test_page_num + 1}")
print("=" * 70)

page = doc[test_page_num]

# Rendu HD
zoom = 300 / 72.0
mat = fitz.Matrix(zoom, zoom)
pix = page.get_pixmap(matrix=mat, alpha=False)

img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
if pix.n == 4:
    img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
elif pix.n == 1:
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

print(f"Image size: {img_gray.shape}")

# OCR
data = pytesseract.image_to_data(
    img_gray,
    output_type=pytesseract.Output.DICT,
    lang='fra'
)

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
    }
    words.append(word)

print(f"Total mots OCR: {len(words)}")

# Afficher les premiers mots (en-têtes?)
print("\nPremiers mots (potentiellement en-têtes):")
sorted_by_y = sorted(words, key=lambda w: w['y'])

for i, w in enumerate(sorted_by_y[:30]):
    print(f"  {i:2d}. Y={w['y']:4d} X={w['x']:4d} Text='{w['text']}'")

# Chercher les mots dans les 150 premiers pixels (zone en-tête)
header_words = [w for w in words if w['y'] < 150]
print(f"\nMots dans première zone (Y < 150): {len(header_words)}")

if header_words:
    # Trier par X
    header_sorted = sorted(header_words, key=lambda w: w['x'])
    print("Ordonnés par X (gauche → droite):")
    for w in header_sorted[:15]:
        print(f"  X={w['x']:4d} Y={w['y']:4d} '{w['text']}'")
    
    # Diviser en 3 colonnes (tiers)
    img_width = img_gray.shape[1]
    third = img_width / 3
    
    col1_w = [w for w in header_words if w['x'] < third]
    col2_w = [w for w in header_words if third <= w['x'] < 2*third]
    col3_w = [w for w in header_words if w['x'] >= 2*third]
    
    print(f"\nColonne 1 ({0} - {int(third)}): {len(col1_w)} mots")
    if col1_w:
        for w in sorted(col1_w, key=lambda x: x['x'])[:5]:
            print(f"  '{w['text']}'")
    
    print(f"\nColonne 2 ({int(third)} - {int(2*third)}): {len(col2_w)} mots")
    if col2_w:
        for w in sorted(col2_w, key=lambda x: x['x'])[:5]:
            print(f"  '{w['text']}'")
    
    print(f"\nColonne 3 ({int(2*third)} - {img_width}): {len(col3_w)} mots")
    if col3_w:
        for w in sorted(col3_w, key=lambda x: x['x'])[:5]:
            print(f"  '{w['text']}'")

doc.close()
print("\nFin du debug")
