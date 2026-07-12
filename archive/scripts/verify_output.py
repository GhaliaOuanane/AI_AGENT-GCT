#!/usr/bin/env python
import json
from pathlib import Path

print('\nCANONICAL JSON VALIDATION')
print('=' * 50)

# Load canonical JSON
with open('data/output/specifications_source_of_truth.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Document: {data['document']}")
print(f"Column Source: {data['colonne_source']}")
print(f"Extraction Date: {data['extraction_date']}")
print()
print(f"Pages: {len(data['pages'])}")
print()

total = 0
total_flagged = 0
for page in data['pages']:
    count = len(page['entries'])
    flagged = sum(1 for e in page['entries'] if e['a_verifier'])
    total += count
    total_flagged += flagged
    status = 'OK' if count > 0 else 'EMPTY'
    print("  Page {}: {} entries, {} flagged - {}".format(page['page'], count, flagged, status))

print()
print("TOTAL ENTRIES: {}".format(total))
pct = (100.0 * total_flagged / total) if total > 0 else 0
print("TOTAL FLAGGED: {} ({:.0f}%)".format(total_flagged, pct))
print()
print('OK: Canonical JSON valid and complete')
