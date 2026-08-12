"""
Module de validation par LLM local (Ollama).

Compare la colonne 2 (spécification technique exigée) avec la colonne 3 (proposition soumissionnaire)
pour déterminer la conformité, en tenant compte de la fiabilité OCR et des débordements de texte.
"""

import requests
import re
from typing import Dict, List, Optional
import json


# Configuration Ollama
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:3b"  # Modèle léger pour comparaisons courtes


def check_ollama_server() -> bool:
    """
    Vérifie que le serveur Ollama local est accessible.
    
    Returns:
        True si le serveur répond, False sinon
    """
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def compare_specification_with_llm(
    specification: str,
    proposition: str,
    ocr_confidence: int,
    has_overflow: bool
) -> Dict[str, str]:
    """
    Compare une spécification technique (colonne 2) avec une proposition (colonne 3) via LLM local.
    
    Args:
        specification: Texte de la spécification technique exigée
        proposition: Texte de la proposition du soumissionnaire
        ocr_confidence: Score de confiance OCR (0-100) pour la proposition
        has_overflow: True si débordement de texte détecté
    
    Returns:
        Dict avec clés:
        - statut: "conforme" | "non_conforme" | "a_verifier_manuellement"
        - commentaire: Explication courte
        - raison_verification: Raison si statut = a_verifier_manuellement
    """
    LOW_CONFIDENCE_THRESHOLD = 60
    
    # GARDE-FOU 1: Confiance OCR faible => à vérifier manuellement
    if ocr_confidence < LOW_CONFIDENCE_THRESHOLD:
        return {
            "statut": "a_verifier_manuellement",
            "commentaire": f"OCR peu fiable (confiance {ocr_confidence}%). Texte manuscrit probablement mal reconnu.",
            "raison_verification": "ocr_faible_confiance"
        }
    
    # GARDE-FOU 2: Débordement détecté => à vérifier manuellement
    if has_overflow:
        return {
            "statut": "a_verifier_manuellement",
            "commentaire": "Débordement de texte détecté. Risque de désalignement entre lignes.",
            "raison_verification": "debordement_texte"
        }
    
    # GARDE-FOU 3: Proposition vide => non conforme
    if not proposition or proposition.strip() == "":
        return {
            "statut": "non_conforme",
            "commentaire": "Aucune proposition fournie par le soumissionnaire.",
            "raison_verification": None
        }
    
    # Appel LLM pour comparaison
    try:
        if not check_ollama_server():
            return {
                "statut": "a_verifier_manuellement",
                "commentaire": "Serveur Ollama inaccessible. Impossible de valider automatiquement.",
                "raison_verification": "llm_indisponible"
            }
        
        # Prompt optimisé pour comparaison courte - TRÈS DIRECTIF
        prompt = f"""TÂCHE: Évalue la conformité technique.

SPÉCIFICATION EXIGÉE:
{specification}

PROPOSITION SOUMISSIONNAIRE:
{proposition}

INSTRUCTIONS STRICTES:
1. Compare UNIQUEMENT ces deux textes
2. Réponds en FRANÇAIS
3. Première ligne: UNIQUEMENT le mot "CONFORME" OU "NON_CONFORME" (rien d'autre)
4. Deuxième ligne: explication courte (maximum 2 phrases)

INTERDICTIONS:
- PAS de préambule ("Je suis prêt à...", "Je vais analyser...")
- PAS de reformulation de la tâche
- PAS de phrases d'introduction

EXEMPLE RÉPONSE VALIDE:
CONFORME
La proposition respecte toutes les exigences techniques spécifiées.

COMMENCE MAINTENANT TA RÉPONSE:"""

        # Appel API Ollama
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Faible température = réponses plus déterministes
                    "num_predict": 100   # Limiter longueur réponse
                }
            },
            timeout=30
        )
        
        if response.status_code != 200:
            return {
                "statut": "a_verifier_manuellement",
                "commentaire": f"Erreur LLM (code {response.status_code}).",
                "raison_verification": "llm_erreur"
            }
        
        llm_response = response.json().get("response", "").strip()
        
        # NETTOYAGE: Retirer préambules courants
        llm_response = re.sub(r"^(Je suis prêt à|Je vais|Voici|Analyse|Évaluation|Résultat).*?\n", "", llm_response, flags=re.IGNORECASE | re.MULTILINE)
        llm_response = llm_response.strip()
        
        # Parser la réponse du LLM
        lines = [l.strip() for l in llm_response.split('\n') if l.strip()]
        if not lines:
            return {
                "statut": "a_verifier_manuellement",
                "commentaire": "Réponse LLM vide ou invalide.",
                "raison_verification": "llm_reponse_invalide"
            }
        
        first_line = lines[0].upper()
        commentaire = ' '.join(lines[1:]) if len(lines) > 1 else "Voir spécification."
        
        # RETRY LOGIC: Si première ligne ne contient pas de statut clair, chercher dans les lignes suivantes
        if "CONFORME" not in first_line:
            # Chercher dans toutes les lignes
            for line in lines:
                line_upper = line.upper()
                if "NON" in line_upper and "CONFORME" in line_upper:
                    first_line = "NON_CONFORME"
                    commentaire = ' '.join([l for l in lines if l != line])[:200]
                    break
                elif "CONFORME" in line_upper:
                    first_line = "CONFORME"
                    commentaire = ' '.join([l for l in lines if l != line])[:200]
                    break
        
        if "CONFORME" in first_line and "NON" not in first_line:
            statut = "conforme"
        elif "NON" in first_line and "CONFORME" in first_line:
            statut = "non_conforme"
        else:
            # Réponse ambiguë
            return {
                "statut": "a_verifier_manuellement",
                "commentaire": f"Réponse LLM ambiguë: {llm_response[:100]}",
                "raison_verification": "llm_reponse_ambigue"
            }
        
        return {
            "statut": statut,
            "commentaire": commentaire[:200],  # Limiter longueur
            "raison_verification": None
        }
    
    except requests.exceptions.Timeout:
        return {
            "statut": "a_verifier_manuellement",
            "commentaire": "Timeout LLM (>30s). Serveur Ollama surchargé ou modèle non chargé.",
            "raison_verification": "llm_timeout"
        }
    except Exception as e:
        return {
            "statut": "a_verifier_manuellement",
            "commentaire": f"Erreur inattendue: {str(e)[:100]}",
            "raison_verification": "llm_exception"
        }


def validate_extractions_with_llm(extractions: List[Dict]) -> List[Dict]:
    """
    Valide chaque ligne extraite en comparant colonne 2 vs colonne 3 via LLM local.
    
    Args:
        extractions: Liste de dicts {cle, valeur, proposition, confiance_ocr_proposition, debordement_detecte, ...}
    
    Returns:
        Liste enrichie avec champ "validation_llm" ajouté à chaque entrée
    """
    print("\n============================================================")
    print("VALIDATION LLM - COMPARAISON COLONNE 2 vs COLONNE 3")
    print("============================================================")
    
    # Vérifier disponibilité Ollama avant de démarrer
    if not check_ollama_server():
        print("[ERROR] Serveur Ollama inaccessible sur http://localhost:11434")
        print("[ERROR] Assurez-vous qu'Ollama est installé et démarré:")
        print("[ERROR]   1. Télécharger: https://ollama.com/download/windows")
        print("[ERROR]   2. Installer OllamaSetup.exe")
        print("[ERROR]   3. Télécharger le modèle: ollama pull llama3.2:3b")
        print("[ERROR]   4. Démarrer le serveur: ollama serve")
        print("[WARN] Toutes les lignes seront marquées 'a_verifier_manuellement'")
        print()
        
        # Marquer toutes les lignes comme à vérifier
        for entry in extractions:
            entry["validation_llm"] = {
                "statut": "a_verifier_manuellement",
                "commentaire": "Serveur Ollama inaccessible.",
                "raison_verification": "llm_indisponible"
            }
        return extractions
    
    print(f"[OK] Serveur Ollama accessible")
    print(f"[INFO] Modèle: {OLLAMA_MODEL}")
    print(f"[INFO] {len(extractions)} ligne(s) à valider\n")
    
    validated_count = {"conforme": 0, "non_conforme": 0, "a_verifier_manuellement": 0}
    
    for idx, entry in enumerate(extractions, 1):
        specification = entry.get("valeur", "")
        proposition = entry.get("proposition", "")
        ocr_conf = entry.get("confiance_ocr_proposition", 0)
        has_overflow = entry.get("debordement_detecte", False)
        
        print(f"[{idx}/{len(extractions)}] Validation: {entry.get('cle', 'N/A')[:40]}...")
        
        validation_result = compare_specification_with_llm(
            specification=specification,
            proposition=proposition,
            ocr_confidence=ocr_conf,
            has_overflow=has_overflow
        )
        
        entry["validation_llm"] = validation_result
        validated_count[validation_result["statut"]] += 1
        
        # Log résultat
        statut_emoji = {
            "conforme": "✓",
            "non_conforme": "✗",
            "a_verifier_manuellement": "?"
        }
        emoji = statut_emoji.get(validation_result["statut"], "?")
        print(f"    {emoji} {validation_result['statut'].upper()}: {validation_result['commentaire'][:80]}")
    
    print(f"\n[RÉSUMÉ VALIDATION]")
    print(f"  Conformes: {validated_count['conforme']}")
    print(f"  Non conformes: {validated_count['non_conforme']}")
    print(f"  À vérifier manuellement: {validated_count['a_verifier_manuellement']}")
    print()
    
    return extractions
