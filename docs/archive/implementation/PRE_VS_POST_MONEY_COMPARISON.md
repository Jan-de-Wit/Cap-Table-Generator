# Pre-Money vs Post-Money Valuation: Quick Comparison

## Visual Example

Starting point: **10M founder shares**

### Scenario 1: Pre-Money Valuation
```
Investment: $10M at $40M pre-money valuation

Before Investment:
┌─────────────────────────┐
│   Founders: 10M shares  │
│   Value: $40M           │  ← Pre-Money Valuation
└─────────────────────────┘

After Investment:
┌─────────────────────────┐
│   Founders: 10M shares  │
│   Investor: 2M shares   │  ← Calculated: $10M × 10M / $50M
│   Total: 12M shares     │
│   Value: $50M           │  ← Post-Money = Pre + Investment
└─────────────────────────┘

Investor Ownership: 2M / 12M = 16.67%
```

### Scenario 2: Post-Money Valuation
```
Investment: $10M at $50M post-money valuation

Before Investment:
┌─────────────────────────┐
│   Founders: 10M shares  │
│   Value: $40M           │  ← Implied Pre-Money
└─────────────────────────┘

After Investment:
┌─────────────────────────┐
│   Founders: 10M shares  │
│   Investor: 2.5M shares │  ← Calculated: (10M × 20%) / 80%
│   Total: 12.5M shares   │
│   Value: $50M           │  ← Post-Money Valuation
└─────────────────────────┘

Investor Ownership: 2.5M / 12.5M = 20%  (Exactly $10M / $50M)
```

## Key Insight

**Pre-Money:** Investment amount determines ownership *indirectly*
- Investor gets: `Investment / (Valuation + Investment)` ownership
- Example: $10M / ($40M + $10M) = 16.67%

**Post-Money:** Investment amount determines ownership *directly*
- Investor gets: `Investment / Valuation` ownership  
- Example: $10M / $50M = 20%

## When to Use Each

### Pre-Money
- **Traditional approach** in early-stage VC
- Company sets a "company worth" before money comes in
- Investor ownership varies based on investment size
- **More common in:** Seed, Series A, B rounds

### Post-Money
- **Founder-friendly** approach
- Guarantees exact ownership percentage
- Simpler for founders to understand dilution
- **More common in:** SAFE notes, YC investments, some modern VCs

## Side-by-Side Formula Comparison

| | Pre-Money | Post-Money |
|---|-----------|------------|
| **Valuation** | Company value BEFORE investment | Company value AFTER investment |
| **Ownership Calc** | `Investment / (Pre-Money + Investment)` | `Investment / Post-Money` |
| **Shares Formula** | `(Inv × PreShares) / (PreMoney + Inv)` | `(PreShares × (Inv/Post)) / (1 - Inv/Post)` |
| **Dilution** | Variable based on investment | Fixed based on target ownership |

## Example Numbers: Same $10M Investment

| Metric | Pre-Money ($40M) | Post-Money ($50M) |
|--------|------------------|-------------------|
| Pre-money value | $40M | $40M (implied) |
| Investment | $10M | $10M |
| Post-money value | $50M | $50M |
| Investor shares | 2,000,000 | 2,500,000 |
| Investor ownership | 16.67% | 20.00% |
| Founder dilution | 16.67% | 20.00% |

## JSON Examples

### Pre-Money
```json
{
  "instrument": {
    "investment_amount": 10000000,
    "valuation_basis": "pre_money"
  },
  "round": {
    "pre_money_valuation": 40000000
  }
}
```
Result: 16.67% ownership

### Post-Money
```json
{
  "instrument": {
    "investment_amount": 10000000,
    "valuation_basis": "post_money"
  },
  "round": {
    "post_money_valuation": 50000000
  }
}
```
Result: 20% ownership (guaranteed)

## Automatic Calculation

Both methods now automatically calculate:
1. ✅ `pre_round_shares` from previous rounds
2. ✅ `initial_quantity` (shares issued) based on investment
3. ✅ `shares_issued` for the round
4. ✅ All using **Excel formulas** for transparency

No manual calculations needed - just specify:
- `investment_amount`
- `valuation_basis` (pre_money or post_money)
- `round_name` (linking to round with valuation)

The system handles the rest! 🎉

