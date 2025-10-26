# Excel Formula Linking - Quick Reference

## Summary of Opportunities

This is a quick reference checklist of all places where Excel formulas should replace hardcoded values.

---

## 🔴 High Priority (High Impact, Medium Effort)

### 1. Create Master Reference Sheets

**New Sheets Needed:**

#### Holders Sheet
```
Columns: holder_name (PK) | holder_type | email | address | notes
Purpose: Single source for all holder information
Impact: Ledger, Vesting, Cap Table Progression
```

#### Classes Sheet
```
Columns: class_name (PK) | class_type | par_value | authorized_shares | description
Purpose: Single source for security class definitions
Impact: Ledger, Waterfall
```

#### Terms Sheet
```
Columns: terms_name (PK) | class_name (FK) | lp_multiple | participation_type | 
         seniority_rank | conversion_ratio | anti_dilution
Purpose: Single source for term sheet provisions
Impact: Waterfall, future conversion analysis
```

---

## 🟡 Medium Priority (High Impact, Low Effort)

### 2. Ledger Sheet - Replace Hardcoded Values

| Column | Current | Improvement | Formula |
|--------|---------|-------------|---------|
| `holder_type` | Hardcoded from Python | Lookup from Holders sheet | `=XLOOKUP([@holder_name], Holders[holder_name], Holders[holder_type], "")` |
| `class_type` | Hardcoded from Python | Lookup from Classes sheet | `=XLOOKUP([@class_name], Classes[class_name], Classes[class_type], "")` |
| `acquisition_price` | Hardcoded value | Can reference Rounds sheet for round-based instruments | `=IF([@round_name]<>"", XLOOKUP([@round_name], Rounds[round_name], Rounds[price_per_share], [@acquisition_price]), [@acquisition_price])` |

### 3. Rounds Sheet - Make Initial Shares Dynamic

| Field | Current | Improvement | Formula |
|-------|---------|-------------|---------|
| `initial_shares` (C2) | Calculated in Python, hardcoded | Formula | `=SUMIF(Ledger[round_name], "", Ledger[initial_quantity])` |
| `investment_amount` (validation) | Hardcoded | Could sum from Ledger | `=SUMIF(Ledger[round_name], [@round_name], Ledger[investment_amount])` |

**Note:** Investment_amount requires adding that column to Ledger table.

### 4. Waterfall Sheet - Link to Terms

| Column | Current | Improvement | Formula |
|--------|---------|-------------|---------|
| `lp_multiple` | Hardcoded from Python | Lookup from Terms sheet | `=XLOOKUP([@class_name], Terms[class_name], Terms[lp_multiple], 1)` |
| `participation_type` | Hardcoded from Python | Lookup from Terms sheet | `=XLOOKUP([@class_name], Terms[class_name], Terms[participation_type], "non_participating")` |
| `seniority_rank` | Hardcoded from Python | Lookup from Terms sheet | `=XLOOKUP([@class_name], Terms[class_name], Terms[seniority_rank], 999)` |

---

## 🟢 Lower Priority (Medium Impact, Varies Effort)

### 5. Vesting Sheet - Link to Ledger or Master

**Option A: Extend Ledger** (Recommended)
- Add columns to Ledger: `grant_date`, `cliff_days`, `vesting_period_days`
- Vesting sheet becomes purely computational with all data from Ledger

**Option B: Create Vesting Terms Master Sheet**
- New sheet with vesting parameters
- Vesting sheet looks up from both Ledger and Vesting Terms

| Column | Current | Improvement | Formula (if extending Ledger) |
|--------|---------|-------------|-------------------------------|
| `holder_name` | Hardcoded | Lookup from Ledger | `=INDEX(Ledger[holder_name], MATCH([@instrument_id], Ledger[instrument_id], 0))` |
| `class_name` | Hardcoded | Lookup from Ledger | `=INDEX(Ledger[class_name], MATCH([@instrument_id], Ledger[instrument_id], 0))` |
| `total_granted` | Hardcoded | Lookup from Ledger | `=INDEX(Ledger[initial_quantity], MATCH([@instrument_id], Ledger[instrument_id], 0))` |
| `grant_date` | Hardcoded | Lookup from Ledger | `=INDEX(Ledger[grant_date], MATCH([@instrument_id], Ledger[instrument_id], 0))` |

### 6. Cap Table Progression - Dynamic Starting Values

| Item | Current | Improvement | Formula |
|------|---------|-------------|---------|
| `start_shares_value` | Calculated in Python, hardcoded | Formula | `=SUMIFS(Ledger[initial_quantity], Ledger[holder_name], A5, Ledger[round_name], "")` |

---

## 📊 Code Changes Required

### Python: excel.py Modifications

#### Line 98-106: Add creation of master sheets
```python
def generate(self) -> str:
    self.workbook = xlsxwriter.Workbook(self.output_path)
    self.workbook.set_calc_mode('auto')
    
    self._create_formats()
    
    # NEW: Create master reference sheets first
    self._create_holders_sheet()
    self._create_classes_sheet()
    self._create_terms_sheet()
    
    self._create_summary_sheet()
    self._create_ledger_sheet()
    # ... rest
```

#### New Methods to Add:

```python
def _create_holders_sheet(self):
    """Create Holders master reference sheet."""
    sheet = self.workbook.add_worksheet('Holders')
    columns = ['holder_name', 'holder_type', 'email', 'address', 'notes']
    holders = self.data.get('holders', [])
    # Create table from holders data
    # ...

def _create_classes_sheet(self):
    """Create Classes master reference sheet."""
    sheet = self.workbook.add_worksheet('Classes')
    columns = ['class_name', 'class_type', 'par_value', 'authorized_shares', 'description']
    classes = self.data.get('classes', [])
    # Create table from classes data
    # ...

def _create_terms_sheet(self):
    """Create Terms master reference sheet."""
    sheet = self.workbook.add_worksheet('Terms')
    columns = ['terms_name', 'class_name', 'lp_multiple', 'participation_type', 
               'seniority_rank', 'conversion_ratio', 'anti_dilution']
    terms = self.data.get('terms', [])
    # Create table from terms data
    # ...
```

#### Line 282-294: Modify Ledger to use formulas

```python
# BEFORE:
row_data = {
    'holder_type': holder.get('type', ''),
    'class_type': sec_class.get('type', ''),
    # ...
}

# AFTER:
row_data = {
    'holder_type': '',  # Will be replaced with formula
    'class_type': '',   # Will be replaced with formula
    # ...
}

# Then after writing table:
for row_idx in range(len(instruments)):
    data_row = start_row + 1 + row_idx
    # Add holder_type formula
    holder_col = columns.index('holder_type')
    sheet.write_formula(data_row, holder_col, 
        f'=XLOOKUP([@holder_name], Holders[holder_name], Holders[holder_type], "")',
        self.formats.get('text'))
    # Add class_type formula
    class_col = columns.index('class_type')
    sheet.write_formula(data_row, class_col,
        f'=XLOOKUP([@class_name], Classes[class_name], Classes[class_type], "")',
        self.formats.get('text'))
```

#### Line 393: Modify Rounds initial_shares to use formula

```python
# BEFORE:
if row_idx == 1:
    sheet.write(row_idx, 2, initial_shares, self.formats['number'])

# AFTER:
if row_idx == 1:
    sheet.write_formula(row_idx, 2, 
        '=SUMIF(Ledger[round_name], "", Ledger[initial_quantity])',
        self.formats['number'])
```

#### Lines 840-847: Modify Waterfall to lookup terms

```python
# BEFORE:
lp_multiple = terms.get('liquidation_multiple', 1.0)
sheet.write(row_idx, 4, lp_multiple, self.formats['decimal'])
participation = terms.get('participation_type', 'non_participating')
sheet.write(row_idx, 5, participation)

# AFTER:
# lp_multiple formula
sheet.write_formula(row_idx, 4,
    f'=XLOOKUP([@class_name], Terms[class_name], Terms[lp_multiple], 1)',
    self.formats['decimal'])
# participation_type formula
sheet.write_formula(row_idx, 5,
    f'=XLOOKUP([@class_name], Terms[class_name], Terms[participation_type], "non_participating")')
```

---

## 🎯 Testing Checklist

After implementing changes, verify:

### ✅ Master Sheets
- [ ] Holders sheet populated with all holders from JSON
- [ ] Classes sheet populated with all classes from JSON
- [ ] Terms sheet populated with all terms from JSON
- [ ] All sheets formatted as Excel Tables with correct names

### ✅ Formula Linking
- [ ] Ledger `holder_type` matches original hardcoded values
- [ ] Ledger `class_type` matches original hardcoded values
- [ ] Rounds `initial_shares` matches calculated Python value
- [ ] Waterfall terms match original hardcoded values
- [ ] All formulas calculate without #REF! or #N/A errors

### ✅ Data Integrity
- [ ] Change a holder type in Holders sheet → Ledger updates automatically
- [ ] Change a class type in Classes sheet → Ledger updates automatically
- [ ] Change lp_multiple in Terms sheet → Waterfall recalculates
- [ ] Add new shares in Ledger → Total_FDS updates
- [ ] All percentages sum to 100% (where expected)

### ✅ Validation
- [ ] Dropdown validation on Ledger `holder_name` (source: Holders[holder_name])
- [ ] Dropdown validation on Ledger `class_name` (source: Classes[class_name])
- [ ] Dropdown validation on Ledger `round_name` (source: Rounds[round_name])
- [ ] Invalid entries prevented or highlighted

---

## 📝 Implementation Order

### Phase 1: Foundation (Day 1)
1. Create `_create_holders_sheet()` method
2. Create `_create_classes_sheet()` method
3. Create `_create_terms_sheet()` method
4. Add method calls to `generate()` before other sheets
5. Test: Verify master sheets populate correctly

### Phase 2: Ledger Linking (Day 1-2)
6. Modify `_create_ledger_sheet()` to use formulas for `holder_type`
7. Modify `_create_ledger_sheet()` to use formulas for `class_type`
8. Test: Compare formula values to original hardcoded values
9. Create validation dropdowns for foreign key fields

### Phase 3: Rounds & Progression (Day 2)
10. Modify `_create_rounds_sheet()` for `initial_shares` formula
11. Modify `_create_cap_table_progression_sheet()` for `start_shares_value`
12. Test: Verify calculations match originals

### Phase 4: Waterfall (Day 2-3)
13. Modify `_create_waterfall_sheet()` to lookup terms
14. Test: Verify waterfall calculations match originals
15. Test scenario: Change terms, verify waterfall updates

### Phase 5: Vesting (Optional, Day 3-4)
16. Decide on Option A or B (extend Ledger vs separate master)
17. Implement chosen approach
18. Test: Verify vesting calculations unchanged

### Phase 6: Polish (Day 4-5)
19. Add data validation dropdowns
20. Add conditional formatting for error highlighting
21. Add audit helper columns in Summary sheet
22. Update documentation
23. Create example showing scenario modeling

---

## 🔍 Quick Validation Formulas

Add these to a new "Audit" sheet to verify data integrity:

```excel
// Check 1: All holder_types match master
=COUNTIF(Ledger[holder_type], "<>"&XLOOKUP(Ledger[@holder_name], Holders[holder_name], Holders[holder_type], "ERROR"))
// Should be 0

// Check 2: All class_types match master
=COUNTIF(Ledger[class_type], "<>"&XLOOKUP(Ledger[@class_name], Classes[class_name], Classes[class_type], "ERROR"))
// Should be 0

// Check 3: Total ownership percentages sum to 100%
=SUM(Ledger[ownership_percent_fds])
// Should be 1.0 (100%)

// Check 4: Rounds pre_round_shares progression valid
=AND(Rounds[pre_round_shares] = LAG(Rounds[pre_round_shares] + Rounds[shares_issued]))
// Should be TRUE

// Check 5: Total FDS consistency
=Summary!Total_FDS = SUM(Ledger[current_quantity]) + SUM(Ledger[net_dilution])
// Should be TRUE
```

---

## 💡 Pro Tips

1. **Use Table Names**: Always reference tables by name (e.g., `Holders[holder_name]`) not ranges (e.g., `$A$2:$A$10`)
2. **XLOOKUP vs VLOOKUP**: Use XLOOKUP if Excel 365, otherwise use INDEX-MATCH
3. **Named Ranges**: Keep using them for Summary sheet constants (Current_PPS, Total_FDS, etc.)
4. **Error Handling**: Wrap lookups in IFERROR or provide default values
5. **Documentation**: Add notes/comments to master sheets explaining their purpose
6. **Freeze Panes**: Freeze header rows in all tables for better UX
7. **Conditional Formatting**: Use to highlight formula vs hardcoded cells during migration
8. **Version Control**: Keep old hardcoded version as backup during migration

---

## 🚫 Common Pitfalls to Avoid

1. **Circular References**: Don't create formulas that reference themselves
2. **Broken Table Names**: Renaming tables breaks formulas - be careful
3. **Mixed References**: Be consistent with structured vs cell references
4. **Volatile Functions**: Avoid INDIRECT, OFFSET in large tables (slow)
5. **Missing Error Handling**: Always handle #N/A from lookups
6. **Hardcoded Row Numbers**: Use structured references, not `A2:A100`
7. **Forgotten Validation**: Add dropdowns to prevent typos in key fields

---

## 📚 Further Reading

- **Excel Tables**: Microsoft Docs on structured references
- **XLOOKUP**: Function reference and examples
- **Named Ranges**: Best practices for financial models
- **Data Validation**: Creating dependent dropdown lists
- **Formula Auditing**: Using Trace Precedents/Dependents

---

## ✅ Success Criteria

You'll know the implementation is successful when:

1. ✅ Users can update master sheets without touching formulas
2. ✅ Changes in master sheets propagate to all dependent sheets
3. ✅ No #REF!, #N/A, or #VALUE! errors in any formulas
4. ✅ All calculations match original hardcoded values
5. ✅ Dropdown validations prevent invalid data entry
6. ✅ Audit checks all pass (0 errors)
7. ✅ File opens in <2 seconds (formulas don't slow it down)
8. ✅ Documentation updated with new architecture
9. ✅ Users can model "what-if" scenarios by changing master data
10. ✅ Data lineage is clear and traceable

---

## 🎓 Example Scenario Modeling

Once implemented, users can easily model scenarios:

**Scenario: What if we change Series A from non-participating to participating?**

1. Open Terms sheet
2. Find Series A row
3. Change `participation_type` from "non_participating" to "participating"
4. Waterfall sheet automatically recalculates
5. Compare payouts - see impact instantly

**Scenario: What if Bob becomes an advisor instead of investor?**

1. Open Holders sheet
2. Find Bob row
3. Change `holder_type` from "investor" to "advisor"
4. Ledger updates automatically
5. Cap Table Progression updates category totals
6. No manual updates needed!

This is the power of formula-linked architecture! 🚀

