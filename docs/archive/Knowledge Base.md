# Cap Table Knowledge Base — Comprehensive Taxonomy

> Structured for direct use in an AI/database schema. For each instrument/term you’ll find: **Definition**, **Typical Terms**, **Dilution Behavior**, **Interactions**, **When It Appears**, and **Key Math/Waterfall Implications.**

---

## 0) Stakeholder & Holder Types

* **Founders / Co-founders**

  * *Definition:* Company creators holding common or founder stock.
  * *Typical terms:* Vesting (4 yrs/1-yr cliff), IP assignment, repurchase rights, reverse vesting, 83(b).
  * *Dilution:* Dilute pro rata with new issuances unless protected by a negotiated **maintain-%** or participation in rounds.
  * *Interactions:* May hold RSAs/RSUs/options; often subject to ROFR/co-sale.
  * *When:* Formation to exit.
  * *Math:* Founder stock often sets baseline **FD (fully diluted)** pool; subject to splits/recaps.
* **Employees**

  * *Definition:* Current team members with options, RSUs, RSAs, PSUs.
  * *Dilution:* Dilute with new issuances; pool refreshes increase dilution to others as allocated.
  * *Interactions:* ESOP/MIP pools; net settlement on RSUs can reduce outstanding via withholding.
* **Advisors / Contractors**

  * *Definition:* Non-employee contributors.
  * *Typical terms:* Option/RSU grants, shorter vesting (1–2 yrs), advisory agreements.
  * *Dilution:* Same as employees.
* **Angel Investors / HNWIs**

  * *Definition:* Individual investors pre-seed/seed.
  * *Instruments:* SAFEs, notes, Series Seed/Preferred, common in some geos.
* **VC Funds / Growth Equity / PE**

  * *Definition:* Institutional investors.
  * *Instruments:* Preferred equity (Series A+), notes/bridges, warrants, pro rata rights, protective provisions.
* **Strategics / Corporate Venture Arms**

  * *Definition:* Corporates investing for strategic fit.
  * *Instruments:* Preferred, warrants, commercial side letters (ROFR, exclusivity).
* **SPVs / Syndicates / Crowdfunding Vehicles**

  * *Definition:* Aggregator entities pooling smaller checks.
  * *Instruments:* Same as lead round security; often one cap-table line.
  * *Interactions:* Carry/fees internal to SPV, not cap table economics (except voting aggregation).
* **Foundations / DAOs (Web3)**

  * *Definition:* Entities representing communities/protocols.
  * *Instruments:* Token warrants/SAFTs, sometimes equity + token rights.

---

## 1) Ownership Unit Types

* **Shares (Corporation):** Common, Preferred (multiple series/classes).
* **Units (LLC/LP):** Common units, **Profits Interests** (PIUs), Class A/B/C units.
* **Tokens (Web3):** On-chain units (fungible/non-fungible) representing rights or economics (not stock unless tokenized equity).

---

## 2) Equity Instruments

### 2.1 Common Stock (incl. Founder/Common, Dual-Class)

* **Definition:** Residual ownership without preferences.
* **Typical terms:** Voting (1×), or dual-class (e.g., Class B 10× votes), vesting for founders via RSAs; ROFR/co-sale; drag/tag.
* **Dilution:** Fully dilutable by new issuances/pools.
* **Interactions:** Converts from preferred (at 1:1 or adjusted), notes/SAFEs convert *into preferred* (typically), not into common unless specified.
* **When:** All stages.
* **Math/Waterfall:** Paid after debt and preferred preferences; receives remaining proceeds as-converted.

### 2.2 Preferred Stock (Series Seed/A/B/…; Participating/Non-Participating)

* **Definition:** Equity with preferences over common.
* **Typical terms (per series):**

  * **Liquidation Preference:** ≥1.0× (non-participating or participating with/without cap).
  * **Conversion:** Initially 1:1 into common; adjustable for **anti-dilution** and stock splits.
  * **Dividends:** Non-cumulative or cumulative (cash/PIK).
  * **Voting:** As-converted + class votes; protective provisions.
  * **Redemption:** Sometimes after N years.
  * **Pay-to-Play:** Conversion to shadow series/common on non-participation in down round.
* **Dilution:** Dilute on new issuances; protected by weighted-average or full-ratchet anti-dilution.
* **Interactions:** Target for SAFE/note conversion; stacks **senior/pari passu/junior** across series; may have **pro rata** rights.
* **When:** Seed through late growth.
* **Math/Waterfall:**

  * **Preference Stack:** Seniority defines distribution ordering; **participating** takes pref + pro rata share until cap.
  * **Conversion Decision:** Each preferred holder chooses greater of preference vs as-converted common (or is forced to convert on qualified IPO).
  * **Anti-dilution (broad-based weighted average):**
    New conversion price:
    `CP2 = CP1 × (A + (C / CP1)) / (A + (C / Pnew))`
    Where `CP1` old conversion price, `A` old FD as-converted shares (often including pool), `C` new money, `Pnew` issue price.
    **Full-ratchet:** `CP2 = min(CP1, Pnew)`.

### 2.3 Special Share Classes

* **Super-Voting Common:** Multiple votes; often founders.
* **Non-Voting Common/Preferred:** For foreign investors or to meet ownership rules.
* **Preferred Variants:** **Participating**, **Capped Participating**, **Redeemable**, **Convertible** only on triggers.
* **Tracking/Alphabet Shares (Corp):** Track specific business line economics.
* **LLC/LP Units:** **Profits Interests (PIUs)** (see 5.6).

---

## 3) Convertible Instruments

### 3.1 Convertible Promissory Notes (Bridge/Seed Notes)

* **Definition:** Debt that converts to equity on triggers.
* **Typical terms:** Interest (simple, 2–10%); maturity (12–36 mo); **valuation cap**; **discount**; **MFN**; **most-favored conversion**; conversion on **Qualified Financing**; optional conversion on **Maturity** at cap/discount or repay.
* **Dilution:** Convert into new money round (usually **shadow preferred** or main series) increasing FD.
* **Interactions:** Often subordinate to venture debt; can have **warrants**; may convert on change of control to common/cash multiple.
* **When:** Pre-seed/seed/bridges.
* **Math:**

  * **Cap conversion price:** `CP_cap = Cap / PM_Shares_PreRound` (or pre-money basis; define precisely).
  * **Discount price:** `CP_disc = P_round × (1 – discount%)`.
  * Conversion uses better of cap vs discount (or specified). **Accrued interest** typically converts at CP used.

### 3.2 SAFEs (Pre-Money & Post-Money) / KISS

* **Definition:** Simple agreement for future equity; not debt (no interest/maturity).
* **Typical terms:** **Valuation cap**, **discount**, **MFN**, **Most Favored Nation**, **Pro rata side letter**, **change-of-control** payout (cap multiple or discount to price), **post-money** vs **pre-money** frameworks.
* **Dilution:**

  * **Post-Money SAFE:** Each SAFE fixes a % of the company *post-SAFE but pre-priced round*, causing dilution to founders and **later investors**, and not mutual among SAFEs (each stacks).
  * **Pre-Money SAFE:** Converts based on pre-money shares; multiple SAFEs dilute each other.
* **Interactions:** Convert into new series preferred (or SAFE-preferred) at `min(CP_cap, CP_disc, P_round)` rules; may include **token side letters** in Web3.
* **When:** Pre-seed/seed.
* **Math:** Define **PM shares** precisely in your engine (include option pool top-up rules consistent with SAFE flavor).

### 3.3 Convertible Equity (No Interest)

* **Definition:** Equity-like instruments that auto-convert at financing (used in some jurisdictions).
* **Terms/Dilution/Math:** Similar to pre-money SAFE but legally equity.

### 3.4 Debt-to-Equity Conversions (Workouts/Recaps)

* **Definition:** Outstanding debt converts to equity in down round or restructuring.
* **Typical terms:** Conversion at negotiated price (may be below last round), sometimes wipes preferences.
* **Dilution:** Highly dilutive to existing equity; may reset option pool.
* **Interactions:** Often paired with **pay-to-play** and recap waterfalls.

---

## 4) Options, Awards & Warrants

### 4.1 Stock Options (ISOs/NSOs)

* **Definition:** Right to purchase common at strike price.
* **Typical terms:** Vesting (time/performance), exercise window, early exercise (with RSA/83(b)), ISO eligibility caps, expiration (7–10 yrs), **net exercise** allowed sometimes.
* **Dilution:** Count in FD pool; exercised options become outstanding common.
* **Interactions:** Option pool **top-ups** often required as pre-money conditions.
* **When:** All stages; larger pools pre-Series A.
* **Math:** **Black-Scholes** not needed for cap table, but **FD** includes ungranted + granted (jurisdictional choice).

### 4.2 Restricted Stock Awards (RSAs)

* **Definition:** Actual shares subject to vesting/repurchase.
* **Typical terms:** Reverse vesting; 83(b); early founder grants.
* **Dilution:** Outstanding from day one; repurchased unvested reduce outstanding.

### 4.3 RSUs / PSUs (Performance RSUs)

* **Definition:** Promise to deliver shares (or cash) on vesting/settlement.
* **Typical terms:** Service/performance vesting; double-trigger acceleration; **net share settlement** with tax withholding.
* **Dilution:** Usually excluded until **settlement** (policy choice); or modeled as FD-equivalent.
* **Interactions:** Settlement can use **treasury** or newly issued shares.

### 4.4 Stock Appreciation Rights (SARs)

* **Definition:** Cash or stock payment equal to appreciation over base price.
* **Dilution:** If settled in stock, dilutive at settlement; if cash-settled, not dilutive but affects proceeds.

### 4.5 Phantom Stock / Phantom Units

* **Definition:** Contractual cash (or sometimes stock) bonus tracking share value.
* **Dilution:** No share issuance unless stock-settled.

### 4.6 ESPP (Employee Stock Purchase Plan)

* **Definition:** Public-company oriented discounted purchase program; rarely private.
* **Dilution:** New issuances at purchase; small.

### 4.7 Warrants

* **Definition:** Right to purchase shares (often preferred or common) at set price.
* **Typical terms:** Coverage % (e.g., 10–20% of debt), exercise price, net exercise, anti-dilution (rare), cashless, expiration.
* **Dilution:** FD include on as-if-exercised basis.
* **Interactions:** Common with **venture debt** and strategic deals.

---

## 5) Debt Instruments (Convertible or Otherwise)

### 5.1 Senior Secured Venture Debt / Bank Term Loans

* **Definition:** Non-convertible debt secured by assets/IP.
* **Typical terms:** Interest, amortization/interest-only, warrants, covenants, MAC, facility size, fees, PIK toggles.
* **Dilution:** From **warrants** only.
* **Waterfall:** Senior to all equity; repaid before any equity proceeds.

### 5.2 Revolvers / Lines of Credit / AR Facilities

* **Definition:** Working capital facilities secured by receivables/cash.
* **Waterfall:** Senior; can sweep exit proceeds.

### 5.3 Mezzanine / Subordinated Debt

* **Definition:** Junior debt; higher interest; often with warrants or conversion.
* **Waterfall:** Below senior, above equity.

### 5.4 Convertible/PIK Notes (see 3.1)

* **Definition:** As in §3.1 with PIK interest increasing principal.

---

## 6) Rights & Preferences (Cross-cutting)

### 6.1 Liquidation Preference

* **Definition:** Return of capital (e.g., 1.0×) before common.
* **Variants:** Non-participating, participating (uncapped/capped), multiple (≥1×).
* **Stacking:** **Senior > Pari Passu > Junior.**

### 6.2 Dividends

* **Definition:** Cash or PIK distributions; cumulative/non-cumulative; compounding rules.

### 6.3 Conversion Rights

* **Definition:** Voluntary/automatic conversion to common (IPO, majority vote).
* **Anti-dilution:** **Weighted-Average** or **Full-Ratchet** (see §2.2 Math).

### 6.4 Voting & Protective Provisions

* **Definition:** Class votes on major actions (new senior prefs, M&A, option pool increases…).

### 6.5 Information Rights

* **Definition:** Financials/KPIs delivery; inspection rights.

### 6.6 Registration Rights (Public-company path)

* **Definition:** Demand/piggyback/S-3; lock-ups.

### 6.7 ROFR / Co-Sale (Tag-Along)

* **Definition:** Company/investors can buy shares before third parties; tag on secondaries.

### 6.8 Drag-Along

* **Definition:** Majority can force sale subject to thresholds.

### 6.9 Redemption Rights

* **Definition:** Company repurchase of preferred after a period at set price.

### 6.10 Pay-to-Play

* **Definition:** Investors must participate in down rounds or suffer conversion to common/shadow series.

### 6.11 Board Rights / Observer Rights

* **Definition:** Board seats, observers; committee rights.

---

## 7) Special Maintenance & Participation Mechanisms

### 7.1 Pro Rata Rights

* **Definition:** Right to purchase in future rounds to maintain **as-converted** ownership.
* **Math:** Allocation `= holder% × new round size / (1 – holder%)` (implementation varies).
* **Dilution:** Reduces dilution for participating holders; increases for non-participants.

### 7.2 Super Pro Rata

* **Definition:** Right to buy **more** than pro rata (e.g., up to 1.5× stake).
* **Dilution:** Greater protection for holder; more dilution to others.

### 7.3 Fixed-Percentage Maintenance (“Maintain 5%”)

* **Definition:** Contractual top-up to preserve a fixed % through specified rounds.
* **Mechanics:** Automatic additional issuances or purchase rights; often capped by $$ or time.
* **Dilution:** Shifts dilution to others; must be modeled as **top-up shares** per round.

### 7.4 Ratchets (Price Protection)

* **Full-Ratchet:** Reset conversion price to lowest subsequent issue price.
* **Narrow-/Broad-Based Weighted Average:** See §2.2 formula; **denominator A** definition (includes pool? treasury method?) is critical.

### 7.5 Option Pool Shuffle/Top-ups

* **Definition:** Increasing ESOP to target % **pre-money** (diluting existing) or **post-money** (diluting new).
* **Math:** Solve for new pool so that `Pool_target% = NewPool / (FD_post)`; circular if SAFEs are post-money.

### 7.6 Participation Rights in Secondaries

* **Definition:** Right to sell specified % in company-led tender or investor-led secondary.

---

## 8) Corporate Actions, Secondaries & Edge Cases

### 8.1 Secondary Transactions

* **Definition:** Transfer of existing shares between holders.
* **Types:**

  * **Tender Offer / Company-led Liquidity:** Employees/investors sell to new buyers; may use **new money + secondary mix**.
  * **Investor-led Secondary:** Purchase from early holders.
* **Dilution:** None from mere transfer; **new option pool refresh** often paired (dilutive).
* **Interactions:** ROFR/co-sale; information rights gating; consent rights.

### 8.2 Buybacks / Repurchases

* **Definition:** Company repurchases shares/options; creates **treasury shares** or cancels.
* **Dilution:** Reduces outstanding; improves remaining holders’ %.

### 8.3 Recapitalizations / Splits

* **Definition:** Forward/reverse split; share reclassifications; down-round recaps.
* **Math:** Adjust conversion ratios, strikes, preferences proportionally.

### 8.4 SPVs / Holding Companies

* **Definition:** Aggregated investors as one holder.
* **Dilution:** Same as a single holder; internal economics off-cap-table.

### 8.5 Tokenized/Digital Equity

* **Tokenized Shares:** On-chain representation of equity; same rights as off-chain class.
* **Token Warrants / SAFT:** Right to future tokens at TGE; may include **equity + token** bundles.
* **Dilution:** Token issuance does **not** dilute equity unless explicitly linked (dual-track modeling).
* **Interactions:** Side letters for governance/lockups; regulatory constraints.

### 8.6 Revenue-Based Financing / Royalty Instruments

* **Definition:** Investors receive % of revenues until a cap multiple repaid.
* **Dilution:** Generally **non-dilutive** to equity; affects **cash waterfall** senior to equity but junior to secured debt as negotiated.

### 8.7 Profit Interests (LLC)

* **Definition:** **PIUs** grant a share of future appreciation above a threshold (liquidation value at grant).
* **Dilution:** Dilute future distributions; do not dilute existing value at grant.
* **Math:** Distribution waterfall per LLC agreement; often vesting like options.

### 8.8 Management Incentive Plans (MIP) in PE

* **Definition:** Sweet-equity pool with hurdle/catch-up; ratchet to management on high returns.
* **Dilution/Math:** Modeled via bespoke waterfall tiers.

### 8.9 Change-of-Control & Exit Triggers

* **Definition:** SAFE/note **cash-out** (e.g., `purchase amount × 1.0–2.0×`) or convert at cap/discount; option/RSU acceleration (single or double trigger).
* **Waterfall:** Respect debt → preferences → participating prefs → common.

### 8.10 Forfeitures / Cancellations / Option Repricing

* **Definition:** Unvested terminations return to pool; repricing resets strikes.
* **Dilution:** Forfeitures **reduce** FD; repricing no direct dilution.

---

## 9) Modeling & Math Primitives (implementation hints)

### 9.1 Share Count Definitions

* **Outstanding Shares:** Issued and not held in treasury.
* **Issued & Exercisable:** Outstanding + exercised options/warrants.
* **Fully Diluted (FD):** Outstanding + (as-converted preferred) + (all options/warrants/RSUs at target assumptions) + (convertibles as if converted at the current round’s terms) + (target ESOP top-up, if pre-money condition). **Choose and document your FD policy** per jurisdiction/round documents.

### 9.2 Prices & Conversions

* **Pre-Money vs Post-Money:**
  `Pre = Price_per_Share × FD_Pre` (define FD basis).
  `Post = Pre + New_Money`.
* **Option/RSU Net Settlement:** Delivered shares `= Vesting_Shares – Tax_Withheld_Shares`.
* **Warrant/Option Net Exercise:** Shares issued `= W × (1 – (ExPrice / FMV))`.

### 9.3 Anti-Dilution Calculations

* **Full-Ratchet:** `CP2 = min(CP1, Pnew)`.
* **Broad-Based WA (common):**
  `CP2 = CP1 × (A + (C/CP1)) / (A + (C/Pnew))`

  * `A` = pre-money FD share count defined in charter (often includes pool on an as-converted, treasury-method definition).
  * **Treasury method** for options may be specified; implement charter-accurate set.

### 9.4 Waterfall Ordering

1. **Secured Debt** (principal, fees, interest)
2. **Unsecured/Subordinated Debt**
3. **Liquidation Preferences** (by seniority; participating then pro rata until cap)
4. **As-Converted Common** (including converted preferred, options exercised/settled).

* **Forced Conversion:** In IPO or with holder vote if as-converted > preference.

### 9.5 Pro Rata Allocation Engine

* For each holder with right `r%` (as-converted):
  `Entitlement = r% × New_Securities_Issued (on same class/series)`
* **Super Pro Rata:** Cap at negotiated maximum; allocate remaining to others.

### 9.6 Option Pool Top-Up Solver

* **Pre-Money Target (%T):** Solve `NewPool = %T × (Common_out + Pref_asConv + SAFEs_asConv + Notes_asConv + NewPool)`.

### 9.7 SAFE/Note Conversion Engine

* **Compute CPs:** `CP_cap`, `CP_disc`, `P_round`.
* **Pick:** `min` per instrument’s docs; convert principal + accrued interest (notes).
* **Series:** Create **shadow series** if liquidation preference/other terms differ.

---

## 10) Data Schema Sketch (for integration)

### Entities

* **Company, Round, SecurityClass, SecuritySeries, Instrument, Holder, Grant, Conversion, Exercise, Transfer, Repurchase, WaterfallTier, Right**
* **Instrument Types (enum):** `COMMON`, `PREFERRED`, `SAFE_PRE`, `SAFE_POST`, `NOTE`, `WARRANT`, `OPTION_ISO`, `OPTION_NSO`, `RSA`, `RSU`, `PSU`, `SAR`, `PHANTOM`, `PIU`, `TOKEN_WARRANT`, `SAFT`, `REVENUE_SHARE`, `DEBT_SENIOR`, `DEBT_SUBORDINATED`, `TRACKING_SHARE`, `REDEEMABLE_PREF`, `PARTICIPATING_PREF`, `CAP_PARTICIPATING_PREF`.

### Core Fields by Instrument

* **Definition/Description**
* **Valuation Method:** (Cap, Discount, Fixed Price, FMV, Hurdle)
* **Conversion Rules:** (ratio, CP formula, triggers)
* **Preference:** (multiple, participating?, cap)
* **Voting:** (votes/share, class rights)
* **Anti-Dilution:** (type, variables A/C/Pnew definitions)
* **Dividend:** (rate, cum?, PIK?)
* **Redemption:** (eligible?, date, price)
* **Maintenance Rights:** (pro rata %, super pro rata %, fixed %)
* **Seniority:** (stack position)
* **When Appears:** (stage tags)
* **Dilution Behavior:** (FD counting policy)
* **Waterfall Behavior:** (priority, participation, cap)
* **Interactions:** (target conversion series, side letters, token links)

### Event Types

* **RoundClose, SecurityIssue, OptionGrant, Exercise, Vesting, Forfeiture, Conversion, SecondarySale, Buyback, PoolIncrease, Split/ReverseSplit, DebtDraw/Repay, WarrantExercise, Redemption, TenderOffer, ChangeOfControl, TokenGenerationEvent**

---

## 11) Quick Reference — “What to Include in FD?”

* As-converted preferred **(yes)**
* All granted options/warrants **(yes)**
* Unallocated option pool **(policy: often yes for pre-money rounds)**
* RSUs **(policy: unsettled often **no**; include if docs require)**
* SAFEs/Notes **(as if converted at round terms)**
* Token instruments **(no, unless explicitly equity-linked)**

---

## 12) Typical Lifecycle by Stage (guidance tags)

* **Pre-seed/Seed:** Founder common/RSAs, ESOP (5–15%), SAFEs (pre/post-money), notes, angels/SPVs.
* **Series A/B:** Preferred with 1× non-participating, WA anti-dilution, pro rata, protective provisions; ESOP top-ups.
* **Growth (C+):** Larger checks, seniority stratification, redemption rights sometimes, venture debt + warrants, secondaries/tenders.
* **Pre-IPO:** Complex waterfalls, registration rights active, RSU migration, dual-class common, ESPP.
* **Web3:** Equity + token warrants/SAFTs; foundation/DAO participants.

---

### Final Notes for Implementers

* **Document-Accuracy First:** Use charter/legal definitions for **A (denominator) and FD basis** in anti-dilution math.
* **Deterministic Ordering:** Apply events chronologically; recompute FD after each event that changes it (pool top-ups, conversions).
* **Waterfall Engine:** Allow **holder-by-holder optimal conversion** vs preference, with **series-level rules** (participation caps, forced conversion).
* **Policy Flags:** (a) Include unallocated pool in FD? (b) RSUs count at grant or settlement? (c) SAFE pre/post-money semantics and pool treatment.

This taxonomy covers the instruments, rights, edge cases, and the key mathematical implications you’ll need to model exhaustive, auditable cap tables across startup and corporate scenarios.
