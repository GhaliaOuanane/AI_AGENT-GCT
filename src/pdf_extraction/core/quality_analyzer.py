"""
Module d'analyse de qualité des valeurs extraites.

Remplace confiance_ocr par une analyse sémantique basée sur des règles.
"""

import re
from typing import Dict, Optional


# ============================================================================
# RÈGLES DE DÉTECTION DE VALEURS SUSPECTES
# ============================================================================

# Placeholders courants
PLACEHOLDER_PATTERNS = [
    r"^a\s+preciser$",
    r"^a\s+definir$",
    r"^n/?a$",
    r"^neant$",
    r"^aucun$",
    r"^sans\s+objet$",
    r"^\.\.\.$",
    r"^-+$",
    r"^_+$",
]

# Mots d'incertitude
UNCERTAINTY_KEYWORDS = [
    r"\bpreciser\b",
    r"\bdefinir\b",
    r"\bspecifier\b",
    r"\benvisager\b",
    r"\beventuel\b",
    r"\bpossible\b",
    r"\bprevoir\b",
]


def analyze_value_quality(value: str, context: Optional[Dict] = None) -> Dict[str, any]:
    """
    Analyse la qualité d'une valeur extraite.
    
    Args:
        value: Valeur extraite de la 2ème colonne
        context: Contexte documentaire (optionnel, pour stats futures)
    
    Returns:
        Dict avec {claire: bool, raison: str|null}
    """
    # Normaliser pour l'analyse
    normalized = value.lower().strip()
    
    # Règle 1: Valeur vide
    if not normalized:
        return {"claire": False, "raison": "valeur_vide"}
    
    # Règle 2: Placeholders explicites
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return {"claire": False, "raison": "placeholder_detecte"}
    
    # Règle 3: Mots d'incertitude
    for keyword in UNCERTAINTY_KEYWORDS:
        if re.search(keyword, normalized, re.IGNORECASE):
            return {"claire": False, "raison": "incertitude_detectee"}
    
    # Règle 4: Valeur très courte (< 3 caractères, sauf chiffres)
    if len(normalized) < 3 and not normalized.isdigit():
        return {"claire": False, "raison": "valeur_trop_courte"}
    
    # Règle 5: Caractères suspects (trop de symboles/ponctuation)
    symbol_ratio = len(re.findall(r"[^\w\s]", normalized)) / max(len(normalized), 1)
    if symbol_ratio > 0.3:
        return {"claire": False, "raison": "symboles_suspects"}
    
    # Valeur claire par défaut
    return {"claire": True, "raison": None}


def batch_analyze(values: list[str], context: Optional[Dict] = None) -> list[Dict]:
    """
    Analyse la qualité de plusieurs valeurs en batch.
    
    Args:
        values: Liste de valeurs extraites
        context: Contexte documentaire (optionnel)
    
    Returns:
        Liste de résultats d'analyse
    """
    return [analyze_value_quality(v, context) for v in values]
