"""
✅ EXTRACTION COLONNE 2 - À PARTIR DE pages_cibles.pdf

Processus:
1. Charger pages_cibles.pdf (pages déjà sélectionnées)
2. Pour chaque page:
   a) Extraire les en-têtes via OCR
   b) Valider Modèle 1 ou 2
   c) Extraire colonne 2 COMPLÈTEMENT
3. Sauvegarder JSON

✅ PAS DE RE-DÉTECTION
✅ UNIQUEMENT PAGES CIBLES
"""

import fitz
import cv2
import pytesseract
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np
import json


# ============================================================================
# UTILITAIRES
# ============================================================================

def normalize_text(text: str) -> str:
    """Normalise pour comparaison."""
    text = text.lower().strip()
    replacements = {
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'à': 'a', 'â': 'a', 'ä': 'a',
        'ù': 'u', 'û': 'u', 'ü': 'u',
        'ô': 'o', 'ö': 'o',
        'ç': 'c', 'î': 'i', 'ï': 'i'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


# ============================================================================
# MOTS-CLÉS MODÈLES
# ============================================================================

MODELE_1 = {
    'col1': ['designat'],  # "désignation"
    'col2': ['specificat'],  # "spécification"
    'col3': ['proposition']
}

MODELE_2 = {
    'col1': ['composant', 'offre'],
    'col2': ['caracteristic', 'technique', 'minimal'],
    'col3': ['proposition']
}


def detect_model(headers: List[str]) -> Optional[Tuple[str, int]]:
    """
    Détecte Modèle 1 ou 2.
    Returns: ('MODELE_1' ou 'MODELE_2', col2_index) ou None
    """
    if len(headers) < 3:
        return None
    
    norm = [normalize_text(h) for h in headers[:3]]
    
    # Modèle 1: Désignation / Spécification / Proposition
    m1_col1 = any(kw in norm[0] for kw in MODELE_1['col1'])
    m1_col2 = any(kw in norm[1] for kw in MODELE_1['col2'])
    m1_col3 = any(kw in norm[2] for kw in MODELE_1['col3'])
    
    if m1_col1 and m1_col2 and m1_col3:
        return ('MODELE_1', 1)
    
    # Modèle 2: Composants / Caractéristiques / Proposition
    m2_col1 = any(kw in norm[0] for kw in MODELE_2['col1'])
    m2_col2 = any(kw in norm[1] for kw in MODELE_2['col2'])
    m2_col3 = any(kw in norm[2] for kw in MODELE_2['col3'])
    
    if m2_col1 and m2_col2 and m2_col3:
        return ('MODELE_2', 1)
    
    return None


# ============================================================================
# EXTRACTION OCR
# ============================================================================

def render_page_hd(pdf_path, page_num, dpi=300):
    """Rendu haute résolution."""
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    
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


def ocr_page(img_gray) -> List[Dict]:
    """OCR + extraction coordonnées."""
    try:
        data = pytesseract.image_to_data(
            img_gray,
            output_type=pytesseract.Output.DICT,
            lang='fra'
        )
    except:
        return []
    
    words = []
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        if text and len(text) > 0:
            words.append({
                'text': text,
                'x': int(data['left'][i]),
                'y': int(data['top'][i]),
                'width': int(data['width'][i]),
                'height': int(data['height'][i])
            })
    
    return words


def extract_headers_by_keywords(words: List[Dict]) -> Optional[Tuple[List[str], List[Tuple]]]:
    """
    ✅ CORRIGÉ: Détecte les en-têtes par MOTS-CLÉS, pas par position Y.
    
    Cherche les mots contenant:
    - Col 1: "désignation" OU "composant" OU "offre"
    - Col 2: "spécification" OU "caractéristique" OU "technique"
    - Col 3: "proposition"
    
    Puis reconstruit les 3 colonnes basées sur leur position X.
    """
    if not words:
        return None
    
    # Chercher les mots clés
    norm_words = [
        {
            **w,
            'norm_text': normalize_text(w['text']),
            'lower_text': w['text'].lower()
        }
        for w in words
    ]
    
    # Identifiersles colonnes par mots-clés
    col1_keywords = ['designat', 'composant', 'offre']
    col2_keywords = ['specificat', 'caracteristic', 'technique', 'minimal']
    col3_keywords = ['proposition']
    
    col1_word = next((w for w in norm_words if any(kw in w['norm_text'] for kw in col1_keywords)), None)
    col2_word = next((w for w in norm_words if any(kw in w['norm_text'] for kw in col2_keywords)), None)
    col3_word = next((w for w in norm_words if any(kw in w['norm_text'] for kw in col3_keywords)), None)
    
    # Si les 3 mots-clés sont trouvés
    if not (col1_word and col2_word and col3_word):
        return None
    
    # Récupérer les Y de ces mots pour déterminer la zone en-tête
    header_y_max = max(col1_word['y'], col2_word['y'], col3_word['y']) + 100
    
    # Regrouper tous les mots de cette zone par colonne X
    header_words = [w for w in words if w['y'] < header_y_max]
    
    if not header_words:
        return None
    
    # Diviser en 3 par X
    img_width = max(w['x'] + w['width'] for w in words)
    third = img_width / 3
    
    col1_words = [w for w in header_words if w['x'] < third]
    col2_words = [w for w in header_words if third <= w['x'] < 2*third]
    col3_words = [w for w in header_words if w['x'] >= 2*third]
    
    headers = []
    boxes = []
    
    for col_words in [col1_words, col2_words, col3_words]:
        if col_words:
            text = ' '.join([w['text'] for w in sorted(col_words, key=lambda x: x['y'])])
            x1 = min(w['x'] for w in col_words)
            y1 = min(w['y'] for w in col_words)
            x2 = max(w['x'] + w['width'] for w in col_words)
            y2 = max(w['y'] + w['height'] for w in col_words)
            
            headers.append(text)
            boxes.append((x1, y1, x2, y2))
        else:
            headers.append("")
            boxes.append(None)
    
    return (headers, boxes)


def extract_column_content(
    words: List[Dict],
    col_box: Tuple,
    start_y: float
) -> List[str]:
    """
    Extrait TOUT le contenu d'une colonne.
    """
    if not col_box:
        return []
    
    x1, _, x2, _ = col_box
    col_center = (x1 + x2) / 2
    col_width = x2 - x1
    tolerance = col_width * 0.6
    
    # Mots dans cette colonne, après en-têtes
    col_words = [
        w for w in words
        if abs(w['x'] + w['width']/2 - col_center) <= tolerance
        and w['y'] >= start_y
    ]
    
    if not col_words:
        return []
    
    # Grouper par ligne (Y)
    col_words = sorted(col_words, key=lambda w: w['y'])
    
    rows = []
    row_threshold = 40
    current_row = [col_words[0]]
    
    for word in col_words[1:]:
        if abs(word['y'] - current_row[0]['y']) <= row_threshold:
            current_row.append(word)
        else:
            rows.append(current_row)
            current_row = [word]
    
    if current_row:
        rows.append(current_row)
    
    # Joindre par ligne
    result = []
    for row in rows:
        line = ' '.join([w['text'] for w in sorted(row, key=lambda w: w['x'])])
        if line.strip():
            result.append(line)
    
    return result


# ============================================================================
# EXTRACTION PRINCIPALE (à partir de pages_cibles.pdf)
# ============================================================================

def find_pages_cibles_pdf() -> Optional[Path]:
    """Recherche automatiquement pages_cibles.pdf."""
    # Chemins possibles
    possible_paths = [
        Path("data/output/pages_cibles.pdf"),
        Path("./data/output/pages_cibles.pdf"),
        Path("data\\output\\pages_cibles.pdf"),
    ]
    
    for p in possible_paths:
        if p.exists():
            return p
    
    return None


def extract_column2_from_cibles_pdf() -> List[Dict]:
    """
    ✅ Extraction à partir de pages_cibles.pdf
    
    - Charge les pages déjà sélectionnées
    - Valide en-têtes (Modèle 1 ou 2)
    - Extrait colonne 2
    - Pas de re-détection
    """
    
    # Chercher pages_cibles.pdf automatiquement
    pages_cibles_path = find_pages_cibles_pdf()
    
    if not pages_cibles_path:
        print("[ERROR] pages_cibles.pdf non trouvé")
        print("Cherché dans:")
        print("  - data/output/pages_cibles.pdf")
        print("  - ./data/output/pages_cibles.pdf")
        return []
    
    print(f"\n{'='*70}")
    print(f"EXTRACTION COLONNE 2 - À PARTIR DE pages_cibles.pdf")
    print(f"{'='*70}\n")
    print(f"Source: {pages_cibles_path}")
    
    doc = fitz.open(str(pages_cibles_path))
    print(f"Pages cibles: {doc.page_count}\n")
    print(f"{'='*70}\n")
    
    results = []
    
    # Traiter CHAQUE page de pages_cibles.pdf
    for page_num in range(doc.page_count):
        try:
            # Rendu + OCR
            img_rgb = render_page_hd(str(pages_cibles_path), page_num, dpi=300)
            img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
            
            words = ocr_page(img_gray)
            
            if not words or len(words) < 5:
                print(f"✗ Page {page_num + 1}: Pas de texte OCR")
                continue
            
            # Extraire en-têtes PAR MOTS-CLÉS (pas par position Y)
            header_info = extract_headers_by_keywords(words)
            
            if not header_info:
                print(f"✗ Page {page_num + 1}: En-têtes non trouvés")
                continue
            
            headers, boxes = header_info
            
            # Valider modèle
            model_match = detect_model(headers)
            
            if not model_match:
                print(f"✗ Page {page_num + 1}: En-têtes invalides (pas Modèle 1 ou 2)")
                print(f"  Trouvés: '{headers[0][:40]}...' / '{headers[1][:40]}...' / '{headers[2][:40]}...'")
                continue
            
            model_name, col2_idx = model_match
            col2_box = boxes[col2_idx]
            
            if not col2_box:
                print(f"✗ Page {page_num + 1}: Colonne 2 non trouvée")
                continue
            
            # Déterminer Y après en-têtes
            header_y_max = max(
                b[3] for b in boxes 
                if b is not None
            )
            start_y = header_y_max + 20
            
            # Extraire colonne 2 COMPLÈTEMENT
            col2_data = extract_column_content(words, col2_box, start_y)
            
            if not col2_data:
                print(f"✗ Page {page_num + 1}: Pas de contenu en colonne 2")
                continue
            
            # Résultat
            result_item = {
                'page': page_num + 1,
                'model': model_name,
                'headers': {
                    'col1': headers[0],
                    'col2': headers[1],
                    'col3': headers[2]
                },
                'column2_lines': col2_data
            }
            
            results.append(result_item)
            
            print(f"✓ Page {page_num + 1}: {len(col2_data):3d} lignes ({model_name})")
            
        except Exception as e:
            print(f"✗ Page {page_num + 1}: ERREUR - {str(e)[:50]}")
            continue
    
    doc.close()
    return results


# ============================================================================
# SAUVEGARDE ET AFFICHAGE
# ============================================================================

def save_results(results: List[Dict], output_path: str = "data/output/column2_from_cibles.json"):
    """Sauvegarde en JSON."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    return output_path


def print_summary(results: List[Dict]):
    """Affiche résumé + aperçu."""
    print(f"\n{'='*70}")
    print("RÉSUMÉ DE L'EXTRACTION")
    print(f"{'='*70}\n")
    
    if not results:
        print("❌ Aucun résultat")
        return
    
    total_pages = len(results)
    total_lines = sum(len(r['column2_lines']) for r in results)
    
    print(f"✅ Pages traitées: {total_pages}")
    print(f"✅ Total lignes extraites: {total_lines}")
    print(f"✅ Moyenne par page: {total_lines / total_pages:.1f}")
    
    # Compte par modèle
    models = {}
    for r in results:
        m = r['model']
        models[m] = models.get(m, 0) + 1
    
    print(f"\n📊 Distribution modèles:")
    for model, count in models.items():
        print(f"   {model}: {count} page(s)")
    
    # Aperçu
    print(f"\n{'='*70}")
    print("APERÇU (3 premières pages)")
    print(f"{'='*70}\n")
    
    for item in results[:3]:
        print(f"Page {item['page']} - {item['model']}")
        print(f"  En-têtes:")
        print(f"    Col 1: {item['headers']['col1'][:50]}")
        print(f"    Col 2: {item['headers']['col2'][:50]}")
        print(f"    Col 3: {item['headers']['col3'][:50]}")
        print(f"  Colonne 2 ({len(item['column2_lines'])} lignes):")
        for i, line in enumerate(item['column2_lines'][:5], 1):
            display = line if len(line) <= 60 else line[:57] + "..."
            print(f"    {i}. {display}")
        if len(item['column2_lines']) > 5:
            print(f"    ... et {len(item['column2_lines']) - 5} autres")
        print()


if __name__ == "__main__":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    # Exécuter
    results = extract_column2_from_cibles_pdf()
    
    # Sauvegarder
    if results:
        output_file = save_results(results)
        print(f"\n{'='*70}")
        print(f"✅ EXTRACTION RÉUSSIE")
        print(f"{'='*70}")
        print(f"\nFichier JSON: {output_file}")
        print_summary(results)
    else:
        print(f"\n{'='*70}")
        print(f"❌ EXTRACTION ÉCHOUÉE - Aucun résultat")
        print(f"{'='*70}\n")
