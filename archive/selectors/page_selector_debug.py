import re
from page_selector import (
    _normalize,
    _has_table_header,
    _looks_like_table_content,
    _looks_like_note_page,
    _looks_like_end_of_table,
    _page_text,
)


def select_target_pages_debug(
    reader,
    pdf_path=None,
    use_ocr=False,
    ocr_func=None,
    poppler_path=None,
    log_path="debug_pages.txt",
):
    selected_pages = []
    in_table = False

    with open(log_path, "w", encoding="utf-8") as log:
        for page_number, page in enumerate(reader.pages):
            raw_text = _page_text(page, page_number, pdf_path, use_ocr, ocr_func, poppler_path)
            text = _normalize(raw_text)

            page_has_header = _has_table_header(text)
            page_is_table_content = _looks_like_table_content(text)
            page_is_note = _looks_like_note_page(text)
            page_is_end = _looks_like_end_of_table(text)

            log.write(f"\n{'='*70}\n")
            log.write(f"PAGE {page_number + 1}\n")
            log.write(f"  longueur texte brut     : {len(raw_text)} caracteres\n")
            log.write(f"  longueur texte normalise: {len(text)} caracteres\n")
            log.write(f"  in_table (avant)        : {in_table}\n")
            log.write(f"  has_header              : {page_has_header}\n")
            log.write(f"  is_table_content        : {page_is_table_content}\n")
            log.write(f"  is_note                 : {page_is_note}\n")
            log.write(f"  is_end                  : {page_is_end}\n")
            log.write(f"  --- extrait du texte normalise (300 premiers car.) ---\n")
            log.write(f"  {text[:300]!r}\n")

            if page_has_header:
                in_table = True
                selected_pages.append(page)
                log.write(f"  => AJOUTEE (header detecte)\n")
                continue


            if not in_table:
                log.write(f"  => IGNOREE (pas de header, hors table)\n")
                continue

            if page_is_note or page_is_table_content or page_is_end:
                selected_pages.append(page)
                log.write(f"  => AJOUTEE (contenu de table / note / fin)\n")
                if page_is_end:
                    in_table = False
                continue

            if (
                len(text.splitlines()) <= 8
                and re.search(r"\d{1,4}", text)
                and not any(k in text for k in ["tableau administratif", "tableau admin", "annexe", "formulaire"])
            ):
                selected_pages.append(page)
                log.write(f"  => AJOUTEE (fallback courte page numerique)\n")
                continue

            in_table = False
            log.write(f"  => IGNOREE (sortie de table)\n")

    print(f"\nLog detaille ecrit dans : {log_path}")
    print(f"Total pages selectionnees : {len(selected_pages)} / {len(reader.pages)}")
    return selected_pages


