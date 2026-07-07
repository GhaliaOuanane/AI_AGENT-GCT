"""
Tests de validation de la refactorisation robuste.
Vérifie que les nouvelles fonctions structurelles fonctionnent correctement.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from page_selector_robust import (
    _analyze_line_structure,
    _detect_column_structure,
    _calculate_data_to_prose_ratio,
    _is_administrative_prose,
    _is_supplier_datasheet,
    _has_table_header,
    _looks_like_table_content,
    _looks_like_end_of_table,
    _normalize
)


class TestStructuralAnalysis(unittest.TestCase):
    """Tests des fonctions d'analyse structurelle."""
    
    def test_table_structure_detection(self):
        """Test : détection de structure tabulaire."""
        table_text = """
designation    quantite    prix
imprimante     5           1200
scanner        3           800
ordinateur     10          1500
"""
        structure = _analyze_line_structure(_normalize(table_text))
        
        self.assertGreater(structure['numeric_density'], 0.2)
        self.assertGreater(structure['lines_with_numbers'], 2)
        self.assertGreater(structure['line_count'], 3)
    
    def test_prose_vs_data_distinction(self):
        """Test : distinction entre prose administrative et données."""
        prose = """
Cet article définit les conditions générales de la consultation.
Les soumissionnaires doivent respecter les délais impartis.
La garantie d'offre est obligatoire pour tous les lots.
"""
        
        data = """
lot 1    imprimante laser    5
lot 2    scanner             3
lot 3    ordinateur          10
"""
        
        prose_ratio = _calculate_data_to_prose_ratio(_normalize(prose))
        data_ratio = _calculate_data_to_prose_ratio(_normalize(data))
        
        self.assertLess(prose_ratio, 0.3, "Prose devrait avoir un faible ratio data")
        self.assertGreater(data_ratio, 0.5, "Data devrait avoir un fort ratio data")
    
    def test_column_detection(self):
        """Test : détection de colonnes alignées."""
        aligned_text = """
reference       description         quantite    prix
ref001          imprimante laser    5           1200
ref002          scanner a4          3           800
"""
        
        columns = _detect_column_structure(_normalize(aligned_text))
        self.assertTrue(columns['has_column_pattern'])
        self.assertGreater(columns['column_confidence'], 0.3)
    
    def test_administrative_prose_detection(self):
        """Test : identification de prose administrative."""
        admin_text = """
Article 6 mode de reglement
Le paiement du montant du marche sera effectue par les moyens des directions 
financieres du gct a la suite de la reception des factures et de tous les 
justificatifs necessaires par virement bancaire.
"""
        
        self.assertTrue(_is_administrative_prose(_normalize(admin_text)))
    
    def test_supplier_datasheet_detection(self):
        """Test : identification de fiche technique fournisseur."""
        datasheet = """
KYOCERA Document Solutions
Ecosys PA5500x
Technology: Laser Monochrome
Speed: 55 pages per minute
Resolution: 1200 x 1200 dpi
Website: www.kyoceradocumentsolutions.fr
Model: PA5500X
"""
        
        self.assertTrue(_is_supplier_datasheet(_normalize(datasheet)))


class TestTableDetection(unittest.TestCase):
    """Tests des fonctions de détection de tableaux."""
    
    def test_table_header_detection(self):
        """Test : détection d'en-tête de tableau."""
        header = """
lot 1 acquisition imprimante laser reseau grand quantite 5
specification proposition
designation a preciser
technologie impression laser monochrome
resolution impression 1200 1200 dpi
"""
        
        self.assertTrue(_has_table_header(_normalize(header)))
    
    def test_table_content_detection(self):
        """Test : détection de contenu tabulaire."""
        content = """
processeur intel core i7 12eme generation
memoire 16 go ddr4
disque dur 512 go ssd
ecran 15 6 pouces
"""
        
        self.assertTrue(_looks_like_table_content(_normalize(content)))
    
    def test_table_end_detection(self):
        """Test : détection de fin de tableau."""
        end_text = """
total general 25000
montant ht 20833
tva 4167
"""
        
        self.assertTrue(_looks_like_end_of_table(_normalize(end_text)))
    
    def test_reject_administrative_as_table_header(self):
        """Test : rejet de prose administrative comme en-tête."""
        admin = """
Mini CCAP consultation
Article 1 objet
Cette consultation a pour objet la fourniture de materiels informatiques.
"""
        
        self.assertFalse(_has_table_header(_normalize(admin)))
    
    def test_reject_supplier_doc_as_table_header(self):
        """Test : rejet de doc fournisseur comme en-tête."""
        supplier = """
Dell Vostro 15 3530
Manuel du proprietaire
www.dell.com/support
Model: P112F
Type: P112F011
"""
        
        self.assertFalse(_has_table_header(_normalize(supplier)))


class TestRegressionPrevention(unittest.TestCase):
    """Tests pour éviter les régressions sur les cas connus."""
    
    def test_original_valid_pages_still_detected(self):
        """Test : les pages valides du document original sont toujours détectées."""
        # Page 3 : en-tête tableau imprimante
        page3_text = """
lot 1 acquisition d une imprimante laser reseau grand quantite 5
specification proposition
marque et modele a preciser
technologie d impression laser monochrome
resolution de l impression 1200 1200 dpi
vitesse d impression jusqu a 55 pages par minute en a4
"""
        
        self.assertTrue(_has_table_header(_normalize(page3_text)),
                       "Page 3 devrait être détectée comme en-tête de tableau")
        
        # Page 4 : caractéristiques ordinateur
        page4_text = """
caracteristiques techniques minimales propositions
reference vostro 3530
processeur central intel core i7 12eme generation min
memoire centrale 16 go min
disque dur capacite proposee
"""
        
        self.assertTrue(_has_table_header(_normalize(page4_text)),
                       "Page 4 devrait être détectée comme en-tête de tableau")
    
    def test_original_invalid_pages_still_rejected(self):
        """Test : les pages invalides du document original sont toujours rejetées."""
        # Page type administrative
        admin_page = """
mini ccap consultation gg 25 4 0019
article i objet
cette consultation a pour objet la fourniture de cing 05 lots de materiels
informatiques pour la division informatique du groupe chimique tunisien a gabes
"""
        
        self.assertFalse(_has_table_header(_normalize(admin_page)),
                        "Page administrative devrait être rejetée")
        
        # Page type fiche fournisseur
        supplier_page = """
kyoceradocumentsolutions fr
kyocera une imprimante laquelle vous pouvez compter
les options de gestion du papier jusqu a 2 600 feuilles
vitesse d impression allant jusqu a 55 pages par minute
imprimante monochrome a4
"""
        
        self.assertFalse(_has_table_header(_normalize(supplier_page)),
                        "Fiche fournisseur devrait être rejetée")


if __name__ == '__main__':
    unittest.main()
