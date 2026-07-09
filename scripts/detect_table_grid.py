"""
Détecter la grille du tableau en utilisant HoughLinesP (segments de lignes).
"""

from pathlib import Path
import sys
import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

# Chercher le PDF
input_dir = Path('data/input')
pdfs = list(input_dir.glob('*.PDF')) + list(input_dir.glob('*.pdf'))
pdf_path = pdfs[0]

poppler_path = r'D:\AI_AGENT GCT\tools\poppler-26.02.0\Library\bin'

# Convertir la page 3 (index 2) en image
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

print("\n" + "="*80)
print("APPROACH: HoughLinesP (Probabilistic Hough Line Transform)")
print("="*80)

# Use Canny for cleaner edges
edges = cv2.Canny(gray, 50, 150)

# HoughLinesP: returns line segments (x1, y1, x2, y2)
# minLineLength: minimum length of line
# maxLineGap: maximum gap between points on the same line
lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=300, maxLineGap=50)

print(f"Total line segments detected: {len(lines)}")

if lines is not None:
    # Filter for vertical lines
    vertical_lines = []
    
    for line in lines:
        # HoughLinesP returns shape (N, 1, 4), so we need lines[i][0]
        x1, y1, x2, y2 = line.flatten()
        
        # Check if line is vertical (x1 ≈ x2)
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        
        # Vertical line: dx < dy and dx is small
        if dx < 20 and dy > 300:
            x_avg = (x1 + x2) // 2
            vertical_lines.append((x_avg, dy, y1, y2))
    
    print(f"\nVertical lines found: {len(vertical_lines)}")
    print(f"\nVertical lines (x, height, y1, y2):")
    for i, (x, h, y1, y2) in enumerate(sorted(vertical_lines)):
        print(f"  {i:2d}: x={x:4d}, height={h:4d}, y={y1:4d}-{y2:4d}")
    
    # Cluster nearby vertical lines
    if vertical_lines:
        vertical_lines_sorted = sorted(vertical_lines, key=lambda l: l[0])
        
        clusters = []
        current_cluster = [vertical_lines_sorted[0]]
        
        for vline in vertical_lines_sorted[1:]:
            if abs(vline[0] - current_cluster[-1][0]) <= 15:
                current_cluster.append(vline)
            else:
                # End cluster
                x_avg = int(np.mean([l[0] for l in current_cluster]))
                h_sum = sum(l[1] for l in current_cluster)
                clusters.append((x_avg, h_sum, len(current_cluster)))
                current_cluster = [vline]
        
        # Last cluster
        if current_cluster:
            x_avg = int(np.mean([l[0] for l in current_cluster]))
            h_sum = sum(l[1] for l in current_cluster)
            clusters.append((x_avg, h_sum, len(current_cluster)))
        
        print(f"\nClustered separators (x, total_height, count):")
        for i, (x, h, count) in enumerate(sorted(clusters)):
            print(f"  {i}: x={x:4d}, height={h:6d}, segments={count}")
        
        # Select top 4 clusters (main table separators)
        main_clusters = sorted(clusters, key=lambda c: c[1], reverse=True)[:4]
        main_clusters = sorted(main_clusters, key=lambda c: c[0])
        
        print(f"\nMain column separators (sorted by X):")
        for i, (x, h, count) in enumerate(main_clusters):
            print(f"  Separator {i}: x={x:4d}")
        
        if len(main_clusters) >= 3:
            sep0, sep1, sep2 = main_clusters[0][0], main_clusters[1][0], main_clusters[2][0]
            print(f"\nColumn 2 would be extracted as:")
            print(f"  Left border:  x={sep0}")
            print(f"  Right border: x={sep1}")
            print(f"  Width: {sep1 - sep0} pixels")
            
            # But maybe we need the separators in a different order?
            print(f"\nAlternative interpretation:")
            print(f"  Maybe columns are: [{sep0}, {sep1}] [{sep1}, {sep2}]")
            print(f"  So column 2 is: left={sep1}, right={sep2}, width={sep2-sep1}")
else:
    print("No lines detected")
