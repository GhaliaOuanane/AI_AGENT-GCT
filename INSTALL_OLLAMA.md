# Installation et Test d'Ollama pour Validation LLM Locale

## Étape 1: Télécharger Ollama

1. Ouvrez votre navigateur web
2. Allez sur: **https://ollama.com/download/windows**
3. Téléchargez `OllamaSetup.exe`
4. Exécutez l'installateur et suivez les instructions

## Étape 2: Vérifier l'installation

Ouvrez PowerShell ou CMD et tapez:
```powershell
ollama --version
```

Vous devriez voir quelque chose comme: `ollama version 0.x.x`

## Étape 3: Télécharger le modèle recommandé

Le projet utilise **llama3.2:3b** (léger et rapide, ~2GB):

```powershell
ollama pull llama3.2:3b
```

⏱️ Cela peut prendre 5-10 minutes selon votre connexion Internet.

**Alternatives (si llama3.2 ne fonctionne pas):**
```powershell
ollama pull phi3:mini        # 3.8B, ~2.3GB, optimisé textes courts
ollama pull mistral:7b       # 7B, ~4GB, plus précis mais plus lent
```

## Étape 4: Tester Ollama

### Test 1: Vérifier que le serveur démarre

```powershell
ollama serve
```

Vous devriez voir:
```
Listening on 127.0.0.1:11434
```

**⚠️ Laissez cette fenêtre PowerShell ouverte!** Le serveur doit tourner en arrière-plan.

### Test 2: Tester le modèle (dans une NOUVELLE fenêtre PowerShell)

```powershell
ollama run llama3.2:3b "Bonjour, réponds en français"
```

Vous devriez recevoir une réponse en français du modèle.

### Test 3: Tester avec une question simple

```powershell
ollama run llama3.2:3b "Est-ce qu'un processeur i5 est conforme à une exigence de processeur i7 ? Réponds CONFORME ou NON_CONFORME puis explique en une phrase."
```

Le modèle devrait répondre avec un format proche de:
```
NON_CONFORME
Un processeur i5 ne satisfait pas l'exigence d'un i7 car il a des performances inférieures.
```

## Étape 5: Tester l'API HTTP (optionnel mais recommandé)

Ouvrez une nouvelle fenêtre PowerShell et testez l'API HTTP:

```powershell
$body = @{
    model = "llama3.2:3b"
    prompt = "Réponds uniquement: CONFORME ou NON_CONFORME"
    stream = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method Post -Body $body -ContentType "application/json"
```

Si vous voyez une réponse JSON avec un champ `response`, c'est bon! ✅

## Étape 6: Activer validation LLM dans le projet

Une fois Ollama installé et testé, éditez `src/pdf_extraction/main.py`:

**Cherchez cette ligne (environ ligne 168):**
```python
# from pdf_extraction.validation.llm_validator import validate_extractions_with_llm
# results = validate_extractions_with_llm(results)
```

**Décommentez pour activer:**
```python
from pdf_extraction.validation.llm_validator import validate_extractions_with_llm
results = validate_extractions_with_llm(results)
```

## Étape 7: Relancer le pipeline complet

**⚠️ IMPORTANT:** Assurez-vous que `ollama serve` tourne en arrière-plan!

```powershell
python src/main.py
```

Vous devriez voir les logs de validation LLM:
```
============================================================
VALIDATION LLM - COMPARAISON COLONNE 2 vs COLONNE 3
============================================================
[OK] Serveur Ollama accessible
[INFO] Modèle: llama3.2:3b
[INFO] 6 ligne(s) à valider

[1/6] Validation: Type de scanner...
    ✓ CONFORME: La proposition respecte le type exigé.
[2/6] Validation: Résolution minimale...
    ✗ NON_CONFORME: La résolution proposée est insuffisante.
...
```

## Dépannage

### Problème: "ollama: command not found" après installation

**Solution 1:** Redémarrez PowerShell ou votre ordinateur

**Solution 2:** Ajoutez manuellement Ollama au PATH:
1. Cherchez le dossier d'installation (généralement `C:\Users\<VotreNom>\AppData\Local\Programs\Ollama\`)
2. Ajoutez ce chemin aux variables d'environnement système

### Problème: "Serveur Ollama inaccessible"

**Vérifiez que le serveur tourne:**
```powershell
netstat -an | findstr "11434"
```

Si rien n'apparaît, démarrez le serveur:
```powershell
ollama serve
```

### Problème: Le modèle télécharge très lentement

**Utilisez un modèle plus petit:**
```powershell
ollama pull phi3:mini
```

Puis modifiez `src/pdf_extraction/validation/llm_validator.py` ligne 11:
```python
OLLAMA_MODEL = "phi3:mini"  # Au lieu de "llama3.2:3b"
```

### Problème: Le pipeline est trop lent

**Désactivez temporairement la validation LLM** en recommentant les lignes dans `main.py`:
```python
# from pdf_extraction.validation.llm_validator import validate_extractions_with_llm
# results = validate_extractions_with_llm(results)
```

L'extraction fonctionnera sans validation LLM (juste qualité OCR).

---

## Ressources

- Documentation Ollama: https://ollama.com/docs
- Liste des modèles disponibles: https://ollama.com/library
- API Reference: https://github.com/ollama/ollama/blob/main/docs/api.md
