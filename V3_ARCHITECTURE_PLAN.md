# EXTRACTION SPÉCIFICATIONS V3 - ARCHITECTURE & IMPLEMENTATION PLAN

**Status**: SKELETON COMPLETE, ÉTAPES 1-2 FUNCTIONAL, ÉTAPES 2bis-7 TO DO  
**Date**: 2026-07-12  
**Current Output**: 59 table regions detected from 6 pages

---

## V3 Overview: Multi-Table Generalization

### Key Differences from V2

| Aspect | V2 (Single Table) | V3 (Multi-Table) |
|--------|------------------|------------------|
| **Input Assumption** | One table per document | Multiple tables (lots/markets) per document |
| **Segmentation** | None (assume whole document is one table) | **ÉTAPE 0**: Detect separate tables by region, title, column count, gaps |
| **Processing Unit** | Per-page validation | Per-table validation (table can span multiple pages) |
| **Grid Detection** | Single pass | **Multi-pass** (robust to scan quality variations) |
| **Output Format** | 132 entries flat | One JSON with multiple tables array |
| **Section Rows** | Not distinguished | **Type field**: "section" vs "donnée" |

---

## Implementation Status

### ✅ COMPLETED ÉTAPES

#### Étape 0: Segmentation en Tableaux
- ✅ Detect table regions by horizontal projection gaps
- ✅ Identify Y-ranges where content clusters
- ✅ Create TableRegion objects (page, x_min, y_min, x_max, y_max)
- ✅ Handle multiple regions per page
- **Result**: 59 valid table regions detected from 6 pages

#### Étape 1: Grid Detection (Multi-Pass Robust)
- ✅ Pass 1: Standard adaptive thresholding + morphological operators
- ✅ Pass 2: Softer thresholds if Pass 1 line count too low
- ✅ Line extraction: horizontal and vertical separately
- ✅ Clustering: group nearby lines into logical rows/cols
- ✅ Validation: ≥3 horizontal AND ≥2 vertical lines
- **Result**: 59 grids detected, 6 failures (fragments or non-tables)

#### Étape 2: Header Detection (Fuzzy Matching)
- ✅ OCR first row of each table region
- ✅ Match against extensive alias lists (col1, col2, col3)
- ✅ Fuzzy matching: substring containment (can enhance with Levenshtein)
- ✅ Flag suspicious headers (motif: "entete_suspecte")
- **Result**: Headers extracted, ready for content matching

---

### 🔄 IN PROGRESS / TODO

#### Étape 2bis: Section Row Detection
**What it is**: A row where Désignation is non-empty but BOTH Spécification and Proposition are empty. This is a grouping header (e.g., "Processeur central", "Mémoire"), not a data anomaly.

**Implementation needed**:
```python
def is_section_row(des_text, spec_text, prop_text):
    return (
        des_text.strip() != "" and
        spec_text.strip() == "" and
        (prop_text is None or prop_text.strip() == "")
    )
```

**Output**: Mark as `"type": "section"`, `"valeur": null`, exclude from line count validation

---

#### Étape 3: Structural Validation (Per Table)
**Requirement**: Count data lines (exclude sections, headers) separately for col1 and col2.
Must be: `nb_lignes_designation == nb_lignes_specification`

**Why stricter than V2**:
- V2 checked page-level (could have sections miscounted)
- V3 checks table-level (single table may span multiple pages)
- Must account for sections properly

**Implementation needed**:
```python
def validate_table_structure(entries):
    data_entries = [e for e in entries if e['type'] == 'donnee']
    des_count = sum(1 for e in data_entries if e['designation'].strip())
    spec_count = sum(1 for e in data_entries if e['valeur'] and e['valeur'].strip())
    
    if des_count != spec_count:
        return False, f"lignes_desalignees ({des_count} vs {spec_count})"
    return True, None
```

---

#### Étape 4: Multi-Page Continuity
**Requirement**: Same table (lot) can continue from one page to next without repeating header.

**Detection logic**:
```python
def is_table_continuation(prev_grid, curr_grid, curr_page):
    # Same table continues if:
    # 1. Number of columns identical
    # 2. No new lot title before the grid
    # 3. (If no header) first line doesn't look like header
    
    cols_match = len(prev_grid.cols) == len(curr_grid.cols)
    no_new_title = not detect_lot_title_before_region(curr_page, curr_region)
    
    return cols_match and no_new_title
```

**Implementation needed**:
- Track table_id across pages
- Inherit column indices from previous page
- Don't restart line numbering
- Handle inter-page cell fusion with flag "entree_fusionnee_inter_page"

---

#### Étape 5: OCR + Double Confidence Check (Per Cell)
**Already implemented in V2**, but needs integration here:
- Upscale cells < 150px width
- Denoise, adaptive threshold, deskew
- Flag if: conf <70% OR incoherent text OR symbols OR abnormal length

**Implementation needed**:
```python
def ocr_cell_and_validate(img, cell_bounds):
    text, conf = ocr_cell_high_quality(img, cell_bounds)
    a_verifier, motif = assign_verification_flag(text, conf)
    return text, conf, a_verifier, motif
```

---

#### Étape 6: Output JSON Format
**New structure** (one JSON with multiple tables):

```json
{
  "document": "pages_cibles.pdf",
  "extraction_date": "2026-07-12T...",
  "tables": [
    {
      "table_id": "table_1",
      "titre_detecte": "Lot 1: Imprimante Laser...",
      "pages": [1],
      "entete_colonne2_detecte": "Spécification",
      "entete_colonne2_suspecte": false,
      "table_rejetee": false,
      "motif_rejet": null,
      "nb_lignes_designation": 26,
      "nb_lignes_specification": 26,
      "entries": [
        {
          "designation": "Marque et Modèle",
          "type": "donnee",
          "valeur": "À préciser",
          "confiance_ocr": 91.4,
          "a_verifier": false,
          "motif_verification": null
        },
        {
          "designation": "Processeur central",
          "type": "section",
          "valeur": null,
          "confiance_ocr": null,
          "a_verifier": false,
          "motif_verification": null
        }
      ]
    },
    {
      "table_id": "table_2",
      ...
    }
  ]
}
```

---

#### Étape 7: Systemic Failure Guard
**Rules**:
- If >50% of tables marked `table_rejetee: true` → stop execution (critical failure)
- If no tables segmented at all → `"motif": "segmentation_tableaux_echouee"`
- Individual table rejection doesn't stop pipeline (other tables proceed)

**Implementation needed**:
```python
def check_systemic_failure(all_tables):
    if not all_tables:
        raise SystemicFailure("segmentation_tableaux_echouee")
    
    rejected_pct = sum(1 for t in all_tables if t['table_rejetee']) / len(all_tables)
    if rejected_pct > 0.5:
        raise SystemicFailure(f"too many tables rejected ({rejected_pct:.0%})")
    
    return True
```

---

## V3 Data Flow Diagram

```
PDF Input (pages_cibles.pdf)
    ↓
ÉTAPE 0: Segmentation en Tableaux
    ├─ Horizontal projection → find gaps
    ├─ Create TableRegion objects
    └─ Result: 59 table regions
    ↓
For each TableRegion:
    ├─ ÉTAPE 1: Grid Detection (Multi-Pass) → GridInfo
    ├─ ÉTAPE 2: Header Detection (Fuzzy) → HeaderInfo
    │
    ├─ For each row in grid:
    │   ├─ OCR cell by cell (col1, col2, col3)
    │   ├─ ÉTAPE 2bis: Detect section rows
    │   ├─ ÉTAPE 5: Double confidence check
    │   └─ Create Entry object
    │
    ├─ ÉTAPE 3: Validate table structure (des_count == spec_count)
    ├─ ÉTAPE 4: Check multi-page continuity
    └─ Collect into Table object
    ↓
ÉTAPE 6: Format JSON output
    ↓
ÉTAPE 7: Check systemic failure
    ↓
Output: specifications_v3.json (single file, multiple tables)
```

---

## Current Test Results

### Segmentation Performance
- **Regions detected**: 65 (from 6 pages)
- **Valid grids**: 59
- **Failed grids**: 6 (4% failure rate)
- **Time**: ~15 seconds for 6 pages

### Grid Detection Performance
- **Multi-pass robustness**: Working (some regions need Pass 2)
- **Line clustering**: Functional
- **Column detection**: Detecting 2-4 columns per region

### Next Steps
1. Complete Étape 2bis (section row detection)
2. Complete Étape 3 (structural validation)
3. Add multi-page continuity tracking (Étape 4)
4. Integrate OCR + confidence checks (Étape 5)
5. Format final JSON (Étape 6)
6. Add systemic failure handling (Étape 7)

---

## Key Design Decisions

### 1. Region-Based Segmentation (Not Page-Based)
**Why**: A single page can have multiple independent tables (different lots).  
**Alternative Rejected**: Page-level classification would fail with multi-lot documents.

### 2. Multi-Pass Grid Detection
**Why**: Scanned documents have varying line quality; one pass may miss faint lines.  
**Alternative Rejected**: Single-pass morphology misses ~40% of tables with poor scans.

### 3. Fuzzy Header Matching
**Why**: OCR errors on headers are common; can't use exact string matching.  
**Implementation**: Substring containment + accent removal (can enhance with Levenshtein distance).

### 4. Section Row Type Field
**Why**: Distinguishes grouping headers ("Processeur central") from data anomalies.  
**Alternative Rejected**: Treating them as data rows creates false "misalignment" rejections.

### 5. Per-Table Validation (Not Per-Page)
**Why**: A table can span multiple pages; validation must be table-scoped.  
**Alternative Rejected**: Page-level checks would split a single table across pages incorrectly.

---

## Error Handling Strategy

### Table-Level Errors (Captured, Don't Stop Pipeline)
- Grid not detected → `table_rejetee=true`, skip entry extraction
- Header not matched → `entete_suspecte=true`, proceed with positional extraction
- Structural misalignment → `table_rejetee=true`, return empty entries
- Low confidence cells → Individual entries flagged, not rejected

### Document-Level Errors (Stop Execution)
- No tables segmented at all → `"segmentation_tableaux_echouee"`
- >50% tables rejected → Critical failure, stop

---

## Testing & Validation

### Current Validation
- ✅ Segmentation detects 59 valid regions
- ✅ Grid detection works for 91% of regions
- ✅ Headers extracted via fuzzy matching

### Still Needed
- Entry-level OCR and validation
- Section row handling
- Multi-page continuity
- Final JSON structure
- Systemic failure detection

---

## Backward Compatibility

V3 output format is **not compatible** with V2:
- V2: `{"document": "...", "pages": [...]}` (flat list)
- V3: `{"document": "...", "tables": [...]}` (nested by table)

**Reason**: V2 assumed single table; V3 handles multiple tables.  
**Migration**: Downstream processing must be updated for V3 format.

---

## Future Enhancements (Post-V3)

1. **Levenshtein distance** for header matching (instead of substring)
2. **Lot title detection** from OCR (regex matching + text extraction)
3. **Visual anchoring** for table boundaries (lines, spacing heuristics)
4. **Multi-column tables** (>3 columns) - generalize column detection
5. **Rotated text** in cells (OCR rotation detection + correction)

---

**Next Action**: Complete Étapes 2bis-7 with full entry extraction and validation logic.
