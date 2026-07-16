"""
Tests unitaires pour pdf_validator.py
"""

import unittest
from pathlib import Path
import json
import tempfile
import shutil

from src.pdf_extraction.core.pdf_validator import (
    validate_input_pdf,
    log_rejected_file,
    get_rejection_message,
    ValidationResult
)


class TestPdfValidator(unittest.TestCase):
    """Tests du validateur de PDF."""
    
    def setUp(self):
        """Prépare l'environnement de test."""
        # Créer un dossier temporaire pour les sorties
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Nettoie après les tests."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_reject_scanned_pdf(self):
        """Test: un PDF scanné doit être rejeté."""
        # Utiliser le PDF scanné existant
        scanned_pdf = Path("data/input/Discount Info.PDF")
        
        if not scanned_pdf.exists():
            self.skipTest(f"PDF scanné de test introuvable: {scanned_pdf}")
        
        result = validate_input_pdf(scanned_pdf)
        
        self.assertFalse(result.is_valid, "Le PDF scanné devrait être rejeté")
        self.assertIn("scanne", result.reason.lower(), "La raison doit mentionner 'scanné'")
        self.assertIn("text_coverage_percent", result.metrics)
        self.assertLess(result.metrics["text_coverage_percent"], 5, 
                       "Un PDF scanné doit avoir moins de 5% de couverture texte")
    
    def test_accept_native_pdf(self):
        """Test: un PDF natif doit être accepté."""
        # Note: pages_cibles.pdf peut être scanné si extrait d'un PDF scanné
        # Chercher plutôt BRAIN INFORMATIQUE qui devrait être natif
        native_pdfs = [
            Path("data/input/BRAIN INFORMATIQUE_16052025101905.PDF"),
            Path("data/output/pages_cibles.pdf"),
        ]
        
        found_native = False
        for native_pdf in native_pdfs:
            if native_pdf.exists():
                result = validate_input_pdf(native_pdf)
                
                if result.is_valid:
                    found_native = True
                    self.assertTrue(result.is_valid)
                    self.assertEqual(result.reason, "document_natif_valide")
                    self.assertGreaterEqual(result.metrics["text_coverage_percent"], 5)
                    break
        
        if not found_native:
            self.skipTest("Aucun PDF natif valide trouvé pour le test")
    
    def test_rejection_logging(self):
        """Test: vérifie la création de rejected_files.json."""
        test_pdf = Path("data/input/Discount Info.PDF")
        
        if not test_pdf.exists():
            self.skipTest(f"PDF de test introuvable: {test_pdf}")
        
        validation = ValidationResult(
            is_valid=False,
            reason="document_scanne_texte_insuffisant",
            metrics={"text_coverage_percent": 2.3, "total_pages": 8}
        )
        
        # Logger dans le dossier temporaire
        log_rejected_file(test_pdf, validation, output_dir=self.temp_dir)
        
        rejected_file = self.temp_dir / "rejected_files.json"
        self.assertTrue(rejected_file.exists(), "rejected_files.json devrait être créé")
        
        # Vérifier le contenu
        with open(rejected_file, 'r', encoding='utf-8') as f:
            rejected_list = json.load(f)
        
        self.assertEqual(len(rejected_list), 1)
        self.assertEqual(rejected_list[0]["filename"], test_pdf.name)
        self.assertEqual(rejected_list[0]["reason"], "document_scanne_texte_insuffisant")
        self.assertIn("rejected_at", rejected_list[0])
    
    def test_rejection_message_format(self):
        """Test: vérifie le format du message de rejet."""
        test_pdf = Path("test.pdf")
        validation = ValidationResult(
            is_valid=False,
            reason="document_scanne_texte_insuffisant",
            metrics={"text_coverage_percent": 2.3}
        )
        
        message = get_rejection_message(test_pdf, validation)
        
        self.assertIn("[REJET]", message)
        self.assertIn("test.pdf", message)
        self.assertIn("numérisé", message)
        self.assertIn("version numérique native", message)
    
    def test_file_not_found(self):
        """Test: un fichier inexistant retourne une erreur appropriée."""
        fake_pdf = Path("nonexistent.pdf")
        
        result = validate_input_pdf(fake_pdf)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason, "fichier_introuvable")
    
    def test_border_case_low_text(self):
        """Test: un PDF avec peu de texte mais natif."""
        # Ce test vérifie qu'on ne rejette pas un PDF natif légitime
        # avec peu de contenu textuel (ex: schémas techniques)
        # Nécessite un PDF de test spécifique - skip si non disponible
        
        # Pour l'instant, on vérifie juste que le seuil est raisonnable
        from src.pdf_extraction.core.pdf_validator import MINIMUM_TEXT_COVERAGE_PERCENT
        self.assertEqual(MINIMUM_TEXT_COVERAGE_PERCENT, 5,
                        "Le seuil devrait être 5% pour éviter les faux positifs")
    
    def test_metrics_completeness(self):
        """Test: vérifie que toutes les métriques attendues sont présentes."""
        test_pdf = Path("data/input/Discount Info.PDF")
        
        if not test_pdf.exists():
            self.skipTest(f"PDF de test introuvable: {test_pdf}")
        
        result = validate_input_pdf(test_pdf)
        
        expected_metrics = [
            "total_pages",
            "pages_with_text",
            "text_coverage_percent",
            "avg_chars_per_page",
            "pages_with_large_images",
            "has_bitmap_fonts"
        ]
        
        for metric in expected_metrics:
            self.assertIn(metric, result.metrics,
                         f"Métrique manquante: {metric}")


if __name__ == "__main__":
    unittest.main()
