# Extraction de la Deuxième Colonne - Tableaux à 3 Colonnes

## 📋 Description

Ce module extrait **uniquement la deuxième colonne** des tableaux à 3 colonnes présents dans les PDF.

### Tableaux Supportés

- **Modèle 1**: Désignation | **Spécification** | Proposition
- **Modèle 2**: Composants de l'offre | **Caractéristiques techniques minimales** | Proposition

### Sortie

Pour chaque page contenant un tableau structuré:
```json
{
  "page": 3,
  "specifications": [
    "dune imprimante Laser",
    "À A préciser R 2E",
    "Lase monochreme S",
    "Jusquà 55 pages par minute en",
    "39 pages A4 par minuto",
    ...
  ]
}
```

---

## 🚀 Utilisation

### Option 1: Script Principal (Recommandé)

```bash
python src/main_specifications.py
```

**Génère:**
- `data/output/specifications.json` - Toutes les pages extraites
- `data/output/specifications_strict.json` - Pages filtrées (haute qualité uniquement)

### Option 2: Script de Test (Détail complet)

```bash
python scripts/test_second_column.py
```

Affiche des statistiques détaillées et un aperçu des résultats.

### Option 3: Utiliser le Module Python

```python
import pytesseract
from src.second_column_extractor import extract_all_specifications

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

results = extract_all_specifications("data/input/mon_fichier.pdf")
print(f"Pages extraites: {len(results)}")

for item in results[:3]:
    print(f"Page {item['page']}: {len(item['specifications'])} spécifications")
```

---

## 📊 Algorithme

### Étapes d'Extraction

1. **Rendu HD** : Conversion PDF → Image (300 DPI)
2. **OCR** : Tesseract avec langue française, récupération coordonnées X/Y
3. **Détection de Colonnes** : K-means sur positions X → 3 colonnes principales
4. **Extraction** : Extraction colonne 2 uniquement
5. **Groupement** : Regroupement des mots par ligne (Y similaire)
6. **Nettoyage** : Suppression du bruit OCR (caractères brisés, symboles invalides)
7. **Filtrage** : Rejet des pages trop bruyeuses (mode strict)

### Détection de Colonnes

L'algorithme utilise les coordonnées X des mots OCR:

```
Colonne 1     Colonne 2 (extraite)     Colonne 3
  |  |            |  |                  |  |
  v  v            v  v                  v  v
┌───────────────────────────────────────────────┐
│ Mot 1   │  Mot 4   │  Mot 7         │
│ Mot 2   │  Mot 5   │  Mot 8         │
│ Mot 3   │  Mot 6   │  Mot 9         │
└───────────────────────────────────────────────┘
```

Clustering K-means identifie les 3 colonnes, chaque mot est assigné à la plus proche.

---

## 🔧 Configuration

### Tesseract

Déjà configuré dans le code:
```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

Assurer que `fra.traineddata` est présent:
```
C:\Program Files\Tesseract-OCR\tessdata\fra.traineddata
```

### Paramètres Ajustables

Dans `src/second_column_extractor.py`:

```python
# Hauteur de ligne pour le groupement (pixels)
group_words_by_row(col2_words, row_height_threshold=30)

# Longueur min/max pour validation
is_valid_specification(text, min_length=3, max_length=200)

# Ratio de bruit max toléré (mode strict)
filter_noisy_pages(results, noise_threshold=0.3)
```

---

## 📈 Résultats & Qualité

### Statistiques Typiques

```
Total pages: 43
Total spécifications: 935
Moyenne par page: 21.7
Pages filtrées (bruyeuses): 2
Mode strict: 43 pages de qualité
```

### Qualité OCR

Deux fichiers JSON:
- `specifications.json` - **Complet** (toutes les pages)
- `specifications_strict.json` - **Filtré** (pages haute qualité uniquement)

Mode strict élimine les pages où:
- Plus de 30% de caractères sont du bruit OCR
- Texte trop court/long
- Pas assez d'alphanumériques

---

## ⚠️ Limitations

1. **OCR Imparfait** : Le texte OCR peut contenir des erreurs
   - Exemple: "Lase monochreme" au lieu de "Laser monochrome"
   - Solution: Post-traitement avec correction orthographique

2. **Tableaux Non-Structurés** : Les pages sans grille claire peuvent donner du bruit
   - Solution: Mode strict filtre ces pages

3. **Colonnes Non-Alignées** : Si les colonnes ne sont pas verticales
   - Solution: Augmenter DPI ou ajuster row_height_threshold

4. **Polices Spéciales** : Certaines polices compliquent la détection
   - Solution: Améliorer la qualité du PDF d'entrée

---

## 🐛 Dépannage

### "No OCR words detected"
- Vérifier que le PDF n'est pas vide ou corrompu
- Augmenter DPI: `render_page(pdf_path, page_num, dpi=400)`

### Colonnes Non-Détectées
- Vérifier que le tableau a bien 3 colonnes
- Augmenter row_height_threshold pour mieux grouper

### Bruit OCR Élevé
- Vérifier la qualité du PDF d'entrée
- Utiliser `specifications_strict.json` au lieu du complet

### ImportError
- Assurer que `second_column_extractor.py` est dans `src/`
- Vérifier les chemins Python

---

## 📝 Format de Sortie

### JSON Structure

```json
[
  {
    "page": <numero_page>,
    "specifications": [
      "<texte_spec_1>",
      "<texte_spec_2>",
      ...
    ]
  },
  ...
]
```

### Exemple

```json
[
  {
    "page": 3,
    "specifications": [
      "dune imprimante Laser",
      "À A préciser R 2E",
      "Lase monochrome S",
      "12001200 dpi",
      "Jusquà 55 pages par minute en",
      "39 pages A4 par minuto",
      "25 secondes -",
      "5 secondes max e"
    ]
  }
]
```

---

## 🎯 Cas d'Usage

### 1. Extraction de Spécifications Techniques
```bash
python src/main_specifications.py
# ↓
# Fichier: specifications_strict.json
# Contient: Colonnes "Caractéristiques techniques" uniquement
```

### 2. Analyse de Contrats
```python
import json

with open("data/output/specifications_strict.json") as f:
    specs = json.load(f)

for item in specs:
    print(f"Page {item['page']}: {len(item['specifications'])} clauses")
```

### 3. Export pour Autre Système
Les JSON peuvent être importés dans Excel, bases de données, etc.

---

## 📚 Fichiers Importants

| Fichier | Description |
|---------|-------------|
| `src/second_column_extractor.py` | Module principal d'extraction |
| `src/main_specifications.py` | Script exécutable principal |
| `src/extract_specifications_main.py` | Utilitaires (filtrage, etc.) |
| `data/output/specifications.json` | Résultat complet |
| `data/output/specifications_strict.json` | Résultat filtré (haute qualité) |

---

## 💡 Améliorations Futures

- [ ] Post-traitement avec correction orthographique
- [ ] Détection de titres vs contenus
- [ ] Support de tables multicolonnes (>3 colonnes)
- [ ] Export format Excel natif
- [ ] Interface web pour visualiser les résultats
- [ ] Apprentissage machine pour détection de colonnes
