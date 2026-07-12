import json

with open('data/output/extraction.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("\n" + "="*70)
print("VERIFICATION extraction.json")
print("="*70 + "\n")

if data:
    print(f"Fichier source: {data[0]['fichier']}")
    print(f"Total lignes extraites: {len(data)}\n")
    
    print("Premières 10 lignes:\n")
    for i, row in enumerate(data[:10], 1):
        page = row.get('page', '?')
        des = row.get('designation', '')[:40] or "(vide)"
        spec = row.get('specification', '')[:40] or "(vide)"
        
        print(f"  {i}. Page {page}: {des:40} -> {spec}")
    
    print("\n" + "="*70)
    
    # Vérifier si c'est du bon contenu (pas BRAIN INFORMATIQUE)
    if "BRAIN INFORMATIQUE" in data[0]['fichier']:
        print("❌ ERREUR: Extrait depuis BRAIN INFORMATIQUE (pas pages_cibles.pdf)")
    elif "pages_cibles" in data[0]['fichier']:
        print("✅ OK: Extrait depuis pages_cibles.pdf")
    
    print("="*70 + "\n")
else:
    print("❌ Fichier vide!")
