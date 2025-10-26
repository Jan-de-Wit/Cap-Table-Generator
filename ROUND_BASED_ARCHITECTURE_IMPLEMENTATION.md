# Round-Based Architecture Implementation Summary

## Overview

This document summarizes the implementation of the round-based architecture for the Cap Table Generator, where instruments are nested within rounds and each round has a calculation type that determines how shares are calculated.

## Completed Implementation

### 1. Schema Updates ✅

**Files Updated:**
- `/cap_table_schema.json`
- `/src/captable/schemas/cap_table_schema.json`

**Key Changes:**
- Updated schema version to `2.0`
- Removed top-level `instruments` array (now nested in rounds)
- Added `calculation_type` to Round (enum: "fixed_shares", "target_percentage", "convertible", "valuation_based")
- Added `valuation_cap_basis` to Round for convertible types
- Added `instruments` array to Round definition
- Updated Instrument definition:
  - Removed `round_name` (implicit from nesting)
  - Removed `valuation_basis` (moved to round level)
  - Removed `percentage_ownership` (replaced with `target_percentage`)
  - Added `target_percentage` for target_percentage type
  - Added `interest_end_date` alongside `interest_start_date`
  - Added `days_passed` as calculated field
  - Added `discount_rate` for convertible instruments
- Removed `ConvertibleTerms` object (fields moved to instrument level)

### 2. Validation Layer ✅

**Files Updated:**
- `/src/captable/validation/business_rules.py`
- `/src/captable/validation/relationship_validator.py`

**Key Changes:**
- Added validation for round-level `calculation_type`
- Added validation for `valuation_cap_basis` on convertible rounds
- Updated instrument validation to check required fields based on round's calculation type:
  - `fixed_shares`: requires `initial_quantity`
  - `target_percentage`: requires `target_percentage`
  - `valuation_based`: requires `investment_amount`
  - `convertible`: requires `investment_amount`, `interest_rate`, `interest_start_date`, `interest_end_date`
- Added date validation for `interest_end_date` > `interest_start_date`
- Updated relationship validator to work with nested structure (removed `round_name` validation)

### 3. DLM (Deterministic Layout Map) ✅

**Files Updated:**
- `/src/captable/dlm.py`

**Key Additions:**
- `register_round_section()`: Register a round section with constants and instruments location
- `register_round_instrument()`: Register individual instruments with format `Round_<idx>_Instrument_<idx>_<field>`
- Support for dynamic row positions as rounds are laid out vertically

### 4. Rounds Sheet Generator ✅

**Files Created/Updated:**
- `/src/captable/excel/sheet_generators/rounds_sheet.py` (completely rewritten)
- Deleted: `/src/captable/excel/sheet_generators/instruments_sheet.py` (replaced)

**Architecture:**
Each round is displayed vertically with:
1. Round heading (name)
2. Constants section:
   - Date
   - Calculation Type
   - Pre-Round Shares (calculated)
   - Valuation fields (if applicable)
   - Valuation Cap Basis (for convertible)
3. Instruments table (columns vary by calculation_type)
4. Spacing (3 rows) before next round

**Column Sets by Calculation Type:**
- `fixed_shares`: holder_name, class_name, acquisition_date, shares
- `target_percentage`: holder_name, class_name, target_percentage, calculated_shares
- `valuation_based`: holder_name, class_name, investment_amount, accrued_interest, calculated_shares
- `convertible`: holder_name, class_name, investment_amount, interest_start_date, interest_end_date, days_passed, interest_rate, interest_type, accrued_interest, discount_rate, calculated_shares

### 5. Excel Generator Updates ✅

**Files Updated:**
- `/src/captable/excel/excel_generator.py`
- `/src/captable/excel/sheet_generators/__init__.py`

**Key Changes:**
- Updated imports to remove `InstrumentsSheetGenerator`
- Updated architecture documentation to reflect round-based design
- Simplified sheet generation to: Rounds → Cap Table Progression
- Rounds sheet is now the SOURCE OF TRUTH

### 6. Formula Resolvers ✅

**Files Updated:**
- `/src/captable/formulas/interest.py`
- `/src/captable/formulas/valuation.py`

**Key Additions:**
- `create_days_passed_formula()`: Calculate days between dates
- `create_convertible_shares_formula()`: Calculate shares from convertible with valuation cap reference
- Existing formulas work with round-based architecture:
  - `create_shares_from_percentage_formula()`: For target_percentage type
  - `create_shares_from_investment_premoney_formula()`: For valuation_based pre-money
  - `create_shares_from_investment_postmoney_formula()`: For valuation_based post-money
  - `create_accrued_interest_formula()`: For interest calculations

### 7. Example JSON Files ✅

**Files Created:**
- `/examples/round_based_example.json`

Demonstrates all four calculation types in new format:
- Incorporation: fixed_shares
- Seed Round: valuation_based
- Series A: convertible
- Strategic Round: target_percentage

## Partial Implementation / TODO

### 8. Cap Table Progression Sheet ⚠️

**Status:** Placeholder implemented with TODO comments

**File:** `/src/captable/excel/sheet_generators/progression_sheet.py`

**Required Work:**
- Collect unique holders across all rounds' instruments
- For each round-holder combination, aggregate shares
- Calculate start/new/total/percentage columns
- Reference nested instrument data from Rounds sheet
- Handle dynamic row positions from vertical round layout

**Current State:** Shows placeholder message directing users to Rounds sheet

### 9. Test Data Migration ❌

**Status:** Not started

**Files Requiring Updates:**
- `/demo_simple.json`
- `/demo_complex.json`
- `/demo_comprehensive_captable.json`
- `/test_new_features.json`
- `/examples/sample_simple_captable.json`
- `/examples/sample_complex_captable.json`
- `/examples/valuation_based_example.json`

**Required Work:**
- Convert flat `instruments` array to nested structure within `rounds`
- Add `calculation_type` to each round
- Move `valuation_basis` from instruments to round level
- Convert `percentage_ownership` to `target_percentage`
- Add `interest_end_date` for convertible instruments
- Update schema_version to "2.0"

### 10. Test Suite Updates ❌

**Status:** Not started

**Files Requiring Updates:**
- `/tests/test_cap_table.py`
- `/tests/test_validation.py`
- `/tests/test_excel_generator.py`
- `/tests/test_integration.py`

**Required Work:**
- Update test fixtures to use new schema format
- Test round-level validation rules
- Test nested instrument structure
- Test Rounds sheet generation
- Update integration tests for new architecture

### 11. Documentation Updates ❌

**Status:** Not started

**Files Requiring Updates:**
- `/docs/SCHEMA_REFERENCE.md`
- `/docs/JSON_INPUT_GUIDE.md`
- `/docs/XLSX Output.md`
- `/README.md`
- `/QUICKSTART.md`

**Required Work:**
- Document new nested structure
- Update examples to show round-based format
- Explain calculation types and their requirements
- Update Excel output documentation with vertical round layout
- Update quick start guide with new JSON format

## Breaking Changes

### For End Users

1. **JSON Format:** All existing JSON files must be converted to new format
   - Schema version changes from "1.0" to "2.0"
   - Instruments must be nested within rounds
   - Each round must have a `calculation_type`

2. **Excel Output:** Significant changes in sheet structure
   - Instruments sheet replaced with Rounds sheet
   - Rounds laid out vertically instead of tabular format
   - Different columns for different calculation types
   - Cap Table Progression temporarily shows placeholder message

3. **API Changes:** If using programmatically
   - Data structure in `data['instruments']` moved to `data['rounds'][i]['instruments']`
   - New required fields: `calculation_type`, `valuation_cap_basis` (for convertible)

### Migration Path

1. **Update JSON files:**
   ```python
   # Old format
   {
     "instruments": [
       {
         "holder_name": "Alice",
         "class_name": "Common",
         "round_name": "Seed",
         "investment_amount": 100000,
         "valuation_basis": "pre_money"
       }
     ]
   }
   
   # New format
   {
     "rounds": [
       {
         "name": "Seed",
         "calculation_type": "valuation_based",
         "pre_money_valuation": 5000000,
         "instruments": [
           {
             "holder_name": "Alice",
             "class_name": "Common",
             "investment_amount": 100000
           }
         ]
       }
     ]
   }
   ```

2. **Determine calculation_type for each round:**
   - If all instruments have `initial_quantity`: → `fixed_shares`
   - If instruments have `percentage_ownership`: → `target_percentage`
   - If instruments have `investment_amount` + `valuation_basis`: → `valuation_based`
   - If instruments have `convertible_terms`: → `convertible`

3. **Move fields from instrument to round level:**
   - `valuation_basis` → determines if round uses pre/post money
   - For convertibles: add `valuation_cap_basis` to round

## Testing the Implementation

### Quick Test with Example File

```bash
# Generate Excel from new format example
python generate_xlsx.py examples/round_based_example.json output_test.xlsx

# Check generated Excel file:
# - Should have "Rounds" sheet with vertical layout
# - Each round should show constants and instruments
# - Cap Table Progression will show placeholder message
```

### Validation Test

```python
from src.captable.validation import validate_cap_table

# Test validation with new format
with open('examples/round_based_example.json') as f:
    data = json.load(f)
    
errors = validate_cap_table(data)
if errors:
    print("Validation errors:", errors)
else:
    print("Valid!")
```

## Next Steps

Priority order for completing the implementation:

1. **Complete Cap Table Progression Sheet** (High Priority)
   - Required for functional end-to-end workflow
   - Implement aggregation logic for nested instruments
   - Create formulas to reference Rounds sheet

2. **Update Test Suite** (High Priority)
   - Ensures stability and correctness
   - Update fixtures to new format
   - Add tests for new validation rules

3. **Migrate Example JSON Files** (Medium Priority)
   - Provides working examples for users
   - Demonstrates different calculation types

4. **Update Documentation** (Medium Priority)
   - Users need clear guidance on new format
   - Update schema reference and examples

5. **Migration Tool** (Low Priority - Nice to Have)
   - Create script to auto-convert old format to new format
   - Helps existing users migrate their data

## File Summary

### Modified Files
- Schema: 2 files
- Validation: 2 files
- DLM: 1 file
- Rounds Sheet Generator: 1 file (rewritten)
- Excel Generator: 2 files
- Formula Resolvers: 2 files
- Cap Table Progression: 1 file (placeholder)

### Deleted Files
- Instruments Sheet Generator: 1 file

### New Files
- Round-based example: 1 file
- This summary: 1 file

**Total**: 12 files modified, 1 deleted, 2 created

## Conclusion

The core infrastructure for round-based architecture has been successfully implemented:
- ✅ Schema and validation
- ✅ Rounds sheet generation with all 4 calculation types
- ✅ Formula resolvers for all calculations
- ✅ Example JSON in new format

Remaining work focuses on:
- ⚠️ Cap Table Progression sheet implementation
- ❌ Test data migration
- ❌ Test suite updates
- ❌ Documentation updates

The system is ready for testing with the provided `round_based_example.json`. The Rounds sheet will generate correctly, showing all instruments nested within their rounds with appropriate columns based on calculation type.

