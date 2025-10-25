# Cap Table JSON Schema Reference

This document provides a quick reference for the cap table JSON schema structure.

## Quick Start

The cap table JSON structure consists of these main sections:

```json
{
  "schema_version": "1.0",
  "company": { ... },
  "holders": [ ... ],
  "classes": [ ... ],
  "terms": [ ... ],           // Optional
  "instruments": [ ... ],
  "rounds": [ ... ],          // Optional
  "waterfall_scenarios": [ ... ]  // Optional
}
```

---

## Required Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string | ✅ | Must be "1.0" |
| `company` | object | ✅ | Company information |
| `holders` | array | ✅ | List of shareholders |
| `classes` | array | ✅ | Security classes |
| `instruments` | array | ✅ | Individual holdings |
| `terms` | array | ⚠️ | Terms packages (needed for preferred) |
| `rounds` | array | ⚠️ | Financing rounds (if applicable) |
| `waterfall_scenarios` | array | ⚠️ | Exit scenarios (optional) |

---

## Entity Definitions

### 1. Company

**Required:**
- `name` (string): Company name

**Optional:**
- `incorporation_date` (string, date): YYYY-MM-DD
- `current_date` (string, date): YYYY-MM-DD
- `current_pps` (number): Current price per share

**Example:**
```json
{
  "name": "My Startup Inc.",
  "incorporation_date": "2023-01-15",
  "current_date": "2024-10-25",
  "current_pps": 5.0
}
```

---

### 2. Holder

**Required:**
- `holder_id` (UUID): Unique identifier
- `name` (string): Holder name
- `type` (enum): "founder", "employee", "investor", "advisor", "option_pool"

**Optional:**
- `email` (string): Contact email

**Types:**
- `founder`: Company founders
- `employee`: Employees with equity
- `investor`: Investors (VCs, angels, etc.)
- `advisor`: Advisory board members
- `option_pool`: Unallocated option pool

**Example:**
```json
{
  "holder_id": "eb71bf51-9903-4f63-806a-feafa08f49a0",
  "name": "Alice Johnson",
  "type": "founder",
  "email": "alice@example.com"
}
```

---

### 3. SecurityClass

**Required:**
- `class_id` (UUID): Unique identifier
- `name` (string): Security name (e.g., "Common Stock", "Series A Preferred")
- `type` (enum): "common", "preferred", "option", "warrant", "safe", "convertible_note"

**Optional:**
- `terms_id` (UUID): Reference to terms (for preferred shares)
- `conversion_ratio` (number, default: 1.0): Conversion ratio to common

**Example:**
```json
{
  "class_id": "b28c35e4-deab-430e-b1db-a711c3e6f8e5",
  "name": "Common Stock",
  "type": "common",
  "conversion_ratio": 1.0
}
```

```json
{
  "class_id": "2c6ef140-3db0-409b-b893-f715f0fed026",
  "name": "Series A Preferred",
  "type": "preferred",
  "terms_id": "35de1352-08dc-40bb-83c5-e4d7c2f120d7",
  "conversion_ratio": 1.0
}
```

---

### 4. TermsPackage

**Required:**
- `terms_id` (UUID): Unique identifier
- `name` (string): Terms package name

**Optional:**
- `liquidation_multiple` (number, default: 1.0): Liquidation preference (1.0, 2.0, etc.)
- `participation_type` (enum): "non_participating", "participating", "capped_participating"
- `participation_cap` (number): Cap for capped participating
- `seniority_rank` (integer): Payout order (lower = more senior)
- `dividend_rate` (number): Annual dividend rate
- `anti_dilution` (enum): "none", "weighted_average", "full_ratchet"

**Example:**
```json
{
  "terms_id": "35de1352-08dc-40bb-83c5-e4d7c2f120d7",
  "name": "Series A Preferred Terms",
  "liquidation_multiple": 1.0,
  "participation_type": "non_participating",
  "seniority_rank": 1,
  "anti_dilution": "weighted_average"
}
```

---

### 5. Instrument

**Required:**
- `instrument_id` (UUID): Unique identifier
- `holder_id` (UUID): Reference to holder
- `class_id` (UUID): Reference to security class
- `initial_quantity` (number): Number of shares/options

**Optional:**
- `round_id` (UUID): Reference to round
- `strike_price` (number): Exercise price for options
- `acquisition_price` (number): Price paid per share
- `acquisition_date` (string, date): Acquisition date
- `current_quantity` (number or FEO): Current shares
- `vesting_terms` (object): Vesting schedule
- `convertible_terms` (object): Conversion terms (for SAFEs, notes)

**Example (Common Stock):**
```json
{
  "instrument_id": "7abf580c-c054-4807-bd0d-570cbda38b3c",
  "holder_id": "eb71bf51-9903-4f63-806a-feafa08f49a0",
  "class_id": "b28c35e4-deab-430e-b1db-a711c3e6f8e5",
  "initial_quantity": 4000000,
  "acquisition_price": 0.001,
  "acquisition_date": "2023-01-15"
}
```

**Example (Options with Vesting):**
```json
{
  "instrument_id": "913321ed-69ce-41de-92ce-da9e56f7aa9a",
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

---

### 6. VestingTerms

**Required:**
- `grant_date` (string, date): Grant date
- `cliff_days` (integer): Cliff period in days
- `vesting_period_days` (integer): Total vesting period in days

**Optional:**
- `vested_quantity` (FEO): Calculated vested shares (auto-generated)

**Example:**
```json
{
  "grant_date": "2022-06-01",
  "cliff_days": 365,
  "vesting_period_days": 1460
}
```

---

### 7. Round

**Required:**
- `round_id` (UUID): Unique identifier
- `name` (string): Round name (e.g., "Seed Round", "Series A")
- `round_date` (string, date): Round closing date

**Optional:**
- `investment_amount` (number): Total investment
- `pre_money_valuation` (number or FEO): Pre-money valuation
- `post_money_valuation` (number or FEO): Post-money valuation
- `price_per_share` (number or FEO): Price per share
- `shares_issued` (number or FEO): Total shares issued
- `option_pool_increase` (object): Option pool details

**Example:**
```json
{
  "round_id": "53617af7-dc61-4174-802e-e2b4663412be",
  "name": "Seed Round",
  "round_date": "2023-06-01",
  "investment_amount": 2000000,
  "pre_money_valuation": 8000000,
  "post_money_valuation": 10000000,
  "price_per_share": 1.0,
  "shares_issued": 2000000
}
```

---

### 8. WaterfallScenario

**Required:**
- `scenario_id` (UUID): Unique identifier
- `name` (string): Scenario name
- `exit_value` (number): Exit valuation

**Optional:**
- `payouts` (array): Payout calculations (auto-generated)

**Example:**
```json
{
  "scenario_id": "56cd0979-7550-4ed2-81c6-c4aa59686ce4",
  "name": "Exit at $30M",
  "exit_value": 30000000
}
```

---

## Relationship Mapping

### UUID References

| Source Entity | Target Field | Target Entity | Purpose |
|--------------|-------------|---------------|---------|
| Instrument | `holder_id` | Holder | Links holding to person |
| Instrument | `class_id` | SecurityClass | Links holding to security type |
| Instrument | `round_id` | Round | Links holding to round |
| SecurityClass | `terms_id` | TermsPackage | Links security to terms |
| Round.Instrument | `round_id` | Round | Links instruments to rounds |

### Example Relationship:

```json
{
  "instruments": [
    {
      "instrument_id": "abc123...",
      "holder_id": "def456...",  // → references holders[].holder_id
      "class_id": "ghi789...",   // → references classes[].class_id
      "round_id": "jkl012...",   // → references rounds[].round_id
      "initial_quantity": 1000000
    }
  ]
}
```

---

## Enums Reference

### Holder Types
- `"founder"`
- `"employee"`
- `"investor"`
- `"advisor"`
- `"option_pool"`

### Security Types
- `"common"`
- `"preferred"`
- `"option"`
- `"warrant"`
- `"safe"`
- `"convertible_note"`

### Participation Types
- `"non_participating"`
- `"participating"`
- `"capped_participating"`

### Anti-Dilution Types
- `"none"`
- `"weighted_average"`
- `"full_ratchet"`

---

## Common Patterns

### Pattern 1: Simple Founder Equity

```json
{
  "holders": [
    {
      "holder_id": "...",
      "name": "Alice",
      "type": "founder"
    }
  ],
  "classes": [
    {
      "class_id": "...",
      "name": "Common Stock",
      "type": "common"
    }
  ],
  "instruments": [
    {
      "instrument_id": "...",
      "holder_id": "...", // Alice's UUID
      "class_id": "...",  // Common Stock UUID
      "initial_quantity": 5000000,
      "acquisition_price": 0.001,
      "acquisition_date": "2023-01-15"
    }
  ]
}
```

### Pattern 2: Seed Round with Preferred

```json
{
  "classes": [
    {"class_id": "A", "name": "Common Stock", "type": "common"},
    {"class_id": "B", "name": "Seed Preferred", "type": "preferred", "terms_id": "T1"}
  ],
  "terms": [
    {
      "terms_id": "T1",
      "name": "Seed Terms",
      "liquidation_multiple": 1.0,
      "participation_type": "non_participating",
      "seniority_rank": 1
    }
  ],
  "rounds": [
    {
      "round_id": "R1",
      "name": "Seed Round",
      "round_date": "2023-06-01",
      "investment_amount": 2000000
    }
  ],
  "instruments": [
    {
      "holder_id": "...",
      "class_id": "B",
      "round_id": "R1",
      "initial_quantity": 2000000
    }
  ]
}
```

### Pattern 3: Options with Vesting

```json
{
  "classes": [
    {"class_id": "O1", "name": "Stock Options", "type": "option"}
  ],
  "instruments": [
    {
      "holder_id": "...",
      "class_id": "O1",
      "initial_quantity": 100000,
      "strike_price": 0.5,
      "vesting_terms": {
        "grant_date": "2024-01-01",
        "cliff_days": 365,
        "vesting_period_days": 1460
      }
    }
  ]
}
```

---

## Validation Checklist

Before finalizing JSON, verify:

- [ ] All required fields present
- [ ] UUIDs in correct format
- [ ] Dates in YYYY-MM-DD format
- [ ] All `holder_id` references exist
- [ ] All `class_id` references exist
- [ ] All `round_id` references exist
- [ ] All `terms_id` references exist (if used)
- [ ] No negative numbers (except where allowed)
- [ ] Enums use valid values
- [ ] Vesting has grant_date, cliff_days, vesting_period_days
- [ ] Preferred shares have terms_id
- [ ] Instruments linked to valid holders and classes

---

## Full Schema

For complete schema definition, see: `cap_table_schema.json`

For working examples, see:
- `sample_simple_captable.json`
- `sample_complex_captable.json`

