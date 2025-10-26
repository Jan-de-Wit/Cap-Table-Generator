# Quick Start Guide

Get up and running with Cap Table Generator in 5 minutes.

## Installation

```bash
pip install xlsxwriter jsonschema python-dateutil
```

## Generate Your First Cap Table

### Option 1: Use Demo Script (Fastest)

```bash
# Generate sample data and Excel files
python demo.py
```

This creates:
- `demo_simple.xlsx` - Basic cap table
- `demo_complex.xlsx` - Advanced cap table with options, vesting, waterfall

Open these files in Excel to see dynamic formulas in action!

### Option 2: From Existing JSON

If you have a cap table JSON file:

```python
from cap_table_generator import generate_from_json

generate_from_json("my_captable.json", "output.xlsx")
```

### Option 3: Programmatic Creation

```python
from cap_table_generator import generate_from_data
import uuid

# Build cap table data
data = {
    "schema_version": "1.0",
    "company": {
        "name": "My Startup",
        "current_date": "2024-10-25",
        "current_pps": 1.0
    },
    "holders": [
        {
            "holder_id": str(uuid.uuid4()),
            "name": "Founder",
            "type": "founder"
        }
    ],
    "classes": [
        {
            "class_id": str(uuid.uuid4()),
            "name": "Common Stock",
            "type": "common"
        }
    ],
    "instruments": [
        {
            "instrument_id": str(uuid.uuid4()),
            "holder_id": "...",  # Use holder_id from above
            "class_id": "...",   # Use class_id from above
            "initial_quantity": 10000000,
            "acquisition_price": 0.001,
            "acquisition_date": "2024-01-01"
        }
    ],
    "terms": [],
    "rounds": []
}

# Generate Excel
generate_from_data(data, "my_captable.xlsx")
```

## Understanding the Output

### Excel Sheets

1. **Summary**: Key metrics and global constants
   - Total Fully Diluted Shares
   - Current Price Per Share (for TSM calculations)
   - Exit Value (for waterfall scenarios)

2. **Ledger**: All instruments with ownership calculations
   - Each row is an instrument (grant/holding)
   - Formulas calculate ownership %, TSM dilution
   - Uses Excel Table for dynamic references

3. **Rounds**: Financing history
   - Investment amounts and valuations
   - Price per share calculations
   - Shares issued per round

4. **Vesting**: Employee grants
   - Vesting schedules with cliff periods
   - Days elapsed and vested shares
   - Automatic updates based on current date

5. **Waterfall**: Liquidation scenarios
   - Preference payouts by seniority
   - Participating vs non-participating logic
   - Common stock residual calculation

### Key Features

**Dynamic Formulas**: All numbers update automatically
```
Change: Current PPS in Summary sheet
Result: All TSM calculations update
        All ownership percentages recalculate
```

**Named Ranges**: Reference global values easily
- `Total_FDS` - Total fully diluted shares
- `Current_PPS` - Current price per share
- `Current_Date` - Evaluation date for vesting
- `Exit_Val` - Exit value for waterfall

**Structured References**: Table formulas are resilient
```excel
=Ledger[@[current_quantity]] / Total_FDS
```
This formula works even if you add/remove rows or columns!

## Common Scenarios

### Add a New Shareholder

1. Open the JSON file
2. Add to `holders` array:
```json
{
  "holder_id": "new-uuid-v4",
  "name": "New Investor",
  "type": "investor"
}
```
3. Add instrument to `instruments` array:
```json
{
  "instrument_id": "new-uuid-v4",
  "holder_id": "new-uuid-v4",
  "class_id": "existing-class-id",
  "initial_quantity": 1000000,
  "acquisition_price": 2.50,
  "acquisition_date": "2024-10-25"
}
```
4. Regenerate Excel

### Add Employee with Vesting

```json
{
  "instrument_id": "uuid-v4",
  "holder_id": "employee-holder-id",
  "class_id": "option-class-id",
  "initial_quantity": 50000,
  "strike_price": 1.00,
  "vesting_terms": {
    "grant_date": "2024-01-01",
    "cliff_days": 365,
    "vesting_period_days": 1460
  }
}
```

### Model a New Financing Round

```json
{
  "rounds": [
    {
      "round_id": "uuid-v4",
      "name": "Series B",
      "round_date": "2024-10-01",
      "investment_amount": 20000000,
      "pre_money_valuation": 80000000,
      "post_money_valuation": 100000000,
      "price_per_share": 5.00,
      "shares_issued": 4000000
    }
  ]
}
```

Then add instruments for investors in this round.

## Testing Your Changes

```bash
# Validate your JSON
python -c "
from cap_table_generator import CapTableGenerator
gen = CapTableGenerator(json_path='my_captable.json')
if gen.validate():
    print('Valid!')
else:
    for err in gen.get_validation_errors():
        print(err)
"

# Generate Excel
python -c "
from cap_table_generator import generate_from_json
generate_from_json('my_captable.json', 'output.xlsx')
print('Generated output.xlsx')
"
```

## Next Steps

1. **Read JSON Input Guide**: `docs/JSON_INPUT_GUIDE.md` - Complete guide for generating valid cap table JSON
2. **Read README.md**: Comprehensive documentation of all features
3. **Explore examples**: Check `example_usage.py` for more patterns
4. **Run tests**: `python test_cap_table.py` to verify installation
5. **Study samples**: Open `sample_simple_captable.json` and `sample_complex_captable.json`

## Tips

### Excel Formula Inspection

In the generated Excel file:
1. Click any calculated cell
2. Look at formula bar to see the actual formula
3. All formulas use clear Named Ranges and Structured References

### Modifying Exit Scenarios

In the Summary sheet:
1. Find "Exit Value (Scenario)"
2. Change the value
3. Watch Waterfall sheet payouts recalculate instantly

### Testing TSM Dilution

In the Summary sheet:
1. Find "Current Price Per Share"
2. Increase the value
3. Watch Ledger sheet "net_dilution" column update
4. See Total FDS change accordingly

### Debugging Validation Errors

```python
from cap_table_generator import CapTableGenerator

gen = CapTableGenerator(json_path='problematic.json')
if not gen.validate():
    for error in gen.get_validation_errors():
        print(f"❌ {error}")
```

Common issues:
- Missing required fields (`holders`, `classes`, `instruments`)
- Invalid UUID format (must be lowercase with hyphens)
- Broken foreign keys (referencing non-existent UUIDs)
- Duplicate UUIDs within same entity type

## Getting Help

- Review full documentation: `README.md`
- Check knowledge base: `docs/Knowledge Base.md`
- Run examples: `python example_usage.py`
- Inspect test cases: `test_cap_table.py`

## Quick Reference

### Minimum Valid JSON

```json
{
  "schema_version": "1.0",
  "company": {
    "name": "Company Name",
    "current_date": "2024-10-25",
    "current_pps": 1.0
  },
  "holders": [...],
  "classes": [...],
  "instruments": [...],
  "terms": [],
  "rounds": []
}
```

### Holder Types
- `founder`, `employee`, `investor`, `advisor`, `option_pool`

### Security Class Types
- `common`, `preferred`, `option`, `warrant`, `safe`, `convertible_note`

### Participation Types
- `non_participating`, `participating`, `capped_participating`

### Required UUIDs
- holder_id, class_id, terms_id, instrument_id, round_id, scenario_id

All UUIDs must be valid v4 format: lowercase, 8-4-4-4-12 hex digits with hyphens.

