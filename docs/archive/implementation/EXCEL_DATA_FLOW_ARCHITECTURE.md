# Excel Data Flow Architecture
## Single Source of Truth Design

This document visualizes how data should flow through the Excel workbook using formulas and master tables.

---

## Current Architecture (Problematic)

```
┌─────────────┐
│   Python    │
│   Code      │
└─────┬───────┘
      │
      │ (Hardcodes values into multiple sheets)
      │
      ├──────────────┬──────────────┬──────────────┬──────────────┐
      │              │              │              │              │
      ▼              ▼              ▼              ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  Ledger  │   │  Rounds  │   │  Vesting │   │ Waterfall│   │   Cap    │
│  Sheet   │   │  Sheet   │   │  Sheet   │   │  Sheet   │   │  Table   │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘

❌ Issues:
- Duplicated data across sheets
- No single source of truth
- Changes in one place don't propagate
- Difficult to audit data lineage
```

---

## Recommended Architecture (Formula-Linked)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MASTER DATA SHEETS                            │
│                     (Single Source of Truth)                         │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐        ┌───────────────┐      ┌───────────────┐
│    Holders    │        │    Classes    │      │     Terms     │
│               │        │               │      │               │
│ • name        │        │ • name        │      │ • name        │
│ • type        │        │ • type        │      │ • class_name  │
│ • email       │        │ • par_value   │      │ • lp_multiple │
│ • address     │        │ • authorized  │      │ • participation│
└───────┬───────┘        └───────┬───────┘      │ • seniority   │
        │                        │              └───────┬───────┘
        │                        │                      │
        └────────────────┬───────┴──────────────────────┘
                         │
                         │ (XLOOKUP, SUMIF, etc.)
                         │
        ┌────────────────┼────────────────────────┐
        │                │                        │
        ▼                ▼                        ▼
┌───────────────┐  ┌───────────────┐    ┌───────────────┐
│    Summary    │  │    Ledger     │    │    Rounds     │
│               │  │               │    │               │
│ • Current_PPS │◄─┤ • holder_name │    │ • round_name  │
│ • Exit_Val    │  │ • class_name  │    │ • investment  │
│ • Total_FDS   │  │ • quantity    │◄───┤ • pre_round   │
└───────┬───────┘  └───────┬───────┘    │ • post_round  │
        │                  │            └───────┬───────┘
        │                  │                    │
        │                  └────────────┬───────┘
        │                               │
        │     (Formulas reference       │
        │      Summary + Ledger)        │
        │                               │
        ├───────────────┬───────────────┼───────────────┐
        │               │               │               │
        ▼               ▼               ▼               ▼
┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐
│  Vesting  │   │ Waterfall │   │  Cap Table│   │  Charts/  │
│           │   │           │   │ Progression│   │  Pivot    │
│ (Formulas)│   │ (Formulas)│   │ (Formulas) │   │  Tables   │
└───────────┘   └───────────┘   └───────────┘   └───────────┘

✅ Benefits:
- Single source of truth for each data type
- Changes propagate automatically
- Clear data lineage
- Audit-friendly
- User can modify master data without breaking formulas
```

---

## Detailed Data Flow

### 1. Master Sheets → Ledger

```
┌──────────────────┐
│  Holders Sheet   │
├──────────────────┤
│ Alice  │ founder │
│ Bob    │ investor│
└────┬─────────────┘
     │
     │ XLOOKUP
     ▼
┌──────────────────────────┐
│      Ledger Sheet        │
├──────────────────────────┤
│ holder_name │ holder_type│ ◄── Formula: =XLOOKUP([@holder_name], 
│ Alice       │ =XLOOKUP() │              Holders[name], Holders[type])
│ Bob         │ =XLOOKUP() │
└──────────────────────────┘
```

### 2. Ledger → Rounds (Validation)

```
┌──────────────────┐
│  Ledger Sheet    │
├──────────────────┤
│ round_name │ qty │
│ Series A   │ 100 │
│ Series A   │ 200 │
│ Series B   │ 150 │
└────┬─────────────┘
     │
     │ SUMIF
     ▼
┌──────────────────┐
│  Rounds Sheet    │
├──────────────────┤
│ round │ shares   │ ◄── Formula: =SUMIF(Ledger[round_name],
│ A     │ =SUMIF() │              [@round_name], Ledger[qty])
│ B     │ =SUMIF() │
└──────────────────┘
```

### 3. Summary → All Sheets (Named Ranges)

```
┌──────────────────┐
│  Summary Sheet   │
├──────────────────┤
│ Current_PPS: $2  │ ◄── Named Range: Current_PPS
│ Total_FDS: 10000 │ ◄── Named Range: Total_FDS
│ Exit_Val: $10M   │ ◄── Named Range: Exit_Val
└────┬─────────────┘
     │
     │ (All sheets reference these names)
     │
     ├──────────────┬───────────────┬───────────────┐
     │              │               │               │
     ▼              ▼               ▼               ▼
   Ledger      Vesting         Waterfall       Cap Table
 (ownership%)  (valuations)    (payouts)      (percentages)
```

### 4. Terms → Waterfall

```
┌────────────────────────────┐
│      Terms Sheet           │
├────────────────────────────┤
│ class │ lp_mult │ particip │
│ Ser A │ 1.0     │ non_part │
│ Ser B │ 1.5     │ particip │
└────┬───────────────────────┘
     │
     │ XLOOKUP
     ▼
┌────────────────────────────┐
│    Waterfall Sheet         │
├────────────────────────────┤
│ class │ lp_mult │ payout   │
│ Ser A │ =XLOOKUP│ =formula │ ◄── Uses lp_mult in calculation
│ Ser B │ =XLOOKUP│ =formula │
└────────────────────────────┘
```

---

## Master Sheets Design

### Holders Sheet
```
┌────────────┬─────────────┬───────────────────┬─────────────────┐
│ holder_name│ holder_type │ email             │ address         │
├────────────┼─────────────┼───────────────────┼─────────────────┤
│ Alice      │ founder     │ alice@company.com │ 123 Main St     │
│ Bob        │ investor    │ bob@vc.com        │ 456 VC Ave      │
│ Carol      │ employee    │ carol@company.com │ 789 Work Ln     │
│ OptionPool │ option_pool │ -                 │ -               │
└────────────┴─────────────┴───────────────────┴─────────────────┘

Primary Key: holder_name
Used By: Ledger, Vesting, Cap Table Progression
```

### Classes Sheet
```
┌────────────┬────────────┬───────────┬────────────────┬──────────────┐
│ class_name │ class_type │ par_value │ authorized_qty │ description  │
├────────────┼────────────┼───────────┼────────────────┼──────────────┤
│ Common     │ common     │ 0.0001    │ 10,000,000     │ Common Stock │
│ Series A   │ preferred  │ 0.0001    │ 2,000,000      │ Series A Pfd │
│ Series B   │ preferred  │ 0.0001    │ 1,500,000      │ Series B Pfd │
│ ISO Options│ option     │ -         │ -              │ Stock Options│
└────────────┴────────────┴───────────┴────────────────┴──────────────┘

Primary Key: class_name
Used By: Ledger, Waterfall
```

### Terms Sheet
```
┌───────────┬────────────┬───────────┬───────────────┬────────────┬──────────┐
│ terms_name│ class_name │ lp_multiple│ participation │ seniority  │ anti_dil │
├───────────┼────────────┼───────────┼───────────────┼────────────┼──────────┤
│ Series_A  │ Series A   │ 1.0       │ non_part      │ 2          │ broad    │
│ Series_B  │ Series B   │ 1.5       │ participating │ 1          │ full     │
└───────────┴────────────┴───────────┴───────────────┴────────────┴──────────┘

Primary Key: terms_name
Foreign Key: class_name → Classes Sheet
Used By: Waterfall, future conversion sheets
```

### Rounds Sheet (Enhanced)
```
┌────────────┬────────────┬────────────┬─────────────┬─────────────┬────────┐
│ round_name │ date       │ pre_round  │ investment  │ pre_money   │ pps    │
├────────────┼────────────┼────────────┼─────────────┼─────────────┼────────┤
│ Seed       │ 2020-01-01 │ =SUMIF()   │ 1,000,000   │ 4,000,000   │ =D2/C2 │
│ Series A   │ 2021-06-01 │ =C2+F2     │ 5,000,000   │ 15,000,000  │ =D3/C3 │
│ Series B   │ 2023-03-01 │ =C3+F3     │ 10,000,000  │ 40,000,000  │ =D4/C4 │
└────────────┴────────────┴────────────┴─────────────┴─────────────┴────────┘

Key Formulas:
- pre_round (C2): =SUMIF(Ledger[round_name], "", Ledger[initial_quantity])
- pre_round (C3+): =C2 + F2  (previous pre_round + previous shares_issued)
- pps: =D2/C2 (if not provided)
- shares_issued: =SUMIF(Ledger[round_name], [@round_name], Ledger[initial_quantity])
```

---

## Formula Examples

### Ledger Sheet (Key Formulas)

```excel
// Column B: holder_type
=XLOOKUP([@holder_name], Holders[holder_name], Holders[holder_type], "unknown")

// Column D: class_type
=XLOOKUP([@class_name], Classes[class_name], Classes[class_type], "unknown")

// Column K: ownership_percent_fds
=IFERROR([@current_quantity] / Total_FDS, 0)

// Column L: gross_itm (TSM)
=IF(Current_PPS > [@strike_price], [@initial_quantity], 0)

// Column O: net_dilution
=[@gross_itm] - [@shares_repurchased]
```

### Vesting Sheet (Formula-Driven)

```excel
// Column B: holder_name (lookup from Ledger via instrument_id)
=INDEX(Ledger[holder_name], MATCH([@instrument_id], Ledger[instrument_id], 0))

// Column D: total_granted
=INDEX(Ledger[initial_quantity], MATCH([@instrument_id], Ledger[instrument_id], 0))

// Column H: days_elapsed
=DAYS(Current_Date, [@grant_date])

// Column I: vested_shares
=[@total_granted] * MIN(1, MAX(0, ([@days_elapsed] - [@cliff_days]) / [@vesting_period_days]))
```

### Waterfall Sheet (Formula-Driven)

```excel
// Column C: shares (sum from Ledger)
=SUMIF(Ledger[class_name], [@class_name], Ledger[current_quantity])

// Column E: lp_multiple (lookup from Terms)
=XLOOKUP([@class_name], Terms[class_name], Terms[lp_multiple], 1)

// Column F: participation_type
=XLOOKUP([@class_name], Terms[class_name], Terms[participation_type], "non_participating")

// Column H: lp_amount
=[@shares] * AVERAGEIF(Ledger[class_name], [@class_name], Ledger[acquisition_price]) * [@lp_multiple]

// Column I: exit_payout (non-participating)
=MAX([@lp_amount], Exit_Val * [@ownership_fds])

// Column I: exit_payout (participating)
=[@lp_amount] + ((Exit_Val - SUM($I$2:I2)) * [@ownership_fds])
```

---

## Data Validation Strategy

### 1. Dropdown Lists (Referential Integrity)

```
Ledger[holder_name]:
  Source: =Holders[holder_name]
  Benefit: Prevents typos, ensures valid holders

Ledger[class_name]:
  Source: =Classes[class_name]
  Benefit: Ensures valid security classes

Ledger[round_name]:
  Source: =Rounds[round_name]
  Benefit: Ensures valid rounds
```

### 2. Conditional Formatting (Error Highlighting)

```
Ledger[holder_type]:
  Rule: =$B2<>XLOOKUP($A2, Holders[name], Holders[type], "ERROR")
  Format: Red background
  Benefit: Highlights mismatches with master data

Waterfall[lp_multiple]:
  Rule: =$E2<>XLOOKUP($A2, Terms[class], Terms[lp_mult], 1)
  Format: Orange background
  Benefit: Shows if terms are out of sync
```

### 3. Named Range Auditing

```
Summary Sheet Helper Column:
  Total_FDS_Check: =SUM(Ledger[current_quantity]) + SUM(Ledger[net_dilution])
  Total_FDS_Match: =IF(Total_FDS = Total_FDS_Check, "✓", "ERROR")
  Benefit: Validates named range calculations
```

---

## Migration Path

### Step 1: Add Master Sheets (Non-Breaking)
- Add new sheets: Holders, Classes, Terms
- Populate with data from JSON
- Don't change existing sheets yet
- Test that master data is complete

### Step 2: Convert Ledger (Partial Breaking)
- Add formula columns alongside static columns
- Example: Add `holder_type_calc` with formula, compare to `holder_type`
- Verify formulas match static values
- Replace static with formulas
- Hide helper columns

### Step 3: Convert Other Sheets
- Follow same pattern for Vesting, Waterfall, Cap Table
- Test each sheet independently
- Verify calculations match original

### Step 4: Add Validation & Auditing
- Add dropdown validations
- Add conditional formatting
- Add audit helper columns in Summary

### Step 5: Documentation & User Training
- Update README with master sheet info
- Create "How to Update" guide
- Show users how to model scenarios

---

## Benefits Summary

### For End Users:
- ✅ **Easy Updates**: Change master data, everything updates
- ✅ **Scenario Modeling**: Modify assumptions, see impact instantly
- ✅ **Data Consistency**: Impossible to have mismatched data
- ✅ **Clear Structure**: Understand where data comes from

### For Developers:
- ✅ **Less Code**: Python only populates master sheets
- ✅ **Easier Testing**: Test master data, formulas handle the rest
- ✅ **Better Audit Trail**: Formula dependencies show data flow
- ✅ **Flexible**: Add new calculations without changing Python

### For Auditors:
- ✅ **Traceable**: Every cell traces back to source
- ✅ **Verifiable**: Formulas are visible and checkable
- ✅ **Consistent**: No hidden calculations in Python
- ✅ **Standard**: Uses native Excel features

---

## Conclusion

Moving to a **formula-linked architecture** transforms the Excel output from a **static report** into a **dynamic financial model**. The key principles are:

1. **Master Sheets** = Single Source of Truth
2. **Ledger** = Transaction/Instrument details
3. **Analysis Sheets** = Pure formulas referencing masters + ledger
4. **Summary** = Global constants + calculated totals

This architecture is:
- **Maintainable**: Easy to update and extend
- **Transparent**: Clear data lineage
- **Flexible**: Supports scenario modeling
- **Professional**: Follows Excel best practices

The recommended implementation is **incremental** and can be done without breaking existing functionality.

