# Bug Fix: #REF! Error in Cap Table Progression Sheet

## Issue
Error message: `=SUMIFS(Ledger[initial_quantity]; Ledger[holder_name]; "Joost Klein"; #REF!; "Series A")`

The `#REF!` error occurs because the formula references `Ledger[round_name]` but this column doesn't exist in the Ledger Excel Table.

## Root Cause

1. **Missing Column**: The Ledger table definition in `excel.py` (lines 182-189) was missing the `round_name` column
2. **JSON Data**: Some instruments have `round_name` (like Joost VC's Series A Preferred) while others don't (like Joost Klein's Common Stock)
3. **Formula Reference**: The Cap Table Progression sheet uses formulas that filter by both `holder_name` and `round_name`

## Problematic JSON Data

```json
"instruments": [
  {
    "holder_name": "Joost Klein",
    "class_name": "Common Stock",
    "initial_quantity": 500000,
    "acquisition_date": "2022-01-22",
    "acquisition_price": 1.0
    // NOTE: NO round_name field!
  },
  {
    "holder_name": "Joost VC",
    "class_name": "Series A Preferred",
    "initial_quantity": 333333,
    "round_name": "Series A"  // ✓ Has round_name
  }
]
```

## Solution

### Changes Made to `src/captable/excel.py`:

1. **Added `round_name` to columns list** (line 186):
```python
columns = [
    'holder_name', 'holder_type',
    'class_name', 'class_type',
    'initial_quantity', 'current_quantity',
    'strike_price', 'acquisition_price', 'acquisition_date', 'round_name',  # ← ADDED
    'ownership_percent_fds',
    'gross_itm', 'proceeds', 'shares_repurchased', 'net_dilution'
]
```

2. **Added `round_name` to row_data** (line 218):
```python
row_data = {
    'holder_name': holder_name,
    'holder_type': holder.get('type', ''),
    'class_name': class_name,
    'class_type': sec_class.get('type', ''),
    'initial_quantity': instrument.get('initial_quantity', 0),
    'current_quantity': instrument.get('current_quantity', instrument.get('initial_quantity', 0)),
    'strike_price': instrument.get('strike_price', 0),
    'acquisition_price': instrument.get('acquisition_price', 0),
    'acquisition_date': instrument.get('acquisition_date', ''),
    'round_name': instrument.get('round_name', ''),  # ← ADDED (defaults to empty string)
}
```

3. **Updated column widths** to accommodate the new column

## Expected Behavior After Fix

### Ledger Table Structure:
| holder_name | ... | round_name | ... |
|-------------|-----|------------|-----|
| Joost Klein | ... | (empty)    | ... |
| Bert Goossen| ... | (empty)    | ... |
| Joost VC    | ... | Series A   | ... |

### Formula Behavior:

**For Joost Klein in Series A round:**
```excel
=SUMIFS(Ledger[initial_quantity], Ledger[holder_name], "Joost Klein", Ledger[round_name], "Series A")
```
- Searches for: holder_name="Joost Klein" AND round_name="Series A"
- Result: 0 (no match, because his round_name is empty string)

**For Joost VC in Series A round:**
```excel
=SUMIFS(Ledger[initial_quantity], Ledger[holder_name], "Joost VC", Ledger[round_name], "Series A")
```
- Searches for: holder_name="Joost VC" AND round_name="Series A"
- Result: 333333 (matches his instrument)

## Testing

1. Export the provided JSON to Excel
2. Verify the Ledger sheet has a `round_name` column
3. Verify the Cap Table Progression sheet formulas work without #REF! errors
4. Check that:
   - Joost Klein shows 0 new shares in Series A
   - Joost VC shows 333,333 new shares in Series A

## Related Formulas

The fix also affects these formulas that use `Ledger[round_name]`:

1. Line 480: `=SUMIFS(Ledger[initial_quantity], Ledger[holder_name], "...", Ledger[round_name], "...")`
2. Line 550: `=SUMIF(Ledger[round_name], "...", Ledger[initial_quantity])`

Both formulas will now work correctly because `Ledger[round_name]` is a valid column.

