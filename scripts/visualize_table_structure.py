"""
Visualizer les lignes détectées sur l'image pour comprendre la structure du tableau.
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
    if h > 100 and w < 20:  # Tall and narrow
        x_center = x + w // 2
        vertical_segments.append(((x_center, y, w, h)))

print(f"\nAll vertical segments (x, y, width, height) - showing top 30:")
vertical_segments_sorted = sorted(vertical_segments, key=lambda s: s[0])
for i, (x, y, w, h) in enumerate(vertical_segments_sorted[:30]):
    print(f"  {i:2d}: x={x:4d}, y={y:4d}, width={w:2d}, height={h:4d}")

# Show the image region around the table to understand structure
print(f"\nLooking for table structure...")

# Create a copy for visualization
vis_image = image_np.copy()

# Draw detected vertical lines
for x, y, w, h in vertical_segments_sorted:
    cv2.line(vis_image, (x, y), (x, y+h), (255, 0, 0), 2)

# Save visualization
output_path = Path('data/output/table_structure_analysis.png')
vis_pil = Image.fromarray(vis_image)
vis_pil.save(str(output_path))
print(f"Saved visualization to: {output_path}")

# Analyze the region with most vertical segments
# This is likely the table
print(f"\nAnalyzing X distribution...")
x_positions = [s[0] for s in vertical_segments_sorted]
x_min, x_max = min(x_positions), max(x_positions)
print(f"X range: {x_min} to {x_max} (width={x_max-x_min})")

# Look for gaps in X distribution (these might separate columns)
x_positions_sorted = sorted(set(x_positions))
print(f"\nUnique X positions ({len(x_positions_sorted)} total):")
print(x_positions_sorted)

# Find largest gaps
gaps = []
for i in range(len(x_positions_sorted)-1):
    gap = x_positions_sorted[i+1] - x_positions_sorted[i]
    if gap > 50:
        gaps.append((gap, x_positions_sorted[i], x_positions_sorted[i+1]))

gaps_sorted = sorted(gaps, reverse=True)
print(f"\nLargest gaps (>50px):")
for gap, x1, x2 in gaps_sorted[:10]:
    print(f"  Gap of {gap}px between x={x1} and x={x2}")
