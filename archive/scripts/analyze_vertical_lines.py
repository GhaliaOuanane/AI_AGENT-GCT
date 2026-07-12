"""
Script pour analyser les lignes verticales détectées et identifier le problème.
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
print("ANALYSING CURRENT ALGORITHM")
print("="*80)

# Current algorithm: morphological gradient + vertical projection
kernel_vertical = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 50))
vertical_edges = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, kernel_vertical)
_, binary = cv2.threshold(vertical_edges, 30, 255, cv2.THRESH_BINARY)
vertical_projection = np.sum(binary, axis=0)

threshold = np.mean(vertical_projection) + np.std(vertical_projection)
peaks = np.where(vertical_projection > threshold)[0]

print(f"Vertical projection stats:")
print(f"  Min: {vertical_projection.min()}, Max: {vertical_projection.max()}")
print(f"  Mean: {vertical_projection.mean():.2f}, Std: {vertical_projection.std():.2f}")
print(f"  Threshold: {threshold:.2f}")
print(f"  Peaks found: {len(peaks)}")
print(f"  First 50 peaks: {peaks[:50]}")

# Group peaks
lines = []
current_group = [peaks[0]]

for p in peaks[1:]:
    if p - current_group[-1] <= 2:
        current_group.append(p)
    else:
        center = int(np.mean(current_group))
        lines.append(center)
        current_group = [p]

if current_group:
    center = int(np.mean(current_group))
    lines.append(center)

print(f"\nGrouped vertical lines: {lines}")

# Now try a better approach: find contours and filter them
print("\n" + "="*80)
print("BETTER APPROACH: CONTOUR-BASED")
print("="*80)

# Use Canny for cleaner edges
edges = cv2.Canny(gray, 100, 200)

# Find contours
contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

print(f"Total contours found: {len(contours)}")

# Filter contours: find vertical lines
vertical_segments = []

for contour in contours:
    x, y, w, h = cv2.boundingRect(contour)
    
    # A vertical line should be: narrow and tall
    # Ratio: height >> width
    if h > 100 and w < 20:  # Tall and narrow
        # Record the X position (use middle of the line)
        x_center = x + w // 2
        vertical_segments.append((x_center, h))

print(f"\nVertical segments (x_center, height):")
for x, h in sorted(vertical_segments)[:20]:
    print(f"  x={x:4d}, height={h:4d}")

# Cluster nearby segments (they represent the same column separator)
print(f"\nClustering nearby segments...")

if vertical_segments:
    # Sort by x position
    vertical_segments = sorted(vertical_segments, key=lambda s: s[0])
    
    # Cluster: group segments within 10 pixels
    clusters = []
    current_cluster = [vertical_segments[0]]
    
    for seg in vertical_segments[1:]:
        if abs(seg[0] - current_cluster[-1][0]) <= 10:
            current_cluster.append(seg)
        else:
            # End of cluster: take the most common X (median)
            x_positions = [s[0] for s in current_cluster]
            cluster_x = int(np.median(x_positions))
            cluster_height = sum(s[1] for s in current_cluster)
            clusters.append((cluster_x, cluster_height, len(current_cluster)))
            current_cluster = [seg]
    
    # Last cluster
    if current_cluster:
        x_positions = [s[0] for s in current_cluster]
        cluster_x = int(np.median(x_positions))
        cluster_height = sum(s[1] for s in current_cluster)
        clusters.append((cluster_x, cluster_height, len(current_cluster)))
    
    print(f"\nClusters (x, total_height, count):")
    for i, (x, h, count) in enumerate(clusters):
        print(f"  Cluster {i}: x={x:4d}, height={h:6d}, segments={count}")
    
    # Filter: keep only the most significant clusters
    # (those with high total height = strong vertical lines)
    significant_clusters = sorted(clusters, key=lambda c: c[1], reverse=True)[:4]
    significant_clusters = sorted(significant_clusters, key=lambda c: c[0])
    
    print(f"\nMost significant clusters (top 4):")
    for i, (x, h, count) in enumerate(significant_clusters):
        print(f"  Column separator {i}: x={x:4d} (height={h}, segments={count})")
    
    # Use these as column boundaries
    if len(significant_clusters) >= 3:
        x1 = significant_clusters[0][0]
        x2 = significant_clusters[1][0]
        x3 = significant_clusters[2][0]
        
        print(f"\nColumn boundaries:")
        print(f"  Col 1/2 separator: x={x1}")
        print(f"  Col 2/3 separator: x={x2}")
        print(f"  Col 3/right edge: x={x3}")
        print(f"\nColumn 2 extraction: left={x1}, right={x2}, width={x2-x1}")
