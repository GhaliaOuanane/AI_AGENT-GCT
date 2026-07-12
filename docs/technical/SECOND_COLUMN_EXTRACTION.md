# Extraction de la Deuxième Colonne - Guide Technique

**Module:** `src/pdf_extraction/extractors/second_column_extractor.py`  
**Usage:** Extraction de la colonne "Spécification" depuis tableaux à 3 colonnes

---

## 🎯 Objectif

Extraire **uniquement la 2ème colonne** (Spécification / Caractéristiques techniques) des tableaux à 3 colonnes dans les PDFs.

**Tableaux supportés:**
- Modèle 1: Désignation | **Spécification** | Proposition
- Modèle 2: Composants | **Caractéristiques techniques** | Proposition

---

## 🚀 Utilisation

### Script Principal
```bash
python src/main_specifications.py
```

**Génère:**
- `data/output/specifications.json` - Toutes les pages
- `data/output/specifications_strict.json` - Pages haute qualité uniquement

### Format de Sortie
```json
[
  {
    "page": 3,
    "specifications": [
      "À préciser",
      "Laser monochrome",
      "1200 × 1200 dpi",
      "Jusqu'à 55 pages par minute"
    ]
  }
]
```

### Utilisation Programmatique
```python
from pdf_extraction.extractors.second_column_extractor import extract_all_specifications

results = extract_all_specifications("mon_fichier.pdf")
for item in results:
    print(f"Page {item['page']}: {len(item['specifications'])} specs")
```

---

## 📊 Algorithme

### Pipeline d'Extraction

1. **Rendu HD** : PDF → Image (300 DPI) via PyMuPDF
2. **OCR** : Tesseract français avec coordonnées X/Y de chaque mot
3. **Détection Colonnes** : K-means (k=3) sur positions X des mots
4. **Extraction** : Mots assignés à la colonne centrale (2ème)
5. **Groupement** : Regroupement par ligne (Y similaire ±15px)
6. **Nettoyage** : Suppression bruit OCR (min 2 caractères alphanumériques)
7. **Filtrage (mode strict)** : Rejet pages < 50% lignes valides

### Détection de Colonnes (K-means)

```
Colonne 1      Colonne 2 (extraite)    Colonne 3
   ↓                  ↓                     ↓
┌──────────────────────────────────────────────┐
│ Désignation  │  Spécification  │  Proposition │
│ Item 1       │  Valeur 1       │  Prix 1      │
│ Item 2       │  Valeur 2       │  Prix 2      │
└──────────────────────────────────────────────┘
```

**K-means identifie 3 clusters** sur l'axe X. Chaque mot OCR est assigné au cluster le plus proche. Seuls les mots du cluster central sont extraits.

---

## 🔧 Configuration

### Paramètres Clés (dans `second_column_extractor.py`)

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| `dpi` | 300 | Résolution du rendu PDF (augmenter si OCR imprécis) |
| `Y_THRESHOLD` | 15 | Tolérance verticale pour regrouper mots en ligne |
| `MIN_VALID_RATIO` | 0.5 | Ratio minimum lignes valides (mode strict) |
| `lang` | 'fra' | Langue Tesseract (nécessite fra.traineddata) |
| `n_clusters` | 3 | Nombre de colonnes attendues |

### Amélioration Qualité OCR

```python
# Dans second_column_extractor.py, fonction render_page()
pix = page.get_pixmap(matrix=mat, alpha=False)

# Passer de 300 à 400 DPI pour meilleure précision
mat = fitz.Matrix(400/72, 400/72)  # Augmente qualité mais ralentit
```

---

## 📈 Résultats Typiques

**Exemple d'exécution:**
```
EXTRACTION DEUXIÈME COLONNE
Source: cahier_charges.pdf (43 pages)
Pages extraites: 43
Spécifications totales: 935
Moyenne par page: 21.7

Mode strict:
✓ Pages conservées: 43
✓ Pages rejetées: 0
```

**Fichiers générés:**
- `specifications.json` : 935 spécifications (complet)
- `specifications_strict.json` : 935 spécifications (haute qualité)

---

## ⚠️ Limitations & Dépannage

### Problèmes Courants

**1. Spécifications manquantes ou incomplètes**
- **Cause:** Qualité OCR insuffisante (PDF basse résolution)
- **Solution:** Augmenter DPI à 400 ou améliorer qualité du PDF source

**2. Bruit OCR (symboles, fragments)**
- **Cause:** Artefacts visuels dans le PDF (lignes de tableau, ombres)
- **Solution:** Utiliser `specifications_strict.json` qui filtre pages bruyantes

**3. Mauvaise détection des colonnes**
- **Cause:** Tableau avec >3 colonnes ou colonnes fusionnées
- **Solution:** K-means assume 3 colonnes distinctes, vérifier structure du tableau

**4. Tesseract non trouvé**
- **Cause:** Tesseract non installé ou PATH incorrect
- **Solution:** Installer Tesseract + fra.traineddata, configurer chemin dans code

### Vérification Installation

```bash
tesseract --version
tesseract --list-langs  # Doit contenir 'fra'
```

---

## 📚 Références Complètes

**Version complète:** `archive/docs/SECOND_COLUMN_EXTRACTION_FULL.md` (30+ pages)  
**Code source:** `src/pdf_extraction/extractors/second_column_extractor.py`  
**Tests:** `tests/integration/test_second_column_extraction.py`

---

**Version condensée - 2 pages** | Dernière mise à jour: 2026-07-12
