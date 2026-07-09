# Plan d'implémentation : Extraction de la 2ᵉ colonne

## Architecture existante

### Flux actuel :
1. `main.py` : Orchestrateur principal
2. `pdf_reader.py` : Lecture du PDF (pypdf)
3. `page_selector.py` : Sélection des pages cibles
4. `text_extractor.py` : Extraction de texte
5. `ocr_reader.py` : Conversion PDF→Image + OCR (pdf2image + pytesseract)
6. `pdf_writer.py` : Création du PDF de sortie

### Points clés :
- Les pages cibles sont déjà sélectionnées
- Les images sont créées à la demande via `pdf2image.convert_from_path()`
- Le projet utilise PIL/Pillow pour les images

## Stratégie d'intégration minimale

### Nouveau module : `src/column_extractor.py`

**Responsabilités :**
1. Convertir une page PDF en image PIL
2. Détecter les lignes verticales du tableau avec OpenCV
3. Déterminer les limites des 3 colonnes
4. Extraire et enregistrer la 2ᵉ colonne

**Fonction publique :**
```python
def extract_and_save_column2(
    pdf_path: str | Path,
    page_number: int,
    output_dir: str | Path,
    model: Literal["model1", "model2"] = "model1",
    poppler_path: Optional[str] = None,
) -> Optional[Path]
```

### Modifications minimales à `main.py`

Ajouter après `write_selected_pages()` :
```python
from column_extractor import extract_all_columns

extract_all_columns(
    reader=reader,
    pdf_path=input_path,
    selected_pages_indices=[],  # indices des pages sélectionnées
    output_dir="data/output",
    poppler_path=poppler_path
)
```

## Algorithme de détection des colonnes

### Étapes :
1. Convertir PDF page en image PIL
2. Convertir en niveaux de gris
3. Détecter les arêtes (Canny)
4. Utiliser Hough Lines pour trouver les lignes verticales
5. Filtrer les lignes verticales significatives (x constant)
6. Classer les x (x1, x2, x3 = limites colonne 1, 2, 3)
7. Extraire la région [x2:x3, 0:hauteur]
8. Enregistrer en PNG

### Robustesse :
- Les lignes verticales seront les délimiteurs du tableau
- Les trois lignes principales déterminent les trois colonnes
- OCR imparfait → détection basée sur structure visuelle
- Pas de coordonnées fixes

## Dépendances à ajouter

`requirements.txt` :
- `opencv-python` (pour Hough Lines, détection d'arêtes)

## Structure de sortie

```
data/output/
├── pages_cibles.pdf
├── column2_extracts/
│   ├── page_003_column2.png
│   ├── page_004_column2.png
│   ├── page_005_column2.png
│   └── ...
```

## Chronologie d'intégration

1. ✓ Créer `src/column_extractor.py` avec détection Hough Lines
2. ✓ Implémenter `extract_and_save_column2()` 
3. ✓ Implémenter `extract_all_columns()` pour boucle sur pages
4. ✓ Intégrer dans `main.py` après PDF output
5. ✓ Tester sur des pages cibles
6. ✓ Valider que detection fonctionne pour Model 1 et Model 2

## Notes importantes

- La détection n'est PAS spécifique au modèle (Model 1 vs 2)
- La structure visuelle du tableau est identique
- Le modèle serait pertinent plus tard pour la validation OCR
- Aucun changement à `page_selector.py` ou `text_extractor.py`
- L'extraction d'image réutilise la logique de `ocr_reader.py`
