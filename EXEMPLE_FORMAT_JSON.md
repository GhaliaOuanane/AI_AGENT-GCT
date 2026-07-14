# 📋 Exemple de Format JSON - Avant/Après

## ❌ AVANT (format ancien - V2)

```json
{
  "fichier": "pages_cibles.pdf",
  "page": 1,
  "modele_detecte": "v2_ratio_based",
  "designation": "Marque et Modele",
  "specification": "A preciser",
  "proposition": "",
  "confiance_ocr": {
    "designation": 0,
    "specification": 93.0,
    "proposition": 0
  }
}
```

**Problème:** Toujours la clé générique `"specification"` même si le PDF dit "Exigé ou à préciser"

---

## ✅ APRÈS (format nouveau - avec détection)

```json
{
  "fichier": "pages_cibles.pdf",
  "page": 1,
  "lot": null,
  "modele_detecte": "modele_1_variant",
  "confiance_ocr": {
    "designation": 80,
    "specification": 50,
    "proposition": 25
  },
  "methode_mapping_headers": "exact_tolerant",
  "detected_headers": {
    "designation": "Désignation",
    "specification": "Exigé ou à préciser",
    "proposition": "Proposition"
  },
  "Désignation": "Marque et Modèle",
  "Exigé ou à préciser": "A préciser",
  "Proposition": "EPSON"
}
```

**Solution:** 
- ✅ La clé est maintenant `"Exigé ou à préciser"` (le vrai nom du header)
- ✅ Les métadonnées `detected_headers` montrent ce qui a été trouvé
- ✅ `modele_detecte: "modele_1_variant"` indique la variante détectée
- ✅ Plus de clés génériques (`designation`, `specification`, `proposition`)

---

## 🎯 Comparaison Visuelle

| Aspect | Ancien Format | Nouveau Format |
|--------|---------------|----------------|
| **Clé colonne 2** | `"specification"` | `"Exigé ou à préciser"` |
| **Clé colonne 1** | `"designation"` | `"Désignation"` |
| **Clé colonne 3** | `"proposition"` | `"Proposition"` |
| **Métadonnées** | ❌ Aucune | ✅ `detected_headers` |
| **Modèle** | `v2_ratio_based` | `modele_1_variant` |
| **Lisibilité** | 😐 Générique | 😊 Spécifique au document |

---

## 📊 Exemples avec Différents Headers

### Modèle 1 Standard
```json
{
  "Désignation": "Processeur",
  "Spécification": "Intel Core i7",
  "Proposition": "i7-12700K"
}
```

### Modèle 1 Variante (nouveau!)
```json
{
  "Désignation": "Processeur", 
  "Exigé ou à préciser": "Intel Core i7",
  "Proposition": "i7-12700K"
}
```

### Modèle 2
```json
{
  "Composants de l'offre": "Ordinateur portable",
  "Caractéristiques techniques minimales": "16 Go RAM",
  "Proposition": "32 Go DDR5"
}
```

---

## 💡 Comment Utiliser le JSON

### Option 1: Accès Direct par Nom Détecté
```python
# Si tu connais le header du document
for row in data:
    valeur = row["Exigé ou à préciser"]
    print(valeur)
```

### Option 2: Accès Dynamique via detected_headers
```python
# Marche avec tous les modèles
for row in data:
    headers = row["detected_headers"]
    colonne2_name = headers["specification"]
    valeur = row[colonne2_name]
    print(f"{colonne2_name}: {valeur}")
```

### Option 3: Retrouver les Clés Génériques
```python
# Si tu as besoin des anciennes clés dans confiance_ocr
for row in data:
    score = row["confiance_ocr"]["specification"]
    # Le score existe toujours avec la clé générique
```

---

## 🔧 Configuration

Pour désactiver cette fonctionnalité et revenir aux clés génériques:

```python
# Dans main.py ou ton script
to_json(results, "output.json", use_detected_headers=False)
```

Résultat: Les clés seront `"designation"`, `"specification"`, `"proposition"` comme avant.

---

## ✅ Statut Actuel

- ✅ Détection: `page_selector.py` reconnaît "Exigé ou à préciser"
- ✅ Extraction: `column_extractor.py` capture les noms détectés
- ✅ Export: `to_json()` remplace les clés génériques
- ✅ Main: `src/main.py` utilise le nouvel extracteur
- ✅ Tests: `test_header_detection.py` et `test_full_extraction.py`

**Le système est prêt! 🚀**
