# Share Issuance Methods

This document explains the three methods for issuing shares in the Cap Table Generator.

## Overview

The system supports three distinct methods for determining share quantities:

1. **Fixed Share Issues** - Direct quantity specification
2. **Valuation-Based Share Calculation** - Calculate shares from investment amount and valuation
3. **Convertible Securities** - SAFEs and Convertible Notes that convert later

## Method 1: Fixed Share Issues

**Use Case**: When you know the exact number of shares upfront

**When to Use**:
- Founder equity grants
- Stock option grants to employees
- Advisor equity awards
- Direct share purchases with known quantity

### JSON Structure

```json
{
  "holder_name": "John Founder",
  "class_name": "Common Stock",
  "initial_quantity": 5000000,
  "acquisition_price": 0.01,
  "acquisition_date": "2022-01-01"
}
```

### Fields

- **initial_quantity** (required): The exact number of shares
- **round_name** (optional): Reference to a financing round if applicable
- **acquisition_price** (optional): Price paid per share
- **acquisition_date** (optional): When shares were acquired

### Example Use Cases

**Founder Shares:**
```json
{
  "holder_name": "Alice Founder",
  "class_name": "Common Stock",
  "initial_quantity": 10000000,
  "acquisition_date": "2021-01-01"
}
```

**Employee Options:**
```json
{
  "holder_name": "Bob Employee",
  "class_name": "Employee Options",
  "initial_quantity": 50000,
  "strike_price": 0.50,
  "acquisition_date": "2024-01-15",
  "vesting_terms": {
    "grant_date": "2024-01-15",
    "cliff_days": 365,
    "vesting_period_days": 1460
  }
}
```

## Method 2: Valuation-Based Share Calculation

**Use Case**: When investors provide capital and you need to calculate shares based on company valuation

**When to Use**:
- Equity financing rounds (Series A, Series B, etc.)
- Convertible preferred share issuances
- Strategic investments

### Pre-Money vs Post-Money

The system supports two valuation bases:

#### Pre-Money Valuation

**Formula:**
```
Shares = (Investment + Interest) × Pre-Round Shares / (Pre-Money + Investment + Interest)
```

Investment is **added on top of** the pre-money valuation.

**Example:**
- Pre-round shares: 10,000,000
- Investment: $10,000,000
- Pre-money valuation: $40,000,000
- **Calculation**: $10M × 10M / $50M = **2,000,000 shares**
- Ownership: 2M / 12M = **16.67%**

#### Post-Money Valuation

**Formula:**
```
Ownership % = (Investment + Interest) / Post-Money
Shares = Pre-Round Shares × Ownership % / (1 - Ownership %)
```

Investment is **included in** the post-money valuation.

**Example:**
- Pre-round shares: 10,000,000
- Investment: $10,000,000
- Post-money valuation: $50,000,000
- **Calculation**: 10M × 0.20 / 0.80 = **2,500,000 shares**
- Ownership: 2.5M / 12.5M = **20%**

### JSON Structure

```json
{
  "holder_name": "Acme Ventures",
  "class_name": "Series A Preferred",
  "round_name": "Series A",
  "investment_amount": 5000000,
  "valuation_basis": "post_money",
  "acquisition_date": "2024-06-01"
}
```

### Required Fields

- **investment_amount** (required): Amount invested
- **valuation_basis** (required): "pre_money" or "post_money"
- **round_name** (required): Must reference a round with valuation data

### Optional Fields

- **interest_rate** (optional): Annual interest rate as decimal (e.g., 0.08 for 8%)
- **interest_start_date** (optional): When interest starts accruing
- **interest_type** (optional): "simple" or "compound" (default: simple)

### Required Round Data

The referenced round must have:

```json
{
  "name": "Series A",
  "round_date": "2024-06-01",
  "pre_money_valuation": 40000000,
  "post_money_valuation": 50000000,
  "price_per_share": 4.0
}
```

### Complete Example

**Step 1: Create the Round**
```json
{
  "name": "Series A",
  "round_date": "2024-06-01",
  "pre_money_valuation": 40000000,
  "post_money_valuation": 50000000
}
```

**Step 2: Create the Instrument**
```json
{
  "holder_name": "Acme Ventures",
  "class_name": "Series A Preferred",
  "round_name": "Series A",
  "investment_amount": 5000000,
  "valuation_basis": "post_money"
}
```

**Result**: System calculates shares automatically using the post-money formula

### Interest Accrual

For investments that accrue interest:

```json
{
  "holder_name": "Bridge Investor",
  "class_name": "Bridge Note",
  "round_name": "Bridge",
  "investment_amount": 1000000,
  "valuation_basis": "pre_money",
  "interest_rate": 0.06,
  "interest_start_date": "2024-01-01",
  "interest_type": "simple"
}
```

The system will calculate: Final Amount = Investment + Accrued Interest

## Method 3: Convertible Securities (SAFEs & Convertible Notes)

**Use Case**: Early-stage investments that convert to equity at a qualified financing

**When to Use**:
- SAFEs (Simple Agreement for Future Equity)
- Convertible notes
- Bridge financing instruments

### Key Differences

| Feature | SAFE | Convertible Note |
|---------|------|------------------|
| Interest | No | Yes (optional) |
| Maturity Date | No | Optional |
| Principal Return | No (converts or returns) | Yes if not converted |
| Structure | Convertible preferred | Debt that converts |

### Conversion Mechanics

Convertibles convert at a **qualifying financing** with these protections:

1. **Discount Rate** (e.g., 20% discount): Investor gets shares at 80% of the price
2. **Valuation Cap** (e.g., $5M cap): Conversion based on lower of (discounted price, cap price)

**Conversion Price Formula:**
```
Conversion Price = MIN(Discounted Price, Cap Price)

Discounted Price = Round PPS × (1 - Discount Rate)
Cap Price = Valuation Cap / Pre-Round Shares
```

**Conversion Shares:**
```
Shares = Investment / Conversion Price
```

### JSON Structure

#### SAFE Example

```json
{
  "holder_name": "Early Investor",
  "class_name": "SAFE",
  "convertible_terms": {
    "investment_amount": 500000,
    "discount_rate": 0.20,
    "price_cap": 5000000
  }
}
```

**What this means**:
- $500,000 invested
- 20% discount on conversion
- $5M valuation cap
- Convertible preferred shares upon qualified financing

#### Convertible Note Example (with Interest)

```json
{
  "holder_name": "Bridge Investor",
  "class_name": "Convertible Note",
  "convertible_terms": {
    "investment_amount": 250000,
    "discount_rate": 0.15,
    "price_cap": 4000000,
    "interest_rate": 0.06,
    "investment_start_date": "2024-01-01",
    "interest_type": "simple"
  }
}
```

**What this means**:
- $250,000 invested
- 15% discount on conversion
- $4M valuation cap
- 6% simple interest accrues from investment date
- Principal + interest converts at qualified financing

### ConvertibleTerms Fields

- **investment_amount** (required): Amount invested in convertible
- **discount_rate** (optional): Discount rate (0-1, e.g., 0.20 = 20%)
- **price_cap** (optional): Valuation cap for conversion
- **interest_rate** (optional): Annual interest rate (0-1)
- **investment_start_date** (optional): When investment was made
- **interest_type** (optional): "simple" or "compound" (default: simple)
- **accrued_interest** (auto-generated): Calculated interest amount
- **conversion_shares** (auto-generated): Calculated shares upon conversion

### Complete Workflow

**Step 1: Create Security Classes**

```json
{
  "name": "SAFE",
  "type": "safe"
}
```

```json
{
  "name": "Convertible Note",
  "type": "convertible_note"
}
```

**Step 2: Create Convertible Instruments**

```json
{
  "holder_name": "Angel Investor",
  "class_name": "SAFE",
  "convertible_terms": {
    "investment_amount": 500000,
    "discount_rate": 0.20,
    "price_cap": 5000000
  }
}
```

**Step 3: Upon Qualified Financing**

When a qualified financing occurs, the SAFE converts:
- Uses the lower of: (Discounted Round PPS, Cap Price)
- Converts investment + accrued interest (if any) to shares
- New instrument created in the qualified round

## When to Use Each Method

### Use Fixed Share Issues When:
- ✅ You know exact share quantities
- ✅ Founder grants
- ✅ Stock option grants
- ✅ Advisory board grants

### Use Valuation-Based When:
- ✅ Equity financing rounds
- ✅ Strategic investments
- ✅ Investor shares based on company valuation
- ✅ Preferred share issuances with known valuations

### Use Convertibles When:
- ✅ Early-stage investments
- ✅ SAFE agreements
- ✅ Convertible notes
- ✅ Bridge financing
- ✅ Seed stage before priced rounds

## Excel Generation Behavior

All three methods integrate seamlessly with the Excel workbook:

1. **Fixed Shares**: Direct entry in Ledger, included in Cap Table Progression
2. **Valuation-Based**: Formulas in Ledger calculate shares, results shown in Cap Table Progression
3. **Convertibles**: Tracked separately, show in Ledger with conversion status

The Cap Table Progression sheet shows the final ownership across all three types, with complete formula traceability back to the source data.


