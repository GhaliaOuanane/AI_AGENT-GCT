"""
Debug script pour analyser la détection des lignes verticales.
"""

from pathlib import Path
import sys
import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from pdf_reader import open_pdf

# Chercher le PDF
input_dir = Path('data/input')
pdfs = list(input_dir.glob('*.PDF')) + list(input_dir.glob('*.pdf'))
pdf_path = pdfs[0]

print(f"Testing on: {pdf_path.name}")
print("=" * 80)

poppler_path = r'D:\AI_AGENT GCT\tools\poppler-26.02.0\Library\bin'

# Convertir la page 2 (index 2 = page 3) en image
print("Converting page 3 to image...")
image_list = convert_from_path(
    str(pdf_path),
    dpi=300,
    first_page=3,
    last_page=3,
    poppler_path=poppler_path,
)
image = image_list[0]

print(f"Image size: {image.width} x {image.height}")

# Convertir en niveaux de gris
image_np = np.array(image)
gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)

print(f"Gray image shape: {gray.shape}")

# Afficher des statistiques
print(f"Gray pixel range: {gray.min()} - {gray.max()}")
print(f"Gray mean: {gray.mean():.2f}")

# Essayer Canny avec différents paramètres
print("\nTesting Canny edge detection...")
edges1 = cv2.Canny(gray, 50, 150)
edges2 = cv2.Canny(gray, 100, 200)
edges3 = cv2.Canny(gray, 30, 100)

print(f"Edges1 (50, 150): {edges1.sum() // 255} pixels")
print(f"Edges2 (100, 200): {edges2.sum() // 255} pixels")
print(f"Edges3 (30, 100): {edges3.sum() // 255} pixels")

# Utiliser edges3 pour Hough
edges = edges3
print(f"\nUsing edges3 for Hough detection...")

# Détecter les lignes avec Hough
lines = cv2.HoughLines(edges, 1, np.pi / 180, 50)

print(f"HoughLines result: {lines is not None}")
if lines is not None:
    print(f"Number of lines detected: {len(lines)}")
    
    # Analyser les lignes
    print("\nFirst 20 lines (rho, theta in degrees):")
    for i, (rho, theta) in enumerate(lines[:20, 0]):
        theta_deg = np.degrees(theta)
        print(f"  Line {i}: rho={rho:6.1f}, theta={theta_deg:6.2f}°")
    
    # Extraire les lignes verticales
    print("\nVertical lines (theta < 10° or > 170°):")
    vertical_lines = []
    for rho, theta in lines[:, 0]:
        theta_deg = np.degrees(theta)
        if theta_deg < 10 or theta_deg > 170:
            x = int(rho)
            vertical_lines.append(x)
            print(f"  x={x}, theta={theta_deg:.2f}°")
    
    print(f"\nTotal vertical lines: {len(vertical_lines)}")
    if vertical_lines:
        vertical_lines = sorted(set(vertical_lines))
        print(f"Sorted unique: {vertical_lines}")
        
        # Fusionner les lignes proches
        merged = []
        for x in vertical_lines:
            if not merged or abs(x - merged[-1]) > 5:
                merged.append(x)
            else:
                merged[-1] = (merged[-1] + x) // 2
        
        print(f"Merged (distance > 5): {merged}")
        
        if len(merged) >= 3:
            x1, x2, x3 = merged[0], merged[1], merged[2]
            print(f"\nColumns: [{x1}, {x2}[ and [{x2}, {x3}[")
            print(f"Column 2 width: {x3 - x2} pixels")
