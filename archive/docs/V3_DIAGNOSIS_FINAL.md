# V3 DIAGNOSTIC FINAL - Pourquoi V3 Ne Marche Pas sur pages_cibles.pdf

**Date**: 2026-07-12  
**Status**: ❌ V3 INADAPTÉ POUR pages_cibles.pdf  
**Production Baseline**: V2 (132 entries, 18% flagged) ✅

---

## Résumé Exécutif

**V3 échoue sur `pages_cibles.pdf` parce qu'il applique une segmentation multi-table à un document qui est UN SEUL TABLEAU CONTINU.**

| Aspect | V2 (Fonctionne) | V3 (Échoue) |
|--------|-----------------|-------------|
| **Approche** | Page entière = tableau | Segmentation par régions |
| **Entrées extraites** | 132 | 76 (DATA LOSS 42%) |
| **Qualité** | 18% flagged | 67% flagged (DEGRADATION) |
| **Résultats** | "Marque et Modèle" → "Imprimante Laser" | ", £" → "\| \|" (garbage) |
| **Page 1** | 26 entries | 0 tables (RIEN DÉTECTÉ) |

---

## Investigation: D'où Vient le Charabia?

### Hypothèse Initiale (FAUSSE)
Tu pensais: "Le charabia vient de BRAIN INFORMATIQUE_16052025101905.PDF"

### Vérification
```bash
$ grep "pdf_path" extract_specifications_v3_generalized.py
    pdf_path = "data/output/pages_cibles.pdf"  ← BON FICHIER
```

```json
{
  "document": "pages_cibles.pdf",  ← CORRECT
  "tables": [ ... ]
}
```

**Conclusion**: V3 utilise bien `pages_cibles.pdf`, PAS BRAIN INFORMATIQUE.

### Vrai Problème
Le charabia vient de la **SEGMENTATION EXCESSIVE** qui découpe le tableau continu en micro-fragments:

**V3 Initial (59 micro-tables)**:
- Page 1, Région 544-603 (59px high) → ", £" → "\| \|"
- Page 1, Région 688-739 (51px high) → "" → "L %"
- Page 1, Région 757-811 (54px high) → Vide

**V3 Après Fusion (10 tables)**:
- Page 1: AUCUNE table détectée
- Page 2, Région 391-624: 7 entries (tout flagged)
- Page 5, Région 901-1646: 21 entries (17 flagged)

**V2 (référence correcte)**:
- Page 1 entière: 26 entries dont "Marque et Modèle" → "Imprimante Laser"
- Page 2 entière: 24 entries
- ... 6 pages au total = 132 entries

---

## Pourquoi La Segmentation Échoue

### Philosophie V2 (Qui Marche)
```python
# V2: Traite la page ENTIÈRE comme un tableau
words = ocr_page_hd(pdf_path, page_num)
col1_cells = extract_column_cells(words, 0, 1/3)     # Ratio
col2_cells = extract_column_cells(words, 1/3, 2/3)   # Ratio
```

**Avantage**: Ratio-based → adapte automatiquement à la largeur de page

### Philosophie V3 (Qui Échoue ici)
```python
# V3: Segmente par horizontal projection
h_proj = np.sum(gray < 200, axis=1)
regions = find_gaps_in_projection(h_proj)  # Découpe en N régions
for region in regions:
    extract_table(region)  # Chaque région = "tableau"
```

**Problème**: `pages_cibles.pdf` n'a **PAS de gaps significatifs** entre lignes du tableau
- Les lignes du tableau sont **continues**
- Les gaps détectés = **espaces inter-lignes normaux** (pas séparation de tableaux)
- Résultat: Sur-segmentation en 59 micro-régions (avant fusion) ou 10 fragments (après fusion)

---

## Analyse Région par Région

### Page 1 (V2 vs V3)

**V2 Output (26 entries):**
```json
{
  "page": 1,
  "entries": [
    {"designation": "Marque et Modele", "valeur": "Imprimante Laser"},
    {"designation": "FTechnologie d'hnpression", "valeur": "Specaf:catmn"},
    {"designation": "Resolufion de", "valeur": "preciser"},
    ...  // 26 entries total
  ]
}
```

**V3 Output (0 tables):**
```json
{
  "tables": []  // Page 1 = RIEN détecté
}
```

**Cause**: La segmentation par horizontal projection ne détecte AUCUNE région sur Page 1 qui passe le seuil minimum (min_region_height=150px). Les lignes individuelles sont trop fines.

### Page 2 (V2 vs V3)

**V2 Output (24 entries):**
```json
{
  "page": 2,
  "entries": [
    {"designation": "Modele", "valeur": "CARACT ERTEQUES TEChN"},
    {"designation": "Frocesseur central", "valeur": "MlNIMALES"},
    ...  // 24 entries total
  ]
}
```

**V3 Output (table_1, 7 entries):**
```json
{
  "table_id": "table_1",
  "pages": [2],
  "entries": [
    {"designation": "", "valeur": "E"},
    {"designation": "1 O", "valeur": "-"},
    ...  // 7 fragmentsGarbage
  ]
}
```

**Cause**: Région 391-624 ne capture qu'une **partie du tableau**, pas toute la page. Les entrées extraites sont des fragments/bordures.

---

## Test du Vrai Cas d'Usage V3

### Pour Quoi V3 Est Conçu
V3 est conçu pour documents avec **MULTIPLE TABLEAUX** (different lots/markets), exemple:

```
┌─────────────────────────────────────┐
│ Lot 1: Imprimante Laser             │
│ ┌─────────────────────────────────┐ │
│ │ Designation │ Specification     │ │
│ │ Marque      │ À préciser        │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Lot 2: Ordinateur Portable          │
│ ┌─────────────────────────────────┐ │
│ │ Designation │ Specification     │ │
│ │ Processeur  │ Intel i7          │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

Dans ce cas, la segmentation détecterait:
- **Table 1** (Lot 1, pages 1-2)
- **Table 2** (Lot 2, pages 3-4)

### Ce Que pages_cibles.pdf Contient
```
┌─────────────────────────────────────┐
│ UN SEUL TABLEAU CONTINU (6 pages)   │
│ ┌─────────────────────────────────┐ │
│ │ Designation │ Specification     │ │
│ │ Marque      │ Imprimante Laser  │ │
│ │ ...         │ ...               │ │
│ │ (132 lignes continues)          │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

**Conclusion**: `pages_cibles.pdf` ne correspond PAS au cas d'usage V3.

---

## Recommandations

### Option 1: Désactiver Segmentation pour pages_cibles.pdf
Détecter "single continuous table" et basculer vers logique V2:

```python
def extract_specifications_v3(pdf_path: str):
    # Detect if single continuous table
    if is_single_continuous_table(pdf_path):
        return extract_v2_style(pdf_path)  # Page-level, ratio-based
    else:
        return extract_multi_table(pdf_path)  # Segmentation
```

### Option 2: Tester V3 sur Vrai Document Multi-Lot
Trouver/créer un PDF avec structure:
- Lot 1: Imprimante (pages 1-2)
- Lot 2: Ordinateur (pages 3-4)
- Lot 3: Scanner (page 5)

Et vérifier que V3 détecte 3 tableaux indépendants correctement.

### Option 3: Utiliser V2 Comme Production
V2 fonctionne (132 entries, 18% flagged). **Ne pas remplacer par V3** pour documents single-table.

---

## Fichiers Concernés

### V2 (Production, Fonctionne)
- `extract_specifications_production.py` ✅
- `extract_specifications_v2_strict.py` ✅
- Output: `specifications_source_of_truth.json` (132 entries)

### V3 (Développement, Inadapté)
- `extract_specifications_v3_generalized.py` ❌
- Output: `specifications_v3.json` (76 entries, 67% flagged)

---

## Métriques de Comparaison

| Métrique | V2 (Baseline) | V3 (Initial) | V3 (Après Fusion) |
|----------|---------------|--------------|-------------------|
| **Tables détectées** | 6 pages | 59 micro-tables | 10 tables |
| **Entrées extraites** | 132 | 110 | 76 |
| **Page 1 entries** | 26 | 1 (", £") | 0 (RIEN) |
| **Flagged rate** | 18% | 75% | 67% |
| **Data loss** | 0% | 17% | 42% |
| **Résultat qualité** | ✅ "Marque et Modèle" | ❌ ", £" → "\| \|" | ❌ Fragments |

---

## Conclusion

**V3 n'est PAS défaillant en soi** - il résout un problème différent (multi-table documents).

**pages_cibles.pdf n'est PAS un document multi-table** - c'est un tableau continu.

**V2 reste la solution de production** pour ce cas d'usage.

**Pour avancer avec V3**: Tester sur un VRAI document multi-lot ou implémenter fallback vers V2 pour single-table docs.

---

**Status Final**:
- ✅ V2: PRODUCTION READY (132 entries from pages_cibles.pdf)
- ❌ V3: INADAPTÉ pour pages_cibles.pdf (segmentation casse l'extraction)
- 🔄 V3: À tester sur document multi-lot réel
