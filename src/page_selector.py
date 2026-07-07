import re
from pathlib import Path
from typing import Any, Callable, Optional


def _normalize(text: str) -> str:
    """Normalise le texte afin de rendre la détection plus robuste."""
    text = text.lower()
    text = text.replace("’", "'")
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


def _contains_any(text: str, options: list[str]) -> bool:
    return any(option in text for option in options)


def _contains_any_word(text: str, options: list[str]) -> bool:
    return any(re.search(rf"\b{re.escape(option)}\b", text) for option in options)


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


MEASURE_TOKENS = ["quantite", "quaniite", "quahtjte", "qte", "prix", "pu", "montant", "euro", "ht", "ttc"]
CONCEPT_TOKENS = ["proposition", "propositions", "specification", "composant", "offre"]
COLUMN_TOKENS = ["designation", "descriptif", "description"]

def _looks_like_procurement_admin_page(text: str) -> bool:
    """Repere les pages administratives de consultation qui listent les lots sans etre une reponse Lot."""
    if _contains_any(text, ["mini ccap", "miniccap", "cahier des charges", "modele de presentation de l offre financiere"]):
        return True

    if "soumissionnaire" in text and _contains_any(text, ["article", "offre financiere", "garantie d offre"]):
        return True

    return False

def _has_section_context(text: str) -> bool:
    """Vérifie qu'un texte évoque bien une section technique ciblée."""
    section_tokens = [
        "lot",
        "specification",
        "specification technique",
        "caracteristiques techniques minimales",
        "proposition",
        "propositions",
        "composants de l'offre",
        "composants de l offre",
        "offre",
        "technique",
        "techniques",
    ]
    column_tokens = [
        "designation",
        "descriptif",
        "description",
        "quantite",
        "quaniite",
        "quahtjte",
        "qte",
        "unite",
        "prix",
        "pu",
        "montant",
        "euro",
        "ht",
        "ttc",
        "proposition",
        "composant",
    ]

    has_section = _contains_any_word(text, section_tokens)
    has_columns = _contains_any_word(text, column_tokens)
    has_technical_title = _contains_any(text, ["lot", "specification", "caracteristiques techniques"])

    return has_section and has_columns and has_technical_title


def _has_table_header(text: str) -> bool:
    """Retourne True si la page semble être l'en-tête d'un tableau technique pertinent."""
    if _contains_any(text, ["tableau administratif", "tableau admin", "annexe", "formulaire", "resume", "schema"]):
        return False

    # Page 42: mini-CCAP administratif listant les lots/offres, pas une reponse technique Lot.
    if _looks_like_procurement_admin_page(text):
        return False

    has_column_group = _contains_any_word(text, COLUMN_TOKENS)
    has_measure_group = _contains_any_word(text, MEASURE_TOKENS)
    has_concept_group = _contains_any_word(text, CONCEPT_TOKENS)
    has_technical_group = _matches_any(
        text,
        [
            r"\blot(?:e)?\b",
            r"\bspecification(?:s)?(?: technique)?\b",
            r"\bcaracteristiques tech(?:n|m)iques(?: minimales)?\b",
            r"\bimprimante\b",
            r"\bscanner\b",
            r"\bordinateur\b",
            r"\bportable\b",
            r"\bmateriel\b",
        ],
    )

    if has_column_group and has_measure_group and has_concept_group:
        return True

    header_score = 0
    header_score += 2 if has_column_group else 0
    header_score += 2 if has_measure_group else 0
    header_score += 2 if has_concept_group else 0
    header_score += 1 if has_technical_group else 0
    header_score += 1 if _contains_any_word(text, ["tableau"]) else 0
    header_score += 1 if _contains_any(text, ["a preciser", "marque et modele"]) else 0

    # Pages 3/4: OCR peut perdre "designation"; les signaux quantite +
    # specification/proposition ou caracteristiques techniques restent fiables.
    if header_score >= 5 and has_measure_group and has_concept_group and has_technical_group:
        return True

    if not has_column_group:
        return False

    has_section = _contains_any_word(
        text,
        [
            "lot",
            "specification technique",
            "specification",
            "caracteristiques techniques minimales",
            "caracteristiques techniques",
            "offre",
            "composants",
            "imprimante",
            "scanner",
            "ordinateur",
            "portable",
            "materiel",
        ],
    )

    return has_section and (has_measure_group or has_concept_group)


def _looks_like_table_content(text: str) -> bool:
    """Retourne True si la page ressemble à un contenu de tableau technique."""
    row_tokens = [
        "designation",
        "descriptif",
        "description",
        "quantite",
        "quaniite",
        "quahtjte",
        "qte",
        "unite",
        "prix",
        "pu",
        "montant",
        "euro",
        "ht",
        "ttc",
        "specification",
        "proposition",
        "composant",
        "offre",
    ]

    if _contains_any(text, ["tableau administratif", "tableau admin", "annexe", "formulaire", "resume", "schema"]):
        return False

    # Page 42: mini-CCAP administratif listant les lots/offres, pas une reponse technique Lot.
    if _looks_like_procurement_admin_page(text):
        return False

    if _contains_any_word(text, row_tokens):
        return True

    for line in text.splitlines():
        if not line:
            continue

        numbers = re.findall(r"\d{1,4}", line)
        if len(numbers) < 2:
            continue

        if _contains_any_word(line, row_tokens):
            return True

    return False

def _has_supplier_document_marker(text: str) -> bool:
    """Repere les fiches/manuels fournisseur pour eviter d'ouvrir une table trop large."""
    return _contains_any(
        text,
        [
            "data sheet",
            "datasheet",
            "ditasheet",
            "fiche technique",
            "manuel du proprietaire",
            "dell technologies",
            "dell com support",
            "kyoceradocumentsolutions",
            "hp scanjet",
            "epson",
        ],
    )


def _looks_like_note_page(text: str) -> bool:
    normalized_text = _normalize(text)
    return bool(re.search(r"\bnb\s*[:\-]", normalized_text)) or "note de continuation" in normalized_text


def _looks_like_end_of_table(text: str) -> bool:
    """Retourne True si le texte indique une vraie fin de tableau."""
    if not _contains_any(text, ["nb", "nombre", "total", "montant", "quantite", "net a payer", "net a regler", "sous total"]):
        return False

    if re.search(r"\b(nb|nombre)\s*[:=]?\s*\d+\b", text):
        return True

    if re.search(r"\b(?:sous total|total(?: general| ttc| ht| net| hors taxe)?|montant total|net a payer|net a regler)\b.*\d", text):
        return True

    if re.search(r"\bquantite(?: totale)?\b.*\d", text):
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
    Analyse tout le PDF et renvoie les pages à conserver.
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

        if (
            len(text.splitlines()) <= 8
            and re.search(r"\d{1,4}", text)
            and not _contains_any(text, ["tableau administratif", "tableau admin", "annexe", "formulaire"])
        ):
            selected_pages.append(page)
            continue

        in_table = False

    return selected_pages












