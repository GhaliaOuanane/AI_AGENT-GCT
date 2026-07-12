# 📄 Extracteur Intelligent de Pages PDF

Agent IA pour l'extraction automatique de pages techniques pertinentes à partir de documents PDF d'appels d'offres et cahiers des charges.

## 🎯 Objectif du Projet

Ce projet automatise l'extraction des pages contenant des **spécifications techniques** à partir de documents PDF volumineux (appels d'offres, réponses fournisseurs, cahiers des charges). L'algorithme intelligent analyse le contenu textuel de chaque page et identifie automatiquement les tableaux de spécifications techniques tout en excluant les pages administratives et les fiches techniques fournisseurs.

### Cas d'usage typiques
- Extraction des spécifications techniques d'équipements informatiques (imprimantes, ordinateurs, scanners)
- Filtrage automatique des pages administratives (CCAP, formulaires, annexes)
- Exclusion des fiches techniques fournisseurs (manuels Dell, HP, Kyocera, Epson, etc.)
- Traitement de PDFs en français avec support OCR pour les documents scannés

## ✨ Fonctionnalités

- **Détection intelligente** : Reconnaissance automatique des en-têtes de tableaux techniques
- **Support OCR** : Extraction de texte à partir de PDFs scannés via Tesseract OCR
- **Analyse contextuelle** : Distinction entre spécifications client et fiches fournisseurs
- **Mode debug** : Fichier de log détaillé pour audit et amélioration
- **Traitement automatique** : Sélection du premier PDF dans le dossier d'entrée
- **Normalisation du texte** : Gestion robuste des accents et caractères spéciaux français

## 🛠️ Technologies Utilisées

| Technologie | Version | Usage |
|------------|---------|-------|
| **Python** | 3.10+ | Langage de développement |
| **pypdf** | Latest | Manipulation et extraction de PDFs |
| **Tesseract OCR** | 5.x | Reconnaissance optique de caractères |
| **pytesseract** | Latest | Interface Python pour Tesseract |
| **pdf2image** | Latest | Conversion PDF en images pour OCR |
| **Pillow** | Latest | Traitement d'images |
| **Poppler** | 26.02.0 | Utilitaires de conversion PDF (inclus) |

## 📋 Prérequis

### Système d'exploitation
- Windows 10/11
- Linux (Ubuntu 20.04+)
- macOS 10.15+

### Logiciels requis

1. **Python 3.10 ou supérieur**
   ```bash
   python --version
   ```

2. **Tesseract OCR**
   
   **Windows :**
   - Télécharger depuis : https://github.com/UB-Mannheim/tesseract/wiki
   - Installer dans : `C:\Program Files\Tesseract-OCR\`
   - Ajouter au PATH système

   **Linux :**
   ```bash
   sudo apt-get update
   sudo apt-get install tesseract-ocr tesseract-ocr-fra tesseract-ocr-eng
   ```

   **macOS :**
   ```bash
   brew install tesseract tesseract-lang
   ```

3. **Poppler** (inclus dans le projet pour Windows)
   
   **Linux :**
   ```bash
   sudo apt-get install poppler-utils
   ```

   **macOS :**
   ```bash
   brew install poppler
   ```

## 🚀 Installation

### 1. Cloner le repository
```bash
git clone <repository-url>
cd AI_AGENT_GCT
```

### 2. Créer un environnement virtuel
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Vérifier l'installation de Tesseract
```bash
# Windows
tesseract --version

# Linux/macOS
tesseract --version
```

Si Tesseract n'est pas dans le PATH, le programme utilisera automatiquement :
- Windows : `C:\Program Files\Tesseract-OCR\tesseract.exe`
- Autres : Chemin système par défaut

## 📖 Utilisation

### Utilisation de base

1. **Placer le PDF à analyser** dans le dossier `data/input/`
   ```
   data/input/mon_document.pdf
   ```

2. **Exécuter le programme**
   ```bash
   python src/main.py
   ```

3. **Récupérer le résultat** dans `data/output/pages_cibles.pdf`

### Exemple de sortie console
```
============================================================
AGENT IA - EXTRACTION DES PAGES CIBLES
============================================================

Ouverture du PDF : data\input\BRAIN INFORMATIQUE_16052025101905.PDF
Nombre de pages : 46

Analyse du document...

Log detaille ecrit dans : debug_pages.txt
Total pages selectionnees : 6 / 46
Pages candidates initiales : 6

PDF créé avec succès.
Fichier enregistré : data/output/pages_cibles.pdf
```

### Scripts d'inspection

**Analyser la sélection des pages :**
```bash
python scripts/inspect_selection.py
```

**Vérifier le contenu du PDF de sortie :**
```bash
python scripts/verify_output.py
```

**Vérifier des pages spécifiques :**
```bash
python scripts/check_pages.py
```

---

### 🎯 Extraction de la Deuxième Colonne (NOUVEAU)

Extraire uniquement la deuxième colonne des tableaux à 3 colonnes (Spécifications / Caractéristiques techniques).

**Utilisation :**
```bash
# Mode complet
python src/main_specifications.py

# Mode détail avec test
python scripts/test_second_column.py

# Visualiser les résultats
python scripts/show_specifications.py
```

**Fichiers générés :**
- `data/output/specifications.json` - Toutes les pages
- `data/output/specifications_strict.json` - Pages haute qualité uniquement

**Format de sortie :**
```json
[
  {
    "page": 3,
    "specifications": [
      "A préciser",
      "Laser monochrome",
      "1200 × 1200 dpi",
      "Jusqu'à 55 pages par minute"
    ]
  }
]
```

Pour plus de détails : voir `SECOND_COLUMN_EXTRACTION.md`

---

## 📁 Structure du Projet

```
AI_AGENT_GCT/
├── data/
│   ├── input/              # PDFs à analyser (placer vos fichiers ici)
│   └── output/             # PDFs extraits (générés automatiquement)
├── src/
│   ├── main.py            # Point d'entrée principal
│   ├── page_selector.py   # Logique de sélection des pages
│   ├── page_selector_debug.py  # Version debug avec logs détaillés
│   ├── pdf_reader.py      # Lecture de PDFs
│   ├── pdf_writer.py      # Écriture de PDFs
│   ├── text_extractor.py  # Extraction de texte
│   └── ocr_reader.py      # OCR via Tesseract
├── scripts/
│   ├── inspect_selection.py    # Inspection détaillée de la sélection
│   ├── verify_output.py        # Vérification du PDF de sortie
│   └── check_pages.py          # Vérification de pages spécifiques
├── tests/
│   └── test_local_page_selection.py  # Tests unitaires
├── tools/
│   └── poppler-26.02.0/   # Utilitaires Poppler (Windows)
├── requirements.txt       # Dépendances Python
├── debug_pages.txt        # Log détaillé (généré automatiquement)
└── README.md             # Ce fichier
```

## 🧠 Algorithme de Sélection

L'algorithme utilise une approche basée sur l'analyse de contenu textuel :

### 1. Normalisation du texte
- Conversion en minuscules
- Suppression des accents français
- Nettoyage des caractères spéciaux

### 2. Détection d'en-têtes de tableaux
Recherche de combinaisons de mots-clés :
- **Colonnes** : désignation, descriptif, description
- **Mesures** : quantité, prix, montant, HT, TTC
- **Concepts** : spécification, proposition, offre
- **Techniques** : lot, caractéristiques techniques, imprimante, scanner, ordinateur

### 3. État de machine à états
```
HORS_TABLE → EN-TÊTE_DÉTECTÉ → DANS_TABLE → FIN_TABLE → HORS_TABLE
```

### 4. Filtrage intelligent
**Pages exclues automatiquement :**
- Pages administratives (mini-CCAP, formulaires)
- Fiches techniques fournisseurs (Dell, HP, Kyocera, Epson)
- Manuels utilisateur
- Annexes non techniques

**Pages incluses :**
- En-têtes de tableaux de spécifications
- Contenu de tableaux techniques
- Notes et pages de continuation
- Pages de fin de tableau (totaux)

## 🔧 Configuration

### Modifier le chemin Tesseract
Éditer `src/ocr_reader.py` :
```python
def _configure_tesseract(tesseract_cmd: Optional[str] = None) -> None:
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        return

    # Modifier ce chemin selon votre installation
    default_windows = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if default_windows.exists():
        pytesseract.pytesseract.tesseract_cmd = str(default_windows)
```

### Modifier le chemin Poppler
Éditer `src/main.py` :
```python
def _resolve_poppler_path() -> str | None:
    candidate = Path(__file__).resolve().parent.parent / "tools" / "poppler-26.02.0" / "Library" / "bin"
    return str(candidate) if candidate.exists() else None
```

### Désactiver l'OCR
Éditer `src/main.py` :
```python
use_ocr = False  # Changer True en False
```

## 🧪 Tests

Exécuter les tests unitaires :
```bash
python -m unittest discover tests
```

Test spécifique :
```bash
python -m unittest tests.test_local_page_selection
```

## 📊 Debug et Logs

Le fichier `debug_pages.txt` est généré automatiquement et contient :
- Numéro de page analysée
- État de chaque détecteur (header, content, note, end)
- Extrait du texte normalisé
- Décision de sélection avec justification

Exemple :
```
PAGE 3 / 46 ==============================
  has_table_header        : True
  looks_like_table_content: True
  looks_like_note_page    : False
  looks_like_end_of_table : True
  --- extrait du texte normalise (300 premiers car.) ---
  'lot 1 acquisition d une imprimante laser reseau grand quantite 5
   specification proposition designation a preciser...'
  => ✓ SELECTIONNEE (header detecte)
```

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Forkez le projet
2. Créez une branche feature (`git checkout -b feature/amelioration`)
3. Committez vos changements (`git commit -m 'Ajout d'une fonctionnalité'`)
4. Pushez vers la branche (`git push origin feature/amelioration`)
5. Ouvrez une Pull Request

## ⚠️ Limitations Connues

- L'OCR nécessite des images de bonne qualité (300 DPI recommandé)
- Les tableaux complexes multi-colonnes peuvent nécessiter un ajustement des seuils
- La détection est optimisée pour les documents en français
- Les PDFs avec des polices non standard peuvent poser problème

## 🔮 Améliorations Futures

- [ ] Support de plusieurs langues (anglais, arabe)
- [ ] Interface graphique (GUI) pour la sélection interactive
- [ ] Export en formats multiples (Excel, JSON, CSV)
- [ ] Amélioration de la détection des tableaux complexes
- [ ] API REST pour intégration dans d'autres systèmes
- [ ] Machine Learning pour améliorer la précision de détection

## 📝 Licence

Ce projet est sous licence privée. Tous droits réservés.

## 👥 Auteurs

Développé pour le Groupe Chimique Tunisien (GCT) - Division Informatique

## 📧 Support

Pour toute question ou problème :
- Créer une issue sur le repository
- Contacter l'équipe de développement

---

**Version** : 1.0.0  
**Dernière mise à jour** : Mai 2025
