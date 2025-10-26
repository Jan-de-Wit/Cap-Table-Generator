# Automatic Pre-Round Shares Calculation Implementation

## Overview
Implemented automatic calculation of `pre_round_shares` for financing rounds based on cumulative shares from previous rounds. This eliminates the need to manually specify this value in the input JSON schema.

## Changes Made

### 1. Validation (`src/captable/validation.py`)
- **Removed** the validation requirement that `pre_round_shares` must be explicitly provided in the input JSON
- Updated `_validate_valuation_calculations()` to only require `pre_money_valuation` or `post_money_valuation`
- Added comment explaining that `pre_round_shares` is now auto-calculated

### 2. Excel Generator (`src/captable/excel.py`)

#### Rounds Sheet Enhancement
- **Added** `pre_round_shares` column to the Rounds sheet
- **For the first round**: Calculates `pre_round_shares` as the sum of all initial (non-round) shares
- **For subsequent rounds**: Uses Excel formula: `=Previous_PreRoundShares + Previous_SharesIssued`
- **Creates named ranges** for each round's pre_round_shares (e.g., `Series_A_PreRoundShares`)
  - Spaces in round names are replaced with underscores for valid Excel named range names

#### Ledger Sheet Enhancement
- **Automatically calculates** `initial_quantity` for instruments with `investment_amount` and `valuation_basis`
- Uses the appropriate formula based on valuation basis:
  - **Pre-money**: `(Investment + Interest) * PreRoundShares / (PreMoney + Investment + Interest)`
  - **Post-money**: `(PreRoundShares * (Investment / PostMoney)) / (1 - (Investment / PostMoney))`
- References the named range for the round's `pre_round_shares`
- References the valuation from the Rounds sheet

#### Shares Issued Calculation
- **Auto-calculates** `shares_issued` in Rounds sheet if not provided
- Uses formula: `=SUMIF(Ledger[round_name], "Round Name", Ledger[initial_quantity])`

### 3. Schema Updates
- Updated schema description for `pre_round_shares` to indicate it's auto-calculated
- Updated both `src/captable/schema.py` and `cap_table_schema.json`

## Benefits

1. **Simpler Input**: Users no longer need to manually calculate and provide `pre_round_shares`
2. **Dynamic Updates**: The Excel file automatically recalculates if valuations or investments change
3. **Reduced Errors**: Eliminates manual calculation mistakes
4. **Linked Transactions**: Rounds are now properly linked and build upon each other

## Example Usage

### Before (Required Manual Calculation)
```json
{
  "rounds": [
    {
      "name": "Series A",
      "pre_money_valuation": 40000000,
      "pre_round_shares": 10000000  // Had to calculate manually
    }
  ]
}
```

### After (Automatic Calculation)
```json
{
  "rounds": [
    {
      "name": "Series A",
      "pre_money_valuation": 40000000
      // pre_round_shares automatically calculated from previous instruments/rounds
    }
  ],
  "instruments": [
    {
      "holder_name": "Investor",
      "class_name": "Series A Preferred",
      "round_name": "Series A",
      "investment_amount": 10000000,
      "valuation_basis": "pre_money"
      // initial_quantity automatically calculated using pre_round_shares
    }
  ]
}
```

## Technical Implementation Details

### Named Range Creation
Each round gets a named range in Excel:
- Format: `{RoundName}_PreRoundShares` (spaces replaced with underscores)
- Example: `Series_A_PreRoundShares` -> Points to cell in Rounds sheet

### Formula References
The system uses three types of references:
1. **Named ranges** for pre_round_shares (e.g., `Series_A_PreRoundShares`)
2. **Absolute cell references** for valuations (e.g., `Rounds!$E$2`)
3. **Structured table references** for Ledger columns (e.g., `Ledger[initial_quantity]`)

### Calculation Flow
1. System counts non-round instruments to get initial founder shares
2. First round's `pre_round_shares` = initial founder shares
3. Each subsequent round's `pre_round_shares` = previous `pre_round_shares` + previous `shares_issued`
4. When calculating shares from investment, formulas reference the round's `pre_round_shares` named range
5. All calculations happen in Excel, maintaining full transparency and auditability

## Testing

Created and verified with test case:
- Founder shares: 10,000,000
- Series A investment: $10,000,000
- Pre-money valuation: $40,000,000
- Result: ~2,500,000 shares issued to Series A investor (~20% ownership)

✅ All validations pass
✅ Excel file generates correctly
✅ Formulas are properly linked
✅ No Excel warnings

## Valuation Basis Support

The implementation supports both **pre-money** and **post-money** valuation bases through the `valuation_basis` flag on instruments:

### Pre-Money Calculation
```excel
Shares = (Investment + Interest) × PreRoundShares / (PreMoney + Investment + Interest)
```

### Post-Money Calculation  
```excel
Shares = (PreRoundShares × (Investment / PostMoney)) / (1 - (Investment / PostMoney))
```

### Example Difference
With 10M founder shares and $10M investment:
- **Pre-money ($40M)**: Investor gets 2M shares = 16.67% ownership
- **Post-money ($50M)**: Investor gets 2.5M shares = 20% ownership

See `VALUATION_BASIS_CALCULATIONS.md` and `PRE_VS_POST_MONEY_COMPARISON.md` for detailed explanations.

## Files Modified

1. `src/captable/validation.py` - Removed validation requirement
2. `src/captable/excel.py` - Added automatic calculations and formulas for both pre-money and post-money
3. `src/captable/formulas.py` - Contains both valuation basis formulas
4. `src/captable/schema.py` - Updated schema descriptions
5. `cap_table_schema.json` - Updated schema descriptions

## Documentation Created

1. `AUTO_PRE_ROUND_SHARES_IMPLEMENTATION.md` - This file
2. `VALUATION_BASIS_CALCULATIONS.md` - Detailed formula documentation
3. `PRE_VS_POST_MONEY_COMPARISON.md` - Visual comparison and examples

