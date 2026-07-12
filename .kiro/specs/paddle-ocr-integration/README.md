# 🎯 Spec : Intégration PaddleOCR comme Fallback

## 📄 Documents Disponibles

Cette spec est organisée en 4 documents complémentaires :

### 1. **SPEC.md** - Vue d'ensemble générale
- Objectifs du projet
- Architecture générale du pipeline
- Flux décisionnel (Tesseract → PaddleOCR)
- Format des données (JSON structuré)
- Résumé des tests et validation

**Pour :** Comprendre QUOI faire et POURQUOI

---

### 2. **DESIGN.md** - Architecture détaillée du code
- Hiérarchie complète des classes
- Implémentation TesseractOCR (détaillée)
- Implémentation PaddleOCREngine (détaillée)
- Router et fallback logic
- Intégration dans column_extractor.py

**Pour :** Comprendre COMMENT faire (signatures, logique, patterns)

**À utiliser pendant l'implémentation pour copier/adapter le code**

---

### 3. **MIGRATION.md** - Points d'intégration et pratique
- Backward compatibility assurée
- Points d'intégration clés (fichiers à modifier, lignes de code)
- Étapes d'implémentation ordonnées
- Dépannage et troubleshooting
- Checklist d'intégration

**Pour :** Intégrer PaddleOCR progressivement dans le code existant

**À utiliser comme guide pratique pendant le refactoring**

---

### 4. **ACCEPTANCE.md** - Critères de succès et validation
- Critères d'acceptation par component
- Scénarios de test (happy path, fallback, etc.)
- Benchmarks de performance
- Checklist de validation avant merge
- Sign-off final

**Pour :** Valider que tout marche correctement

**À utiliser après implémentation pour tester et valider**

---

## 🚀 Quick Start (Ordre de Lecture)

### Pour les Product Owners / Reviewers
1. Lire cette intro
2. Lire SPEC.md (Vue d'ensemble)
3. Lire ACCEPTANCE.md (Critères de succès)

### Pour les Développeurs
1. Lire cette intro
2. Lire SPEC.md (Comprendre le "quoi")
3. Lire DESIGN.md (Copier/adapter l'architecture)
4. Lire MIGRATION.md (Intégrer dans le code existant)
5. Implémente (voir tasks.md)
6. Valider avec ACCEPTANCE.md

### Pour les DevOps / Tests
1. Lire ACCEPTANCE.md (Tests)
2. Lire MIGRATION.md (Checklist)
3. Valider avec les tests

---

## 📋 tasks.md - Tâches d'Implémentation

Document séparé listant 15 tâches concrètes organisées en 5 phases :

- **Phase 1 : Setup** (3 tasks)
- **Phase 2 : Intégration** (3 tasks)
- **Phase 3 : CLI** (2 tasks)
- **Phase 4 : Tests** (4 tasks)
- **Phase 5 : Documentation** (3 tasks)

Chaque task inclut :
- Objectif clair
- Fichier(s) à modifier
- Éléments à implémenter
- Tests attendus
- Livrable

---

## 🎯 Objectifs du Projet

### Court terme (cette spec)
✅ Ajouter PaddleOCR comme **fallback optionnel**  
✅ Tesseract reste le moteur par défaut (zéro impact si PaddleOCR absent)  
✅ Fallback automatique en cas d'erreur ou confiance basse (<70%)  
✅ Router intelligente avec stats de fallback  
✅ Support GPU optionnel (auto-détecté)  
✅ JSON structuré avec `ocr_details` par colonne  

### Long terme (pas dans cette spec)
🔮 Fine-tuning des modèles Paddle sur documents métier  
🔮 Cache LRU pour cellules identiques  
🔮 Multi-GPU support  
🔮 Modèles spécialisés pour manuscrit  

---

## 📊 Impact Prévisible

### Avant
```
OCR = Tesseract uniquement
├─ Performance ✓ (rapide, léger)
├─ Robustesse ⚠ (faible sur bruit)
└─ Manuscrit ✗ (très mauvais)
```

### Après
```
OCR = Tesseract → PaddleOCR (fallback)
├─ Performance ✓ (Tesseract rapide, Paddle rare)
├─ Robustesse ✓ (PaddleOCR pour cas difficiles)
├─ Manuscrit ⚠ (mieux, pas parfait)
├─ GPU optionnel ✓ (pérf +40% si dispo)
└─ Backward compat ✓ (zéro breaking change)
```

---

## 💾 Dépendances Ajoutées

```
paddleocr>=2.7.0              (150KB)
paddlepaddle>=2.5.0           (100MB, CPU)
paddlepaddle-gpu>=2.5.0       (optionnel, pour GPU)
```

**Installation :**
```bash
# Setup standard (CPU)
pip install -r requirements.txt

# Setup avec GPU (optionnel)
pip install paddlepaddle-gpu
python src/main.py --gpu
```

---

## 🧪 Validation

### Tests à implémenter
- ✓ Unitaires : OCREngine classes (8+ tests)
- ✓ Intégration : Router + column_extractor (5+ tests)
- ✓ Performance : Benchmarks (comparaison temps/RAM)
- ✓ Précision : F1-score vs Tesseract

### Couverture minimale
- Tests > 80% couverture
- Fallback sur erreur validé
- Fallback sur confiance basse validé
- Mode tesseract-only marche sans Paddle

### Performance acceptable
- Tesseract : ≤200ms/cell (inchangé)
- Hybrid : ≤250ms/cell avg (5% overhead)
- Paddle (CPU) : ≤500ms/cell
- Paddle (GPU) : ≤300ms/cell

---

## 🔐 Backward Compatibility

**✅ Garanti :**
- Mode "tesseract" par défaut = zéro impact si PaddleOCR absent
- Ancien JSON compatible (ocr_details optionnel)
- Ancien code marche sans modification (opt-in)
- Rollback possible en 1 git revert

**⚠️ À noter :**
- RAM légèrement plus haute en mode hybrid (2 engines loaded)
- Nouveau champ `ocr_details` dans JSON (optionnel, peut être ignoré)

---

## 🐛 Troubleshooting Rapide

| Problème | Solution |
|----------|----------|
| `ImportError: paddleocr` | `pip install paddleocr paddlepaddle` |
| GPU non détecté | `python -c "import torch; print(torch.cuda.is_available())"` |
| Paddle fallback jamais appelé | Normal ! Tesseract marche bien. Check stats avec `--ocr-stats` |
| Crash en mode hybrid | Tesseract crash → vérifier fra.traineddata, relancer avec `--ocr-mode paddle` pour debug |
| RAM trop haute | Utiliser mode "tesseract" ou réduire taille batch |

---

## 📞 Questions Fréquentes

### Q: Pourquoi PaddleOCR en fallback et pas primaire ?
**A:** Tesseract est **5x plus rapide** sur texte imprimé standard. PaddleOCR n'est utile que sur scans bruités/manuscrits. Fallback = le meilleur des deux mondes.

### Q: GPU est-il obligatoire ?
**A:** Non. PaddleOCR marche en CPU. GPU ~2x plus rapide mais optionnel. Tesseract reste le moteur par défaut (no GPU needed).

### Q: Quel impact sur la performance globale ?
**A:** Zéro en mode "tesseract". +5% en mode "hybrid" (si peu de fallbacks). Acceptable car fallback rare sur PDFs bien scannés.

### Q: Et si je veux juste Tesseract pour toujours ?
**A:** `python src/main.py --ocr-mode tesseract`. Zéro changement par rapport à avant. PaddleOCR reste inutilisé.

### Q: Quand activer le fallback PaddleOCR ?
**A:** 
- Scans bruités/anciens
- Beaucoup de manuscrit
- Qualité d'impression médiocre
En cas de doute, mode "hybrid" décide automatiquement.

---

## 📈 Timeline Estimée

| Phase | Durée | Status |
|-------|-------|--------|
| Phase 1 (Setup) | 1-2j | À faire |
| Phase 2 (Intégration) | 1j | À faire |
| Phase 3 (CLI) | 0.5j | À faire |
| Phase 4 (Tests) | 1-2j | À faire |
| Phase 5 (Docs) | 0.5j | À faire |
| **TOTAL** | **4-6j** | **En cours** |

**Checkpoint intermédiaire recommandé après Phase 2** (avant de continuer, valider que hybrid marche sur PDF réel)

---

## ✅ Next Steps

1. **Lire SPEC.md** pour bien comprendre l'architecture
2. **Lire DESIGN.md** pour obtenir les implémentations détaillées
3. **Lire MIGRATION.md** pour savoir où intégrer le code
4. **Consulter tasks.md** pour les tâches concrètes
5. **Commencer par Phase 1 (Setup)** : créer ocr_engine.py + dépendances
6. **Valider avec Phase 2 (Intégration)** : tester sur PDF réel
7. **Finaliser avec Phases 3-5** : CLI, tests, docs
8. **Valider avec ACCEPTANCE.md** : critères de succès

---

## 📞 Support

En cas de question ou blocage :
- Relire le document pertinent (SPEC / DESIGN / MIGRATION)
- Vérifier ACCEPTANCE.md pour les critères attendus
- Consulter la section Troubleshooting ci-dessus
- Si besoin, créer une issue avec `[PADDLE_OCR]` tag

---

**Spec Version:** 1.0  
**Date:** Juillet 2026  
**Status:** 📋 Ready for Implementation

