"""
Tests unitaires pour detection_rules.py
"""

import unittest
from unittest.mock import Mock

from src.pdf_extraction.core.detection_rules import (
    evaluate_page,
    looks_like_table_content,
    looks_like_note_page,
    PageContext,
    _normalize_text
)


class TestDetectionRules(unittest.TestCase):
    """Tests du module de règles de détection."""
    
    def test_normalize_text(self):
        """Test: la normalisation de texte fonctionne correctement."""
        text = "Désignation | Spécification | Proposition"
        normalized = _normalize_text(text)
        
        self.assertIn("designation", normalized)
        self.assertIn("specification", normalized)
        self.assertIn("proposition", normalized)
        self.assertNotIn("é", normalized)
    
    def test_single_evaluation_per_page(self):
        """Test: evaluate_page est appelé une seule fois par page."""
        # Créer une page mock
        mock_page = Mock()
        mock_page.get_text.return_value = "Désignation | Spécification | Proposition\nContenu du tableau"
        
        # Appeler evaluate_page
        context = evaluate_page(mock_page, 0)
        
        # Vérifier que get_text n'est appelé qu'une fois
        self.assertEqual(mock_page.get_text.call_count, 1)
        
        # Vérifier le résultat
        self.assertIsInstance(context, PageContext)
        self.assertEqual(context.page_num, 0)
    
    def test_page_context_reuse(self):
        """Test: le PageContext contient toutes les informations nécessaires."""
        mock_page = Mock()
        mock_page.get_text.return_value = "Désignation | Spécification | Proposition\nLOT 1\nNB: remarque"
        
        context = evaluate_page(mock_page, 5)
        
        # Vérifier que le context contient toutes les données
        self.assertEqual(context.page_num, 5)
        self.assertTrue(context.has_valid_header)
        self.assertIn(context.detected_model, ["modele_1", "modele_1_variant"])
        self.assertEqual(context.column_count, 3)
        self.assertIn("designation", context.detected_headers)
        self.assertIn("specification", context.detected_headers)
        self.assertIn("proposition", context.detected_headers)
        self.assertTrue(context.has_lot_keyword)
        self.assertTrue(context.has_nb_keyword)
        self.assertIsInstance(context.normalized_text, str)
    
    def test_model_detection_accuracy(self):
        """Test: détection correcte des 3 modèles."""
        # Modèle 1
        mock_page1 = Mock()
        mock_page1.get_text.return_value = "Désignation | Spécification | Proposition"
        context1 = evaluate_page(mock_page1, 0)
        self.assertEqual(context1.detected_model, "modele_1")
        self.assertTrue(context1.has_valid_header)
        
        # Modèle 1 Variante
        mock_page2 = Mock()
        mock_page2.get_text.return_value = "Désignation | Exigé ou à préciser | Proposition"
        context2 = evaluate_page(mock_page2, 0)
        self.assertEqual(context2.detected_model, "modele_1_variant")
        self.assertTrue(context2.has_valid_header)
        
        # Modèle 2
        mock_page3 = Mock()
        mock_page3.get_text.return_value = "Composants de l'offre | Caractéristiques techniques minimales | Proposition"
        context3 = evaluate_page(mock_page3, 0)
        self.assertEqual(context3.detected_model, "modele_2")
        self.assertTrue(context3.has_valid_header)
        
        # Pas de modèle
        mock_page4 = Mock()
        mock_page4.get_text.return_value = "Texte quelconque sans en-tête"
        context4 = evaluate_page(mock_page4, 0)
        self.assertEqual(context4.detected_model, "unknown")
        self.assertFalse(context4.has_valid_header)
    
    def test_looks_like_table_content(self):
        """Test: détection de contenu tabulaire."""
        # Cas 1: Page courte avec nombres
        short_numeric = "12\n34\n56"
        self.assertTrue(looks_like_table_content(_normalize_text(short_numeric)))
        
        # Cas 2: Mots-clés + nombres
        with_keywords = "specification: valeur 123"
        self.assertTrue(looks_like_table_content(_normalize_text(with_keywords)))
        
        # Cas 3: Prose administrative (devrait être exclue par pattern "article X")
        admin_text = "L'article 5 du chapitre 2 page 10 specifie les modalites"
        self.assertFalse(looks_like_table_content(_normalize_text(admin_text)))
        
        # Cas 4: Texte sans nombres
        no_numbers = "texte sans chiffres"
        self.assertFalse(looks_like_table_content(_normalize_text(no_numbers)))
    
    def test_looks_like_note_page(self):
        """Test: détection de pages de notes."""
        # Avec NB:
        with_nb = "NB: remarque importante"
        self.assertTrue(looks_like_note_page(_normalize_text(with_nb)))
        
        # Avec Note:
        with_note = "Note: information complémentaire"
        self.assertTrue(looks_like_note_page(_normalize_text(with_note)))
        
        # Sans marqueur
        without_marker = "texte normal"
        self.assertFalse(looks_like_note_page(_normalize_text(without_marker)))
    
    def test_detected_headers_normalized(self):
        """Test: les headers détectés sont normalisés vers valeurs canoniques."""
        mock_page = Mock()
        mock_page.get_text.return_value = "Désignation | Exigé ou à préciser | Proposition"
        
        context = evaluate_page(mock_page, 0)
        
        # Vérifier que les headers sont normalisés
        self.assertEqual(context.detected_headers["specification"], "Exigé ou à préciser")
        self.assertEqual(context.detected_headers["designation"], "Désignation")
        self.assertEqual(context.detected_headers["proposition"], "Proposition")
    
    def test_keyword_detection(self):
        """Test: détection des mots-clés NB et LOT."""
        # NB
        mock_nb = Mock()
        mock_nb.get_text.return_value = "Contenu\nNB: remarque"
        context_nb = evaluate_page(mock_nb, 0)
        self.assertTrue(context_nb.has_nb_keyword)
        
        # LOT
        mock_lot = Mock()
        mock_lot.get_text.return_value = "LOT 3\nContenu"
        context_lot = evaluate_page(mock_lot, 0)
        self.assertTrue(context_lot.has_lot_keyword)
        
        # Aucun
        mock_none = Mock()
        mock_none.get_text.return_value = "Contenu normal"
        context_none = evaluate_page(mock_none, 0)
        self.assertFalse(context_none.has_nb_keyword)
        self.assertFalse(context_none.has_lot_keyword)


if __name__ == "__main__":
    unittest.main()
