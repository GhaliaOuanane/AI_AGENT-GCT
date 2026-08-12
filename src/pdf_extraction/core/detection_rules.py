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

def evaluate_page(page, page_num: int, pdf_path=None, ocr_text: Optional[str] = None) -> PageContext:
    """
    Évalue TOUTES les règles de détection pour une page (appelé UNE SEULE FOIS).
    
    LOGIQUE ROBUSTE ET CONTEXTUELLE:
    - Page cible = présence de "lot n°X" en début de page/section avec structure tabulaire
    - "NB" seul n'est PAS un critère suffisant (trop de bruit OCR)
    - Position du "lot" dans le texte est critique (premiers 20% du texte)
    
    Args:
        page: Page PyMuPDF ou objet page avec .get_text()
        page_num: Numéro de page (0-indexed)
        pdf_path: Chemin du PDF (optionnel, pour debug)
        ocr_text: Texte OCR pré-extrait (prioritaire sur page.get_text() si fourni)
    
    Returns:
        PageContext avec tous les résultats de détection
    """
    # Extraction et normalisation du texte
    if ocr_text is not None:
        raw_text = ocr_text
    else:
        try:
            raw_text = page.get_text() if hasattr(page, 'get_text') else str(page)
        except Exception:
            raw_text = ""
    
    normalized_text = _normalize_text(raw_text)
    
    # =====================================================================
    # CRITÈRE PRINCIPAL: LOT en début de page/section
    # =====================================================================
    
    # Pattern "lot" avec numéro obligatoire
    # Variantes supportées:
    # - "lot 1", "lot 2" (espace simple)
    # - "lot n°1", "lot n 01" (avec n ou n°)
    # - "lot:1", "lot : 1" (avec deux-points)
    # - "lot5", "LOT5" (collé, sans espace)
    # - "lots specification" (cas particulier: OCR confond "5" avec "S", devient "LOTS : Spécification...")
    #   Après normalisation, "LOTS :" devient "lots" donc on cherche "lots specification"
    # Évite faux positifs: "lotissement5" grâce à \b (frontière de mot)
    
    # Pattern principal: lot + numéro
    lot_pattern = re.compile(r"\blot\s*(?:n\s*°?\s*)?:?\s*(\d+)", re.IGNORECASE)
    lot_match = lot_pattern.search(normalized_text)
    
    # Pattern alternatif: "lots specification" (erreur OCR fréquente: "LOT5:" → "LOTS:")
    # Après normalisation, les deux-points sont supprimés, donc chercher "lots" + "specification"
    # STRICT: Évite "lots de matériels" car jamais suivi de "specification"
    lots_spec_pattern = re.compile(r"\blots\s+specification\b", re.IGNORECASE)
    lots_match = lots_spec_pattern.search(normalized_text) if not lot_match else None
    
    has_lot_in_header = False
    lot_number = None
    lot_position_percent = 100.0
    
    if lot_match:
        lot_number = int(lot_match.group(1))
        # Position relative dans le texte (0-100%)
        lot_position_percent = (lot_match.start() / max(len(normalized_text), 1)) * 100
        
        # Accepter le "lot" UNIQUEMENT s'il apparaît dans les premiers 20% du texte
        # Cela élimine les mentions incidentes comme "lot 3" dans un article sur les paiements
        has_lot_in_header = lot_position_percent <= 20.0
    
    elif lots_match:
        # Cas "LOTS :" détecté (probablement erreur OCR de "LOT5:")
        # Appliquer les mêmes critères de position
        lot_position_percent = (lots_match.start() / max(len(normalized_text), 1)) * 100
        has_lot_in_header = lot_position_percent <= 20.0
        # Pas de numéro extrait, mais présence validée
        lot_number = None
    
    # =====================================================================
    # CRITÈRES SECONDAIRES: Présence d'indicateurs de structure tabulaire
    # =====================================================================
    
    # Mots-clés de colonnes typiques (détection INDIVIDUELLE, pas en paire)
    # Tolérant au bruit OCR: un seul mot-clé suffit si lot valide en tête
    column_keywords = [
        r"\bdesignation\b",
        r"\bspecification\b",
        r"\bproposition\b",
        r"\bcaracteristiques?\s+techniques?\b",
        r"\bcomposants?\s+(de\s+)?l\s*offre\b",
        r"\bexige\b",  # "Exigé ou à préciser"
        r"\ba\s+preciser\b"
    ]
    
    # Compter combien de mots-clés sont présents
    keyword_count = sum(
        1 for pattern in column_keywords
        if re.search(pattern, normalized_text, re.IGNORECASE)
    )
    
    # Critères alternatifs pour détecter une structure tabulaire:
    # Option A: Au moins 1 mot-clé de colonne SI lot valide en début (lot = garde-fou)
    #           OU au moins 2 mots-clés si pas de lot (plus strict sans lot)
    # Option B: Présence de séparateurs répétés (pipes, multiples espaces)
    
    # Si lot en début de section détecté, 1 seul mot-clé suffit (tolérance OCR)
    # Sinon, exiger au moins 2 mots-clés (plus strict sans contexte lot)
    min_keywords_required = 1 if has_lot_in_header else 2
    has_sufficient_keywords = keyword_count >= min_keywords_required
    
    # Détection de séparateurs de colonnes (pipes, ou 3+ espaces consécutifs répétés)
    has_separators = (
        normalized_text.count('|') >= 3 or  # Au moins 3 pipes dans la page
        len(re.findall(r'\s{3,}', normalized_text)) >= 5  # Au moins 5 zones de 3+ espaces
    )
    
    # Structure tabulaire détectée si:
    # - Mots-clés suffisants selon contexte (1 si lot, 2 sinon), OU
    # - Présence de séparateurs visuels répétés
    has_table_structure = has_sufficient_keywords or has_separators
    
    # =====================================================================
    # NB: Détecté mais NON utilisé comme critère de décision
    # =====================================================================
    
    nb_pattern = re.compile(r"(?<![a-z0-9])n\.?\s?b\.?\s*:?(?![a-z0-9])", re.IGNORECASE)
    nb_match = nb_pattern.search(normalized_text)
    has_nb = bool(nb_match)
    
    # =====================================================================
    # DÉCISION FINALE
    # =====================================================================
    
    # Une page est cible SI:
    # 1. "lot n°X" apparaît dans les premiers 20% du texte (début de section)
    # 2. ET présence d'au moins un indicateur de structure tabulaire
    
    has_valid_header = has_lot_in_header and has_table_structure
    
    # =====================================================================
    # LOGS DE DEBUG
    # =====================================================================
    
    print(f"\n[DEBUG] ========== Page {page_num + 1} ==========")
    
    if lot_match:
        print(f"  - Lot detecte: {lot_match.group()} (n {lot_number})")
        print(f"    Position: {lot_position_percent:.1f}% du texte")
        print(f"    En debut de section: {'OUI' if has_lot_in_header else 'NON (trop tard)'}")
    elif lots_match:
        print(f"  - Lot detecte: 'lots specification' (erreur OCR LOT5)")
        print(f"    Position: {lot_position_percent:.1f}% du texte")
        print(f"    En debut de section: {'OUI' if has_lot_in_header else 'NON (trop tard)'}")
    else:
        print(f"  - Lot detecte: NON")
    
    print(f"  - Structure tabulaire: {'OUI' if has_table_structure else 'NON'}")
    if has_table_structure:
        print(f"    Mots-cles colonnes trouves: {keyword_count}")
        print(f"    Separateurs detectes: {'OUI' if has_separators else 'NON'}")
    
    if has_nb:
        print(f"  - NB detecte: OUI (pos {nb_match.start()}) [INFO SEULEMENT]")
    
    if has_valid_header:
        print(f"  >>> Page {page_num + 1} ACCEPTEE comme page cible")
        print(f"      Raison: Lot {lot_number} en debut + structure tabulaire")
    else:
        raisons = []
        if not lot_match:
            raisons.append("pas de 'lot nX'")
        elif not has_lot_in_header:
            raisons.append(f"'lot' trop tard dans le texte ({lot_position_percent:.0f}%)")
        if not has_table_structure:
            raisons.append(f"pas de structure tabulaire (mots-cles:{keyword_count}, separateurs:{has_separators})")
        print(f"  XXX Page {page_num + 1} REJETEE")
        print(f"      Raison: {' + '.join(raisons)}")
    
    if not has_valid_header and (lot_match or has_nb):
        # Preview pour debug des rejets avec indices
        text_preview = normalized_text[:300].replace('\n', ' | ')
        print(f"  - Preview: {text_preview}...")
    
    # Headers génériques
    detected_headers = {
        "designation": "Colonne 1",
        "specification": "Colonne 2",
        "proposition": "Colonne 3"
    }
    
    # Construction du contexte
    return PageContext(
        page_num=page_num,
        has_valid_header=has_valid_header,
        detected_model="generic_3col",
        column_count=3,
        detected_headers=detected_headers,
        has_nb_keyword=has_nb,
        has_lot_keyword=bool(lot_match),  # True si lot détecté, même si position incorrecte
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
    
    # Exclure AVANT tout les documents administratifs ET fiches techniques fournisseur
    is_admin_doc = bool(re.search(
        r"\b(?:article\s+\d+|signature|cachet|page\s+\d+|chapitre\s+\d+|table\s+des\s+matieres|manuel|guide|installation\s+du|configuration\s+du|deplacement\s+du|protocole\s+de|modalites|stipule|conditions\s+generales|specifie|precise)\b",
        normalized_text,
        re.IGNORECASE
    ))
    
    # Détecter fiches techniques fournisseur (marques commerciales, noms de modèles)
    is_vendor_spec_sheet = bool(re.search(
        r"\b(?:kyocera|ecosys|hp|scanjet|dell|lenovo|asus|acer|samsung|epson|canon|brother|marque|modele|famille\s+de\s+produit|code\s+produit|nom\s+du\s+produit|fiche\s+technique)\b",
        normalized_text,
        re.IGNORECASE
    ))
    
    if is_admin_doc or is_vendor_spec_sheet:
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
