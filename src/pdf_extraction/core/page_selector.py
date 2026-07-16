"""
Module de sélection de pages basé sur la détection directe d'en-têtes de tableaux.

Utilise detection_rules.py comme source unique de vérité pour les règles.
"""

import re
from pathlib import Path
from typing import Any, Callable, Optional, List, Tuple

from pdf_extraction.core.detection_rules import (
    evaluate_page,
    looks_like_table_content,
    looks_like_note_page,
    PageContext
)


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
    - Spécification (ou variantes: "Exigé ou à préciser", "Exigé", "À préciser")
    - Proposition
    
    Retourne True si AU MOINS 2 des 3 colonnes sont présentes.
    
    Rationale : L'OCR peut oublier ou mal reconnaître une colonne.
    Si 2 colonnes sur 3 sont présentes (en particulier "Spécification" + "Proposition"),
    c'est hautement probablement une page cible de tableau.
    
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
    # Nouvelles variantes: "Exigé ou à préciser", "Exigé", "à préciser"
    has_specification = bool(re.search(
        r"\bspec[il1][fj][il1][cf]at[io0ln]+\b|"
        r"\bexige\s+(ou\s+)?a\s+preciser\b|"
        r"\bexige\b|"
        r"\ba\s+preciser\b",
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
    
    # Accepter si AU MOINS 2 colonnes détectées
    column_count = sum([has_designation, has_specification, has_proposition])
    return column_count >= 2


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
    
    TRÈS STRICT pour éviter les faux positifs :
    - Doit être court (≤8 lignes) ET avoir des nombres
    - OU doit contenir EXPLICITEMENT les mots-clés de colonnes cibles
      * Model 1: "specification" ou "designation"
      * Model 2: "caracteristiques" ou "propositions" (ou leurs variantes)
    
    Ne capture PAS les brochures, manuels, ou documents administratifs.
    """
    line_count = len([line for line in text.splitlines() if line.strip()])
    
    # Critère 1 : Page TRÈS courte avec contenu numérique
    # (probable fin ou continuation de tableau)
    is_short_numeric = line_count <= 8 and bool(re.search(r"\d", text))
    if is_short_numeric:
        return True
    
    # Critère 2 : PRÉSENCE EXPLICITE de mots-clés de tableau cible
    # Model 1: "specification" ou "designation" ou "exigé" ou "à préciser"
    # Model 2: "caracteristiques" ou "propositions"
    has_model1_keywords = bool(re.search(
        r"\b(?:specification|designation|exige|a\s+preciser)\b",
        text,
        re.IGNORECASE
    ))
    
    has_model2_keywords = bool(re.search(
        r"\b(?:caracteristiques?|propositions?)\b",
        text,
        re.IGNORECASE
    ))
    
    has_numbers = bool(re.search(r"\d", text))
    
    # Exclure SEULEMENT les documents administratifs clairs
    # (pas juste la mention d'un mot, mais une vraie indication de document)
    is_admin_doc = bool(re.search(
        r"\b(?:article|signature|cachet|remargue|remarque|page\s+\d|chapitre|table\s+des\s+matieres|manuel|installation\s+du|configuration\s+du|deplacement\s+du|protocole\s+de)\b",
        text,
        re.IGNORECASE
    ))
    
    # Accepter si : (Model1 ou Model2) ET chiffres ET pas exclu
    if (has_model1_keywords or has_model2_keywords) and has_numbers and not is_admin_doc:
        return True
    
    return False


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
        from pdf_extraction.core import ocr_reader
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
) -> List[Tuple[Any, PageContext]]:
    """
    Sélectionne les pages cibles contenant des tableaux de spécifications.
    
    Utilise detection_rules.evaluate_page() comme source unique de vérité.
    
    Args:
        reader: Lecteur PDF (pypdf.PdfReader)
        pdf_path: Chemin du fichier PDF
        use_ocr: Si True, utilise l'OCR pour l'extraction de texte
        ocr_func: Fonction OCR personnalisée (optionnel)
        poppler_path: Chemin vers Poppler (pour OCR)
    
    Returns:
        Liste de tuples (page, PageContext) pour les pages sélectionnées
    """
    if use_ocr and ocr_func is None:
        from pdf_extraction.core.ocr_reader import ocr_page
        ocr_func = ocr_page
    
    selected_pages = []
    in_table_sequence = False
    
    for page_num, page in enumerate(reader.pages):
        # ÉVALUATION UNIQUE DES RÈGLES (source de vérité)
        context = evaluate_page(page, page_num, pdf_path)
        
        # Cas 1: En-tête de tableau détecté
        if context.has_valid_header:
            selected_pages.append((page, context))
            in_table_sequence = True
            continue
        
        # Cas 2: Dans une séquence de tableau (continuation)
        if in_table_sequence:
            # Vérifier si c'est du contenu de tableau ou page de notes
            if looks_like_table_content(context.normalized_text) or looks_like_note_page(context.normalized_text):
                selected_pages.append((page, context))
                continue
            
            # Fin de la séquence de tableau
            in_table_sequence = False
    
    return selected_pages
