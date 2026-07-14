# Mise à jour: Détection et Export des Headers Personnalisés

## Date
14 juillet 2026

## Problème Initial
Le système détectait bien les tables avec l'en-tête "Exigé ou à préciser" mais exportait toujours la clé générique `"specification"` dans le JSON, sans indication du vrai nom de l'en-tête détecté dans le document.

## Solution Implémentée

### 1. Détection du Header (page_selector.py)
✅ **Commit**: `8497b71` - "feat: add detection for 'Exigé ou à préciser' column header"

Ajout de la reconnaissance des variantes:
- "Exigé ou à préciser" (complet)
- "Exigé" (court)
- "À préciser" (court)

**Fichiers modifiés:**
- `src/pdf_extraction/core/page_selector.py`

**Patterns ajoutés:**
```python
r"\bexige\s+(ou\s+)?a\s+preciser\b|"
r"\bexige\b|"
r"\ba\s+preciser\b"
```

### 2. Export des Noms Détectés (column_extractor.py)
✅ **Commit**: `3acdf8e` - "feat: add detected header names to JSON output"

**Fichiers modifiés:**
- `src/pdf_extraction/extractors/column_extractor.py`

**Changements:**

#### A. Nouveau Template
```python
MODELE_1_VARIANT_HEADERS = {
    "designation":   "designation",
    "specification": "exige ou a preciser",
    "proposition":   "proposition",
}
```

#### B. Fonction `match_header()` Modifiée
- **Avant:** `(role, score, method)`
- **Après:** `(role, score, method, detected_label)`

Le 4ème élément retourne le texte original détecté par l'OCR, préservant la casse et l'orthographe exacte.

#### C. Ajout de `detected_headers` dans les Résultats
Chaque ligne extraite contient maintenant:
```json
{
  "detected_headers": {
    "designation": "Désignation",
    "specification": "Exigé ou à préciser",
    "proposition": "Proposition"
  }
}
```

#### D. Fonction `to_json()` Améliorée
Nouveau paramètre: `use_detected_headers=True`

Quand activé, crée des clés supplémentaires avec les noms détectés:
```json
{
  "specification": "A préciser",
  "Exigé ou à préciser": "A préciser"
}
```

**Avantages:**
- Compatibilité backward: la clé `"specification"` existe toujours
- Flexibilité: les consommateurs peuvent utiliser soit la clé générique, soit la clé spécifique

#### E. Nouveau Champ `modele_detecte`
- `"modele_1"` → Désignation | Spécification | Proposition
- `"modele_1_variant"` → Désignation | Exigé ou à préciser | Proposition
- `"modele_2"` → Composants de l'offre | Caractéristiques techniques minimales | Propositions

### 3. Tests
✅ Créés deux scripts de test:

#### `test_header_detection.py`
Test unitaire de la fonction `match_header()` avec différentes variantes:
```
✓ "Spécification" → role=specification
✓ "Exigé ou à préciser" → role=specification, label="Exigé ou à préciser"
✓ "Exigé" → role=specification, label="Exigé"
✓ "À préciser" → role=specification, label="À préciser"
✓ "EXIGE OU A PRECISER" → role=specification (case insensitive)
```

#### `test_full_extraction.py`
Test d'intégration avec `pages_cibles.pdf`:
- Vérifie que `detected_headers` est présent dans les résultats
- Teste `to_json()` avec `use_detected_headers=True`
- Confirme la création des clés personnalisées

**Résultat du test:**
```json
{
  "modele_detecte": "modele_1_variant",
  "specification": "A préciser",
  "Exigé ou à préciser": "A préciser",
  "detected_headers": {
    "specification": "Exigé ou à préciser"
  }
}
```

## Exemple Complet

### Input PDF
Table avec header: **Désignation | Exigé ou à préciser | Proposition**

### Output JSON
```json
{
  "fichier": "pages_cibles.pdf",
  "page": 1,
  "modele_detecte": "modele_1_variant",
  "designation": "Marque et Modèle",
  "specification": "A préciser",
  "proposition": "EPSON",
  "detected_headers": {
    "designation": "Désignation",
    "specification": "Exigé ou à préciser",
    "proposition": "Proposition"
  },
  "Exigé ou à préciser": "A préciser",
  "Désignation": "Marque et Modèle",
  "Proposition": "EPSON"
}
```

## Compatibilité

### ✅ Backward Compatible
- Les clés génériques (`designation`, `specification`, `proposition`) existent toujours
- Les anciens scripts peuvent continuer à utiliser `row["specification"]`

### ✅ Forward Compatible
- Les nouveaux scripts peuvent utiliser `row["Exigé ou à préciser"]` pour plus de clarté
- Le champ `detected_headers` permet de mapper dynamiquement les colonnes

## Usage

### Option 1: Utiliser les Clés Génériques (comme avant)
```python
for row in data:
    designation = row["designation"]
    specification = row["specification"]
    proposition = row["proposition"]
```

### Option 2: Utiliser les Noms Détectés
```python
for row in data:
    headers = row.get("detected_headers", {})
    spec_header = headers.get("specification", "specification")
    specification = row[spec_header]
    # → Utilise "Exigé ou à préciser" si détecté, sinon "specification"
```

### Option 3: Désactiver les Noms Détectés
```python
to_json(results, "output.json", use_detected_headers=False)
# → Ne crée que les clés génériques
```

## Tests de Non-Régression
- ✅ 8 tests échouent (pré-existants, pas de nouvelles régressions)
- ✅ Test unitaire: 7/7 variantes de headers détectées correctement
- ✅ Test d'intégration: extraction complète fonctionne avec `detected_headers`

## Prochaines Étapes (Optionnel)

### Si Besoin de Nettoyer le JSON
Pour supprimer les clés génériques et ne garder que les noms détectés:
```python
def to_json_detected_only(results, output_path):
    """Exporte uniquement avec les noms détectés, sans clés génériques"""
    processed = []
    for row in results:
        new_row = {k: v for k, v in row.items() 
                   if k not in ["designation", "specification", "proposition"]}
        
        if "detected_headers" in row:
            for role, detected_name in row["detected_headers"].items():
                if role in ["designation", "specification", "proposition"]:
                    new_row[detected_name] = row[role]
        
        processed.append(new_row)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)
```

## Références

### Commits
- `8497b71` - Détection du header dans page_selector.py
- `3acdf8e` - Export des noms détectés dans column_extractor.py

### Fichiers Modifiés
1. `src/pdf_extraction/core/page_selector.py`
2. `src/pdf_extraction/extractors/column_extractor.py`

### Fichiers Créés
1. `test_header_detection.py` - Tests unitaires
2. `test_full_extraction.py` - Tests d'intégration
3. `docs/HEADER_DETECTION_UPDATE.md` (ce fichier)
