# Cap Table Excel Export Architecture

This document maps out the complete architecture and flow for exporting cap tables to Excel format.

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Entry Points](#entry-points)
3. [Data Flow](#data-flow)
4. [Component Breakdown](#component-breakdown)
5. [Sheet Generation Process](#sheet-generation-process)
6. [Formula Generation](#formula-generation)
7. [Formatting and Styling](#formatting-and-styling)
8. [Reference Management](#reference-management)
9. [File Structure](#file-structure)

---

## High-Level Architecture

The Excel export system follows a **round-based architecture** where:

- **Rounds Sheet** is the **source of truth** - contains all rounds with nested instruments
- **Cap Table Sheet** is a **summary view** - shows ownership evolution across rounds
- **Pro Rata Allocations Sheet** handles pro rata share calculations separately

All calculations are **formula-driven** and **fully traceable** - no hardcoded values.

### Key Design Principles

1. **Modular Sheet Generators**: Each sheet type has its own generator class
2. **Centralized Formatting**: All cell formats defined in one place
3. **Deterministic Layout**: DLM (Deterministic Layout Map) tracks all cell references
4. **Formula-Based Calculations**: All share calculations use Excel formulas
5. **Structured References**: Uses Excel Tables with structured references where possible

---

## Entry Points

### 1. FastAPI Endpoint (`fastapi/main.py`)

**Route**: `POST /generate-excel`

**Flow**:

```
HTTP Request (JSON)
  → CapTableRequest (Pydantic model)
  → CapTableGenerator.validate()
  → CapTableGenerator.generate_excel()
  → ExcelGenerator.generate()
  → Excel file (binary response)
```

**Key Code**:

```python
@app.post("/generate-excel")
async def generate_excel(request: CapTableRequest, background_tasks: BackgroundTasks):
    data = request.model_dump()
    generator = CapTableGenerator(json_data=data)
    generator.validate()
    generator.generate_excel(excel_path)
    return FileResponse(excel_path, ...)
```

### 2. Direct Python Functions

**Functions**:

- `generate_from_json(json_path, output_path)` - From JSON file
- `generate_from_data(data, output_path)` - From data dictionary

**Location**: `fastapi/captable/generator.py`

---

## Data Flow

### Input: JSON Cap Table Structure

```json
{
  "schema_version": "2.0",
  "holders": [...],
  "rounds": [
    {
      "name": "Round 1",
      "calculation_type": "valuation_based",
      "round_date": "2024-01-01",
      "valuation": 1000000,
      "valuation_basis": "pre_money",
      "instruments": [
        {
          "holder_name": "Investor A",
          "class_name": "Common",
          "investment_amount": 100000,
          "pro_rata_rights": "standard"
        }
      ]
    }
  ]
}
```

### Processing Pipeline

```
1. Validation
   ├── Schema validation (structure, types)
   ├── Relationship validation (foreign keys)
   └── Business rules validation (logic)

2. Excel Generation
   ├── Create workbook (xlsxwriter)
   ├── Create formats (ExcelFormatters)
   ├── Initialize DLM (DeterministicLayoutMap)
   └── Generate sheets (in order):
       ├── Cap Table (empty, created first for ordering)
       ├── Rounds (source of truth)
       ├── Pro Rata Allocations
       └── Cap Table (populated, references other sheets)

3. Output: .xlsx file
```

---

## Component Breakdown

### 1. CapTableGenerator (`fastapi/captable/generator.py`)

**Purpose**: Main orchestrator for cap table generation

**Responsibilities**:

- Load JSON data (from file or dict)
- Validate data (schema, relationships, business rules)
- Coordinate Excel generation
- Export JSON

**Key Methods**:

- `validate()` - Runs all validation steps
- `generate_excel(output_path, force=False)` - Generates Excel file
- `export_json(output_path)` - Exports JSON

### 2. ExcelGenerator (`fastapi/captable/excel/excel_generator.py`)

**Purpose**: Orchestrates Excel workbook creation

**Responsibilities**:

- Create xlsxwriter workbook
- Initialize shared resources (formats, DLM)
- Coordinate sheet generation
- Manage sheet creation order

**Key Methods**:

- `generate()` - Main generation method
  - Creates workbook
  - Sets default format (font size 10, bg color #869A78)
  - Creates formats dictionary
  - Generates sheets in order:
    1. Cap Table (empty, for ordering)
    2. Rounds (source of truth)
    3. Pro Rata Allocations
    4. Cap Table (populated)

**Dependencies**:

- `ExcelFormatters` - Cell formatting
- `DeterministicLayoutMap` - Reference tracking
- Sheet generators: `RoundsSheetGenerator`, `ProgressionSheetGenerator`, `ProRataSheetGenerator`

### 3. BaseSheetGenerator (`fastapi/captable/excel/base.py`)

**Purpose**: Abstract base class for all sheet generators

**Responsibilities**:

- Common utilities (column letters, cell references)
- Table formatting helpers
- Padding and border management
- Round header writing utilities

**Key Utilities**:

- `_col_letter(col_idx)` - Convert 0-based index to Excel column letter
- `_sanitize_excel_name(name)` - Sanitize names for Excel named ranges
- `_get_cell_reference(row, col, sheet_name, absolute)` - Generate cell references
- `setup_table_formatting()` - Apply borders, padding, backgrounds
- `write_round_headers()` - Write merged round name headers

### 4. RoundsSheetGenerator (`fastapi/captable/excel/sheet_generators/rounds_sheet.py`)

**Purpose**: Creates the Rounds sheet (source of truth)

**Structure**:

- Each round displayed vertically
- Round heading + constants section
- Instruments table (columns vary by `calculation_type`)
- Pro rata calculations excluded (handled separately)

**Round Constants Section**:

- Round Date
- Pre-investment Valuation (formula-based for valuation rounds)
- Investment (sum of instrument investments)
- Post-investment Valuation (formula-based)
- Price Per Share (calculated for convertible/SAFE)

**Instruments Table Columns** (varies by `calculation_type`):

1. **fixed_shares**: Holder Name, Class Name, Pro Rata, Shares
2. **target_percentage**: Holder Name, Class Name, Target %, Pro Rata, Shares
3. **valuation_based**: Holder Name, Class Name, Investment Amount, Pro Rata, Shares
4. **convertible**: Holder Name, Class Name, Principal, Interest %, Discount %, Payment Date, Expected Conversion Date, Days Outstanding, Interest Type, Accrued Interest, Conversion Amount, Valuation Cap Type, Valuation Cap, Pro Rata, Shares
5. **safe**: Holder Name, Class Name, Principal, Discount %, Expected Conversion Date, Valuation Cap Type, Valuation Cap, Pro Rata, Shares

**Key Features**:

- Creates Excel Tables for each round's instruments
- Uses structured references (`TableName[[#All],[Shares]]`)
- Registers named ranges for valuations and price per share
- Tracks round ranges for other sheets to reference
- Calculates shares using formulas from `formulas/valuation.py`

**Output**: Round ranges dictionary passed to other generators

### 5. ProgressionSheetGenerator (`fastapi/captable/excel/sheet_generators/progression_sheet.py`)

**Purpose**: Creates the Cap Table sheet (summary view)

**Structure**:

- Shareholders column (with grouping: Founders, ESOP, Noteholders, Investors, etc.)
- Description column
- For each round: Start (#), New (#), Total (#), (%)

**Data Flow**:

- **Start**: Previous round's Total (or 0 for first round)
- **New**: Sum of shares from Rounds sheet + Pro-rata Shares from Pro Rata Allocations sheet
- **Total**: Start + New (rounded)
- **%**: Total / Sum of all Totals for this round

**Key Features**:

- Groups holders by their `group` field
- Uses SUMIF to lookup shares from Rounds sheet
- References Pro Rata Allocations sheet for pro rata shares
- Creates named ranges for Pre-Round Shares (used by Rounds sheet)
- Freezes panes below column headers

**References**:

- Rounds sheet: Uses structured references or SUMIF over table
- Pro Rata Allocations sheet: Direct cell references

### 6. ProRataSheetGenerator (`fastapi/captable/excel/sheet_generators/pro_rata_sheet.py`)

**Purpose**: Creates the Pro Rata Allocations sheet

**Structure**:

- Shareholders column (same order as Cap Table)
- Description column
- For each round: Pro-rata Rights, Super pro rata %, Exercise Type, Partial Amount, Partial %, Effective %, Pro-rata Shares, Price per Share, Investment

**Pro Rata Types**:

- **None**: No pro rata rights (shows "-" if no previous shares)
- **Standard**: Maintain current ownership percentage
- **Super**: Achieve target ownership percentage

**Exercise Types**:

- **Full**: Exercise all pro rata rights
- **Partial**: Exercise partial rights (with amount or percentage constraint)

**Key Calculations**:

- **Effective %**: Calculated based on pro rata type, exercise type, and partial constraints
- **Pro-rata Shares**: Formula from `formulas/ownership.py` using effective %
- **Price Per Share**: Pre-investment Valuation / Pre-round Shares
- **Investment**: Price Per Share × Pro-rata Shares

**Key Features**:

- Dropdown validation for Pro-rata Rights (None/Standard/Super)
- Dropdown validation for Exercise Type (Full/Partial)
- Conditional formatting for errors (red background)
- Data validation to prevent sum of pro rata % >= 100%
- Creates named ranges for total Pro-rata Shares per round

**Formula Complexity**:

- Effective % formula handles multiple scenarios (full/partial, standard/super, amount/percentage constraints)
- Pro-rata Shares uses complex ownership formula with denominator calculations

### 7. ExcelFormatters (`fastapi/captable/excel/formatters.py`)

**Purpose**: Centralized cell format definitions

**Format Types**:

- **Text formats**: `text`, `italic_text`, `header`, `label`, `round_name`
- **Round headers**: `round_header`, `round_header_plain`
- **Number formats**: `currency`, `percent`, `number`, `decimal`, `date`, `empty`
- **Total row formats**: `total_label`, `total_number`, `total_percent`, `total_currency`, `total_text`
- **Table formats**: `table_currency`, `table_number`, `table_date`, `table_percent`
- **Special formats**: `white_bg`, `table_border`, `error`, `error_text`

**Font**: PT Sans (11pt) for body text, Century Gothic (14pt Bold) for round headers

**Default Format**: Font size 10, background color #869A78 (applied to all cells)

### 8. TableBuilder (`fastapi/captable/excel/table_builder.py`)

**Purpose**: Utilities for creating Excel Tables

**Key Methods**:

- `create_table()` - Creates Excel Table with data and formulas
- `add_data_validation()` - Adds dropdown validation to columns

**Features**:

- Handles empty tables (creates structure with headers)
- Supports column formulas
- Uses "Table Style Medium 2" by default

### 9. DeterministicLayoutMap (`fastapi/captable/dlm.py`)

**Purpose**: Tracks mapping between JSON data and Excel locations

**Responsibilities**:

- Named range registration
- Table registration
- UUID/JSON pointer to Excel reference mapping
- Structured reference generation

**Key Methods**:

- `register_named_range()` - Register global constants
- `register_table()` - Register Excel Tables
- `register_round_section()` - Register round locations
- `register_round_instrument()` - Register instrument locations
- `resolve_reference()` - Resolve identifier to Excel reference

**Usage**: Used by sheet generators to track and resolve references

### 10. Formula Modules (`fastapi/captable/formulas/`)

**Purpose**: Generate Excel formulas for calculations

**Modules**:

- **valuation.py**: Share calculations for valuation-based, convertible, SAFE rounds
- **ownership.py**: Pro rata share calculations
- **interest.py**: Interest calculations for convertible notes
- **tsm.py**: TSM (Total Shares Method) calculations
- **resolver.py**: Formula resolution utilities

**Key Functions**:

- `create_shares_from_percentage_formula()` - Target percentage rounds
- `create_shares_from_valuation_formula()` - Valuation-based rounds
- `create_convertible_shares_formula()` - Convertible/SAFE rounds
- `create_accrued_interest_formula()` - Interest calculations
- `create_pro_rata_formula()` - Pro rata share calculations

---

## Sheet Generation Process

### Generation Order

1. **Cap Table** (empty) - Created first so it appears first in Excel
2. **Rounds** - Source of truth, generates round ranges
3. **Pro Rata Allocations** - Uses round ranges from Rounds sheet
4. **Cap Table** (populated) - Uses round ranges and references other sheets

### Rounds Sheet Generation

**Process**:

1. Create worksheet
2. Write title "Input for Cap-Table"
3. For each round:
   - Write round name heading
   - Write round constants (date, valuations, price per share)
   - Write instruments table with appropriate columns
   - Register round section with DLM
   - Store round range info (start_row, end_row, holder_col, shares_col, table_name)
4. Apply formatting (borders, padding, column widths)
5. Return round ranges dictionary

**Round Constants Logic**:

- **Pre-investment Valuation**: Direct value if `valuation_basis == 'pre_money'`, otherwise calculated from Post-investment - Investment
- **Investment**: SUM of instrument investment amounts (or conversion amounts for convertible)
- **Post-investment Valuation**: Direct value if `valuation_basis == 'post_money'`, otherwise calculated from Pre-investment + Investment
- **Price Per Share**: Pre-investment Valuation / Pre-round Shares (for convertible/SAFE)

**Shares Calculation** (varies by type):

- **fixed_shares**: Direct value from `initial_quantity`
- **target_percentage**: Formula: `ROUND((target_pct * pre_round_shares) / (1 - target_pct) - holder_current_shares, 0)`
- **valuation_based**: Formula: `ROUND((investment / pre_investment_valuation) * pre_round_shares, 0)`
- **convertible/SAFE**: Complex formula considering discount, valuation cap, future round references

### Cap Table Sheet Generation

**Process**:

1. Extract unique holders from all rounds
2. Group holders by their `group` field
3. Sort groups (Founders, ESOP, Noteholders, Investors, then alphabetically)
4. Write headers (Shareholders, Description, then round headers)
5. For each holder:
   - Write holder name and description
   - For each round:
     - **Start**: Previous round's Total (or 0)
     - **New**: SUMIF from Rounds sheet + reference to Pro Rata Allocations sheet
     - **Total**: Start + New
     - **%**: Total / Sum of all Totals
6. Write total row with named ranges for Pre-Round Shares
7. Apply formatting and freeze panes

**References**:

- Rounds sheet: Uses structured references (`TableName[[#All],[Shares]]`) or SUMIF
- Pro Rata Allocations: Direct cell reference to Pro-rata Shares column

### Pro Rata Allocations Sheet Generation

**Process**:

1. Extract unique holders (same order as Cap Table)
2. Write headers (Shareholders, Description, then round headers)
3. For each holder and round:
   - **Pro-rata Rights**: Dropdown (None/Standard/Super) - only if holder has previous shares
   - **Super pro rata %**: Value from data (only if type is Super and value provided)
   - **Exercise Type**: Dropdown (Full/Partial)
   - **Partial Amount**: Value from data (if partial exercise)
   - **Partial %**: Value from data (if partial exercise)
   - **Effective %**: Complex formula based on type, exercise type, and constraints
   - **Pro-rata Shares**: Formula from ownership.py using effective %
   - **Price Per Share**: Pre-investment Valuation / Pre-round Shares
   - **Investment**: Price Per Share × Pro-rata Shares
4. Write total row with validation
5. Create named ranges for total Pro-rata Shares per round

**Effective % Formula Logic**:

- If type is None: empty
- If Full exercise:
  - Standard: Previous round ownership %
  - Super: Super pro rata % (if provided)
- If Partial exercise:
  - Standard: MIN(partial_pct, prev_ownership_pct) capped by partial_amount if specified
  - Super: MIN(partial_pct, super_pct) capped by partial_amount if specified

**Pro-rata Shares Formula**:

```
T = (P + B - C) / (1 - R)
shares = (effective_pct * T) - current_shares
```

Where:

- P = pre_round_shares
- B = shares_issued (base shares)
- C = sum of current shares for all pro rata participants
- R = sum of effective % for all pro rata participants
- T = total shares after pro rata
- current_shares = prev_round_total + base_shares_issued

---

## Formula Generation

### Formula Modules

**Location**: `fastapi/captable/formulas/`

#### valuation.py

**Functions**:

- `create_shares_from_percentage_formula()` - Target percentage rounds
- `create_shares_from_valuation_formula()` - Valuation-based rounds
- `create_convertible_shares_formula()` - Convertible/SAFE rounds
- `create_price_per_share_from_valuation_formula()` - Price per share calculation

**Convertible/SAFE Formula**:

- Considers discount rate
- Uses valuation cap (pre-conversion, post-conversion own, post-conversion total)
- Can reference future valuation-based rounds
- Handles per-instrument valuation caps

#### ownership.py

**Functions**:

- `create_pro_rata_formula()` - Pro rata share calculations

**Formula**:

- Uses effective % (from Pro Rata Allocations sheet)
- Calculates total shares considering all pro rata participants
- Subtracts current shares to get shares to purchase

#### interest.py

**Functions**:

- `create_days_passed_formula()` - Days between payment and conversion dates
- `create_accrued_interest_formula()` - Interest calculation based on type

**Interest Types**:

- No interest
- Simple interest
- Compounded yearly
- Compounded monthly
- Compounded daily

### Formula Characteristics

1. **All formulas are Excel-native** - No Python calculations embedded
2. **Formulas use cell references** - Dynamic, update when data changes
3. **Formulas use named ranges** - For global constants (valuations, pre-round shares)
4. **Formulas use structured references** - For Excel Tables where possible
5. **Formulas include error handling** - IFERROR wrappers for safety
6. **Formulas round to integers** - ROUND() for share calculations

---

## Formatting and Styling

### Default Format

**Applied to all cells**:

- Font size: 10
- Background color: #869A78

### Cell Formats

**Defined in**: `fastapi/captable/excel/formatters.py`

**Format Categories**:

1. **Text Formats**:

   - `text`: PT Sans 11pt, black, white bg
   - `italic_text`: PT Sans 11pt italic
   - `header`: PT Sans 11pt bold, bottom border
   - `label`: PT Sans 11pt bold
   - `round_name`: PT Sans 11pt bold

2. **Round Headers**:

   - `round_header`: Century Gothic 14pt bold
   - `round_header_plain`: Century Gothic 14pt bold (no background)

3. **Number Formats**:

   - `currency`: $#,##0.00 format, shows "-" when empty
   - `percent`: 0.00% format, shows "-" when empty
   - `number`: #,##0 format, shows "-" when empty
   - `decimal`: #,##0.00 format
   - `date`: yyyy-mm-dd format
   - `empty`: Shows "-" for empty cells

4. **Total Row Formats**:

   - `total_label`: Bold, top and bottom borders
   - `total_number`: Number format with borders
   - `total_percent`: Percent format with borders
   - `total_currency`: Currency format with borders
   - `total_text`: Text format with borders

5. **Table Formats**:

   - `table_currency`: Left-aligned currency
   - `table_number`: Left-aligned number
   - `table_date`: Left-aligned date
   - `table_percent`: Left-aligned percent

6. **Special Formats**:
   - `white_bg`: White background
   - `error`: Red background for errors
   - `error_text`: Red background for text errors

### Table Formatting

**Applied by**: `BaseSheetGenerator.setup_table_formatting()`

**Features**:

- Padding cells with white background
- White background for entire table
- Borders on all edges
- Custom row heights
- Custom column widths

### Conditional Formatting

**Used for**:

- Error highlighting (red background when pro rata enabled but no previous shares)
- Validation warnings (red background when pro rata % >= 100%)

---

## Reference Management

### Named Ranges

**Created for**:

- Round valuations: `{RoundName}_PreMoneyValuation`, `{RoundName}_PostMoneyValuation`
- Price per share: `{RoundName}_PricePerShare`
- Pre-round shares: `{RoundName}_PreRoundShares`
- Pro-rata shares: `{RoundName}_ProRataShares`
- Holder names: `ProRata_HolderNames`

**Naming Convention**:

- Sanitized round names (spaces/hyphens → underscores)
- Cannot start with numbers
- Cannot contain special characters

### Structured References

**Used for**:

- Excel Tables: `TableName[[#All],[Shares]]`
- Current row: `TableName[@[Shares]]`
- Column ranges: `TableName[[Shares]]`

**Benefits**:

- Automatic expansion when rows added
- More readable than A1 references
- Type-safe column references

### Cell References

**Types**:

- Absolute: `$A$1`
- Relative: `A1`
- Cross-sheet: `'Sheet Name'!$A$1`

**Generated by**: `BaseSheetGenerator._get_cell_reference()`

### Reference Resolution

**Handled by**: `DeterministicLayoutMap`

**Capabilities**:

- UUID to Excel reference mapping
- JSON pointer to Excel reference mapping
- Named range resolution
- Structured reference generation

---

## File Structure

### Core Excel Generation

```
fastapi/captable/excel/
├── __init__.py                 # Module exports
├── excel_generator.py          # Main orchestrator
├── base.py                     # Base sheet generator
├── formatters.py               # Cell format definitions
├── table_builder.py            # Excel Table utilities
└── sheet_generators/
    ├── __init__.py
    ├── rounds_sheet.py         # Rounds sheet generator
    ├── progression_sheet.py    # Cap Table sheet generator
    └── pro_rata_sheet.py       # Pro Rata Allocations generator
```

### Formula Modules

```
fastapi/captable/formulas/
├── __init__.py
├── valuation.py                # Share calculations
├── ownership.py                # Pro rata calculations
├── interest.py                 # Interest calculations
├── tsm.py                      # TSM calculations
└── resolver.py                 # Formula resolution
```

### Core Components

```
fastapi/captable/
├── generator.py                # Main orchestrator
├── dlm.py                      # Deterministic Layout Map
├── schema.py                   # Data schema
└── validation/
    ├── validator.py            # Main validator
    ├── schema_validator.py     # Schema validation
    ├── relationship_validator.py  # Relationship validation
    └── business_rules.py       # Business rules validation
```

### Entry Points

```
fastapi/
├── main.py                     # FastAPI application
└── captable/
    └── generator.py            # Python API
```

---

## Key Dependencies

### External Libraries

- **xlsxwriter**: Excel file generation
- **pydantic**: Data validation (FastAPI)
- **fastapi**: Web API framework

### Internal Dependencies

- **DeterministicLayoutMap**: Reference tracking
- **ExcelFormatters**: Format definitions
- **Formula modules**: Excel formula generation

---

## Data Validation Flow

### Validation Steps

1. **Schema Validation** (`schema_validator.py`):

   - Structure validation (required fields, types)
   - Type checking (strings, numbers, dates, etc.)
   - Enum validation (calculation_type, pro_rata_type, etc.)

2. **Relationship Validation** (`relationship_validator.py`):

   - Foreign key validation (holder_name exists in holders)
   - Round references (conversion_round_ref exists)
   - Circular reference detection

3. **Business Rules Validation** (`business_rules.py`):
   - Business logic validation
   - Constraint checking
   - Data consistency checks

### Validation Integration

**Called by**: `CapTableGenerator.validate()`

**Returns**: `(is_valid: bool, errors: List[str])`

**Usage**: Must pass validation before Excel generation (unless `force=True`)

---

## Round Calculation Types

### 1. fixed_shares

**Input**: `initial_quantity` (direct share count)

**Output**: Shares = `initial_quantity`

**Columns**: Holder Name, Class Name, Pro Rata, Shares

### 2. target_percentage

**Input**: `target_percentage` (desired ownership %)

**Output**: Shares calculated to achieve target % (accounting for existing shares)

**Formula**: `ROUND((target_pct * pre_round_shares) / (1 - target_pct) - holder_current_shares, 0)`

**Columns**: Holder Name, Class Name, Target %, Pro Rata, Shares

### 3. valuation_based

**Input**: `investment_amount`, `valuation`, `valuation_basis`

**Output**: Shares = `(investment / pre_investment_valuation) * pre_round_shares`

**Columns**: Holder Name, Class Name, Investment Amount, Pro Rata, Shares

### 4. convertible

**Input**: `investment_amount`, `interest_rate`, `discount_rate`, `payment_date`, `expected_conversion_date`, `interest_type`, `valuation_cap_type`, `valuation_cap`

**Output**: Complex formula considering:

- Conversion amount (Principal + Accrued Interest)
- Discount rate
- Valuation cap (pre-conversion, post-conversion own, post-conversion total)
- Future round references

**Columns**: Holder Name, Class Name, Principal, Interest %, Discount %, Payment Date, Expected Conversion Date, Days Outstanding, Interest Type, Accrued Interest, Conversion Amount, Valuation Cap Type, Valuation Cap, Pro Rata, Shares

### 5. safe

**Input**: `investment_amount`, `discount_rate`, `expected_conversion_date`, `valuation_cap_type`, `valuation_cap`

**Output**: Similar to convertible but without interest

**Columns**: Holder Name, Class Name, Principal, Discount %, Expected Conversion Date, Valuation Cap Type, Valuation Cap, Pro Rata, Shares

---

## Pro Rata Rights

### Types

1. **None**: No pro rata rights
2. **Standard**: Maintain current ownership percentage
3. **Super**: Achieve target ownership percentage

### Exercise Types

1. **Full**: Exercise all pro rata rights
2. **Partial**: Exercise partial rights with constraints:
   - **Partial Amount**: Maximum investment amount
   - **Partial %**: Maximum ownership percentage

### Calculation Flow

1. Determine if holder has previous shares (from JSON data)
2. If yes, show dropdown (None/Standard/Super)
3. Calculate Effective % based on:
   - Pro rata type
   - Exercise type
   - Partial constraints (if any)
4. Calculate Pro-rata Shares using ownership formula
5. Calculate Price Per Share and Investment Amount

---

## Error Handling

### Validation Errors

**Handled by**: `CapTableGenerator.validate()`

**Types**:

- Schema errors (missing fields, wrong types)
- Relationship errors (invalid references)
- Business rule errors (logic violations)

**Response**: Returns list of error messages, prevents Excel generation

### Excel Generation Errors

**Handled by**: Try-catch blocks in FastAPI endpoint

**Types**:

- File I/O errors
- Formula generation errors
- Reference resolution errors

**Response**: HTTP 500 with error message and traceback (if DEBUG enabled)

### Excel Formula Errors

**Handled by**: IFERROR wrappers in formulas

**Types**:

- Division by zero
- Invalid references
- Type mismatches

**Response**: Formulas return 0 or empty string on error

---

## Performance Considerations

### Optimization Strategies

1. **Structured References**: More efficient than A1 references for large tables
2. **Named Ranges**: Reduce formula complexity
3. **Formula Caching**: Reuse formula strings where possible
4. **Batch Operations**: Write multiple cells in single operations where possible

### Scalability

- **Rounds**: Linear complexity O(n) where n = number of rounds
- **Instruments**: Linear complexity O(m) where m = number of instruments
- **Holders**: Linear complexity O(h) where h = number of holders

**Total Complexity**: O(n × m × h) for full generation, but optimized with:

- Single-pass holder extraction
- Pre-calculated round ranges
- Batch formula generation

---

## Testing Considerations

### Test Points

1. **Validation**: Schema, relationships, business rules
2. **Formula Generation**: Correct Excel formulas for each calculation type
3. **Reference Resolution**: Named ranges, structured references
4. **Formatting**: Cell formats, borders, column widths
5. **Sheet Structure**: Correct layout, headers, totals
6. **Cross-Sheet References**: Formulas referencing other sheets

### Test Data

**Location**: `examples/`

**Files**:

- `chatgpt.json`: Example cap table
- `round_based_example.json`: Round-based example

---

## Future Enhancements

### Potential Improvements

1. **Additional Calculation Types**: Support for new round types
2. **Enhanced Formatting**: More customization options
3. **Performance**: Optimize for very large cap tables
4. **Validation**: More comprehensive business rules
5. **Documentation**: In-sheet documentation/notes
6. **Charts**: Visual representations of ownership evolution

---

## Summary

The Excel export system is a sophisticated, formula-driven architecture that:

1. **Validates** JSON input through multiple validation layers
2. **Generates** Excel workbooks with three main sheets:
   - Rounds (source of truth)
   - Cap Table (summary view)
   - Pro Rata Allocations (pro rata calculations)
3. **Uses** Excel formulas for all calculations (no hardcoded values)
4. **Tracks** references using DeterministicLayoutMap
5. **Formats** consistently using centralized format definitions
6. **Supports** multiple calculation types and pro rata scenarios

The system is designed to be maintainable, extensible, and fully traceable through Excel formulas.
