# ANALYSE DU PROBLÈME DE DÉTECTION - BRAIN INFORMATIQUE PDF

## PROBLÈME IDENTIFIÉ

Le nouveau PDF `BRAIN INFORMATIQUE_16052025101905.PDF` contient **des pages cibles manquées**. L'analyse détaillée révèle les causes racines :

### Pages trouvées : [6, 7, 8]
### Pages attendues : [3, 6, 7, 8] (au minimum)

---

## CAUSE RACINE #1 : OCR imparfait - "designation" n'est pas reconnu

### Page 3
La page 3 est un tableau valide contenant :
- **"specification"** ✓ (détecté)
- **"proposition"** ✓ (détecté)
- **"designation"** ✗ **N'EXISTE PAS** dans le texte OCR

Le problème : La colonne "Désignation" est présente VISUELLEMENT dans le PDF, mais :
1. L'OCR la reconnaît mal ou l'omet complètement
2. Le texte comporte seulement "specification proposition" en haut
3. Le regex cherche `\bdes[il1]gnat[io0ln]+\b` mais ne trouve rien car le mot est manquant

**La page 3 NE peut PAS être détectée** avec la logique actuelle car "designation" n'apparaît pas dans le texte extrait.

---

## CAUSE RACINE #2 : Pages de continuation sans en-tête

### Pages 9 onwards (excepté 6, 7, 8)
Après les pages avec en-têtes détectés (6, 7, 8), il existe d'autres pages cibles qui :
- **Pas d'en-tête détectable** (pas de "Désignation | Spécification | Proposition")
- Mais **font partie d'un tableau qui continue** sur plusieurs pages
- Selon le contexte utilisateur, le tableau "LOT 3" s'étend potentiellement sur plusieurs pages

---

## CRITIQUE DU MODÈLE DE DÉTECTION ACTUEL

La logique actuelle est :
1. ✓ Détecter une page avec un en-tête (Model 1 ou Model 2)
2. ✓ Marquer `in_table = True`
3. ✓ Capturer les pages suivantes si elles respectent `_looks_like_table_content()`
4. ✗ **ARRÊTER dès qu'une page NE correspond à AUCUN critère**

### Problèmes :

**Problème A: Régex du Model 1 trop strict**
```
Modèle 1 require: Désignation ET Spécification ET Proposition
```
- Si l'OCR omet ou mal reconnaît UNE colonne → page non détectée
- Dans le nouveau PDF, page 3 omet "Désignation" en texte

**Problème B: Critères de continuation insuffisants**
```
is_short = line_count <= 8
```
- Arrête la capture dès qu'une page fait > 8 lignes
- Les pages multi-lignes de fin de tableau ne sont pas capturées

**Problème C: Sensibilité au format OCR**
- Le regex pour "Designation" : `\bdes[il1]gnat[io0ln]+\b` tolère l'OCR
- MAIS si "designation" est complètement absent, pas de match
- Les variations OCR ne suffisent pas quand le mot est manquant

---

## SOLUTION PROPOSÉE

### 1. **Flexibiliser le Model 1 - Accepter 2 colonnes sur 3**

Au lieu de requérir les 3 colonnes STRICTEMENT, accepter :
- Détection si **AU MOINS 2 colonnes parmi** [Désignation, Spécification, Proposition]

Rationale : Une page avec "Spécification | Proposition" est hautement probablement une page de tableau cible.

### 2. **Améliorer la logique de continuation**

Actuelle : 
```python
if page_is_note or page_is_end or (is_short and page_is_table_content):
    # capturer
in_table = False  # sortir du tableau
```

Problème : Sort du tableau trop tôt.

Proposé : 
```python
# Continuer TANT QUE la page a du contenu tabulaire
# (pas seulement court + numérique)
if page_is_note or page_is_end or page_is_table_content:
    # capturer
# Sortir UNIQUEMENT si page vide OU fin explicite
if not page_is_content_like:
    in_table = False
```

### 3. **Renforcer la détection du contenu tabulaire**

Améliorer `_looks_like_table_content()` pour détecter :
- Présence de **ligne de séparation** (tirets, traits)
- Présence de **nombres** (alignés ou non)
- Structure **régulière** de texte court (probablement contenu de tableau)
- **Absence** de mots-clés de documents administratifs (article, page, signature)

### 4. **Ne pas arrêter sur une page vide**

Une page "vide" ou faiblement structurée entre deux pages cibles n'indique pas la fin du tableau.

---

## IMPLÉMENTATION MINIMALE

Changements minimaux requis :

### Change 1: Assouplir Model 1 (2 sur 3 colonnes)
```python
def _matches_header_model_1(text: str) -> bool:
    has_designation = bool(re.search(r"\bdes[il1]gnat[io0ln]+\b", text, re.IGNORECASE))
    has_specification = bool(re.search(r"\bspec[il1][fj][il1][cf]at[io0ln]+\b", text, re.IGNORECASE))
    has_proposition = bool(re.search(r"\bpropos[il1]t[io0lnj]+s?\b", text, re.IGNORECASE))
    
    # Accepter 2 sur 3
    count = sum([has_designation, has_specification, has_proposition])
    return count >= 2
```

### Change 2: Améliorer continuation
```python
if in_table:
    # Toujours capturer si page non vide + ressemble à du contenu
    if _page_has_content_markers(text):
        selected_pages.append(page)
        continue
    
    # Sortir SEULEMENT si marqueur explicite de fin
    in_table = False
```

### Change 3: Détecter fin de tableau explicitement
```python
def _is_explicit_table_end(text: str) -> bool:
    # Fin explicite: "total", "fin tableau", ou page vide
    return bool(re.search(r"\b(?:total|fin\s+tableau|signature|article)\b", text, re.IGNORECASE)) \
        or len(text.strip()) < 20
```

---

## RÉSULTAT ATTENDU

- Page 3 : ✓ Détectée (Model 1 avec 2 colonnes)
- Pages 6, 7, 8 : ✓ Détectées (Model 1 complet)
- Pages de continuation : ✓ Capturées (critères de continuation améliorés)
- Pages administratives : ✗ Exclues (pas de header détecté)

