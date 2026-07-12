from pathlib import Path
from typing import Any, Iterable

from pypdf import PdfWriter


def write_selected_pages(pages: Iterable[Any], output_path: str | Path = "pages_cibles.pdf") -> Path:
    """Create the final PDF from selected pages."""
    writer = PdfWriter()
    for page in pages:
        writer.add_page(page)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("wb") as output_file:
        writer.write(output_file)

    return output_path
