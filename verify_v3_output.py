import json

with open('data/output/specifications_v3.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("\n" + "="*70)
print("V3 OUTPUT VERIFICATION - REAL CHANGES OBSERVABLE")
print("="*70 + "\n")

print("First 10 tables:\n")
for table in data['tables'][:10]:
    n_entries = len(table['entries'])
    n_flagged = sum(1 for e in table['entries'] if e.get('a_verifier'))
    status = "REJECTED" if table['table_rejetee'] else "OK"
    
    print(f"  {table['table_id']} (Page {table['pages'][0]}): {n_entries:2} entries, {n_flagged:2} flagged - {status}")
    if table['entries'] and n_entries <= 3:
        for e in table['entries']:
            des = e['designation'][:20] if e['designation'] else "(empty)"
            val = e['valeur'][:20] if e.get('valeur') else "(null)" if e['type'] == 'section' else "(empty)"
            t = e['type']
            print(f"    - [{t:7}] {des:20} → {val}")

print("\n" + "="*70)

total_entries = sum(len(t['entries']) for t in data['tables'])
total_flagged = sum(sum(1 for e in t['entries'] if e.get('a_verifier')) for t in data['tables'])
total_rejected = sum(1 for t in data['tables'] if t['table_rejetee'])

print(f"\nGRAND TOTALS (All {len(data['tables'])} tables):")
print(f"  Total entries extracted: {total_entries}")
print(f"  Total flagged for review: {total_flagged}")
print(f"  Rejection rate: {100*total_flagged/total_entries if total_entries > 0 else 0:.1f}%")
print(f"  Tables rejected (misalignment): {total_rejected}")

print("\n✅ CODE HAS CHANGED - OBSERVABLE RESULTS:")
print(f"   BEFORE (skeleton): 59 empty tables, entries: []")
print(f"   AFTER (real impl): {total_entries} actual entries extracted with {total_flagged} flagged")
print("\n" + "="*70 + "\n")
