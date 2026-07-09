"""
Module d'extraction de la 2ᵉ colonne des tableaux.

Détecte automatiquement les limites des colonnes à partir des lignes verticales
du tableau (détection visuelle, pas de coordonnées fixes).

Pour chaque page cible, extrait et enregistre l'image de la 2ᵉ colonne.
"""

from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image
from pypdf import PdfReader


def _pdf_page_to_image(
    pdf_path: str | Path,
    page_number: int,
    dpi: int = 300,
    poppler_path: Optional[str] = None,
) -> Optional[Image.Image]:
    """
    Convertit une page PDF en image PIL.
    
    Args:
        pdf_path: Chemin du fichier PDF
        page_number: Numéro de page (0-indexed)
        dpi: Résolution (pixels per inch)
        poppler_path: Chemin vers les binaires Poppler
    
    Returns:
        Image PIL ou None si erreur
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"[ERROR] PDF not found: {pdf_path}")
        return None
    
    try:
        image_list = convert_from_path(
            str(pdf_path),
            dpi=dpi,
            first_page=page_number + 1,
            last_page=page_number + 1,
            poppler_path=poppler_path,
        )
        
        if not image_list:
            print(f"[ERROR] Failed to convert page {page_number}")
            return None
        
        return image_list[0]
    
    except Exception as e:
        print(f"[ERROR] PDF to image conversion failed: {e}")
        return None


def _detect_vertical_lines(image: Image.Image) -> List[int]:
    """
    Détecte les lignes verticales du tableau en utilisant HoughLinesP.
    
    Identifie les séparateurs de colonnes principaux du tableau en:
    1. Détectant les segments de lignes verticales longues (HoughLinesP)
    2. Filtrant les lignes verticales (dx << dy)
    3. Regroupant (clustering) les lignes proches (même séparateur)
    4. Sélectionnant les 4 séparateurs principaux par importance (hauteur totale)
    
    Args:
        image: Image PIL d'une page PDF
    
    Returns:
        Liste des positions X (en pixels) des 4 séparateurs principaux,
        triées en ordre croissant.
        Retourne une liste vide si impossible de détecter.
    """
    # Convertir PIL → numpy array
    image_np = np.array(image)
    if len(image_np.shape) == 3:
        gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    else:
        gray = image_np
    
    # Détecter les arêtes
    edges = cv2.Canny(gray, 50, 150)
    
    # HoughLinesP: détecte les segments de lignes
    # minLineLength: minimum 300 pixels
    # maxLineGap: tolérer les brèches jusqu'à 50 pixels
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=300, maxLineGap=50)
    
    if lines is None or len(lines) == 0:
        print("[WARN] No line segments detected")
        return []
    
    # Filtrer les lignes verticales
    vertical_lines = []
    
    for line in lines:
        x1, y1, x2, y2 = line.flatten()
        
        # Calculer dx et dy
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        
        # Une ligne verticale: dx petit, dy grand
        if dx < 20 and dy > 300:
            x_avg = (x1 + x2) // 2
            vertical_lines.append((x_avg, dy))
    
    if not vertical_lines:
        print("[WARN] No vertical lines found")
        return []
    
    # Trier par X
    vertical_lines = sorted(vertical_lines, key=lambda l: l[0])
    
    # Regrouper les lignes proches (même séparateur)
    # Tolérance: 15 pixels
    clusters = []
    current_cluster = [vertical_lines[0]]
    
    for vline in vertical_lines[1:]:
        if abs(vline[0] - current_cluster[-1][0]) <= 15:
            current_cluster.append(vline)
        else:
            # Fin du groupe
            x_avg = int(np.mean([l[0] for l in current_cluster]))
            h_sum = sum(l[1] for l in current_cluster)
            clusters.append((x_avg, h_sum))
            current_cluster = [vline]
    
    # Dernier groupe
    if current_cluster:
        x_avg = int(np.mean([l[0] for l in current_cluster]))
        h_sum = sum(l[1] for l in current_cluster)
        clusters.append((x_avg, h_sum))
    
    if len(clusters) < 3:
        print(f"[WARN] Expected at least 3 separators, got {len(clusters)}")
        return []
    
    # Sélectionner les 4 séparateurs principaux (par hauteur totale)
    main_clusters = sorted(clusters, key=lambda c: c[1], reverse=True)[:4]
    # Les retrier par X
    main_clusters = sorted(main_clusters, key=lambda c: c[0])
    
    result = [c[0] for c in main_clusters]
    
    print(f"[INFO] Detected {len(result)} main column separators at: {result}")
    
    return result


def _extract_column_region(
    image: Image.Image,
    vertical_lines: List[int],
    column_number: int = 2,
) -> Optional[Image.Image]:
    """
    Extrait une colonne spécifique du tableau.
    
    Les 4 lignes principales déterminent 3 colonnes :
    - Colonne 1 : [line[0], line[1][
    - Colonne 2 : [line[1], line[2][  ← celle-ci par défaut
    - Colonne 3 : [line[2], line[3][
    
    Args:
        image: Image PIL d'une page
        vertical_lines: Liste des 4 positions X des séparateurs principaux
        column_number: Numéro de colonne à extraire (1, 2, ou 3)
    
    Returns:
        Image PIL contenant la colonne, ou None si erreur
    """
    # Nous attendons exactement 4 lignes (séparateurs pour 3 colonnes)
    if len(vertical_lines) < 4:
        print(f"[WARN] Expected 4 vertical lines, got {len(vertical_lines)}")
        print(f"       Available lines: {vertical_lines}")
        return None
    
    # Prendre les 4 premières lignes principales
    x0, x1, x2, x3 = vertical_lines[0], vertical_lines[1], vertical_lines[2], vertical_lines[3]
    
    # Déterminer les limites selon la colonne demandée
    if column_number == 1:
        left, right = x0, x1
    elif column_number == 2:
        left, right = x1, x2
    elif column_number == 3:
        left, right = x2, x3
    else:
        print(f"[ERROR] Invalid column number: {column_number}")
        return None
    
    # Vérifier que les coordonnées sont valides
    if left >= right:
        print(f"[ERROR] Invalid column boundaries: left={left}, right={right}")
        return None
    
    # Extraire la région (crop)
    # PIL crop : (left, top, right, bottom)
    print(f"[INFO] Column {column_number}: left={left}, right={right}, width={right-left}px")
    column_image = image.crop((left, 0, right, image.height))
    
    return column_image


def extract_and_save_column2(
    pdf_path: str | Path,
    page_number: int,
    output_dir: str | Path,
    poppler_path: Optional[str] = None,
    dpi: int = 300,
) -> Optional[Path]:
    """
    Extrait la 2ᵉ colonne d'une page PDF et l'enregistre.
    
    Args:
        pdf_path: Chemin du fichier PDF
        page_number: Numéro de page (0-indexed)
        output_dir: Dossier de sortie
        poppler_path: Chemin vers les binaires Poppler
        dpi: Résolution
    
    Returns:
        Chemin du fichier PNG créé, ou None si erreur
    """
    # Convertir PDF → image
    image = _pdf_page_to_image(
        pdf_path,
        page_number,
        dpi=dpi,
        poppler_path=poppler_path,
    )
    
    if image is None:
        print(f"[ERROR] Failed to convert page {page_number} to image")
        return None
    
    # Détecter les lignes verticales
    vertical_lines = _detect_vertical_lines(image)
    
    if not vertical_lines:
        print(f"[WARN] No vertical lines detected for page {page_number}")
        return None
    
    print(f"[INFO] Page {page_number}: detected {len(vertical_lines)} vertical lines at: {vertical_lines[:5]}...")
    
    # Extraire la 2ᵉ colonne
    column_image = _extract_column_region(image, vertical_lines, column_number=2)
    
    if column_image is None:
        print(f"[ERROR] Failed to extract column 2 from page {page_number}")
        return None
    
    # Enregistrer l'image
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Nommer le fichier
    output_path = output_dir / f"page_{page_number+1:03d}_column2.png"
    
    try:
        column_image.save(str(output_path), "PNG")
        print(f"[OK] Saved column 2 to: {output_path}")
        return output_path
    
    except Exception as e:
        print(f"[ERROR] Failed to save image: {e}")
        return None


def extract_all_columns(
    reader: PdfReader,
    pdf_path: str | Path,
    selected_pages: Optional[List] = None,
    output_dir: str | Path = "data/output",
    poppler_path: Optional[str] = None,
    dpi: int = 300,
) -> List[Path]:
    """
    Extrait la 2ᵉ colonne pour toutes les pages sélectionnées.
    
    Args:
        reader: PdfReader ouvert
        pdf_path: Chemin du fichier PDF
        selected_pages: Liste des objets page (ou None pour traiter toutes)
        output_dir: Dossier de sortie
        poppler_path: Chemin vers les binaires Poppler
        dpi: Résolution
    
    Returns:
        Liste des chemins des fichiers PNG créés
    """
    # Si des pages sont spécifiées, trouver leurs indices
    if selected_pages is not None:
        selected_indices = []
        for page_obj in selected_pages:
            for idx, reader_page in enumerate(reader.pages):
                if reader_page is page_obj:
                    selected_indices.append(idx)
                    break
    else:
        selected_indices = list(range(len(reader.pages)))
    
    output_paths = []
    
    print(f"\n[INFO] Extracting column 2 from {len(selected_indices)} pages...")
    
    for page_idx in selected_indices:
        output_path = extract_and_save_column2(
            pdf_path,
            page_idx,
            output_dir,
            poppler_path=poppler_path,
            dpi=dpi,
        )
        
        if output_path:
            output_paths.append(output_path)
    
    print(f"[OK] Extracted {len(output_paths)} column images")
    return output_paths
