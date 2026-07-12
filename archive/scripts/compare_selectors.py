"""
Compare l'ancien sélecteur (avec mots-clés) et le nouveau (robuste).
Vérifie qu'il n'y a pas de régression sur le document réel.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from pdf_reader import open_pdf
from text_extractor import extract_page_texts

# Import des deux versions
import page_selector as old_selector
import page_selector_robust as new_selector

pdf_path = Path('data/input/ETS BOUATTOUR TATFHI_16052025102203.PDF')
if not pdf_path.exists():
    # Chercher n'importe quel PDF
    input_dir = Path('data/input')
    pdfs = list(input_dir.glob('*.PDF')) + list(input_dir.glob('*.pdf'))
    if not pdfs:
        print(f"⚠️  No PDF found in data/input/")
        sys.exit(1)
    pdf_path = pdfs[0]
    print(f"ℹ️  Using PDF: {pdf_path.name}")

reader = open_pdf(pdf_path)
poppler_path = r'D:\AI_AGENT GCT\tools\poppler-26.02.0\Library\bin'

print("=" * 70)
print("COMPARAISON : Ancien sélecteur VS Nouveau sélecteur robuste")
print("=" * 70)

# Sélection avec l'ancien
old_pages = old_selector.select_target_pages(
    reader=reader,
    pdf_path=pdf_path,
    use_ocr=True,
    poppler_path=poppler_path
)
old_indices = [i + 1 for i, p in enumerate(reader.pages) if p in old_pages]

# Sélection avec le nouveau
new_pages = new_selector.select_target_pages(
    reader=reader,
    pdf_path=pdf_path,
    use_ocr=True,
    poppler_path=poppler_path
)
new_indices = [i + 1 for i, p in enumerate(reader.pages) if p in new_pages]

print(f"\n📄 PDF: {pdf_path.name}")
print(f"📊 Total pages: {len(reader.pages)}")
print(f"\n{'Sélecteur':<20} {'Pages sélectionnées':<30} {'Total':<10}")
print("-" * 70)
print(f"{'Ancien (mots-clés)':<20} {str(old_indices):<30} {len(old_indices):<10}")
print(f"{'Nouveau (robuste)':<20} {str(new_indices):<30} {len(new_indices):<10}")

# Analyse des différences
only_old = set(old_indices) - set(new_indices)
only_new = set(new_indices) - set(old_indices)
common = set(old_indices) & set(new_indices)

print(f"\n📈 Analyse:")
print(f"  ✓ Pages communes      : {sorted(common)}")
print(f"  ⊖ Perdues (nouveau)   : {sorted(only_old) if only_old else 'Aucune'}")
print(f"  ⊕ Ajoutées (nouveau)  : {sorted(only_new) if only_new else 'Aucune'}")

# Verdict
print(f"\n{'='*70}")
if not only_old:
    print("✅ SUCCÈS : Aucune page valide perdue !")
    if only_new:
        print(f"ℹ️  {len(only_new)} nouvelles pages détectées (à vérifier)")
else:
    print(f"⚠️  ATTENTION : {len(only_old)} pages perdues avec le nouveau sélecteur")
    print("   → Vérifier si ces pages sont vraiment importantes")

if len(only_old) == 0 and len(only_new) == 0:
    print("🎯 PARFAIT : Résultats identiques !")

print("=" * 70)
