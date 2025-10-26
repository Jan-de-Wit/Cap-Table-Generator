# Excel Formula Linking Analysis
## Opportunities for Single Source of Truth

This document identifies places in the Excel output where information is currently **hardcoded** but could be **linked with Excel formulas** from a single source of truth.

---

## Summary Sheet
**Current State**: Serves as the primary source of truth with Named Ranges  
**Status**: ✅ Well-designed

### Opportunities:
1. **Exit Value** (line 133-138)
   - Currently: Takes first scenario value or defaults to $10M
   - **Improvement**: If multiple waterfall scenarios exist, could link to a Scenarios sheet with a dropdown/selector

---

## Ledger Sheet
**Current State**: Main data table with some hardcoded values from Python dictionaries  
**Status**: ⚠️ Needs improvement

### Opportunities:

#### 1. **holder_type** (line 284)
```python
'holder_type': holder.get('type', ''),
```
- **Current**: Hardcoded from Python `holders_map`
- **Better**: Reference a **Holders Master Sheet** with columns: `holder_name`, `holder_type`
- **Formula**: `=XLOOKUP([@holder_name], Holders[holder_name], Holders[holder_type], "")`
- **Benefit**: Single place to update holder types; changes propagate automatically

#### 2. **class_type** (line 286)
```python
'class_type': sec_class.get('type', ''),
```
- **Current**: Hardcoded from Python `classes_map`
- **Better**: Reference a **Classes Master Sheet** with columns: `class_name`, `class_type`, `description`
- **Formula**: `=XLOOKUP([@class_name], Classes[class_name], Classes[class_type], "")`
- **Benefit**: Single place to manage security classes

#### 3. **strike_price** (line 289)
- **Current**: Hardcoded value
- **Potential**: If strike prices follow patterns (e.g., % of round PPS), could be calculated
- **Formula Example**: `=IF([@class_type]="option", VLOOKUP([@round_name], Rounds[round_name], [price_per_share]) * 0.5, 0)`

#### 4. **acquisition_price** (line 290)
- **Current**: Hardcoded value
- **Potential**: For round-based instruments, could reference Rounds sheet
- **Formula Example**: `=IF([@round_name]<>"", XLOOKUP([@round_name], Rounds[round_name], Rounds[price_per_share], 0), [@acquisition_price])`
- **Benefit**: Ensures consistency with round pricing

---

## Rounds Sheet
**Current State**: Mix of calculated formulas and hardcoded values  
**Status**: ⚠️ Partially optimized

### Opportunities:

#### 1. **initial_shares calculation** (lines 376-380)
```python
initial_shares = sum(
    inst.get('initial_quantity', 0) 
    for inst in instruments 
    if not inst.get('round_name')
)
```
- **Current**: Calculated in Python and hardcoded into first row
- **Better**: Use Excel formula in cell C2
- **Formula**: `=SUMIF(Ledger[round_name], "", Ledger[initial_quantity])`
- **Benefit**: Updates automatically if founder shares change in Ledger

#### 2. **round_date** (line 386)
- **Current**: Hardcoded value
- **Potential**: Could validate against acquisition_date range in Ledger
- **Formula Example (validation)**: Add a helper column to check if date is reasonable

#### 3. **investment_amount** (line 416)
- **Current**: Hardcoded value
- **Better**: Could be calculated from Ledger
- **Formula**: `=SUMIF(Ledger[round_name], [@round_name], Ledger[investment_amount])`
- **Note**: Would require adding `investment_amount` column to Ledger table
- **Benefit**: Single source of truth for investment data

---

## Cap Table Progression Sheet
**Current State**: Uses formulas well, but some hardcoded starting values  
**Status**: ⚠️ Mostly good, minor improvements possible

### Opportunities:

#### 1. **start_shares_value** (lines 580-583)
```python
start_shares_value = 0
for instrument in instruments:
    if instrument.get('holder_name') == holder_name and not instrument.get('round_name'):
        start_shares_value += instrument.get('initial_quantity', 0)
```
- **Current**: Calculated in Python and hardcoded as static value
- **Better**: Use formula even for first round
- **Formula**: `=SUMIFS(Ledger[initial_quantity], Ledger[holder_name], "Alice", Ledger[round_name], "")`
- **Benefit**: Updates if founder/initial shares change

---

## Vesting Sheet
**Current State**: Heavily hardcoded from instrument data  
**Status**: ❌ Needs major improvement

### Opportunities:

#### 1. **All Base Data Fields** (lines 754-760)
Currently hardcoded:
- `holder_name`
- `class_name`
- `total_granted`
- `grant_date`
- `cliff_days`
- `vesting_period_days`

**Better Approach**: Create a **Vesting Terms Master Sheet**
- Columns: `instrument_id`, `holder_name`, `class_name`, `total_granted`, `grant_date`, `cliff_days`, `vesting_period_days`
- Vesting sheet becomes purely computational with formulas:
  - `holder_name`: `=XLOOKUP([@instrument_id], VestingTerms[instrument_id], VestingTerms[holder_name])`
  - `total_granted`: `=XLOOKUP([@instrument_id], VestingTerms[instrument_id], VestingTerms[total_granted])`
  - etc.

**Alternative**: Link directly to Ledger
- `total_granted`: `=SUMIFS(Ledger[initial_quantity], Ledger[holder_name], [@holder_name], Ledger[class_name], [@class_name])`
- **Issue**: Vesting terms (cliff, period) not in Ledger currently

**Best Solution**: Extend Ledger table to include vesting columns
- Add to Ledger: `grant_date`, `cliff_days`, `vesting_period_days`
- Then Vesting sheet formulas can reference Ledger with FILTER or XLOOKUP
- **Benefit**: One table holds all instrument data

---

## Waterfall Sheet
**Current State**: Hardcoded liquidation terms from Python dictionaries  
**Status**: ❌ Needs improvement

### Opportunities:

#### 1. **Liquidation Terms** (lines 840-847)
Currently hardcoded from `terms_map`:
- `lp_multiple` (liquidation preference multiple)
- `participation_type`
- `seniority_rank`

**Better Approach**: Create a **Terms Master Sheet**
- Columns: `class_name`, `lp_multiple`, `participation_type`, `seniority_rank`, `conversion_rights`, etc.
- Waterfall sheet references this:
  - `lp_multiple`: `=XLOOKUP([@class_name], Terms[class_name], Terms[lp_multiple], 1)`
  - `participation_type`: `=XLOOKUP([@class_name], Terms[class_name], Terms[participation_type], "non_participating")`
  - `seniority_rank`: `=XLOOKUP([@class_name], Terms[class_name], Terms[seniority_rank], 999)`

**Benefit**: 
- Single place to manage term sheet provisions
- Easy scenario modeling (change terms in one place)
- Clear documentation of rights

#### 2. **Exit Value Scenarios**
- **Current**: Single exit value in Summary sheet
- **Better**: Create **Exit Scenarios Sheet**
  - Columns: `scenario_name`, `exit_value`, `description`
  - Multiple waterfalls could reference different scenarios
  - Add dropdown selector in Summary sheet
- **Benefit**: Model multiple exit scenarios side-by-side

---

## Recommended Implementation Priority

### Phase 1: Master Reference Sheets (High Value, Medium Effort)
1. **Create Holders Sheet**
   - Columns: `holder_name`, `holder_type`, `email`, `address`, etc.
   - Update Ledger to use XLOOKUP for `holder_type`

2. **Create Classes Sheet**
   - Columns: `class_name`, `class_type`, `par_value`, `authorized_shares`, `description`
   - Update Ledger to use XLOOKUP for `class_type`

3. **Create Terms Sheet**
   - Columns: `terms_name`, `class_name`, `lp_multiple`, `participation_type`, `seniority_rank`, `conversion_ratio`, `anti_dilution`, etc.
   - Update Waterfall to use XLOOKUP for terms data

### Phase 2: Formula-Based Calculations (High Value, Low Effort)
4. **Update Rounds Sheet**
   - Replace hardcoded `initial_shares` with formula: `=SUMIF(Ledger[round_name], "", Ledger[initial_quantity])`
   - Consider adding formula for `investment_amount` validation

5. **Update Cap Table Progression**
   - Replace hardcoded `start_shares_value` with formulas

### Phase 3: Extend Ledger Table (Medium Value, High Effort)
6. **Add Vesting Columns to Ledger**
   - Add: `grant_date`, `cliff_days`, `vesting_period_days`
   - Vesting sheet becomes fully formula-driven from Ledger

### Phase 4: Advanced Features (Lower Priority)
7. **Exit Scenarios Sheet**
   - Multiple scenario modeling
   - Scenario selector in Summary

8. **Validation Helper Columns**
   - Data consistency checks
   - Highlight mismatches between sheets

---

## Benefits of Formula Linking

### 1. **Single Source of Truth**
- Change holder type in one place → updates everywhere
- Change term sheet provisions → waterfall recalculates automatically

### 2. **Data Consistency**
- Impossible to have mismatched data across sheets
- Formulas enforce referential integrity

### 3. **Easier Maintenance**
- Users can update master tables without touching formulas
- Clear separation between data and calculations

### 4. **Audit Trail**
- Can trace where every value comes from
- Formula dependencies show data flow

### 5. **Scenario Modeling**
- Change assumptions in master sheets
- See impact across all analyses instantly

### 6. **Reduced File Size**
- Formulas are smaller than repeated data
- Less duplication

---

## Implementation Notes

### Excel Functions to Use:
- **XLOOKUP**: Primary lookup function (modern, powerful)
  - Fallback to VLOOKUP/INDEX-MATCH for older Excel versions
- **SUMIF/SUMIFS**: Aggregate data from master tables
- **FILTER**: Create dynamic subsets (Excel 365)
- **LET**: Create intermediate variables in complex formulas (Excel 365)

### Named Ranges Strategy:
- All master sheets should have table names
- Key lookup columns should have named ranges
- Makes formulas more readable: `=XLOOKUP([@class], Classes[name], Classes[type])`

### Validation:
- Add data validation dropdowns for foreign key fields
- Prevents typos and ensures referential integrity
- Example: `round_name` in Ledger should be dropdown from Rounds[round_name]

---

## Example: Current vs Improved

### Current State (Ledger)
| holder_name | holder_type | class_name | class_type |
|-------------|-------------|------------|------------|
| Alice       | founder     | Common     | common     |
| Bob         | investor    | Series A   | preferred  |

`holder_type` and `class_type` are **hardcoded values** from Python.

### Improved State

**Holders Sheet:**
| holder_name | holder_type | email              |
|-------------|-------------|--------------------|
| Alice       | founder     | alice@company.com  |
| Bob         | investor    | bob@vc.com         |

**Classes Sheet:**
| class_name | class_type | par_value |
|------------|------------|-----------|
| Common     | common     | 0.0001    |
| Series A   | preferred  | 0.0001    |

**Ledger Sheet (with formulas):**
| holder_name | holder_type                                                    | class_name | class_type                                                   |
|-------------|----------------------------------------------------------------|------------|--------------------------------------------------------------|
| Alice       | `=XLOOKUP([@holder_name], Holders[name], Holders[type])`      | Common     | `=XLOOKUP([@class_name], Classes[name], Classes[type])`     |
| Bob         | `=XLOOKUP([@holder_name], Holders[name], Holders[type])`      | Series A   | `=XLOOKUP([@class_name], Classes[name], Classes[type])`     |

**Benefits:**
- Change Bob from "investor" to "advisor" in Holders sheet → updates in Ledger automatically
- Change "Series A" class type → updates everywhere
- Add new classes in Classes sheet → available in validation dropdowns

---

## Conclusion

The current Excel output is **functionally correct** but has **significant opportunities** for improvement through formula-based linking. The main issues are:

1. **Data Duplication**: Many values hardcoded from Python dictionaries
2. **No Master Tables**: Missing canonical sources for holders, classes, terms
3. **Limited Flexibility**: Users can't easily modify scenarios or assumptions

Implementing formula linking would transform this from a **static report** into a **dynamic financial model** that users can:
- Update with new data
- Model scenarios
- Trace calculations
- Ensure consistency

The recommended approach is to implement **Phase 1 and Phase 2** first, as they provide the highest value with reasonable effort.

