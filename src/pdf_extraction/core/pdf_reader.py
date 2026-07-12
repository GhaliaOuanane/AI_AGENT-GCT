from pathlib import Path
from typing import Iterator

from pypdf import PdfReader
from pypdf.errors import PdfReadError


def open_pdf(path: str | Path) -> PdfReader:
    """Open a PDF file and return a PdfReader object."""
    pdf_path = Path(path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    try:
        return PdfReader(pdf_path)
    except PdfReadError as e:
        raise ValueError(f"Corrupted or invalid PDF: {pdf_path}") from e


def count_pages(reader: PdfReader) -> int:
    """Return the number of pages in the opened PDF."""
    return len(reader.pages)


def iter_pages(reader: PdfReader) -> Iterator:
    """Yield each page object from the opened PDF."""
    for page in reader.pages:
        yield page
