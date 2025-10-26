# Valuation-Based Share Calculations

This guide explains how to use the Cap Table Generator's valuation-based share calculation feature, which allows you to calculate the number of shares issued based on investment amount and company valuation.

## Overview

Instead of specifying the exact number of shares in an instrument, you can provide:
- **Investment amount**: The dollar amount invested
- **Valuation basis**: Whether to use pre-money or post-money valuation
- **Round reference**: The financing round with valuation information
- **Interest (optional)**: Interest rate and start date for accruing interest

The system will automatically calculate:
- Number of shares issued
- Accrued interest (if applicable)
- Price per share
- Ownership percentage

## Use Cases

### 1. Standard Equity Investment

When an investor commits to invest based on a company valuation rather than a specific number of shares.

**Example**: "We'll invest $2M at a $10M post-money valuation"

```json
{
  "holder_name": "Investor Name",
  "class_name": "Series A Preferred",
  "round_name": "Series A",
  "investment_amount": 2000000,
  "valuation_basis": "post_money",
  "acquisition_date": "2024-06-15"
}
```

### 2. Convertible Note with Interest

When a convertible note accrues interest over time before converting to equity.

**Example**: "We lent $500K at 8% annual interest starting Jan 1, 2024"

```json
{
  "holder_name": "Bridge Investor",
  "class_name": "Convertible Note",
  "round_name": "Bridge Round",
  "investment_amount": 500000,
  "valuation_basis": "pre_money",
  "interest_rate": 0.08,
  "interest_start_date": "2024-01-01",
  "acquisition_date": "2024-01-01"
}
```

### 3. SAFE Note

When a SAFE converts based on a valuation cap or discount.

```json
{
  "holder_name": "Angel Investor",
  "class_name": "SAFE",
  "round_name": "Seed Round",
  "investment_amount": 100000,
  "valuation_basis": "post_money",
  "acquisition_date": "2023-03-01"
}
```

## Mathematical Formulas

### Pre-Money Valuation

When using **pre_money** valuation:

```
Post-Money Valuation = Pre-Money Valuation + Investment + Interest
Ownership % = (Investment + Interest) / Post-Money Valuation
Shares Issued = (Investment + Interest) × Pre-Round Shares / Post-Money Valuation
```

**Example**:
- Pre-money valuation: $8M
- Investment: $2M
- Interest: $0
- Pre-round shares: 8M

```
Post-Money = $8M + $2M = $10M
Ownership = $2M / $10M = 20%
Shares = $2M × 8M / $10M = 1.6M shares
```

### Post-Money Valuation

When using **post_money** valuation:

```
Ownership % = (Investment + Interest) / Post-Money Valuation
Shares Issued = Pre-Round Shares × Ownership % / (1 - Ownership %)
```

**Example**:
- Post-money valuation: $10M
- Investment: $2M
- Interest: $0
- Pre-round shares: 8M

```
Ownership = $2M / $10M = 20%
Shares = 8M × 0.20 / 0.80 = 2M shares
```

### Interest Calculation

Simple interest formula:

```
Accrued Interest = Principal × Interest Rate × (Days Elapsed / 365)
```

**Example**:
- Principal: $500K
- Rate: 8% annually (0.08)
- Days elapsed: 365 (1 year)

```
Interest = $500K × 0.08 × (365/365) = $40K
```

## Round Configuration

When instruments use valuation-based calculations, the corresponding round must include:

### Required Fields
- `name`: Round identifier
- `round_date`: Closing date
- `pre_round_shares`: Total shares outstanding before the round

### Valuation Fields (at least one required)
- `pre_money_valuation`: Company value before investment
- `post_money_valuation`: Company value after investment

### Example Round

```json
{
  "name": "Series A",
  "round_date": "2024-06-15",
  "post_money_valuation": 15000000,
  "pre_round_shares": 10000000
}
```

## Validation Rules

The system validates:

1. **Instrument Requirements**: Must have EITHER:
   - `initial_quantity` (explicit shares), OR
   - `investment_amount` + `valuation_basis` + `round_name` (calculated shares)

2. **Round Requirements**: When instruments calculate shares, the round must have:
   - At least one of: `pre_money_valuation` or `post_money_valuation`
   - `pre_round_shares`

3. **Valuation Basis**: Must be exactly `"pre_money"` or `"post_money"`

4. **Interest Fields**: 
   - `interest_rate`: Must be between 0 and 1 (as decimal)
   - `interest_start_date`: Must be valid date in YYYY-MM-DD format

## Excel Formula Generation

The system generates Excel formulas for dynamic calculations:

### Accrued Interest Formula
```excel
=IFERROR(investment_amount * interest_rate * (DAYS(current_date, interest_start_date) / 365), 0)
```

### Shares from Pre-Money Valuation
```excel
=IFERROR((investment + interest) * pre_round_shares / (pre_money + investment + interest), 0)
```

### Shares from Post-Money Valuation
```excel
=IFERROR((pre_round_shares * (investment + interest) / post_money) / (1 - ((investment + interest) / post_money)), 0)
```

## Complete Example

Here's a complete cap table using valuation-based calculations:

```json
{
  "schema_version": "1.0",
  "company": {
    "name": "Example Corp",
    "current_date": "2024-12-01"
  },
  "holders": [
    {
      "name": "Founder",
      "type": "founder"
    },
    {
      "name": "VC Fund",
      "type": "investor"
    }
  ],
  "classes": [
    {
      "name": "Common",
      "type": "common"
    },
    {
      "name": "Series A",
      "type": "preferred",
      "terms_name": "Series A Terms"
    }
  ],
  "terms": [
    {
      "name": "Series A Terms",
      "liquidation_multiple": 1.0,
      "participation_type": "non_participating"
    }
  ],
  "instruments": [
    {
      "holder_name": "Founder",
      "class_name": "Common",
      "initial_quantity": 8000000,
      "acquisition_date": "2023-01-01"
    },
    {
      "holder_name": "VC Fund",
      "class_name": "Series A",
      "round_name": "Series A",
      "investment_amount": 5000000,
      "valuation_basis": "post_money",
      "acquisition_date": "2024-06-15"
    }
  ],
  "rounds": [
    {
      "name": "Series A",
      "round_date": "2024-06-15",
      "post_money_valuation": 20000000,
      "pre_round_shares": 8000000
    }
  ]
}
```

**Result**:
- VC Fund ownership: $5M / $20M = 25%
- Shares issued: 8M × 0.25 / 0.75 = 2,666,667 shares
- Total shares after round: 8M + 2.67M = 10.67M shares
- Price per share: $20M / 10.67M = $1.875/share

## Best Practices

1. **Always specify pre_round_shares**: This is essential for accurate calculations
2. **Be consistent with valuation basis**: Use the same basis (pre or post) as agreed in term sheets
3. **Include round dates**: Helps with interest calculations and audit trails
4. **Document interest terms**: Clearly specify rates and start dates for convertible instruments
5. **Validate before generating**: Use the validation tool to catch errors early

## Migration from Explicit Shares

If you have existing instruments with explicit share counts and want to convert to valuation-based:

**Before** (explicit shares):
```json
{
  "holder_name": "Investor",
  "class_name": "Series A",
  "initial_quantity": 2000000,
  "acquisition_price": 2.50
}
```

**After** (valuation-based):
```json
{
  "holder_name": "Investor",
  "class_name": "Series A",
  "round_name": "Series A",
  "investment_amount": 5000000,
  "valuation_basis": "post_money"
}
```

Note: You'll also need to add the corresponding round with valuation details.

## FAQ

**Q: Can I mix explicit shares and valuation-based calculations?**
A: Yes! Some instruments can have `initial_quantity` while others use `investment_amount`.

**Q: What happens if I specify both initial_quantity and investment_amount?**
A: The system will use `initial_quantity` if present and ignore investment-based fields.

**Q: How is interest calculated for partial years?**
A: Simple interest is pro-rated based on days: `(Days Elapsed / 365) × Annual Rate`

**Q: Can I use this for option pool calculations?**
A: Not directly. Option pools should still use explicit `initial_quantity`.

**Q: What if the round date is after the current date?**
A: The system will calculate based on all dates provided. For future rounds, set an appropriate `current_date` in the company section.

## See Also

- [JSON Input Guide](JSON_INPUT_GUIDE.md) - Complete schema documentation
- [Schema Reference](SCHEMA_REFERENCE.md) - Quick reference
- [Formula Documentation](../src/captable/formulas.py) - Excel formula implementations

