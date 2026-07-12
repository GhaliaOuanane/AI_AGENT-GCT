"""
Module de sélection de pages robuste basé sur des critères structurels.
Cette version élimine les dépendances aux mots-clés spécifiques au profit
de critères généralisables : structure tabulaire, densité numérique, alignement.
"""

import re
from pathlib import Path
from typing import Any, Callable, Optional, List, Tuple


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


def _contains_any_word(text: str, options: list[str]) -> bool:
    """Vérifie si le texte contient au moins un des mots complets de la liste."""
    return any(re.search(rf"\b{re.escape(option)}\b", text) for option in options)


def _matches_any(text: str, patterns: list[str]) -> bool:
    """Vérifie si le texte correspond à au moins un des patterns regex."""
    return any(re.search(pattern, text) for pattern in patterns)


# ============================================================================
# CRITÈRES STRUCTURELS GÉNÉRIQUES (remplacement des mots-clés)
# ============================================================================

def _analyze_line_structure(text: str) -> dict:
    """
    Analyse la structure des lignes pour détecter des patterns tabulaires.
    
    Retourne un dictionnaire avec :
    - line_count: nombre de lignes non vides
    - avg_words_per_line: moyenne de mots par ligne
    - numeric_density: ratio de tokens numériques
    - lines_with_numbers: nombre de lignes contenant des nombres
    - regular_pattern_score: score de régularité (0-1)
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    if not lines:
        return {
            'line_count': 0,
            'avg_words_per_line': 0,
            'numeric_density': 0,
            'lines_with_numbers': 0,
            'regular_pattern_score': 0
        }
    
    total_words = 0
    total_tokens = 0
    numeric_tokens = 0
    lines_with_numbers = 0
    word_counts = []
    
    for line in lines:
        words = line.split()
        word_count = len(words)
        word_counts.append(word_count)
        total_words += word_count
        
        for word in words:
            total_tokens += 1
            if re.search(r'\d', word):
                numeric_tokens += 1
                
        if re.search(r'\d', line):
            lines_with_numbers += 1
    
    avg_words = total_words / len(lines) if lines else 0
    numeric_density = numeric_tokens / total_tokens if total_tokens > 0 else 0
    
    # Calcul de régularité : variance du nombre de mots par ligne
    # Une table a souvent des lignes de longueur similaire
    if len(word_counts) > 1:
        variance = sum((x - avg_words) ** 2 for x in word_counts) / len(word_counts)
        regularity = 1 / (1 + variance)  # Score entre 0 et 1
    else:
        regularity = 0
    
    return {
        'line_count': len(lines),
        'avg_words_per_line': avg_words,
        'numeric_density': numeric_density,
        'lines_with_numbers': lines_with_numbers,
        'regular_pattern_score': regularity
    }


def _detect_column_structure(text: str) -> dict:
    """
    Détecte la présence d'une structure en colonnes.
    
    Analyse :
    - Espacement régulier (alignement)
    - Répétition de patterns
    - Ratio lignes courtes vs longues
    
    Retourne :
    - has_column_pattern: True si structure en colonnes détectée
    - column_confidence: score de confiance (0-1)
    """
    lines = [line for line in text.splitlines() if line.strip()]
    
    if len(lines) < 3:
        return {'has_column_pattern': False, 'column_confidence': 0}
    
    # Détection de séparateurs potentiels (espaces multiples, tabulations)
    separator_counts = []
    for line in lines:
        # Compte les séquences de 2+ espaces (indicateur de colonnes)
        separators = len(re.findall(r'\s{2,}', line))
        separator_counts.append(separators)
    
    # Si plusieurs lignes ont un nombre similaire de séparateurs
    if separator_counts and max(separator_counts) > 0:
        avg_separators = sum(separator_counts) / len(separator_counts)
        consistent_separators = sum(1 for c in separator_counts if abs(c - avg_separators) <= 1)
        consistency_ratio = consistent_separators / len(separator_counts)
        
        if consistency_ratio > 0.6 and avg_separators >= 1:
            return {
                'has_column_pattern': True,
                'column_confidence': min(consistency_ratio, 1.0)
            }
    
    # Détection alternative : lignes avec patterns répétés (ex: mot nombre mot nombre)
    pattern_scores = []
    for line in lines:
        tokens = line.split()
        if len(tokens) >= 4:
            # Alterne mot/nombre ?
            alternation_score = 0
            for i in range(len(tokens) - 1):
                has_digit_curr = bool(re.search(r'\d', tokens[i]))
                has_digit_next = bool(re.search(r'\d', tokens[i + 1]))
                if has_digit_curr != has_digit_next:  # Alternance
                    alternation_score += 1
            pattern_scores.append(alternation_score / (len(tokens) - 1))
    
    if pattern_scores:
        avg_pattern = sum(pattern_scores) / len(pattern_scores)
        if avg_pattern > 0.3:  # Au moins 30% d'alternance
            return {
                'has_column_pattern': True,
                'column_confidence': min(avg_pattern, 1.0)
            }
    
    return {'has_column_pattern': False, 'column_confidence': 0}


def _calculate_data_to_prose_ratio(text: str) -> float:
    """
    Calcule le ratio entre contenu tabulaire et texte narratif.
    
    Un tableau a beaucoup de tokens courts et numériques.
    Un texte narratif a des phrases longues et peu de nombres.
    
    Retourne un score entre 0 (prose) et 1 (data).
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    if not lines:
        return 0
    
    short_lines = 0  # Lignes < 10 mots
    lines_with_numbers = 0
    lines_with_long_sentences = 0  # Lignes > 15 mots
    
    for line in lines:
        word_count = len(line.split())
        
        if word_count < 10:
            short_lines += 1
        if word_count > 15:
            lines_with_long_sentences += 1
        if re.search(r'\d', line):
            lines_with_numbers += 1
    
    total = len(lines)
    
    # Calcul du score
    data_score = (
        (short_lines / total) * 0.4 +          # Lignes courtes
        (lines_with_numbers / total) * 0.6     # Présence de nombres
    )
    
    # Pénalité si beaucoup de lignes longues (prose)
    prose_penalty = (lines_with_long_sentences / total) * 0.5
    
    return max(0, min(1, data_score - prose_penalty))


def _is_administrative_prose(text: str) -> bool:
    """
    Détecte si le texte ressemble à de la prose administrative plutôt qu'à un tableau.
    
    Critères structurels :
    - Longueur moyenne des lignes élevée
    - Peu de nombres
    - Densité de texte narratif élevée
    """
    structure = _analyze_line_structure(text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    # Si peu de contenu, pas administrative
    if structure['line_count'] < 3:
        return False
    
    # Critère 1: Si moyenne de mots par ligne très élevée et peu de nombres = prose
    if structure['avg_words_per_line'] > 15 and structure['numeric_density'] < 0.1:
        return True
    
    # Critère 2: Si très peu de lignes contiennent des nombres (< 25% des lignes)
    lines_with_numbers_ratio = structure['lines_with_numbers'] / structure['line_count']
    if lines_with_numbers_ratio < 0.25 and structure['line_count'] > 6:
        return True
    
    # Critère 3: Compter les LIGNES (pas les séquences) qui ressemblent à de la prose
    # Une ligne de prose : >12 mots ET pas de nombre
    prose_lines = 0
    for line in lines:
        word_count = len(line.split())
        has_number = bool(re.search(r'\d', line))
        if word_count > 12 and not has_number:
            prose_lines += 1
    
    # Si plus de 50% des lignes sont de la prose
    if len(lines) > 0 and prose_lines / len(lines) > 0.5:
        return True
    
    return False


def _is_supplier_datasheet(text: str) -> bool:
    """
    Détecte les fiches techniques fournisseurs en utilisant des critères structurels.
    
    Caractéristiques des datasheets :
    - Format liste (lignes courtes)
    - Paires clé-valeur
    - Haute densité d'informations techniques
    - URLs, emails, références produits
    - Peu de structure tabulaire répétée
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    if len(lines) < 5:
        return False
    
    # Détection de URLs (pattern plus large après normalisation)
    has_urls = bool(re.search(r'www|\.com|\.fr|http', text))
    
    # Détection de format clé-valeur (mot : valeur)
    key_value_lines = sum(1 for line in lines if ':' in line or '=' in line)
    key_value_ratio = key_value_lines / len(lines)
    
    # Détection de références techniques (patterns alphanumérique)
    tech_refs = len(re.findall(r'\b[A-Z]{2,}[0-9]{2,}|\b[A-Z][0-9]+[A-Z0-9]*\b', text))
    
    # Détection de listes à puces ou numérotées
    bullet_lines = sum(1 for line in lines if re.match(r'^[\-\*•]\s|^\d+[\.\)]\s', line))
    bullet_ratio = bullet_lines / len(lines)
    
    # Détection de longues descriptions (caractéristique de datasheet)
    long_description_lines = sum(1 for line in lines if len(line.split()) > 12)
    long_desc_ratio = long_description_lines / len(lines)
    
    # Score composite (seuils ajustés)
    datasheet_score = 0
    
    if has_urls:
        datasheet_score += 0.4  # Augmenté : URLs sont un fort indicateur
    if key_value_ratio > 0.3:  # Abaissé de 0.4 à 0.3
        datasheet_score += 0.3
    if tech_refs > 3:  # Abaissé de 5 à 3
        datasheet_score += 0.2
    if bullet_ratio > 0.2:  # Abaissé de 0.3 à 0.2
        datasheet_score += 0.2
    if long_desc_ratio > 0.3:  # Nouveau critère
        datasheet_score += 0.2
    
    return datasheet_score >= 0.6  # Augmenté de 0.5 à 0.6 pour éviter faux positifs


# ============================================================================
# FONCTIONS DE DÉTECTION REFACTORISÉES
# ============================================================================

def _has_table_header(text: str) -> bool:
    """
    Détecte un en-tête de tableau basé sur des critères structurels.
    
    AVANT (fragile) : Exclusion par mots-clés ("tableau administratif", "annexe")
    APRÈS (robuste) : Analyse structurelle
    
    Critères positifs pour un en-tête :
    - Présence de colonnes conceptuelles (générique : tokens courts répétés)
    - Structure alignée suggérant des en-têtes
    - Présence modérée de contenu (ni trop verbeux ni vide)
    
    Critères négatifs :
    - Prose administrative (lignes longues, narratif)
    - Fiche technique fournisseur (URLs, clé-valeur)
    """
    # Exclusion structurelle : prose administrative
    if _is_administrative_prose(text):
        return False
    
    # Exclusion structurelle : datasheet fournisseur
    if _is_supplier_datasheet(text):
        return False
    
    structure = _analyze_line_structure(text)
    columns = _detect_column_structure(text)
    data_ratio = _calculate_data_to_prose_ratio(text)
    
    # Critères positifs (seuils ajustés)
    has_enough_content = 3 <= structure['line_count'] <= 50
    has_data_format = data_ratio > 0.2  # Abaissé de 0.3 à 0.2
    has_column_structure = columns['column_confidence'] > 0.2  # Abaissé de 0.4 à 0.2
    moderate_numeric_density = 0.05 <= structure['numeric_density'] <= 0.8  # Élargi
    has_numbers_present = structure['lines_with_numbers'] >= 2
    
    # En-tête détecté si plusieurs critères positifs
    positive_score = (
        (1 if has_enough_content else 0) +
        (1 if has_data_format else 0) +
        (1 if has_column_structure else 0) +
        (1 if moderate_numeric_density else 0) +
        (1 if has_numbers_present else 0)
    )
    
    return positive_score >= 3


def _looks_like_table_content(text: str) -> bool:
    """
    Détecte le contenu d'un tableau (suite d'en-tête).
    
    AVANT (fragile) : Recherche de mots-clés + exclusions
    APRÈS (robuste) : Analyse de la densité de données
    
    Critères :
    - Haute densité numérique
    - Lignes courtes et régulières
    - Pas de prose administrative
    """
    if _is_administrative_prose(text):
        return False
    
    if _is_supplier_datasheet(text):
        return False
    
    structure = _analyze_line_structure(text)
    data_ratio = _calculate_data_to_prose_ratio(text)
    
    # Contenu tabulaire : beaucoup de données, peu de prose (seuils ajustés)
    is_data_dense = data_ratio > 0.25  # Abaissé de 0.4 à 0.25
    has_numbers = structure['numeric_density'] > 0.08  # Abaissé de 0.15 à 0.08
    reasonable_length = 2 <= structure['line_count'] <= 100
    has_some_numbers = structure['lines_with_numbers'] >= 1
    
    return (is_data_dense or has_numbers) and reasonable_length and has_some_numbers


def _looks_like_note_page(text: str) -> bool:
    """
    Détecte une page de notes/continuation.
    Garde la logique existante (pattern "nb:" est structurel, pas un mot-clé fragile).
    """
    normalized_text = _normalize(text)
    return bool(re.search(r'\bnb\s*[:\-]', normalized_text))


def _looks_like_end_of_table(text: str) -> bool:
    """
    Détecte la fin d'un tableau.
    
    AVANT (fragile) : Mots-clés "total", "montant total", "net à payer"
    APRÈS (robuste) : Pattern structurel de ligne de synthèse
    
    Critères :
    - Ligne isolée avec nombre significatif
    - Apparition d'un nombre en fin de texte
    - Réduction soudaine de la densité de lignes
    """
    structure = _analyze_line_structure(text)
    
    # Si très peu de lignes avec un nombre => possiblement ligne de total
    if structure['line_count'] <= 3 and structure['lines_with_numbers'] >= 1:
        # Recherche pattern : nombre important (> 3 chiffres)
        if re.search(r'\b\d{3,}(?:[.,]\d+)?\b', text):
            return True
    
    # Pattern : mot suivi de nombre en fin de ligne (total-like)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[-3:]:  # Vérifie les 3 dernières lignes
        # Pattern: un ou deux mots suivis d'un nombre
        if re.search(r'\b\w+(?:\s+\w+)?\s*[:\-]?\s*\d+', line):
            return True
    
    return False


def _page_text(
    page: Any,
    page_number: int,
    pdf_path: Optional[Path],
    use_ocr: bool,
    ocr_func: Optional[Callable[..., str]],
    poppler_path: Optional[str],
) -> str:
    """Extrait le texte d'une page (avec OCR si nécessaire)."""
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
    Sélectionne les pages de tableaux pertinents.
    
    REFACTORISATION MAJEURE :
    - Suppression de toutes les vérifications par mots-clés
    - Remplacement par analyse structurelle
    - Logique de machine à états conservée (in_table)
    """
    selected_pages = []
    in_table = False

    for page_number, page in enumerate(reader.pages):
        raw_text = _page_text(page, page_number, pdf_path, use_ocr, ocr_func, poppler_path)
        text = _normalize(raw_text)

        page_has_header = _has_table_header(text)
        page_is_table_content = _looks_like_table_content(text)
        page_is_note = _looks_like_note_page(text)
        page_is_end = _looks_like_end_of_table(text)

        if page_has_header:
            in_table = True
            selected_pages.append(page)
            continue

        if not in_table:
            continue

        if page_is_note or page_is_table_content or page_is_end:
            selected_pages.append(page)
            if page_is_end:
                in_table = False
            continue

        # Vérification finale : page courte avec contenu numérique
        # AVANT : exclusion par mots-clés "tableau administratif"
        # APRÈS : exclusion structurelle (prose administrative)
        structure = _analyze_line_structure(text)
        if (
            structure['line_count'] <= 8
            and structure['numeric_density'] > 0.1
            and not _is_administrative_prose(text)
        ):
            selected_pages.append(page)
            continue

        in_table = False

    return selected_pages
