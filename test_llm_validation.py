"""
Script de test rapide pour la validation LLM locale.
"""

from src.pdf_extraction.validation.llm_validator import compare_specification_with_llm, check_ollama_server

# Test 1: Vérifier serveur
print("=" * 60)
print("TEST 1: Vérification serveur Ollama")
print("=" * 60)

if check_ollama_server():
    print("✓ Serveur Ollama accessible sur http://localhost:11434")
else:
    print("✗ Serveur Ollama INACCESSIBLE")
    print("  Démarrez le serveur: ollama serve")
    exit(1)

print()

# Test 2: Cas conforme
print("=" * 60)
print("TEST 2: Cas CONFORME (scanner à défilement)")
print("=" * 60)

result = compare_specification_with_llm(
    specification="Scanner à défilement",
    proposition="HP ScanJet Pro 2600 (scanner à défilement)",
    ocr_confidence=85,
    has_overflow=False
)

print(f"Statut: {result['statut']}")
print(f"Commentaire: {result['commentaire']}")
print()

# Test 3: Cas non conforme
print("=" * 60)
print("TEST 3: Cas NON CONFORME (résolution insuffisante)")
print("=" * 60)

result = compare_specification_with_llm(
    specification="Résolution minimale: 1200 x 1200 DPI",
    proposition="600 x 600 DPI",
    ocr_confidence=90,
    has_overflow=False
)

print(f"Statut: {result['statut']}")
print(f"Commentaire: {result['commentaire']}")
print()

# Test 4: Cas à vérifier (OCR faible)
print("=" * 60)
print("TEST 4: Cas À VÉRIFIER (confiance OCR faible)")
print("=" * 60)

result = compare_specification_with_llm(
    specification="Processeur Intel Core i7",
    proposition="lnte1 c0re 17",  # Texte mal OCRisé
    ocr_confidence=45,  # Très faible
    has_overflow=False
)

print(f"Statut: {result['statut']}")
print(f"Commentaire: {result['commentaire']}")
print(f"Raison: {result['raison_verification']}")
print()

# Test 5: Cas à vérifier (débordement)
print("=" * 60)
print("TEST 5: Cas À VÉRIFIER (débordement de texte)")
print("=" * 60)

result = compare_specification_with_llm(
    specification="Mémoire RAM minimale: 8 GB",
    proposition="16 GB DDR4",
    ocr_confidence=80,
    has_overflow=True  # Débordement détecté
)

print(f"Statut: {result['statut']}")
print(f"Commentaire: {result['commentaire']}")
print(f"Raison: {result['raison_verification']}")
print()

print("=" * 60)
print("TESTS TERMINÉS")
print("=" * 60)
