from pathlib import Path
from typing import Optional

import pytesseract
from pdf2image import convert_from_path


def _configure_tesseract(tesseract_cmd: Optional[str] = None) -> None:
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        return

    default_windows = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if default_windows.exists():
        pytesseract.pytesseract.tesseract_cmd = str(default_windows)


def ocr_page(
    pdf_path: str | Path,
    page_number: int,
    dpi: int = 300,
    tesseract_cmd: Optional[str] = None,
    poppler_path: Optional[str] = None,
) -> str:
    """Convert a PDF page to an image and return OCR text."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found for OCR: {pdf_path}")

    _configure_tesseract(tesseract_cmd)

    image_list = convert_from_path(
        str(pdf_path),
        dpi=dpi,
        first_page=page_number + 1,
        last_page=page_number + 1,
        poppler_path=poppler_path,
    )

    if not image_list:
        return ""

    return pytesseract.image_to_string(image_list[0], lang="fra+eng")
