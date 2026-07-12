import unittest

from src.page_selector import select_target_pages


class DummyPage:
    def __init__(self, text: str):
        self._text = text

    def extract_text(self):
        return self._text


class DummyReader:
    def __init__(self, texts):
        self.pages = [DummyPage(text) for text in texts]


class PageSelectorTests(unittest.TestCase):
    def test_keeps_continuation_pages_without_headers(self):
        texts = [
            "Lot : Specification technique de l'offre\nDesignation Specification Proposition",
            "Produit A 10 5",
            "Produit B 12 7",
            "NB : note de continuation",
            "Produit C 15 8",
        ]

        selected = select_target_pages(DummyReader(texts), use_ocr=False)

        self.assertEqual(5, len(selected))

    def test_ignores_unrelated_tables_without_section_context(self):
        texts = [
            "Tableau administratif\nDesignation Quantite Prix",
            "Service A 10 5",
            "Service B 11 6",
        ]

        selected = select_target_pages(DummyReader(texts), use_ocr=False)

        self.assertEqual([], selected)



    def test_detects_ocr_header_without_designation(self):
        texts = [
            "specification proposition quantite 5 a preciser imprimante laser reseau",
            "webcam avec micro 10 100 1000 mbps garantie",
            "caracteristiques techmiques minimales propositions quaniite os reference vostue 3530 ordinateur portable",
        ]

        selected = select_target_pages(DummyReader(texts), use_ocr=False)

        self.assertEqual(3, len(selected))

    def test_excludes_supplier_datasheets_after_lot_tables(self):
        texts = [
            "Lot specification technique imprimante laser quantite 05 designation specification proposition",
            "kyoceradocumentsolutions fr kyocera couverture produit",
            "caracteristiques techniques informations generales technologie laser monochrome kyocera vitesse d impression 55 pages resolution 1200 dpi",
            "caracteristiques techmiques minimales propositions quaniite os reference vostue 3530 ordinateur portable",
            "caracteristiques de ordinateur vostro 15 3530 tableau 3 dimensions et poids description ordinateur",
            "tableau 4 processeur suite vitesse du processeur 1 90 ghz a 4 50 ghz",
        ]
        reader = DummyReader(texts)

        selected = select_target_pages(reader, use_ocr=False)
        selected_indices = [i + 1 for i, page in enumerate(reader.pages) if page in selected]

        self.assertEqual([1, 4], selected_indices)

if __name__ == "__main__":
    unittest.main()




