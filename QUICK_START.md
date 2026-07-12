# 🚀 Guide de Démarrage Rapide

## Extraction de la Deuxième Colonne

### En 3 étapes :

#### 1️⃣ Préparer le PDF
```bash
# Placer votre PDF dans:
data/input/mon_fichier.pdf
```

#### 2️⃣ Lancer l'extraction
```bash
python src/main_specifications.py
```

#### 3️⃣ Voir les résultats
```bash
# Fichiers générés:
data/output/specifications.json           # Toutes les pages
data/output/specifications_strict.json    # Pages de qualité
```

---

## Exemples de Commandes

### Affichage rapide
```bash
python scripts/show_specifications.py
```

### Générer un rapport Markdown
```bash
python scripts/generate_extraction_report.py
```

### Test détaillé
```bash
python scripts/test_second_column.py
```

---

## Structure JSON de Sortie

```json
[
  {
    "page": 3,
    "specifications": [
      "A préciser",
      "Laser monochrome",
      "1200 × 1200 dpi",
      "Jusqu'à 55 pages par minute",
      "39 pages A4 par minute",
      "25 secondes",
      "5 secondes max"
    ]
  },
  {
    "page": 4,
    "specifications": [
      "À préciser",
      "Intel Core i7 11ème génération"
    ]
  }
]
```

---

## Fichiers Clés

| Fichier | Rôle |
|---------|------|
| `src/main_specifications.py` | 🎯 Script principal |
| `src/second_column_extractor.py` | 🔧 Module d'extraction |
| `src/extract_specifications_main.py` | 🛠️ Utilitaires (filtrage) |
| `scripts/show_specifications.py` | 👀 Visualiseur |
| `SECOND_COLUMN_EXTRACTION.md` | 📚 Documentation complète |

---

## Résultat Attendu

```
[INFO] Traitement : mon_fichier.pdf
============================================================
[OK] Page 2: 36 spécifications (valides)
[OK] Page 3: 24 spécifications (valides)
[OK] Page 4: 17 spécifications (valides)
...
============================================================
[RÉSULTATS]

Fichier complet: specifications.json
  43 pages extraites

Fichier filtré: specifications_strict.json
  43 pages de haute qualité

Spécifications totales: 935
Moyenne par page: 21.7
```

---

## ⚙️ Configuration Requise

✅ Python 3.10+  
✅ Tesseract OCR (fra.traineddata installé)  
✅ pypdf, pytesseract, numpy, opencv-python  

Pour vérifier :
```bash
tesseract --version
python --version
```

---

## 🎓 Comment ça Marche?

1. **Rendu HD** : Convertit chaque page PDF en image (300 DPI)
2. **OCR** : Extrait le texte avec Tesseract (langue française)
3. **Détection** : Identifie les 3 colonnes par clustering K-means
4. **Extraction** : Garde uniquement la colonne du milieu
5. **Nettoyage** : Supprime le bruit OCR
6. **Filtrage** : Rejette les pages trop bruyeuses (mode strict)

---

## 💡 Astuces

### Si les résultats sont bruyeux:
Utilisez le fichier `specifications_strict.json` au lieu de `specifications.json`

### Pour améliorer la qualité OCR:
- Augmentez le DPI dans `src/second_column_extractor.py`: `render_page(..., dpi=400)`
- Améliorez la qualité du PDF d'entrée

### Pour comprendre le processus:
Lisez `SECOND_COLUMN_EXTRACTION.md` pour la documentation complète

---

## 📞 Besoin d'Aide?

1. Vérifiez que Tesseract est installé: `tesseract --version`
2. Vérifiez que `fra.traineddata` existe: `ls "C:\Program Files\Tesseract-OCR\tessdata\fra.traineddata"`
3. Lisez la section "Dépannage" dans `SECOND_COLUMN_EXTRACTION.md`
4. Consultez le fichier `debug_pages.txt` pour les logs détaillés

---

**Besoin d'en savoir plus?** Voir `SECOND_COLUMN_EXTRACTION.md` 📚
