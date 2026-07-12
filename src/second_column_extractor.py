"""
Extraction ciblée de la deuxième colonne des tableaux à 3 colonnes.

Stratégie :
1. Utiliser les coordonnées OCR (x, y) pour identifier les colonnes
2. Trier les mots par position Y (lignes)
3. Identifier 3 colonnes principales par clustering des coordonnées X
4. Extraire uniquement la colonne du milieu
5. Grouper par lignes (Y) pour reconstituer le texte de chaque cellule
6. Nettoyer le texte OCR pour éliminer le bruit
"""

import fitz
import cv2
import pytesseract
from pathlib import Path
from typing import List, Dict
from collections import defaultdict
import numpy as np
import re


def render_page(pdf_path, page_num, dpi=300):
    """Rendu haute résolution d'une page PDF."""
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    
    # Facteur de zoom pour atteindre la résolution DPI demandée
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
    elif pix.n == 1:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    
    doc.close()
    return img


def extract_ocr_data_with_coordinates(img_gray) -> List[Dict]:
    """
    Récupère les données OCR avec coordonnées précises.
    
    Retourne une liste de dictionnaires :
    {
        'text': 'mot',
        'x': left,
        'y': top,
        'width': width,
        'height': height,
        'x_end': left + width,
        'y_end': top + height,
        'conf': confiance
    }
    """
    data = pytesseract.image_to_data(img_gray, output_type=pytesseract.Output.DICT, lang='fra')
    
    words = []
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        if not text:
            continue
        
        word = {
            'text': text,
            'x': int(data['left'][i]),
            'y': int(data['top'][i]),
            'width': int(data['width'][i]),
            'height': int(data['height'][i]),
            'x_end': int(data['left'][i]) + int(data['width'][i]),
            'y_end': int(data['top'][i]) + int(data['height'][i]),
            'conf': int(data['conf'][i])
        }
        words.append(word)
    
    return words


def detect_three_columns(words: List[Dict]) -> tuple:
    """
    Détecte les 3 colonnes en utilisant les coordonnées X des mots.
    
    Retourne : (x_col1_center, x_col2_center, x_col3_center)
    """
    if not words:
        return None, None, None
    
    # Extraire les positions X (centre de chaque mot)
    x_centers = [w['x'] + w['width'] // 2 for w in words]
    
    # Clustering K-means pour identifier 3 groupes de colonnes
    x_array = np.array(x_centers).reshape(-1, 1)
    
    try:
        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        kmeans.fit(x_array)
        centers = sorted(kmeans.cluster_centers_.flatten())
        return float(centers[0]), float(centers[1]), float(centers[2])
    except ImportError:
        # Fallback sans sklearn : utiliser percentiles
        x_sorted = sorted(x_centers)
        idx_33 = len(x_sorted) // 3
        idx_66 = 2 * len(x_sorted) // 3
        return float(x_sorted[idx_33]), float(x_sorted[idx_66 // 2 + idx_33 // 2]), float(x_sorted[idx_66])


def assign_column_to_word(word: Dict, col1_x: float, col2_x: float, col3_x: float) -> int:
    """
    Assigne un mot à l'une des 3 colonnes basé sur sa position X.
    Retourne 1, 2 ou 3.
    """
    word_x = word['x'] + word['width'] // 2
    
    # Distance euclidienne à chaque centre de colonne
    dist1 = abs(word_x - col1_x)
    dist2 = abs(word_x - col2_x)
    dist3 = abs(word_x - col3_x)
    
    min_dist = min(dist1, dist2, dist3)
    
    if min_dist == dist1:
        return 1
    elif min_dist == dist2:
        return 2
    else:
        return 3


def group_words_by_row(words: List[Dict], row_height_threshold=50) -> List[List[Dict]]:
    """
    Groupe les mots par ligne (Y similaire).
    Retourne une liste de listes, chaque sous-liste contient les mots d'une même ligne.
    """
    if not words:
        return []
    
    # Trier par Y
    sorted_words = sorted(words, key=lambda w: w['y'])
    
    rows = []
    current_row = [sorted_words[0]]
    
    for word in sorted_words[1:]:
        # Si le mot est à proximité verticale (Y) du premier mot de la ligne actuelle
        if abs(word['y'] - current_row[0]['y']) <= row_height_threshold:
            current_row.append(word)
        else:
            rows.append(current_row)
            current_row = [word]
    
    rows.append(current_row)
    return rows


def clean_ocr_noise(text: str) -> str:
    """
    Nettoie le texte OCR en supprimant les caractères de bruit.
    Garde les caractères accentués français mais supprime les symboles brisés.
    """
    if not text:
        return ""
    
    # Garder : a-z A-Z 0-9, accents français, tirets, espaces, virgules, points, parenthèses
    # Supprimer : caractères spéciaux brisés, symboles mathématiques brisés, etc.
    cleaned = re.sub(r'[^\w\s\-àâäæçéèêëïîôœùûüÀÂÄÆÇÉÈÊËÏÎÔŒÙÛÜ.,()%/×]', '', text)
    
    # Supprimer les espaces multiples
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Supprimer les tirets isolés
    if cleaned == '-' or cleaned == '—':
        return ""
    
    return cleaned


def is_valid_specification(text: str, min_length=3, max_length=200) -> bool:
    """
    Vérifie si le texte est une spécification valide.
    Filtre les bruit OCR, les caractères isolés, etc.
    """
    if not text:
        return False
    
    cleaned = clean_ocr_noise(text)
    
    if len(cleaned) < min_length or len(cleaned) > max_length:
        return False
    
    # Compter les différents types de caractères
    alpha_count = sum(1 for c in cleaned if c.isalpha())
    digit_count = sum(1 for c in cleaned if c.isdigit())
    space_count = sum(1 for c in cleaned if c.isspace())
    other_count = len(cleaned) - alpha_count - digit_count - space_count
    
    total_meaningful = alpha_count + digit_count
    
    # Au moins 60% de caractères alphanumériques (pas trop de symboles)
    if len(cleaned) > 0 and total_meaningful / len(cleaned) < 0.6:
        return False
    
    # Au moins 50% de lettres (pas juste des chiffres/symboles)
    if len(cleaned) > 0 and alpha_count / len(cleaned) < 0.3:
        return False
    
    return True


def is_valid_specification_page(specifications: List[str], min_specs=3) -> bool:
    """
    Vérifie si une page contient un tableau valide de spécifications.
    Une page valide doit avoir au minimum min_specs spécifications de qualité.
    """
    if len(specifications) < min_specs:
        return False
    
    # Compter les spécifications valides
    valid_count = sum(1 for spec in specifications if is_valid_specification(spec))
    
    return valid_count >= min_specs


def extract_second_column_from_page(pdf_path: str, page_num: int) -> List[str]:
    """
    Extrait UNIQUEMENT la deuxième colonne d'une page.
    
    Retourne une liste de strings, chaque string est le contenu d'une cellule (ligne).
    """
    try:
        # Rendu HD
        img_rgb = render_page(pdf_path, page_num, dpi=300)
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    except Exception as e:
        print(f"[ERROR] Page {page_num}: Render failed - {e}")
        return []
    
    # Récupérer données OCR avec coordonnées
    words = extract_ocr_data_with_coordinates(img_gray)
    
    if not words:
        print(f"[WARN] Page {page_num}: No OCR words detected")
        return []
    
    # Détecter les 3 colonnes
    col1_x, col2_x, col3_x = detect_three_columns(words)
    
    if col1_x is None or col2_x is None or col3_x is None:
        print(f"[WARN] Page {page_num}: Could not detect 3 columns")
        return []
    
    # Assigner chaque mot à une colonne
    for word in words:
        word['column'] = assign_column_to_word(word, col1_x, col2_x, col3_x)
    
    # Filtrer uniquement les mots de la colonne 2
    col2_words = [w for w in words if w['column'] == 2]
    
    if not col2_words:
        print(f"[WARN] Page {page_num}: No words in column 2")
        return []
    
    # Grouper les mots de col2 par ligne (Y)
    rows = group_words_by_row(col2_words, row_height_threshold=30)
    
    # Pour chaque ligne, concatener les mots en respectant l'ordre X
    specifications = []
    for row in rows:
        # Trier les mots par X (gauche à droite)
        row_sorted = sorted(row, key=lambda w: w['x'])
        
        # Joindre les mots avec un espace
        row_text = ' '.join([w['text'] for w in row_sorted])
        
        # Nettoyer le texte OCR
        cleaned_text = clean_ocr_noise(row_text)
        
        # Ajouter uniquement si valide
        if is_valid_specification(cleaned_text):
            specifications.append(cleaned_text)
    
    return specifications


def extract_all_specifications(pdf_path: str, min_valid_specs_per_page=3) -> List[Dict]:
    """
    Extrait les spécifications (colonne 2) de toutes les pages.
    Ne garde que les pages avec des tableaux valides.
    
    Retourne une liste de dictionnaires :
    {
        'page': page_number,
        'specifications': [list of strings]
    }
    """
    results = []
    doc = fitz.open(pdf_path)
    
    for page_num in range(doc.page_count):
        specs = extract_second_column_from_page(pdf_path, page_num)
        
        # Filtrer : garder uniquement les pages avec des tableaux valides
        if is_valid_specification_page(specs, min_specs=min_valid_specs_per_page):
            results.append({
                'page': page_num + 1,
                'specifications': specs
            })
            print(f"[OK] Page {page_num + 1}: {len(specs)} spécifications (valides)")
        else:
            valid_count = sum(1 for s in specs if is_valid_specification(s))
            print(f"[SKIP] Page {page_num + 1}: {len(specs)} spécifications brutes, {valid_count} valides (filtré)")
    
    doc.close()
    return results
