# Cap Table Input JSON Generation Guide

This guide provides comprehensive instructions for generating valid JSON input for the Cap Table Generator. Use this guide to structure JSON that accurately represents a company's capitalization table.

---

## Table of Contents

1. [Overview](#overview)
2. [Required Structure](#required-structure)
3. [Entity Specifications](#entity-specifications)
4. [Data Relationships](#data-relationships)
5. [UUID Requirements](#uuid-requirements)
6. [Common Patterns](#common-patterns)
7. [Validation Rules](#validation-rules)
8. [Complete Examples](#complete-examples)

---

## Overview

The Cap Table JSON schema models a company's equity structure, including:
- Shareholders (founders, employees, investors, option pools)
- Security classes (common stock, preferred shares, options, etc.)
- Individual holdings (instruments)
- Financing rounds
- Terms and conditions (liquidation preferences, participation rights)
- Vesting schedules
- Exit scenarios (waterfall analysis)

The system generates Excel spreadsheets with dynamic formulas that automatically calculate ownership percentages, fully diluted shares, and exit scenario payouts.

---

## Required Structure

Every valid JSON file must include these top-level sections:

```json
{
  "schema_version": "1.0",     // REQUIRED - Must be exactly "1.0"
  "company": { ... },         // REQUIRED - Company information
  "holders": [ ... ],         // REQUIRED - List of shareholders
  "classes": [ ... ],         // REQUIRED - Security classes
  "instruments": [ ... ],     // REQUIRED - Individual holdings
  "terms": [ ... ],          // CONDITIONAL - Only needed for preferred shares
  "rounds": [ ... ],         // OPTIONAL - Financing round history
  "waterfall_scenarios": [ ... ] // OPTIONAL - Exit scenario modeling
}
```

---

## Entity Specifications

### 1. Company (Required)

**Purpose:** Defines the company and provides key metrics for calculations.

**Structure:**
```json
{
  "name": "string (REQUIRED)",
  "incorporation_date": "YYYY-MM-DD (OPTIONAL)",
  "current_date": "YYYY-MM-DD (OPTIONAL)",
  "current_pps": number (OPTIONAL)
}
```

**Field Details:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ YES | Legal company name |
| `incorporation_date` | date | ❌ NO | Date of company formation (format: YYYY-MM-DD) |
| `current_date` | date | ❌ NO | Evaluation date for vesting calculations (format: YYYY-MM-DD) |
| `current_pps` | number | ❌ NO | Current price per share for TSM dilution calculations |

**Example:**
```json
{
  "name": "TechVenture Corp",
  "incorporation_date": "2022-01-01",
  "current_date": "2024-10-25",
  "current_pps": 7.50
}
```

**Notes:**
- `current_pps` is critical for calculating net dilution using the Treasury Stock Method
- `current_date` determines how many options have vested for employees
- Dates must be in ISO 8601 format (YYYY-MM-DD)

---

### 2. Holders (Required)

**Purpose:** Lists all shareholders, including founders, employees, investors, advisors, and option pools.

**Structure:**
```json
[
  {
    "holder_id": "UUID (REQUIRED)",
    "name": "string (REQUIRED)",
    "type": "enum (REQUIRED)",
    "email": "string (OPTIONAL)"
  }
]
```

**Field Details:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `holder_id` | UUID | ✅ YES | Unique identifier (UUID v4 format) |
| `name` | string | ✅ YES | Full name or institution name |
| `type` | enum | ✅ YES | One of: `founder`, `employee`, `investor`, `advisor`, `option_pool` |
| `email` | string | ❌ NO | Contact email address |

**Holder Types:**

- **`founder`**: Company founders who typically hold common stock
- **`employee`**: Current or former employees with equity grants
- **`investor`**: VCs, angels, or other investment entities
- **`advisor`**: Advisory board members with equity
- **`option_pool`**: Unallocated option pool (special entity for tracking unissued options)

**Example:**
```json
[
  {
    "holder_id": "b5c77236-6c7f-4811-a3be-119c6af50d45",
    "name": "David Chen",
    "type": "founder",
    "email": "david@techventure.com"
  },
  {
    "holder_id": "4f73ed1c-49cf-4be7-b997-2d8cbdbeee8a",
    "name": "Frank Thomas",
    "type": "employee",
    "email": "frank@techventure.com"
  },
  {
    "holder_id": "91a2c80e-3210-46e0-bc32-d3b326fedec7",
    "name": "Seed Ventures LLC",
    "type": "investor"
  },
  {
    "holder_id": "2b2d1491-5539-4771-9ea8-056ea41d5c50",
    "name": "Unallocated Option Pool",
    "type": "option_pool"
  }
]
```

**Important:**
- Each holder must have a unique UUID
- Option pools should be added as special holders with type `option_pool`
- Email is typically only included for founders and employees

---

### 3. Classes (Required)

**Purpose:** Defines the different security types available (common stock, preferred stock, options, etc.).

**Structure:**
```json
[
  {
    "class_id": "UUID (REQUIRED)",
    "name": "string (REQUIRED)",
    "type": "enum (REQUIRED)",
    "terms_id": "UUID (CONDITIONAL)",
    "conversion_ratio": number (OPTIONAL)
  }
]
```

**Field Details:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `class_id` | UUID | ✅ YES | Unique identifier for this security class |
| `name` | string | ✅ YES | Security name (e.g., "Common Stock", "Series A Preferred") |
| `type` | enum | ✅ YES | Security type (see options below) |
| `terms_id` | UUID | ⚠️ REQUIRED for preferred | Reference to terms package (only for preferred shares) |
| `conversion_ratio` | number | ❌ NO | Default conversion ratio to common stock (default: 1.0) |

**Security Class Types:**

- **`common`**: Common stock (no special rights)
- **`preferred`**: Preferred stock (requires `terms_id`)
- **`option`**: Stock options (ESO)
- **`warrant`**: Stock warrants
- **`safe`**: Simple Agreement for Future Equity
- **`convertible_note`**: Convertible debt instrument

**Examples:**

```json
[
  {
    "class_id": "221af0ec-6f6b-4535-8ace-9ee1c7945563",
    "name": "Common Stock",
    "type": "common",
    "conversion_ratio": 1.0
  },
  {
    "class_id": "1c3b53cc-975e-4b93-b9ca-40477cb2907a",
    "name": "Stock Options",
    "type": "option",
    "conversion_ratio": 1.0
  },
  {
    "class_id": "2140f8bb-239f-45ef-a882-8e3e1fec7863",
    "name": "Series A Preferred",
    "type": "preferred",
    "terms_id": "00fc791c-3a3d-4af4-9ae9-453733ce83e2",
    "conversion_ratio": 1.0
  }
]
```

**Important:**
- Every company should have at least one `common` stock class
- Preferred shares MUST reference a `terms_id` from the `terms` array
- Options are typically granted to employees with vesting schedules
- Each class needs a unique UUID

---

### 4. Terms (Conditional)

**Purpose:** Defines the legal and financial terms for preferred share classes (liquidation preferences, participation rights, anti-dilution protection).

**Structure:**
```json
[
  {
    "terms_id": "UUID (REQUIRED)",
    "name": "string (REQUIRED)",
    "liquidation_multiple": number (OPTIONAL),
    "participation_type": "enum (OPTIONAL)",
    "participation_cap": number (OPTIONAL),
    "seniority_rank": integer (OPTIONAL),
    "dividend_rate": number (OPTIONAL),
    "anti_dilution": "enum (OPTIONAL)"
  }
]
```

**Field Details:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `terms_id` | UUID | ✅ YES | Unique identifier for terms package |
| `name` | string | ✅ YES | Descriptive name (e.g., "Series A Preferred Terms") |
| `liquidation_multiple` | number | ❌ NO | Liquidation preference multiple (default: 1.0) |
| `participation_type` | enum | ❌ NO | Participation rights (default: "non_participating") |
| `participation_cap` | number | ❌ NO | Cap multiple for capped participating (e.g., 2.0 for 2x) |
| `seniority_rank` | integer | ❌ NO | Payout order in waterfall (lower = more senior) |
| `dividend_rate` | number | ❌ NO | Annual dividend rate as decimal (e.g., 0.08 for 8%) |
| `anti_dilution` | enum | ❌ NO | Anti-dilution protection type |

**Participation Types:**

- **`non_participating`**: Investor gets liquidation preference OR converts to common (whichever is higher)
- **`participating`**: Investor gets liquidation preference PLUS pro-rata share of remaining proceeds
- **`capped_participating`**: Investor participates up to a cap multiple, then converts to non-participating

**Anti-Dilution Types:**

- **`none`**: No anti-dilution protection
- **`weighted_average`**: Weighted average anti-dilution (most common)
- **`full_ratchet`**: Full ratchet anti-dilution (most investor-friendly)

**Example:**
```json
[
  {
    "terms_id": "00fc791c-3a3d-4af4-9ae9-453733ce83e2",
    "name": "Series A Preferred Terms",
    "liquidation_multiple": 1.0,
    "participation_type": "participating",
    "seniority_rank": 2,
    "anti_dilution": "weighted_average"
  },
  {
    "terms_id": "e413afee-897d-4bcd-b23c-c9062ba55c44",
    "name": "Series B Preferred Terms",
    "liquidation_multiple": 1.5,
    "participation_type": "participating",
    "seniority_rank": 1,
    "anti_dilution": "weighted_average"
  }
]
```

**Critical Notes:**
- Only required when you have preferred stock classes
- `liquidation_multiple` of 1.0 = 1x preference (investor gets 1x their investment back first)
- `liquidation_multiple` of 2.0 = 2x preference (investor gets 2x their investment back first)
- `seniority_rank` determines payment order in exit scenarios (lower number = paid first)
- Higher seniority ranks are actually LESS senior (higher number = paid later)

**Waterfall Priority Order:**
- Rank 1 = MOST senior (paid first)
- Rank 2 = Next senior (paid second)
- Rank 3 = Paid third
- etc.

---

### 5. Instruments (Required)

**Purpose:** Represents individual holdings of securities by shareholders.

**Structure:**
```json
[
  {
    "instrument_id": "UUID (REQUIRED)",
    "holder_id": "UUID (REQUIRED)",
    "class_id": "UUID (REQUIRED)",
    "initial_quantity": number (REQUIRED),
    "round_id": "UUID (OPTIONAL)",
    "current_quantity": "number or FEO (OPTIONAL)",
    "strike_price": number (OPTIONAL),
    "acquisition_price": number (OPTIONAL),
    "acquisition_date": "date (OPTIONAL)",
    "vesting_terms": { ... } (OPTIONAL),
    "convertible_terms": { ... } (OPTIONAL)
  }
]
```

**Field Details:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `instrument_id` | UUID | ✅ YES | Unique identifier for this holding |
| `holder_id` | UUID | ✅ YES | Reference to holder in `holders` array |
| `class_id` | UUID | ✅ YES | Reference to security class in `classes` array |
| `initial_quantity` | number | ✅ YES | Number of shares/options initially granted |
| `round_id` | UUID | ❌ NO | Reference to financing round (for newly issued shares) |
| `current_quantity` | number or FEO | ❌ NO | Current shares (may be calculated for vesting) |
| `strike_price` | number | ❌ NO | Exercise price for options/warrants |
| `acquisition_price` | number | ❌ NO | Original issue price (price paid per share) |
| `acquisition_date` | date | ❌ NO | Date shares were acquired/granted (format: YYYY-MM-DD) |
| `vesting_terms` | object | ❌ NO | Vesting schedule (for options/grants) |
| `convertible_terms` | object | ❌ NO | Conversion terms (for SAFEs, convertible notes) |

**Examples:**

### Common Stock Holding:
```json
{
  "instrument_id": "3a1ee839-e71f-4cc2-a74c-65b330dc9586",
  "holder_id": "b5c77236-6c7f-4811-a3be-119c6af50d45",
  "class_id": "221af0ec-6f6b-4535-8ace-9ee1c7945563",
  "initial_quantity": 5000000,
  "acquisition_price": 0.001,
  "acquisition_date": "2022-01-01"
}
```

### Options with Vesting:
```json
{
  "instrument_id": "60601400-b350-43eb-935b-74b9d8252933",
  "holder_id": "4f73ed1c-49cf-4be7-b997-2d8cbdbeee8a",
  "class_id": "1c3b53cc-975e-4b93-b9ca-40477cb2907a",
  "initial_quantity": 400000,
  "strike_price": 0.5,
  "acquisition_date": "2022-06-01",
  "vesting_terms": {
    "grant_date": "2022-06-01",
    "cliff_days": 365,
    "vesting_period_days": 1460
  }
}
```

### Preferred Shares from Round:
```json
{
  "instrument_id": "098d9685-df3d-4826-a177-61546aa50163",
  "holder_id": "91a2c80e-3210-46e0-bc32-d3b326fedec7",
  "class_id": "2140f8bb-239f-45ef-a882-8e3e1fec7863",
  "round_id": "e99459e8-1027-4c73-8966-5fc11ed5f350",
  "initial_quantity": 3000000,
  "acquisition_price": 1.0,
  "acquisition_date": "2022-12-01"
}
```

**Important:**
- `holder_id` must reference an existing UUID in the `holders` array
- `class_id` must reference an existing UUID in the `classes` array
- `round_id` (if provided) must reference an existing UUID in the `rounds` array
- `strike_price` is required for options and warrants
- `vesting_terms` is typically used for employee stock options
- `convertible_terms` is used for SAFE and convertible note instruments

---

### 6. Vesting Terms (Optional)

**Purpose:** Defines the vesting schedule for options and stock grants.

**Structure:**
```json
{
  "grant_date": "YYYY-MM-DD (REQUIRED)",
  "cliff_days": integer (REQUIRED)",
  "vesting_period_days": integer (REQUIRED)"
}
```

**Field Details:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `grant_date` | date | ✅ YES | Date options were granted (format: YYYY-MM-DD) |
| `cliff_days` | integer | ✅ YES | Cliff period in days (e.g., 365 for 1 year cliff) |
| `vesting_period_days` | integer | ✅ YES | Total vesting period in days (e.g., 1460 for 4 years) |

**Common Vesting Schedules:**

| Schedule | Cliff Days | Vesting Period | Description |
|----------|-----------|---------------|-------------|
| 1 year cliff, 4 year vest | 365 | 1460 | Standard employee options |
| No cliff, 4 year vest | 0 | 1460 | Immediate vesting |
| 6 month cliff, 2 year vest | 182 | 730 | Accelerated vesting |
| 2 year cliff, 4 year vest | 730 | 1460 | Extended cliff |

**Example:**
```json
{
  "grant_date": "2022-06-01",
  "cliff_days": 365,
  "vesting_period_days": 1460
}
```
This means:
- 1 year cliff (no vesting until June 1, 2023)
- 4 year vesting period (fully vested on June 1, 2026)
- Linear vesting after cliff (25% after cliff, 50% after 2 years, etc.)

---

### 7. Convertible Terms (Optional)

**Purpose:** Defines conversion terms for SAFEs and convertible notes.

**Structure:**
```json
{
  "investment_amount": number,
  "discount_rate": number,
  "price_cap": number
}
```

**Field Details:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `investment_amount` | number | ✅ YES | Amount invested in convertible security |
| `discount_rate` | number | ❌ NO | Discount on conversion price (0.00 to 1.00, e.g., 0.20 for 20%) |
| `price_cap` | number | ❌ NO | Valuation cap for conversion |

**Example:**
```json
{
  "investment_amount": 100000,
  "discount_rate": 0.20,
  "price_cap": 5000000
}
```

---

### 8. Rounds (Optional)

**Purpose:** Tracks financing rounds and their valuations.

**Structure:**
```json
[
  {
    "round_id": "UUID (REQUIRED)",
    "name": "string (REQUIRED)",
    "round_date": "YYYY-MM-DD (REQUIRED)",
    "investment_amount": number (OPTIONAL),
    "pre_money_valuation": number or FEO (OPTIONAL),
    "post_money_valuation": number or FEO (OPTIONAL),
    "price_per_share": number or FEO (OPTIONAL),
    "shares_issued": number or FEO (OPTIONAL),
    "option_pool_increase": { ... } (OPTIONAL)
  }
]
```

**Field Details:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `round_id` | UUID | ✅ YES | Unique identifier for the round |
| `name` | string | ✅ YES | Round name (e.g., "Seed Round", "Series A") |
| `round_date` | date | ✅ YES | Round closing date (format: YYYY-MM-DD) |
| `investment_amount` | number | ❌ NO | Total investment amount |
| `pre_money_valuation` | number or FEO | ❌ NO | Valuation before investment |
| `post_money_valuation` | number or FEO | ❌ NO | Valuation after investment |
| `price_per_share` | number or FEO | ❌ NO | Price per share for this round |
| `shares_issued` | number or FEO | ❌ NO | Total shares issued in this round |
| `option_pool_increase` | object | ❌ NO | Option pool expansion details |

**Example:**
```json
[
  {
    "round_id": "e99459e8-1027-4c73-8966-5fc11ed5f350",
    "name": "Seed Round",
    "round_date": "2022-12-01",
    "investment_amount": 3000000,
    "pre_money_valuation": 12000000,
    "post_money_valuation": 15000000,
    "price_per_share": 1.0,
    "shares_issued": 3000000
  },
  {
    "round_id": "157bae6a-8482-48e4-857e-05d7e01827d6",
    "name": "Series A",
    "round_date": "2023-09-01",
    "investment_amount": 10000000,
    "pre_money_valuation": 40000000,
    "post_money_valuation": 50000000,
    "price_per_share": 2.5,
    "shares_issued": 4000000
  }
]
```

**Important:**
- Rounds are optional but recommended for tracking financing history
- Instruments issued in a round should reference the `round_id`
- Valuations and PPS are used for calculations but are not required
- Post-money = Pre-money + Investment Amount
- Price per share = Post-money / Total Fully Diluted Shares

---

### 9. Waterfall Scenarios (Optional)

**Purpose:** Models exit scenarios and calculates payouts to each security class.

**Structure:**
```json
[
  {
    "scenario_id": "UUID (REQUIRED)",
    "name": "string (REQUIRED)",
    "exit_value": number (REQUIRED),
    "payouts": [...] (OPTIONAL - auto-generated)
  }
]
```

**Field Details:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `scenario_id` | UUID | ✅ YES | Unique identifier for the scenario |
| `name` | string | ✅ YES | Scenario name (e.g., "Exit at $200M") |
| `exit_value` | number | ✅ YES | Exit valuation for this scenario |
| `payouts` | array | ❌ NO | Payout calculations (auto-generated by system) |

**Example:**
```json
[
  {
    "scenario_id": "fdcf9901-2b51-4a1b-9abf-43bb5827a520",
    "name": "Exit at $200M",
    "exit_value": 200000000
  },
  {
    "scenario_id": "a2b3c4d5-6e7f-8901-2345-6789abcdef01",
    "name": "Downside: Exit at $50M",
    "exit_value": 50000000
  },
  {
    "scenario_id": "z9y8x7w6-5v4u-3t2s-1r0q-p9o8n7m6l5k4",
    "name": "Upside: Exit at $500M",
    "exit_value": 500000000
  }
]
```

**Important:**
- Used for modeling different exit valuations
- System automatically calculates payouts to each security class
- Payouts respect liquidation preferences and seniority ranks
- Common use: "walk through" different exit values to understand investor vs. founder economics

---

## Data Relationships

Understanding how entities reference each other is critical:

### Foreign Key Relationships

| Source Entity | Target Field | Target Entity | Purpose |
|---------------|--------------|---------------|---------|
| Instrument | `holder_id` | Holder | Links holding to shareholder |
| Instrument | `class_id` | SecurityClass | Links holding to security type |
| Instrument | `round_id` | Round | Links holding to financing round |
| SecurityClass | `terms_id` | TermsPackage | Links preferred shares to terms |
| Round | instruments | Instrument | Links round to instruments issued |

### Example Chain:

```
Holder (holder_id) 
  → Instrument (holder_id references Holder.holder_id)
    → SecurityClass (class_id references SecurityClass.class_id)
      → TermsPackage (terms_id references TermsPackage.terms_id)
        → WaterfallScenario (calculates payouts using Terms.seniority_rank)
```

---

## UUID Requirements

All ID fields must be valid UUID v4 format.

**Format:** `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`
- `x` = any hexadecimal digit (0-9, a-f)
- `4` = literal "4" indicating version 4
- `y` = one of: 8, 9, a, or b

**Example:**
```json
{
  "holder_id": "b5c77236-6c7f-4811-a3be-119c6af50d45",
  "class_id": "221af0ec-6f6b-4535-8ace-9ee1c7945563",
  "instrument_id": "3a1ee839-e71f-4cc2-a74c-65b330dc9586"
}
```

**Validation:**
- Must be lowercase
- Must include hyphens
- Must have exactly 36 characters
- Must start with a digit after hyphen
- 13th character must be '4'
- 17th character must be one of: 8, 9, a, b

---

## Common Patterns

### Pattern 1: Simple Founder Equity

**Scenario:** Company with three founders, equal split of common stock.

```json
{
  "schema_version": "1.0",
  "company": {
    "name": "My Startup Inc.",
    "incorporation_date": "2023-01-15",
    "current_date": "2024-10-25",
    "current_pps": 1.0
  },
  "holders": [
    {
      "holder_id": "f1f1f1f1-f1f1-4f1f-8f1f-f1f1f1f1f1f1",
      "name": "Founder 1",
      "type": "founder",
      "email": "founder1@startup.com"
    },
    {
      "holder_id": "f2f2f2f2-f2f2-4f2f-8f2f-f2f2f2f2f2f2",
      "name": "Founder 2",
      "type": "founder",
      "email": "founder2@startup.com"
    },
    {
      "holder_id": "f3f3f3f3-f3f3-4f3f-8f3f-f3f3f3f3f3f3",
      "name": "Founder 3",
      "type": "founder",
      "email": "founder3@startup.com"
    }
  ],
  "classes": [
    {
      "class_id": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
      "name": "Common Stock",
      "type": "common",
      "conversion_ratio": 1.0
    }
  ],
  "instruments": [
    {
      "instrument_id": "i1111111-1111-4111-8111-111111111111",
      "holder_id": "f1f1f1f1-f1f1-4f1f-8f1f-f1f1f1f1f1f1",
      "class_id": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
      "initial_quantity": 3333333,
      "acquisition_price": 0.001,
      "acquisition_date": "2023-01-15"
    },
    {
      "instrument_id": "i2222222-2222-4222-8222-222222222222",
      "holder_id": "f2f2f2f2-f2f2-4f2f-8f2f-f2f2f2f2f2f2",
      "class_id": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
      "initial_quantity": 3333333,
      "acquisition_price": 0.001,
      "acquisition_date": "2023-01-15"
    },
    {
      "instrument_id": "i3333333-3333-4333-8333-333333333333",
      "holder_id": "f3f3f3f3-f3f3-4f3f-8f3f-f3f3f3f3f3f3",
      "class_id": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
      "initial_quantity": 3333334,
      "acquisition_price": 0.001,
      "acquisition_date": "2023-01-15"
    }
  ],
  "terms": [],
  "rounds": []
}
```

### Pattern 2: Seed Round with Preferred Stock

**Scenario:** Seed round with $2M investment, 20% sold, 80% pre-money valuation.

**Key Data:**
- Pre-money valuation: $8M (founders own 80%)
- Post-money valuation: $10M (founders own 80%, investors own 20%)
- Investment: $2M for 20% equity
- Price per share: Calculated
- Shares issued: 2M preferred shares

```json
{
  "holders": [
    {
      "holder_id": "founder-uuid-1",
      "name": "Founder A",
      "type": "founder"
    },
    {
      "holder_id": "investor-uuid-1",
      "name": "Seed Ventures LLC",
      "type": "investor"
    }
  ],
  "classes": [
    {
      "class_id": "common-uuid",
      "name": "Common Stock",
      "type": "common",
      "conversion_ratio": 1.0
    },
    {
      "class_id": "preferred-uuid",
      "name": "Seed Preferred",
      "type": "preferred",
      "terms_id": "terms-uuid",
      "conversion_ratio": 1.0
    }
  ],
  "terms": [
    {
      "terms_id": "terms-uuid",
      "name": "Seed Preferred Terms",
      "liquidation_multiple": 1.0,
      "participation_type": "non_participating",
      "seniority_rank": 1,
      "anti_dilution": "weighted_average"
    }
  ],
  "rounds": [
    {
      "round_id": "round-uuid",
      "name": "Seed Round",
      "round_date": "2023-06-01",
      "investment_amount": 2000000,
      "pre_money_valuation": 8000000,
      "post_money_valuation": 10000000,
      "price_per_share": 1.0,
      "shares_issued": 2000000
    }
  ],
  "instruments": [
    {
      "instrument_id": "inst-common-1",
      "holder_id": "founder-uuid-1",
      "class_id": "common-uuid",
      "initial_quantity": 8000000,
      "acquisition_price": 0.001,
      "acquisition_date": "2023-01-15"
    },
    {
      "instrument_id": "inst-preferred-1",
      "holder_id": "investor-uuid-1",
      "class_id": "preferred-uuid",
      "round_id": "round-uuid",
      "initial_quantity": 2000000,
      "acquisition_price": 1.0,
      "acquisition_date": "2023-06-01"
    }
  ]
}
```

### Pattern 3: Employee Options with 4-Year Vesting

**Scenario:** Employee granted 400k options with 1-year cliff, 4-year vesting, $0.50 strike.

```json
{
  "classes": [
    {
      "class_id": "option-class-uuid",
      "name": "Stock Options",
      "type": "option",
      "conversion_ratio": 1.0
    }
  ],
  "instruments": [
    {
      "instrument_id": "inst-option-1",
      "holder_id": "employee-holder-uuid",
      "class_id": "option-class-uuid",
      "initial_quantity": 400000,
      "strike_price": 0.5,
      "acquisition_date": "2022-06-01",
      "vesting_terms": {
        "grant_date": "2022-06-01",
        "cliff_days": 365,
        "vesting_period_days": 1460
      }
    }
  ]
}
```

### Pattern 4: Multiple Rounds with Participating Preferred

**Scenario:** Seed round with non-participating preferred, Series A with participating preferred, Series B with participating preferred and 1.5x liquidation preference.

```json
{
  "terms": [
    {
      "terms_id": "seed-terms-uuid",
      "name": "Seed Preferred Terms",
      "liquidation_multiple": 1.0,
      "participation_type": "non_participating",
      "seniority_rank": 3,
      "anti_dilution": "weighted_average"
    },
    {
      "terms_id": "series-a-terms-uuid",
      "name": "Series A Preferred Terms",
      "liquidation_multiple": 1.0,
      "participation_type": "participating",
      "seniority_rank": 2,
      "anti_dilution": "weighted_average"
    },
    {
      "terms_id": "series-b-terms-uuid",
      "name": "Series B Preferred Terms",
      "liquidation_multiple": 1.5,
      "participation_type": "participating",
      "seniority_rank": 1,
      "anti_dilution": "weighted_average"
    }
  ]
}
```

**Waterfall Priority:**
1. Series B (most senior, rank 1) - gets 1.5x liquidation preference AND participation
2. Series A (rank 2) - gets 1.0x liquidation preference AND participation
3. Seed (rank 3) - gets 1.0x liquidation preference OR conversion
4. Common stock - gets residual after all preferred paid

---

## Validation Rules

Before finalizing your JSON, verify these requirements:

### 1. Required Fields

- ✅ `schema_version` = "1.0"
- ✅ `company.name`
- ✅ At least one holder in `holders` array
- ✅ At least one class in `classes` array
- ✅ At least one instrument in `instruments` array

### 2. UUID Format

- ✅ All IDs follow UUID v4 format
- ✅ All IDs are unique within their entity type
- ✅ All IDs use lowercase letters and hyphens

### 3. Reference Integrity

- ✅ All `holder_id` references in instruments exist in `holders`
- ✅ All `class_id` references in instruments exist in `classes`
- ✅ All `round_id` references in instruments exist in `rounds` (if provided)
- ✅ All `terms_id` references in classes exist in `terms` (if provided)

### 4. Preferred Stock Requirements

- ✅ All preferred stock classes have a `terms_id`
- ✅ No orphaned terms (all terms are referenced by at least one class)

### 5. Vesting Requirements

- ✅ All vesting schedules have `grant_date`, `cliff_days`, and `vesting_period_days`
- ✅ `cliff_days` ≥ 0
- ✅ `vesting_period_days` ≥ 1
- ✅ `cliff_days` ≤ `vesting_period_days`

### 6. Dates

- ✅ All dates use YYYY-MM-DD format
- ✅ No invalid dates (e.g., 2024-13-45)
- ✅ Grant dates are not in the future (or at least reasonable)

### 7. Numbers

- ✅ No negative quantities
- ✅ No negative prices (except in special cases)
- ✅ No negative valuations
- ✅ `initial_quantity` > 0

### 8. Enums

- ✅ Holder types are valid: `founder`, `employee`, `investor`, `advisor`, `option_pool`
- ✅ Security class types are valid: `common`, `preferred`, `option`, `warrant`, `safe`, `convertible_note`
- ✅ Participation types are valid: `non_participating`, `participating`, `capped_participating`
- ✅ Anti-dilution types are valid: `none`, `weighted_average`, `full_ratchet`

---

## Complete Examples

For working examples, see:
- `examples/sample_simple_captable.json` - Simple founder equity structure
- `examples/sample_complex_captable.json` - Complex multi-round structure with vesting
- `demo_simple.json` - Minimal viable cap table
- `demo_complex.json` - Full-featured cap table with options, vesting, and waterfall

---

## Quick Checklist

Before submitting your JSON, ensure:

- [ ] `schema_version` is "1.0"
- [ ] All UUIDs are valid v4 format (lowercase, hyphenated)
- [ ] All dates are YYYY-MM-DD format
- [ ] All required fields are present
- [ ] All references point to existing UUIDs
- [ ] Preferred shares have `terms_id`
- [ ] Vesting has all three required fields
- [ ] No negative numbers
- [ ] All enums use valid values
- [ ] Company name is descriptive
- [ ] Holder names are complete
- [ ] Security class names are descriptive
- [ ] At least one common stock class exists

---

## Tips for LLM Generation

When generating JSON for this system:

1. **Generate valid UUIDs** - Use lowercase, hyphenated v4 format
2. **Keep references consistent** - If you use a UUID in `holders`, reference it in instruments
3. **Follow naming conventions** - Security classes should be descriptive ("Series A Preferred" not "ClassA")
4. **Include optional metadata** - Adding `email`, `acquisition_date`, etc. makes output more useful
5. **Verify relationships** - Every `holder_id`, `class_id`, `round_id`, `terms_id` must exist
6. **Test edge cases** - Consider vesting cliffs, different participation types, multiple rounds
7. **Use realistic numbers** - Share quantities should be reasonable (typically 100k-10M range)
8. **Model real scenarios** - Think about actual startup financing patterns

---

## Common Mistakes to Avoid

❌ **Wrong UUID format:**
```json
❌ "holder_id": "12345"
✅ "holder_id": "b5c77236-6c7f-4811-a3be-119c6af50d45"
```

❌ **Missing terms_id for preferred:**
```json
❌ {
  "class_id": "...",
  "name": "Series A Preferred",
  "type": "preferred"
}
✅ {
  "class_id": "...",
  "name": "Series A Preferred",
  "type": "preferred",
  "terms_id": "..."
}
```

❌ **Orphaned references:**
```json
❌ "holder_id": "nonexistent-uuid-12345"
✅ Use UUID that exists in holders array
```

❌ **Invalid dates:**
```json
❌ "acquisition_date": "01/15/2023"
✅ "acquisition_date": "2023-01-15"
```

❌ **Negative numbers:**
```json
❌ "initial_quantity": -1000
✅ "initial_quantity": 1000000
```

---

## Next Steps

After generating valid JSON:

1. **Validate:** Run through the system's validation checks
2. **Generate Excel:** Use the generator to create the Excel output
3. **Verify:** Check that all formulas calculate correctly
4. **Test Scenarios:** Try different exit values and current PPS values

For more information, see:
- `README.md` - System overview
- `docs/SCHEMA_REFERENCE.md` - Schema details
- `QUICKSTART.md` - Getting started guide
- `docs/Knowledge Base.md` - Advanced technical details

