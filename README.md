# Cap Table Generator

A comprehensive system for generating dynamic Excel-based capitalization tables from structured JSON data. Built with formula-driven calculations that remain live and updateable in Excel.

## Overview

The Cap Table Generator transforms structured JSON cap table data into fully functional Excel workbooks with:

- **Dynamic Formulas**: All calculations use Excel formulas, not static values
- **Cross-Sheet References**: Named Ranges and Structured References maintain integrity
- **Advanced Financial Calculations**: TSM dilution, liquidation waterfalls, vesting schedules
- **Schema Validation**: Comprehensive validation ensures data integrity
- **Extensible Architecture**: Modular design supports new features and instruments

## Features

### Core Capabilities

- **Multiple Entity Types**: Holders, Security Classes, Terms Packages, Instruments, Rounds
- **Formula Encoding Objects (FEO)**: Symbolic formula representation in JSON
- **Relationship Tracking**: UUID-based references maintain data integrity
- **Excel Standards Compliance**: Named Ranges, Structured References, Excel Tables

### Advanced Financial Calculations

- **Treasury Stock Method (TSM)**: Dynamic option dilution based on current share price
- **Ownership Percentages**: Automatic calculation based on fully diluted shares
- **Vesting Schedules**: Time-based vesting with cliff periods
- **SAFE/Convertible Notes**: Conversion calculations with discount rates and caps
- **Liquidation Waterfall**: Sequential payout logic with seniority and participation rights
- **Option Pool Top-Ups**: Calculate shares needed to reach target pool percentage

### Excel Workbook Structure

Generated workbooks include standardized sheets:

- **Summary**: Global constants with Named Ranges (Total FDS, Current PPS, Exit Value)
- **Ledger**: Excel Table with all instruments and calculated ownership
- **Rounds**: Financing round details with valuations and pricing
- **Cap Table Progression**: Visual progression of ownership across rounds by category
- **Vesting**: Employee grants with vesting calculations
- **Waterfall**: Liquidation scenarios with preference payouts

## Installation

### Requirements

- Python 3.8+
- Dependencies: xlsxwriter, jsonschema, python-dateutil

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Or install individually
pip install xlsxwriter jsonschema python-dateutil
```

## Quick Start

### Generate Sample Cap Tables

```bash
# Create sample JSON files
python sample_data_generator.py

# Generate demo Excel files
python demo.py
```

This creates:
- `sample_simple_captable.json` - Basic example with founders and seed round
- `sample_complex_captable.json` - Advanced example with multiple rounds, options, vesting
- `demo_simple.xlsx` - Excel output for simple scenario
- `demo_complex.xlsx` - Excel output for complex scenario

### Programmatic Usage

#### From JSON File

```python
from src.captable import generate_from_json

excel_path = generate_from_json(
    json_path="my_captable.json",
    output_path="my_captable.xlsx"
)
```

#### From Data Dictionary

```python
from src.captable import generate_from_data

data = {
    "schema_version": "1.0",
    "company": {...},
    "holders": [...],
    "classes": [...],
    "instruments": [...]
}

excel_path = generate_from_data(data, "output.xlsx")
```

#### With Validation

```python
from src.captable import CapTableGenerator

generator = CapTableGenerator(json_path="captable.json")

if generator.validate():
    excel_path = generator.generate_excel("output.xlsx")
else:
    for error in generator.get_validation_errors():
        print(f"Error: {error}")
```

## JSON Schema Structure

### Core Entities

#### Company

```json
{
  "company": {
    "name": "Startup Inc.",
    "incorporation_date": "2023-01-01",
    "current_date": "2024-10-25",
    "current_pps": 2.50
  }
}
```

#### Holders (Stakeholders)

```json
{
  "holders": [
    {
      "holder_id": "uuid-v4",
      "name": "Alice Johnson",
      "type": "founder",
      "email": "alice@startup.com"
    }
  ]
}
```

Holder types: `founder`, `employee`, `investor`, `advisor`, `option_pool`

#### Security Classes

```json
{
  "classes": [
    {
      "class_id": "uuid-v4",
      "name": "Common Stock",
      "type": "common",
      "conversion_ratio": 1.0
    },
    {
      "class_id": "uuid-v4",
      "name": "Series A Preferred",
      "type": "preferred",
      "terms_id": "uuid-v4-of-terms-package"
    }
  ]
}
```

Class types: `common`, `preferred`, `option`, `warrant`, `safe`, `convertible_note`

#### Terms Packages

```json
{
  "terms": [
    {
      "terms_id": "uuid-v4",
      "name": "Series A Terms",
      "liquidation_multiple": 1.0,
      "participation_type": "participating",
      "seniority_rank": 1,
      "anti_dilution": "weighted_average"
    }
  ]
}
```

Participation types: `non_participating`, `participating`, `capped_participating`

#### Instruments (Holdings)

```json
{
  "instruments": [
    {
      "instrument_id": "uuid-v4",
      "holder_id": "uuid-v4-of-holder",
      "class_id": "uuid-v4-of-class",
      "round_id": "uuid-v4-of-round",
      "initial_quantity": 1000000,
      "acquisition_price": 1.00,
      "acquisition_date": "2023-06-01"
    }
  ]
}
```

With vesting:

```json
{
  "instrument_id": "uuid-v4",
  "holder_id": "uuid-v4",
  "class_id": "uuid-v4",
  "initial_quantity": 400000,
  "strike_price": 0.50,
  "vesting_terms": {
    "grant_date": "2023-01-01",
    "cliff_days": 365,
    "vesting_period_days": 1460
  }
}
```

#### Rounds (Financing Events)

```json
{
  "rounds": [
    {
      "round_id": "uuid-v4",
      "name": "Series A",
      "round_date": "2023-06-01",
      "investment_amount": 10000000,
      "pre_money_valuation": 40000000,
      "post_money_valuation": 50000000,
      "price_per_share": 2.50,
      "shares_issued": 4000000
    }
  ]
}
```

### Formula Encoding Objects (FEO)

For calculated fields, use FEO structure:

```json
{
  "ownership_percent_fds": {
    "is_calculated": true,
    "formula_string": "SharesHeld / TotalFDS",
    "dependency_refs": [
      {
        "placeholder": "SharesHeld",
        "path": "#/instruments/0/current_quantity",
        "reference_type": "structured_reference"
      },
      {
        "placeholder": "TotalFDS",
        "path": "Total_FDS",
        "reference_type": "named_range"
      }
    ],
    "output_type": "cell_reference"
  }
}
```

## Architecture

### Component Overview

The code is organized in the `src/captable/` package:

1. **schema.py**: JSON Schema definition (Draft 2019-09)
2. **validation.py**: Validation engine with custom validators
3. **dlm.py**: Maps JSON → Excel addresses
4. **formulas.py**: Translates FEO → Excel formulas
5. **excel.py**: Creates workbooks with xlsxwriter
6. **generator.py**: Main orchestrator

### Formula Resolution Pipeline

```
JSON Data → Schema Validation → DLM Creation → Formula Resolution → Excel Generation
```

1. **Validation**: Check schema compliance and relationships
2. **DLM Creation**: Map UUIDs to Excel addresses during sheet structure creation
3. **Formula Resolution**: Convert symbolic FEO formulas to Excel syntax
4. **Excel Generation**: Write data, formulas, and formatting

### Reference Types

The system uses three types of Excel references for robustness:

- **Named Ranges**: Global constants (e.g., `Total_FDS`, `Current_PPS`)
- **Structured References**: Table columns (e.g., `Ledger[@[shares]]`)
- **Cell References**: Direct addresses (e.g., `Summary!$B$5`)

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest tests/test_cap_table.py -v

# Or from the tests directory
cd tests && python test_cap_table.py
```

Test coverage includes:
- Schema validation (valid/invalid data, foreign keys, UUIDs)
- DLM functionality (named ranges, tables, references)
- Formula resolution (ownership, TSM, vesting, waterfall)
- End-to-end generation (simple and complex scenarios)

## Examples

See `example_usage.py` for comprehensive examples:

```bash
python example_usage.py
```

Examples cover:
1. Generate from JSON file
2. Generate from data dictionary
3. Use generator class with validation
4. Build custom cap table programmatically

## Advanced Topics

### Adding New Instrument Types

1. Define new security class type in `json_schema.py`
2. Add terms package if needed
3. Implement formulas in `formula_resolver.py`
4. Update `excel_generator.py` to handle new columns

### Custom Formulas

Use FEO structure to add calculated fields:

```python
{
  "my_metric": {
    "is_calculated": true,
    "formula_string": "Value1 * Value2 / Denominator",
    "dependency_refs": [
      {"placeholder": "Value1", "path": "...", "reference_type": "..."},
      {"placeholder": "Value2", "path": "...", "reference_type": "..."},
      {"placeholder": "Denominator", "path": "...", "reference_type": "..."}
    ],
    "output_type": "cell_reference"
  }
}
```

### Waterfall Scenarios

Define multiple exit scenarios:

```json
{
  "waterfall_scenarios": [
    {
      "scenario_id": "uuid-v4",
      "name": "Conservative Exit",
      "exit_value": 50000000
    },
    {
      "scenario_id": "uuid-v4",
      "name": "Target Exit",
      "exit_value": 100000000
    },
    {
      "scenario_id": "uuid-v4",
      "name": "Optimistic Exit",
      "exit_value": 200000000
    }
  ]
}
```

## Troubleshooting

### Excel shows #NAME? errors

- Excel file opened before recalculation completed
- Close and reopen the file
- Or press Ctrl+Alt+F9 (Windows) / Cmd+Opt+F9 (Mac) to force recalculation

### Validation errors

Check:
- All UUIDs are valid v4 format
- Foreign key references exist (holder_id, class_id, etc.)
- No duplicate UUIDs within entity types
- Required fields present

### Formulas not updating

- Check that Named Ranges are defined correctly
- Verify Excel Tables are created (not just ranges)
- Ensure `workbook.set_calc_mode('auto')` is set

## Contributing

To extend the system:

1. Add new entity types to `json_schema.py`
2. Implement validation in `cap_table_schema.py`
3. Create formula helpers in `formula_resolver.py`
4. Update Excel generation in `excel_generator.py`
5. Add tests to `test_cap_table.py`

## License

MIT License - See LICENSE file for details

## References

Based on industry-standard cap table practices:
- [Wall Street Prep: Cap Tables](https://www.wallstreetprep.com/knowledge/the-ultimate-guide-to-capitalization-tables/)
- [Treasury Stock Method](https://www.wallstreetprep.com/knowledge/treasury-stock-method/)
- [Liquidation Preferences](https://breakingintowallstreet.com/kb/venture-capital/liquidation-preference/)
- [JSON Schema Specification](https://json-schema.org/draft/2019-09/json-schema-core.html)

## Support

For issues, questions, or contributions, please refer to the documentation in the `docs/` directory.

