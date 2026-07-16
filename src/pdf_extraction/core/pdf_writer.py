from pathlib import Path
from typing import Any, Iterable, Tuple, Union

from pypdf import PdfWriter


def write_selected_pages(pages: Iterable[Union[Any, Tuple[Any, Any]]], output_path: str | Path = "pages_cibles.pdf") -> Path:
    """
    Create the final PDF from selected pages.
    
    Args:
        pages: Iterable of pages or tuples (page, context)
        output_path: Output PDF path
    
    Returns:
        Path to created PDF
    """
    writer = PdfWriter()
    
    for item in pages:
        # Gérer à la fois l'ancien format (page seule) et le nouveau (page, context)
        if isinstance(item, tuple):
            page, context = item
        else:
            page = item
        
        writer.add_page(page)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("wb") as output_file:
        writer.write(output_file)

    return output_path
