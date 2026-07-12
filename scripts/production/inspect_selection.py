from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from pdf_reader import open_pdf
from page_selector import (
    select_target_pages,
    _normalize,
    _has_table_header,
    _looks_like_table_content,
    _looks_like_note_page,
    _looks_like_end_of_table,
)
from text_extractor import extract_page_texts

pdf_path = Path('data/input/BRAIN INFORMATIQUE_16052025101905.PDF')
reader = open_pdf(pdf_path)
poppler_path = r'D:\AI_AGENT GCT\tools\poppler-26.02.0\Library\bin'
page_texts = extract_page_texts(reader=reader, pdf_path=pdf_path, use_ocr=True, poppler_path=poppler_path)
selected = select_target_pages(reader, pdf_path=pdf_path, use_ocr=True, poppler_path=poppler_path)
selected_indices = [i + 1 for i, p in enumerate(reader.pages) if p in selected]
print('selected indices:', selected_indices)
print('total pages:', len(reader.pages))
print('')
for i, text in enumerate(page_texts, start=1):
    norm = _normalize(text)
    print('PAGE', i)
    print('  selected:', i in selected_indices)
    print('  len:', len(text))
    print('  header:', _has_table_header(norm))
    print('  content:', _looks_like_table_content(norm))
    print('  note:', _looks_like_note_page(norm))
    print('  end:', _looks_like_end_of_table(norm))
    print('  preview:', repr(norm[:400]))
    print('')
