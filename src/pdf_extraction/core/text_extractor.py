from pathlib import Path
from typing import List, Optional

from pypdf import PdfReader

import ocr_reader


def extract_page_texts(
    reader: PdfReader,
    pdf_path: Path,
    use_ocr: bool = False,
    poppler_path: Optional[str] = None,
) -> List[str]:
    """Extract text from every page of the PDF, using OCR when necessary."""
    page_texts: List[str] = []

    for page_number, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if not text.strip() and use_ocr:
            text = ocr_reader.ocr_page(
                pdf_path,
                page_number,
                poppler_path=poppler_path,
            )

        page_texts.append(text.replace("\r", "\n"))

    return page_texts
