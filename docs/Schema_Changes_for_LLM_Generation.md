## Cap Table Schema: LLM-Generation Optimization Plan

This document outlines inconsistencies found in the current JSON Schema and changes to make the schema easier and safer to generate with large language models.

### Single Source of Truth
- Remove the unused root-level `cap_table_schema.json` and keep only `src/captable/schemas/cap_table_schema.json` as the canonical schema.

### Align Implementation and Schema
- Keep the expanded `interest_type` enum as implemented: `simple`, `compound_yearly`, `compound_monthly`, `compound_daily`, `no_interest`.

### Add Structural Rigor
- Add `additionalProperties: false` at the root and for each `$defs` object (`Company`, `Holder`, `Instrument`, `Round`, `VestingTerms`, `FormulaEncodingObject`) to prevent hallucinated keys.
- Make `holders` required, or (preferably) introduce stable identifiers and references to enforce referential integrity.

### Introduce Stable Identifiers and Security Classes
- Add `id` (UUID string) to: `Holder`, `SecurityClass`, `Instrument`.
- Add top-level `security_classes: SecurityClass[]` with a new `$defs/SecurityClass` (e.g., `id`, `name`, `type` enum such as `common`, `preferred`, `option`, `warrant`, `convertible_note`; optional params like `conversion_ratio`, `liquidation_pref`, etc.).
- Allow `Instrument` to reference by `class_ref` (ID) and optionally `class_name` for convenience. Same for `holder_ref`/`holder_name` (prefer IDs, keep names as optional convenience).

### Conditional Requirements by Calculation Mode
Use `if`/`then` (Draft 2019-09) at the `Round` level:
- `fixed_shares`: require `instruments[].initial_quantity`.
- `target_percentage`: require `instruments[].target_percentage` and relevant context such as `pre_round_shares` and/or `price_per_share`.
- `convertible`: require `valuation_cap_basis`, interest fields when accruing interest, and either valuation-based inputs or `price_per_share` when basis is `fixed`.
- `valuation_based`: require `valuation_basis`, `investment_amount`, and either `pre_money_valuation` or `post_money_valuation`.

Add `if`/`then` inside `Instrument` for type-specific fields, e.g., `strike_price` for options/warrants, `vesting_terms` for options, and interest inputs for convertibles.

### FormulaEncodingObject Ergonomics
- Keep the current design, but consider:
  - Allowing omission of `is_calculated` when `formula_string` is present (imply `true`).
  - Accepting a simpler `path` format (e.g., `rounds[Seed].price_per_share`) alongside JSON Pointer.
  - Include concise examples showing `dependency_refs` placeholders mapping into `formula_string` for each `output_type`.

### Option Pool Consistency
- In `Round.option_pool_increase.shares_added`, allow `oneOf: [number, FormulaEncodingObject]` (currently formula-only) to align with other numeric formula-enabled fields.
- Add `if`/`then` to require `target_pool_percent` when the option pool increase object is present.

### LLM Guidance and Examples
- Add field-level `examples` where ambiguity exists (dates, decimals for percentages like `0.20`, realistic holder/company names). Add `$comment` notes near enums describing when to use each.
- Clarify the semantics of `company.current_pps` vs. `rounds[].price_per_share`.

### Immediate Actions
1. Delete root `cap_table_schema.json` to avoid confusion.
2. Add `additionalProperties: false` throughout.
3. Add `security_classes` and ID-based references, keep name-based references as optional.
4. Add `if`/`then` constraints for `calculation_type` and convertible specifics.
5. Relax `option_pool_increase.shares_added` to number-or-formula.
6. Add examples and `$comment`s aimed at LLMs.

---
