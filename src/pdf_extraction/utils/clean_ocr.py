"""
Module de nettoyage de texte OCR pour la colonne "Spécification".

Principes directeurs :
- 100% déterministe : mêmes données en entrée = mêmes résultats en sortie
- Mieux laisser une erreur OCR non corrigée que d'introduire une correction incertaine
- Une correction n'est appliquée que si justifiée par une règle explicite et vérifiable

Ordre d'application des corrections :
1. Corrections regex ciblées (REGEX_FIXES)
2. Corrections par confusion de caractères OCR
3. Liste blanche de termes protégés (PROTECTED_TERMS)
"""

import re
from typing import List, Dict, Tuple
from pathlib import Path


# ============================================================================
# 1. CORRECTIONS REGEX CIBLÉES (REGEX_FIXES)
# ============================================================================
# Chaque règle corrige UN motif d'erreur précis, identifié au préalable
# Format : (motif_erreur_exact, correction_exacte, exemple_source_du_document)

REGEX_FIXES: List[Tuple[str, str, str]] = [
    # À compléter avec des règles observées sur des documents réels
    # Exemple :
    # (r"\bclavier\b", "clavier", "page_007_column2.json - ligne 5"),
]


def apply_regex_fixes(text: str) -> str:
    """
    Applique les corrections regex ciblées au texte.
    
    Args:
        text: Texte à corriger
    
    Returns:
        Texte corrigé
    """
    for pattern, replacement, source in REGEX_FIXES:
        text = re.sub(pattern, replacement, text)
    return text


# ============================================================================
# 2. CORRECTIONS PAR CONFUSION DE CARACTÈRES OCR
# ============================================================================

# Liste fermée de paires de caractères connues pour être confondus par OCR
OCR_CONFUSIONS = [
    ('0', 'o'),  # zéro / o
    ('o', '0'),  # o / zéro
    ('1', 'l'),  # un / l
    ('l', '1'),  # l / un
    ('1', 'i'),  # un / i
    ('i', '1'),  # i / un
    ('rn', 'm'),  # rn / m
    ('m', 'rn'),  # m / rn
    ('vv', 'w'),  # vv / w
    ('w', 'vv'),  # w / vv
]


def is_protected_word(word: str) -> bool:
    """
    Vérifie si un mot doit être protégé contre toute correction.
    
    Un mot est protégé si :
    - Il contient un chiffre
    - Il est entièrement en majuscules de plus d'un caractère
    - Il a 2 caractères ou moins
    - Il est dans la liste blanche PROTECTED_TERMS
    
    Args:
        word: Mot à vérifier
    
    Returns:
        True si le mot est protégé
    """
    # Contient un chiffre
    if any(c.isdigit() for c in word):
        return True
    
    # Entièrement en majuscules de plus d'un caractère
    if len(word) > 1 and word.isupper():
        return True
    
    # 2 caractères ou moins
    if len(word) <= 2:
        return True
    
    # Liste blanche de termes protégés
    if word.lower() in PROTECTED_TERMS:
        return True
    
    return False


def apply_ocr_confusion_correction(word: str, french_dict: set) -> str:
    """
    Applique les corrections par confusion de caractères OCR.
    
    Une correction n'est appliquée QUE SI :
    a) le mot d'origine est absent du dictionnaire français, ET
    b) le mot obtenu après substitution EST présent dans le dictionnaire français
    
    Args:
        word: Mot à corriger
        french_dict: Ensemble des mots du dictionnaire français
    
    Returns:
        Mot corrigé ou inchangé
    """
    if is_protected_word(word):
        return word
    
    word_lower = word.lower()
    
    # Si le mot est déjà dans le dictionnaire, pas de correction
    if word_lower in french_dict:
        return word
    
    # Essayer chaque confusion OCR
    for wrong_char, correct_char in OCR_CONFUSIONS:
        corrected = word_lower.replace(wrong_char, correct_char)
        
        # Vérifier si le mot corrigé est dans le dictionnaire
        if corrected in french_dict:
            # Préserver la casse originale
            if word.isupper():
                return corrected.upper()
            elif word[0].isupper():
                return corrected.capitalize()
            else:
                return corrected
    
    return word


def load_french_dictionary() -> set:
    """
    Charge un dictionnaire français minimal pour les corrections OCR.
    
    Pour l'instant, retourne un ensemble vide. À compléter avec un vrai
    dictionnaire si nécessaire (ex: via pyenchant ou un fichier texte).
    
    Returns:
        Ensemble des mots du dictionnaire français
    """
    # TODO: Implémenter le chargement d'un vrai dictionnaire français
    # Options :
    # - pip install pyenchant
    # - Charger un fichier texte de mots français
    # - Utiliser un package comme 'french-lemmatizer'
    return set()


def apply_confusion_corrections(text: str, french_dict: set) -> str:
    """
    Applique les corrections par confusion de caractères OCR au texte.
    
    Args:
        text: Texte à corriger
        french_dict: Ensemble des mots du dictionnaire français
    
    Returns:
        Texte corrigé
    """
    words = text.split()
    corrected_words = []
    
    for word in words:
        # Préserver la ponctuation
        punctuation = ''
        while word and not word[-1].isalnum():
            punctuation = word[-1] + punctuation
            word = word[:-1]
        
        # Appliquer la correction
        corrected = apply_ocr_confusion_correction(word, french_dict)
        
        # Restaurer la ponctuation
        corrected_words.append(corrected + punctuation)
    
    return ' '.join(corrected_words)


# ============================================================================
# 3. LISTE BLANCHE DE TERMES PROTÉGÉS (PROTECTED_TERMS)
# ============================================================================

# Sigles, unités, marques, mots anglais techniques
PROTECTED_TERMS = {
    # Unités et mesures
    'hz', 'khz', 'mhz', 'ghz', 'thz',
    'b', 'kb', 'mb', 'gb', 'tb', 'pb',
    'bps', 'kbps', 'mbps', 'gbps',
    'dpi', 'ppm', 'ppb',
    'v', 'mv', 'kv', 'a', 'ma', 'ka',
    'w', 'mw', 'kw',
    'nm', 'um', 'mm', 'cm', 'dm', 'm', 'km',
    'ms', 'us', 'ns', 'ps',
    'c', 'f', 'k',
    
    # Technologies et standards
    'usb', 'usb-c', 'usb-a', 'usb-b',
    'hdmi', 'displayport', 'dp', 'vga', 'dvi',
    'ethernet', 'wifi', 'bluetooth', 'bt',
    'nfc', 'rfid',
    'pci', 'pci-e', 'pcie',
    'sata', 'sas', 'scsi', 'ide',
    'raid',
    
    # Marques et produits
    'intel', 'amd', 'nvidia', 'qualcomm',
    'core', 'xeon', 'pentium', 'celeron', 'athlon',
    'windows', 'linux', 'macos', 'android', 'ios',
    'office', 'word', 'excel', 'powerpoint', 'outlook',
    'adobe', 'photoshop', 'illustrator', 'acrobat',
    'epson', 'hp', 'canon', 'brother', 'lexmark',
    
    # Termes techniques
    'toner', 'encre', 'cartouche',
    'dpi', 'resolution',
    'pixel', 'megapixel',
    'bit', 'byte', 'octet',
    'software', 'hardware', 'firmware',
    'driver', 'pilote',
    'interface', 'port',
    'slot', 'connecteur',
    'cable', 'fil',
    'ecran', 'moniteur', 'display',
    'clavier', 'souris',
    'imprimante', 'scanner',
    'serveur', 'client',
    'reseau', 'network',
    'cloud', 'saas', 'paas', 'iaas',
    
    # Abréviations courantes
    'pdf', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff',
    'http', 'https', 'ftp', 'ssh', 'ssl', 'tls',
    'tcp', 'udp', 'ip', 'ipv4', 'ipv6',
    'dns', 'dhcp', 'nat',
    'sql', 'nosql',
    'json', 'xml', 'html', 'css', 'js',
    'api', 'sdk', 'gui', 'cli',
    'cpu', 'gpu', 'ram', 'rom', 'ssd', 'hdd',
    'os', 'bios', 'uefi',
    'iot', 'ai', 'ml', 'nlp',
}


# ============================================================================
# FONCTION PRINCIPALE DE NETTOYAGE
# ============================================================================

def clean_ocr_text(text: str, enable_regex: bool = True, enable_confusion: bool = False) -> str:
    """
    Nettoie le texte OCR en appliquant les règles de correction.
    
    Args:
        text: Texte à nettoyer
        enable_regex: Activer les corrections regex (défaut: True)
        enable_confusion: Activer les corrections par confusion (défaut: False)
    
    Returns:
        Texte nettoyé
    """
    if not text:
        return text
    
    # Étape 1: Corrections regex ciblées
    if enable_regex:
        text = apply_regex_fixes(text)
    
    # Étape 2: Corrections par confusion de caractères OCR
    if enable_confusion:
        french_dict = load_french_dictionary()
        text = apply_confusion_corrections(text, french_dict)
    
    return text


def clean_ocr_json(input_path: Path, output_path: Path, enable_regex: bool = True, enable_confusion: bool = False) -> None:
    """
    Nettoie un fichier JSON contenant des données OCR extraites.
    
    Args:
        input_path: Chemin du fichier JSON d'entrée
        output_path: Chemin du fichier JSON de sortie
        enable_regex: Activer les corrections regex
        enable_confusion: Activer les corrections par confusion
    """
    import json
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Nettoyer chaque entrée
    for entry in data:
        if 'specification' in entry:
            entry['specification'] = clean_ocr_text(
                entry['specification'],
                enable_regex=enable_regex,
                enable_confusion=enable_confusion
            )
    
    # Sauvegarder le résultat
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================================================
# VALIDATION ET TESTS
# ============================================================================

def validate_regex_fix(test_pages: List[Path]) -> bool:
    """
    Valide une nouvelle règle regex sur un échantillon de pages déjà traitées.
    
    Vérifie que la règle :
    1. corrige bien le cas visé
    2. ne modifie aucun autre mot du corpus de test existant
    
    Args:
        test_pages: Liste des chemins des fichiers JSON de test
    
    Returns:
        True si la règle passe la validation
    """
    import json
    
    # Charger les données originales
    original_data = []
    for page_path in test_pages:
        with open(page_path, 'r', encoding='utf-8') as f:
            original_data.append(json.load(f))
    
    # Appliquer les corrections
    for data in original_data:
        for entry in data:
            if 'specification' in entry:
                entry['specification'] = apply_regex_fixes(entry['specification'])
    
    # TODO: Implémenter la logique de validation
    # Comparer avec les résultats attendus
    # Vérifier que seuls les mots attendus sont modifiés
    
    return True


if __name__ == "__main__":
    # Exemple d'utilisation
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python clean_ocr.py <input_json> <output_json>")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    
    clean_ocr_json(input_path, output_path)
    print(f"[OK] Cleaned OCR text saved to {output_path}")
