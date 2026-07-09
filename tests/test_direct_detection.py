"""
Tests de validation de la détection directe d'en-têtes.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from page_selector import (
    _normalize,
    _matches_header_model_1,
    _matches_header_model_2,
    _has_table_header,
    _looks_like_table_content,
    _looks_like_end_of_table
)


class TestHeaderModel1Detection(unittest.TestCase):
    """Tests de détection du Modèle 1 : Désignation | Spécification | Proposition"""
    
    def test_perfect_model_1(self):
        """Test avec en-tête parfait Modèle 1."""
        text = """
        Désignation    Spécification    Proposition
        Imprimante     Laser A4         EPSON ABC
        """
        normalized = _normalize(text)
        self.assertTrue(_matches_header_model_1(normalized))
        self.assertTrue(_has_table_header(normalized))
    
    def test_model_1_with_ocr_errors(self):
        """Test avec erreurs OCR typiques."""
        text = """
        Designatlon    Speclfication    Propositjon
        Imprimante     Laser A4         EPSON ABC
        """
        normalized = _normalize(text)
        self.assertTrue(_matches_header_model_1(normalized))
    
    def test_model_1_case_insensitive(self):
        """Test insensible à la casse."""
        text = """
        DESIGNATION    SPECIFICATION    PROPOSITION
        """
        normalized = _normalize(text)
        self.assertTrue(_matches_header_model_1(normalized))
    
    def test_model_1_incomplete(self):
        """Test avec en-tête incomplet (devrait échouer)."""
        text = """
        Désignation    Spécification
        """
        normalized = _normalize(text)
        self.assertFalse(_matches_header_model_1(normalized))


class TestHeaderModel2Detection(unittest.TestCase):
    """Tests de détection du Modèle 2 : Composants de l'offre | Caractéristiques techniques minimales | Proposition"""
    
    def test_perfect_model_2(self):
        """Test avec en-tête parfait Modèle 2."""
        text = """
        Composants de l'offre    Caractéristiques techniques minimales    Proposition
        Ordinateur              Intel i7, 16 GB RAM                      Dell XPS
        """
        normalized = _normalize(text)
        self.assertTrue(_matches_header_model_2(normalized))
        self.assertTrue(_has_table_header(normalized))
    
    def test_model_2_variations(self):
        """Test avec variations d'écriture."""
        # Variation 1 : "composants de l'offre"
        text1 = "Composants de l'offre Caracteristiques techniques minimales Proposition"
        self.assertTrue(_matches_header_model_2(_normalize(text1)))
        
        # Variation 2 : "composants offre" (sans "de l'")
        text2 = "Composants offre Caracteristiques techniques minimales Proposition"
        self.assertTrue(_matches_header_model_2(_normalize(text2)))
        
        # Variation 3 : "composant" (singulier)
        text3 = "Composant de l'offre Caracteristique technique minimale Proposition"
        self.assertTrue(_matches_header_model_2(_normalize(text3)))
    
    def test_model_2_incomplete(self):
        """Test avec en-tête incomplet (devrait échouer)."""
        text = """
        Composants de l'offre    Caractéristiques techniques
        """
        normalized = _normalize(text)
        self.assertFalse(_matches_header_model_2(normalized))


class TestTableContentDetection(unittest.TestCase):
    """Tests de détection de contenu tabulaire."""
    
    def test_technical_content_with_numbers(self):
        """Test avec contenu technique et nombres."""
        text = """
        Processeur Intel Core i7
        Mémoire 16 Go
        Vitesse 3.5 GHz
        """
        normalized = _normalize(text)
        self.assertTrue(_looks_like_table_content(normalized))
    
    def test_no_numbers(self):
        """Test sans nombres (devrait échouer)."""
        text = """
        Processeur Intel Core
        Mémoire DDR
        """
        normalized = _normalize(text)
        self.assertFalse(_looks_like_table_content(normalized))
    
    def test_single_line(self):
        """Test avec une seule ligne (devrait échouer)."""
        text = "Processeur Intel 7"
        normalized = _normalize(text)
        self.assertFalse(_looks_like_table_content(normalized))


class TestEndOfTableDetection(unittest.TestCase):
    """Tests de détection de fin de tableau."""
    
    def test_total_with_number(self):
        """Test avec indicateur 'total' et nombre."""
        text = "Total : 25000"
        normalized = _normalize(text)
        self.assertTrue(_looks_like_end_of_table(normalized))
    
    def test_nb_with_number(self):
        """Test avec indicateur 'NB' et nombre."""
        text = "NB : 15"
        normalized = _normalize(text)
        self.assertTrue(_looks_like_end_of_table(normalized))
    
    def test_long_page_with_total(self):
        """Test avec page longue (devrait échouer)."""
        text = "\n".join(["Ligne " + str(i) for i in range(10)]) + "\nTotal : 100"
        normalized = _normalize(text)
        self.assertFalse(_looks_like_end_of_table(normalized))


class TestRegressionPrevention(unittest.TestCase):
    """Tests pour éviter les régressions."""
    
    def test_real_example_page_3(self):
        """Test avec un exemple réel de page 3 (Modèle 1)."""
        text = """
        LOT 1 : Acquisition d'une Imprimante Laser Réseau Grand. Quantité : 5.
        
        Désignation    Spécification                    Proposition
        
        Marque et Modèle         À préciser             KYOCERA EcoSys
        Technologie d'impression Laser monochrome       Laser
        Résolution               1200 x 1200 dpi        1200 DPI
        Vitesse                  55 pages par minute    55 ppm
        """
        normalized = _normalize(text)
        self.assertTrue(_has_table_header(normalized),
                       "La page 3 du document réel devrait être détectée")
    
    def test_real_example_page_4(self):
        """Test avec un exemple réel de page 4 (Modèle 2)."""
        text = """
        LOT 2 : Ordinateurs portables. Quantité : 05
        
        Composants de l'offre    Caractéristiques techniques minimales    Proposition
        
        Processeur central       Intel Core i7 12ème génération min       i7-1255U
        Mémoire centrale         16 GO min                                 16 GB DDR4
        Disque dur               512 GO min                                512 GB SSD
        """
        normalized = _normalize(text)
        self.assertTrue(_has_table_header(normalized),
                       "La page 4 du document réel devrait être détectée")


if __name__ == '__main__':
    # Lancer les tests avec verbosité
    unittest.main(verbosity=2)
