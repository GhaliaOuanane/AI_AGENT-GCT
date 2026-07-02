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

    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())


def _contains_any(text: str, options: list[str]) -> bool:
    return any(option in text for option in options)


def _has_table_header(text: str) -> bool:
    """Retourne True si le texte contient les titres de colonne attendus."""
    if not _contains_any(text, ["designation", "descriptif", "designation"]):
        return False

    spec_options = [
        "specification",
        "specifications",
        "caracteristiques techniques minimales",
        "caracteristique technique minimale",
        "caracteristiques techniques minimale",
    ]

    comp_options = [
        "composants de l offre",
        "composants de l'offre",
        "propositions",
        "proposition",
    ]

    return _contains_any(text, spec_options) and _contains_any(text, comp_options)


def _looks_like_end_of_table(text: str) -> bool:
    """Retourne True si le texte indique la fin d'un ensemble de pages cibles."""
    return any(token in text for token in ["nb :", "nb:", "nombre :", "nombre:", "total", "montant", "quantite"])


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
    page_has_header = False

    for page_number, page in enumerate(reader.pages):
        raw_text = _page_text(page, page_number, pdf_path, use_ocr, ocr_func, poppler_path)
        text = _normalize(raw_text)

        if _has_table_header(text):
            page_has_header = True
            in_table = True

        if in_table:
            selected_pages.append(page)

        if in_table and _looks_like_end_of_table(text):
            in_table = False

    return selected_pages
