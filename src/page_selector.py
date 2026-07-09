"""
Module de sélection de pages basé sur la détection directe d'en-têtes de tableaux.

Détecte deux modèles d'en-tête spécifiques :
- Modèle 1 : Désignation | Spécification | Proposition
- Modèle 2 : Composants de l'offre | Caractéristiques techniques minimales | Proposition

Une fois un en-tête détecté, capture les pages suivantes jusqu'à la fin du tableau.
"""

import re
from pathlib import Path
from typing import Any, Callable, Optional


def _normalize(text: str) -> str:
    """Normalise le texte afin de rendre la détection plus robuste."""
    text = text.lower()
    text = text.replace("'", "'")
    text = text.replace("œ", "oe")
    text = text.replace("æ", "ae")

    replacements = {
        "é": "e",
        "è": "e",
        "ê": "e",
        "à": "a",
        "â": "a",
        "ù": "u",
        "û": "u",
        "ô": "o",
        "î": "i",
        "ï": "i",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"[^a-z0-9\s\n]", " ", text)
    normalized_lines = []
    for line in text.splitlines():
        cleaned = " ".join(line.split())
        if cleaned:
            normalized_lines.append(cleaned)
    return "\n".join(normalized_lines)


def _matches_header_model_1(text: str) -> bool:
    """
    Détecte le Modèle 1 d'en-tête de tableau :
    - Désignation
    - Spécification
    - Proposition
    
    Retourne True si les trois colonnes sont présentes.
    Tolère les variations OCR et la casse.
    """
    # Recherche de "designation" (ou variations OCR)
    # Tolère: designatlon, designat1on, desiynation, etc.
    has_designation = bool(re.search(
        r"\bdes[il1]gnat[io0ln]+\b",
        text,
        re.IGNORECASE
    ))
    
    # Recherche de "specification" (ou variations)
    # Tolère: specificatlon, specifjcation, spec1fication, etc.
    has_specification = bool(re.search(
        r"\bspec[il1][fj][il1][cf]at[io0ln]+\b",
        text,
        re.IGNORECASE
    ))
    
    # Recherche de "proposition" (ou variations)
    # Tolère: propositlon, propositjon, proposit1on, etc.
    has_proposition = bool(re.search(
        r"\bpropos[il1]t[io0lnj]+s?\b",
        text,
        re.IGNORECASE
    ))
    
    return has_designation and has_specification and has_proposition


def _matches_header_model_2(text: str) -> bool:
    """
    Détecte le Modèle 2 d'en-tête de tableau :
    - Composants de l'offre
    - Caractéristiques techniques minimales
    - Proposition
    
    Retourne True si les trois colonnes sont présentes.
    Tolère les variations OCR et la casse.
    """
    # Recherche de "composants de l'offre" (ou variations)
    has_composants = bool(re.search(
        r"\bcomposants?\b.*\b(?:de\s+l['\s]?|de\s+la?\s+)?offre\b",
        text,
        re.IGNORECASE
    ))
    
    # Recherche de "caractéristiques techniques minimales" (ou variations)
    has_caracteristiques = bool(re.search(
        r"\bcaracteristiques?\b.*\btechniques?\b.*\bminimales?\b",
        text,
        re.IGNORECASE
    ))
    
    # Recherche de "proposition" (ou variations)
    has_proposition = bool(re.search(
        r"\b(?:proposition|proposit[io]on|propositjons?)\b",
        text,
        re.IGNORECASE
    ))
    
    return has_composants and has_caracteristiques and has_proposition


def _has_table_header(text: str) -> bool:
    """
    Détection directe d'en-tête de tableau.
    
    Retourne True si la page contient l'un des deux modèles d'en-tête :
    - Modèle 1 : Désignation | Spécification | Proposition
    - Modèle 2 : Composants de l'offre | Caractéristiques techniques minimales | Proposition
    
    Aucune logique d'exclusion : détection positive uniquement.
    """
    return _matches_header_model_1(text) or _matches_header_model_2(text)


def _looks_like_table_content(text: str) -> bool:
    """
    Détecte le contenu de tableau (pages suivant un en-tête détecté).
    
    Critères simples :
    - Présence de mots liés aux spécifications techniques
    - Présence de valeurs numériques
    - Format tabulaire (lignes avec plusieurs tokens)
    
    Aucune logique d'exclusion.
    """
    # Vérifier la présence de contenu technique/tabulaire
    has_technical_content = bool(re.search(
        r"\b(?:specification|proposition|quantite|prix|montant|marque|modele|type|capacite|vitesse|resolution)\b",
        text,
        re.IGNORECASE
    ))
    
    # Vérifier la présence de nombres (caractéristique de tableau de spécifications)
    has_numbers = bool(re.search(r"\d", text))
    
    # Vérifier qu'il y a plusieurs lignes (pas juste un titre isolé)
    line_count = len([line for line in text.splitlines() if line.strip()])
    
    return has_technical_content and has_numbers and line_count >= 2


def _looks_like_note_page(text: str) -> bool:
    """
    Détecte une page de notes ou continuation.
    
    Recherche le pattern "NB:" ou "note de continuation".
    """
    return bool(re.search(r"\bnb\s*[:\-]", text, re.IGNORECASE)) or "note de continuation" in text.lower()


def _looks_like_end_of_table(text: str) -> bool:
    """
    Détecte une page de fin de tableau.
    
    Critères simples :
    - Présence de mots indicateurs de totalisation
    - Format court (peu de lignes)
    - Présence de nombres
    """
    # Indicateurs de fin (total, nombre, etc.)
    has_end_marker = bool(re.search(
        r"\b(?:total|nb|nombre|montant\s+total|quantite\s+totale)\b",
        text,
        re.IGNORECASE
    ))
    
    # Page courte
    line_count = len([line for line in text.splitlines() if line.strip()])
    is_short = line_count <= 5
    
    # Présence de nombre
    has_number = bool(re.search(r"\d", text))
    
    return has_end_marker and is_short and has_number


def _page_text(
    page: Any,
    page_number: int,
    pdf_path: Optional[Path],
    use_ocr: bool,
    ocr_func: Optional[Callable[..., str]],
    poppler_path: Optional[str],
) -> str:
    """
    Extrait le texte d'une page PDF.
    
    Utilise l'extraction directe si disponible, sinon l'OCR.
    """
    text = page.extract_text() or ""
    if text.strip():
        return text

    if not use_ocr:
        return ""

    if pdf_path is None:
        raise ValueError("pdf_path is required when use_ocr=True")

    if ocr_func is None:
        import ocr_reader
        ocr_func = ocr_reader.ocr_page

    return ocr_func(
        pdf_path,
        page_number,
        poppler_path=poppler_path,
    )


def select_target_pages(
    reader,
    pdf_path: Optional[str | Path] = None,
    use_ocr: bool = False,
    ocr_func: Optional[Callable[..., str]] = None,
    poppler_path: Optional[str] = None,
):
    """
    Sélectionne les pages contenant les tableaux ciblés.
    
    Logique de détection directe :
    1. Parcourt chaque page du PDF
    2. Recherche les en-têtes correspondant aux modèles 1 ou 2
    3. Une fois un en-tête détecté, capture les pages suivantes jusqu'à la fin du tableau
    
    Modèle 1 : Désignation | Spécification | Proposition
    Modèle 2 : Composants de l'offre | Caractéristiques techniques minimales | Proposition
    
    Args:
        reader: Lecteur PDF (pypdf.PdfReader)
        pdf_path: Chemin vers le fichier PDF (requis si use_ocr=True)
        use_ocr: Si True, utilise l'OCR pour les pages sans texte
        ocr_func: Fonction OCR personnalisée (optionnel)
        poppler_path: Chemin vers les binaires Poppler (pour OCR)
    
    Returns:
        Liste des pages sélectionnées
    """
    selected_pages = []
    in_table = False

    for page_number, page in enumerate(reader.pages):
        raw_text = _page_text(page, page_number, pdf_path, use_ocr, ocr_func, poppler_path)
        text = _normalize(raw_text)

        # Détection directe d'en-tête (Modèle 1 ou Modèle 2)
        page_has_header = _has_table_header(text)
        
        if page_has_header:
            # En-tête détecté : début de tableau
            in_table = True
            selected_pages.append(page)
            continue

        # Si on est dans un tableau, continuer à capturer les pages
        if in_table:
            # Détection de contenu tabulaire
            page_is_table_content = _looks_like_table_content(text)
            
            # Détection de page de notes
            page_is_note = _looks_like_note_page(text)
            
            # Détection de fin de tableau
            page_is_end = _looks_like_end_of_table(text)
            
            # Page courte avec contenu numérique (probable continuation)
            line_count = len([line for line in text.splitlines() if line.strip()])
            is_short_numeric = line_count <= 8 and bool(re.search(r"\d", text))
            
            # Capturer la page si elle fait partie du tableau
            if page_is_note or page_is_table_content or page_is_end or is_short_numeric:
                selected_pages.append(page)
                
                # Si fin détectée, sortir du tableau
                if page_is_end:
                    in_table = False
                continue
            
            # Page ne correspond à aucun critère : fin du tableau
            in_table = False

    return selected_pages
