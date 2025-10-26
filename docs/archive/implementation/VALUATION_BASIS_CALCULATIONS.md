# Valuation Basis Calculations (Pre-Money vs Post-Money)

## Overview
The Cap Table Generator now supports **automatic share calculation** based on investment amount and valuation, with support for both **pre-money** and **post-money** valuation bases. The system uses the `valuation_basis` flag to determine which formula to apply.

## Supported Valuation Bases

### 1. Pre-Money Valuation
Investment is added **on top of** the pre-money valuation.

**Formula:**
```
Shares Issued = (Investment + Interest) × Pre-Round Shares / (Pre-Money + Investment + Interest)
```

**Excel Formula:**
```excel
=IFERROR(({Investment} + {Interest}) * {PreRoundShares} / ({PreMoney} + {Investment} + {Interest}), 0)
```

**Example:**
- Pre-round shares: 10,000,000
- Investment: $10,000,000
- Pre-money valuation: $40,000,000
- **Calculation:**
  - Post-money = $40M + $10M = $50M
  - Shares = $10M × 10M / $50M = **2,000,000 shares**
  - Ownership = 2M / 12M = **16.67%**

### 2. Post-Money Valuation
Investment is **included in** the post-money valuation.

**Formula:**
```
Ownership % = (Investment + Interest) / Post-Money
Shares Issued = Pre-Round Shares × Ownership % / (1 - Ownership %)
```

**Excel Formula:**
```excel
=IFERROR(({PreRoundShares} * (({Investment} + {Interest}) / {PostMoney})) / (1 - (({Investment} + {Interest}) / {PostMoney})), 0)
```

**Example:**
- Pre-round shares: 10,000,000
- Investment: $10,000,000
- Post-money valuation: $50,000,000
- **Calculation:**
  - Ownership % = $10M / $50M = 20%
  - Shares = 10M × 0.20 / (1 - 0.20) = 10M × 0.20 / 0.80 = **2,500,000 shares**
  - Ownership = 2.5M / 12.5M = **20%**

## Key Differences

| Aspect | Pre-Money | Post-Money |
|--------|-----------|------------|
| **Valuation includes investment?** | No | Yes |
| **Investor ownership** | Variable (depends on investment size) | Fixed (Investment / Post-Money) |
| **Dilution calculation** | Post-Money = Pre-Money + Investment | Pre-Money = Post-Money - Investment |
| **Typical use case** | Traditional VC rounds | Founder-friendly, predictable ownership |

## JSON Schema Usage

### Pre-Money Example
```json
{
  "instruments": [
    {
      "holder_name": "Series A Investor",
      "class_name": "Series A Preferred",
      "round_name": "Series A",
      "investment_amount": 10000000,
      "valuation_basis": "pre_money",
      "acquisition_date": "2024-04-01"
    }
  ],
  "rounds": [
    {
      "name": "Series A",
      "round_date": "2024-04-01",
      "pre_money_valuation": 40000000
    }
  ]
}
```

### Post-Money Example
```json
{
  "instruments": [
    {
      "holder_name": "Series A Investor",
      "class_name": "Series A Preferred",
      "round_name": "Series A",
      "investment_amount": 10000000,
      "valuation_basis": "post_money",
      "acquisition_date": "2024-04-01"
    }
  ],
  "rounds": [
    {
      "name": "Series A",
      "round_date": "2024-04-01",
      "post_money_valuation": 50000000
    }
  ]
}
```

## Implementation Details

### Automatic pre_round_shares Calculation
The system automatically calculates `pre_round_shares` for each round:
- **First round:** Sum of all non-round instruments (founder shares)
- **Subsequent rounds:** Previous round's `pre_round_shares` + previous round's `shares_issued`

This is done via Excel formulas, ensuring dynamic recalculation.

### Excel Formula References
The formulas use:
1. **Named ranges** for pre_round_shares: `{RoundName}_PreRoundShares`
2. **Absolute references** for valuations: `Rounds!$E$2` (pre-money) or `Rounds!$F$2` (post-money)
3. **Numeric values** for investment amount and interest

### Interest Support
Both formulas support accrued interest on investments:
- Simple interest: `Principal × Rate × Time`
- Compound interest: `Principal × ((1 + Rate)^Time - 1)`

## Multi-Round Example with Mixed Valuation Bases

You can mix pre-money and post-money valuations across different rounds:

```json
{
  "instruments": [
    {
      "holder_name": "Founder",
      "class_name": "Common Stock",
      "initial_quantity": 10000000
    },
    {
      "holder_name": "Seed Investor",
      "round_name": "Seed",
      "investment_amount": 2000000,
      "valuation_basis": "post_money"  // Seed uses post-money
    },
    {
      "holder_name": "Series A Investor",
      "round_name": "Series A",
      "investment_amount": 10000000,
      "valuation_basis": "pre_money"  // Series A uses pre-money
    }
  ],
  "rounds": [
    {
      "name": "Seed",
      "post_money_valuation": 10000000  // Post-money
    },
    {
      "name": "Series A",
      "pre_money_valuation": 40000000  // Pre-money
    }
  ]
}
```

**Calculations:**
1. **Seed Round (Post-Money $10M)**
   - Pre-round: 10M shares
   - Ownership: $2M / $10M = 20%
   - Shares issued: ~2.5M
   - Total after Seed: 12.5M shares

2. **Series A Round (Pre-Money $40M)**
   - Pre-round: 12.5M shares (auto-calculated from Seed)
   - Post-money: $40M + $10M = $50M
   - Shares issued: $10M × 12.5M / $50M = 2.5M
   - Total after Series A: 15M shares
   - Series A ownership: 2.5M / 15M = 16.67%

## Required Fields

### For Pre-Money Calculation
- `investment_amount` (required)
- `valuation_basis`: "pre_money" (required)
- `round_name` (required)
- Round must have `pre_money_valuation` (required)

### For Post-Money Calculation
- `investment_amount` (required)
- `valuation_basis`: "post_money" (required)
- `round_name` (required)
- Round must have `post_money_valuation` (required)

### Optional Fields (Both)
- `accrued_interest` or interest calculation fields
- `interest_rate`, `interest_start_date`, `interest_type`

## Excel Output Structure

### Rounds Sheet
Includes automatically calculated columns:
- `pre_round_shares` (auto-calculated via formula)
- `shares_issued` (auto-calculated via SUMIF from Ledger)
- Named ranges: `{RoundName}_PreRoundShares`

### Ledger Sheet
- `initial_quantity` uses appropriate formula based on `valuation_basis`
- `current_quantity` defaults to reference `initial_quantity`
- All formulas maintain Excel reference integrity

## Benefits

1. **Flexibility:** Support both pre-money and post-money conventions
2. **Automatic:** No manual share calculations needed
3. **Transparent:** All calculations visible as Excel formulas
4. **Dynamic:** Changes to valuations automatically recalculate shares
5. **Mixed Rounds:** Different valuation bases per round supported

## Testing

All three scenarios have been tested and validated:
✅ Pre-money valuation calculations
✅ Post-money valuation calculations  
✅ Mixed valuation bases across multiple rounds
✅ Automatic pre_round_shares linking between rounds

## Formula References in Code

Implementation in `src/captable/formulas.py`:
- `create_shares_from_investment_premoney_formula()`
- `create_shares_from_investment_postmoney_formula()`

Applied in `src/captable/excel.py`:
- Ledger sheet creation with automatic formula injection
- Rounds sheet with pre_round_shares calculation

