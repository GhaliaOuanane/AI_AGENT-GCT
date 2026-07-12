"""
Analyze separators in detail to understand why extraction is wrong.
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

# Test pages 0, 1, and 2
for page_num in [0, 1, 2]:
    print(f"\n{'='*80}")
    print(f"PAGE {page_num + 1}")
    print(f"{'='*80}")
    
    # Convert to image
    image_list = convert_from_path(
        str(pdf_path),
        dpi=300,
        first_page=page_num + 1,
        last_page=page_num + 1,
        poppler_path=poppler_path,
    )
    image = image_list[0]
    print(f"Image size: {image.width} x {image.height}")
    
    # Convert to gray
    image_np = np.array(image)
    gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    
    # Detect edges
    edges = cv2.Canny(gray, 50, 150)
    
    # HoughLinesP
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=300, maxLineGap=50)
    
    if lines is None or len(lines) == 0:
        print("No lines detected!")
        continue
    
    # Filter vertical lines
    vertical_lines = []
    for line in lines:
        x1, y1, x2, y2 = line.flatten()
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        
        if dx < 20 and dy > 300:
            x_avg = (x1 + x2) // 2
            vertical_lines.append((x_avg, dy))
    
    vertical_lines = sorted(vertical_lines, key=lambda l: l[0])
    
    print(f"\nAll vertical lines (x, height) - {len(vertical_lines)} total:")
    for i, (x, h) in enumerate(vertical_lines):
        print(f"  {i:2d}: x={x:4d}, h={h:4d}")
    
    # Cluster
    clusters = []
    current_cluster = [vertical_lines[0]]
    
    for vline in vertical_lines[1:]:
        if abs(vline[0] - current_cluster[-1][0]) <= 15:
            current_cluster.append(vline)
        else:
            x_avg = int(np.mean([l[0] for l in current_cluster]))
            h_sum = sum(l[1] for l in current_cluster)
            clusters.append((x_avg, h_sum, len(current_cluster)))
            current_cluster = [vline]
    
    if current_cluster:
        x_avg = int(np.mean([l[0] for l in current_cluster]))
        h_sum = sum(l[1] for l in current_cluster)
        clusters.append((x_avg, h_sum, len(current_cluster)))
    
    print(f"\nClusters (x, total_height, count) - {len(clusters)} total:")
    for i, (x, h, c) in enumerate(sorted(clusters, key=lambda x: x[0])):
        print(f"  {i}: x={x:4d}, h={h:6d}, count={c:2d}")
    
    # Select top 4
    main_clusters = sorted(clusters, key=lambda x: x[1], reverse=True)[:4]
    main_clusters = sorted(main_clusters, key=lambda x: x[0])
    
    print(f"\nTop 4 clusters (by height):")
    for i, (x, h, c) in enumerate(main_clusters):
        print(f"  Separator {i}: x={x:4d}, height={h}")
    
    if len(main_clusters) >= 4:
        x0, x1, x2, x3 = [c[0] for c in main_clusters]
        print(f"\nColumn extraction:")
        print(f"  Col 1: [{x0:4d}, {x1:4d}] width={x1-x0:4d}")
        print(f"  Col 2: [{x1:4d}, {x2:4d}] width={x2-x1:4d}")
        print(f"  Col 3: [{x2:4d}, {x3:4d}] width={x3-x2:4d}")
        
        # Show sample of what's in each region
        print(f"\nImage regions (visual check):")
        print(f"  Col 1 sample: x={x0}..{x1}")
        print(f"  Col 2 sample: x={x1}..{x2}")
        print(f"  Col 3 sample: x={x2}..{x3}")
