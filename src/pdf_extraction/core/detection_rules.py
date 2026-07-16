"""
Module de règles de détection consolidées (source unique de vérité).

Principe:
- Évaluation unique des règles de détection par page
- Résultat réutilisable par page_selector.py et column_extractor.py
- Zéro duplication de logique
"""

from dataclasses import dataclass
from typing import Dict, Optional, List
import re


@dataclass
class PageContext:
    """
    Contexte d'une page après évaluation des règles de détection.
    
    Ce contexte est créé UNE FOIS par page et réutilisé par tous les modules.
    """
    page_num: int
    has_valid_header: bool
    detected_model: str  # "modele_1", "modele_1_variant", "modele_2", "unknown"
    column_count: int
    detected_headers: Dict[str, str]  # {role: detected_name}
    has_nb_keyword: bool
    has_lot_keyword: bool
    normalized_text: str
    
    def __repr__(self):
        return f"PageContext(page={self.page_num}, model={self.detected_model}, valid={self.has_valid_header})"


# ============================================================================
# CONFIGURATION DES MODÈLES D'EN-TÊTE
# ============================================================================

# Modèle 1: Désignation | Spécification | Proposition
MODELE_1_PATTERNS = {
    "designation": r"\bdes[il1]gnat[io0ln]+\b",
    "specification": r"\bspec[il1][fj][il1][cf]at[io0ln]+\b",
    "proposition": r"\bpropos[il1]t[io0lnj]+s?\b"
}

# Modèle 1 Variante: Désignation | Exigé ou à préciser | Proposition
MODELE_1_VARIANT_PATTERNS = {
    "designation": r"\bdes[il1]gnat[io0ln]+\b",
    # Pattern plus strict: chercher explicitement "exige" AVANT de chercher specification
    "specification": r"\bexige\b",
    "proposition": r"\bpropos[il1]t[io0lnj]+s?\b"
}

# Modèle 2: Composants de l'offre | Caractéristiques techniques minimales | Proposition
MODELE_2_PATTERNS = {
    "designation": r"\bcomposants?\b.*\b(?:de\s+l['\s]?|de\s+la?\s+)?offre\b",
    "specification": r"\bcaracteristiques?\b.*\btechniques?\b.*\bminimales?\b",
    "proposition": r"\b(?:proposition|proposit[io]on|propositjons?)\b"
}

# Noms canoniques pour la normalisation (utilisé par quality_analyzer)
CANONICAL_HEADER_NAMES = {
    "modele_1": {
        "designation": "Désignation",
        "specification": "Spécification",
        "proposition": "Proposition"
    },
    "modele_1_variant": {
        "designation": "Désignation",
        "specification": "Exigé ou à préciser",
        "proposition": "Proposition"
    },
    "modele_2": {
        "designation": "Composants de l'offre",
        "specification": "Caractéristiques techniques minimales",
        "proposition": "Proposition"
    }
}


# ============================================================================
# NORMALISATION DE TEXTE
# ============================================================================

def _normalize_text(text: str) -> str:
    """
    Normalise le texte pour la détection (identique à page_selector.py).
    
    Args:
        text: Texte brut
    
    Returns:
        Texte normalisé (lowercase, sans accents, sans ponctuation)
    """
    text = text.lower()
    text = text.replace("'", "'")
    text = text.replace("œ", "oe")
    text = text.replace("æ", "ae")

    replacements = {
        "é": "e", "è": "e", "ê": "e",
        "à": "a", "â": "a",
        "ù": "u", "û": "u",
        "ô": "o",
        "î": "i", "ï": "i",
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


# ============================================================================
# DÉTECTION DES MODÈLES D'EN-TÊTE
# ============================================================================

def _detect_columns_in_text(normalized_text: str, patterns: Dict[str, str]) -> Dict[str, bool]:
    """
    Détecte la présence des colonnes selon les patterns.
    
    Args:
        normalized_text: Texte normalisé
        patterns: Dict {role: regex_pattern}
    
    Returns:
        Dict {role: found}
    """
    results = {}
    for role, pattern in patterns.items():
        results[role] = bool(re.search(pattern, normalized_text, re.IGNORECASE))
    return results


def _matches_model_1(normalized_text: str) -> bool:
    """Vérifie si le texte correspond au Modèle 1 (au moins 2/3 colonnes)."""
    detected = _detect_columns_in_text(normalized_text, MODELE_1_PATTERNS)
    return sum(detected.values()) >= 2


def _matches_model_1_variant(normalized_text: str) -> bool:
    """Vérifie si le texte correspond au Modèle 1 Variante (au moins 2/3 colonnes)."""
    detected = _detect_columns_in_text(normalized_text, MODELE_1_VARIANT_PATTERNS)
    return sum(detected.values()) >= 2


def _matches_model_2(normalized_text: str) -> bool:
    """Vérifie si le texte correspond au Modèle 2 (3/3 colonnes)."""
    detected = _detect_columns_in_text(normalized_text, MODELE_2_PATTERNS)
    return all(detected.values())


def _extract_detected_headers(text: str, normalized_text: str, model: str) -> Dict[str, str]:
    """
    Extrait les noms d'en-têtes détectés dans le texte original.
    
    Args:
        text: Texte original (non normalisé)
        normalized_text: Texte normalisé
        model: Modèle détecté
    
    Returns:
        Dict {role: detected_name} avec noms normalisés
    """
    # Pour l'instant, utiliser les noms canoniques
    # Une extraction plus fine peut être ajoutée si nécessaire
    canonical = CANONICAL_HEADER_NAMES.get(model, {})
    
    return {
        "designation": canonical.get("designation", "Désignation"),
        "specification": canonical.get("specification", "Spécification"),
        "proposition": canonical.get("proposition", "Proposition")
    }


# ============================================================================
# DÉTECTION DE MOTS-CLÉS
# ============================================================================

def _has_keyword_nb(normalized_text: str) -> bool:
    """Détecte la présence du mot-clé 'NB' ou 'Note'."""
    # Après normalisation, "NB:" devient "nb" (sans :)
    return bool(re.search(r"\bnb\b", normalized_text, re.IGNORECASE)) or \
           bool(re.search(r"\bnote\b", normalized_text, re.IGNORECASE))


def _has_keyword_lot(normalized_text: str) -> bool:
    """Détecte la présence du mot-clé 'LOT'."""
    return bool(re.search(r"\blot\s+\d+", normalized_text, re.IGNORECASE))


# ============================================================================
# FONCTION PRINCIPALE D'ÉVALUATION
# ============================================================================

def evaluate_page(page, page_num: int, pdf_path=None) -> PageContext:
    """
    Évalue TOUTES les règles de détection pour une page (appelé UNE SEULE FOIS).
    
    Args:
        page: Page PyMuPDF ou objet page avec .get_text()
        page_num: Numéro de page (0-indexed)
        pdf_path: Chemin du PDF (optionnel, pour debug)
    
    Returns:
        PageContext avec tous les résultats de détection
    """
    # Extraction et normalisation du texte
    try:
        raw_text = page.get_text() if hasattr(page, 'get_text') else str(page)
    except Exception:
        raw_text = ""
    
    normalized_text = _normalize_text(raw_text)
    
    # Détection du modèle d'en-tête
    # Ordre: tester la variante D'ABORD car plus spécifique ("exige" est unique)
    # puis modele_1 standard, puis modele_2
    detected_model = "unknown"
    has_valid_header = False
    
    # Test spécifique pour variant: chercher UNIQUEMENT "exige", pas "specification"
    has_exige = bool(re.search(r"\bexige\b", normalized_text, re.IGNORECASE))
    has_specification_word = bool(re.search(r"\bspec[il1][fj][il1][cf]at[io0ln]+\b", normalized_text, re.IGNORECASE))
    
    if has_exige and _matches_model_1_variant(normalized_text):
        detected_model = "modele_1_variant"
        has_valid_header = True
    elif has_specification_word and _matches_model_1(normalized_text):
        detected_model = "modele_1"
        has_valid_header = True
    elif _matches_model_2(normalized_text):
        detected_model = "modele_2"
        has_valid_header = True
    
    # Extraction des noms d'en-têtes détectés
    detected_headers = _extract_detected_headers(raw_text, normalized_text, detected_model)
    
    # Détection des mots-clés
    has_nb = _has_keyword_nb(normalized_text)
    has_lot = _has_keyword_lot(normalized_text)
    
    # Construction du contexte
    return PageContext(
        page_num=page_num,
        has_valid_header=has_valid_header,
        detected_model=detected_model,
        column_count=3,  # Toujours 3 colonnes dans nos modèles
        detected_headers=detected_headers,
        has_nb_keyword=has_nb,
        has_lot_keyword=has_lot,
        normalized_text=normalized_text
    )


def looks_like_table_content(normalized_text: str) -> bool:
    """
    Détecte si le texte ressemble à du contenu de tableau (pour pages suivant un header).
    
    TRÈS STRICT pour éviter les faux positifs.
    
    Args:
        normalized_text: Texte normalisé
    
    Returns:
        True si ressemble à du contenu de tableau
    """
    line_count = len([line for line in normalized_text.splitlines() if line.strip()])
    
    # Critère 1: Page TRÈS courte avec contenu numérique
    # MAIS exclure immédiatement si prose administrative détectée
    
    # Exclure AVANT tout les documents administratifs
    is_admin_doc = bool(re.search(
        r"\b(?:article\s+\d+|signature|cachet|page\s+\d+|chapitre\s+\d+|table\s+des\s+matieres|manuel|guide|installation\s+du|configuration\s+du|deplacement\s+du|protocole\s+de|modalites|stipule|conditions\s+generales|specifie|precise)\b",
        normalized_text,
        re.IGNORECASE
    ))
    
    if is_admin_doc:
        return False
    
    is_short_numeric = line_count <= 8 and bool(re.search(r"\d", normalized_text))
    if is_short_numeric:
        return True
    
    # Critère 2: PRÉSENCE EXPLICITE de mots-clés de tableau cible
    has_model1_keywords = bool(re.search(
        r"\b(?:specification|designation|exige|a\s+preciser)\b",
        normalized_text,
        re.IGNORECASE
    ))
    
    has_model2_keywords = bool(re.search(
        r"\b(?:caracteristiques?|propositions?)\b",
        normalized_text,
        re.IGNORECASE
    ))
    
    has_numbers = bool(re.search(r"\d", normalized_text))
    
    # Accepter si : (Model1 ou Model2) ET chiffres
    if (has_model1_keywords or has_model2_keywords) and has_numbers:
        return True
    
    return False


def looks_like_note_page(normalized_text: str) -> bool:
    """
    Détecte une page de notes ou continuation (pattern 'NB' ou 'Note').
    
    Args:
        normalized_text: Texte normalisé (sans ponctuation)
    
    Returns:
        True si page de notes
    """
    # Après normalisation, "NB:" devient "nb" (sans :)
    return bool(re.search(r"\bnb\b", normalized_text, re.IGNORECASE)) or \
           bool(re.search(r"\bnote\b", normalized_text, re.IGNORECASE))
