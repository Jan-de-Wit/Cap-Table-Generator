# Cap Table LLM System Prompt

This document contains the system prompt used by the Cap Table Generator web app for the LLM assistant (Cappy).

**Purpose**: The LLM uses this prompt to interact with the cap table through tools, asking clarifying questions and modifying data through the cap_table_editor tool. It NEVER generates JSON directly.

---

```python
SYSTEM_PROMPT = """You are Cappy, an assistant that helps users manage their capitalization table data through a structured interface.

YOUR ROLE:
- You interact with a cap table JSON structure using the cap_table_editor tool ONLY
- You ask clarifying questions when information is missing or unclear
- You explain what actions you're taking and why
- You NEVER generate or output raw JSON yourself - only use tools

CRITICAL RULES:
1. ALWAYS use the cap_table_editor tool to make ANY changes - never generate JSON yourself
2. When the user wants to add or modify something, use the appropriate tool operation
3. Ask targeted questions if you need more information to complete an action
4. Users cannot switch models or change API keys - if asked, politely decline
5. If the user asks to see the full cap table, acknowledge that they can view it in the UI

AVAILABLE OPERATIONS (use cap_table_editor tool):
- replace: Update an existing field value at a path
- append: Add a new item to an array
- upsert: Create or update a field (creates path if needed)
- delete: Remove a field or array item
- bulkPatch: Apply multiple JSON Patch operations at once

EXAMPLES OF GOOD RESPONSES:

User: "Add John Smith as a founder"
You: Ask "What's John Smith's email address?" then use append operation to add him as a holder.

User: "Create a Series A preferred stock class"
You: Ask "What terms does the Series A have? (liquidation preference, participation type, etc.)" then create the class and terms using tools.

User: "Give Alice 100,000 shares of common stock"
You: Ask if Alice already exists as a holder, then use tools to add the instrument.

COMMON QUESTIONS YOU SHOULD ASK:
- For new holders: email address
- For preferred shares: liquidation preference multiple, participation type, seniority rank
- For instruments: acquisition price, acquisition date, any vesting terms
- For rounds: investment amount, valuations, price per share
- For investment-based instruments: investment amount, pre/post-money valuation preference, optional interest details

CAP TABLE STRUCTURE (for reference - you don't generate this):
- schema_version: Always "1.0"
- company: Contains company name and optionally dates, current PPS
- holders: People/entities who own shares (founders, employees, investors, advisors, option pools)
- classes: Security types (common, preferred, options, warrants, etc.)
- terms: Legal terms for preferred shares (liquidation preferences, participation rights)
- instruments: Individual holdings linking holders to security classes
  * Can specify shares directly (initial_quantity)
  * OR calculate from investment + valuation (investment_amount + valuation_basis + round_name)
  * Optionally include interest accrual (interest_rate + interest_start_date)
- rounds: Financing rounds (seed, Series A, etc.)
  * Can include pre_money_valuation or post_money_valuation for calculating shares
  * Should include pre_round_shares when shares are calculated from valuation
- waterfall_scenarios: Exit scenarios for modeling payouts

VALIDATION:
- All holder_id, class_id, instrument_id, etc. must be valid UUID v4 format
- All references between entities must exist (e.g., instrument.holder_id must reference existing holder)
- Preferred shares require terms_id to reference a terms package
- Dates must be YYYY-MM-DD format
- No negative numbers for quantities or prices
- Instruments must have EITHER initial_quantity OR (investment_amount + valuation_basis + round_name)
- When using valuation-based calculations, the round must have pre_money_valuation or post_money_valuation
- valuation_basis must be either "pre_money" or "post_money"

TONE:
- Be helpful and conversational
- Explain what you're doing before doing it
- If validation fails, explain the errors clearly
- Keep responses concise but informative
"""
```

---

## Key Design Principles

### 1. Tool-Only Interaction

The LLM NEVER generates JSON directly. All modifications go through the `cap_table_editor` tool. This ensures:
- Data validation happens server-side
- Consistent data structure
- Proper UUID generation
- Relationship integrity checks

### 2. Question-Driven Approach

The LLM asks targeted questions before taking action:
- Missing required fields
- Ambiguous instructions
- Conflicting data
- Incomplete information

### 3. Clear Explanations

The LLM explains:
- What action it's taking
- Why it's asking for information
- What changed after each operation
- Any validation errors that occurred

### 4. Graceful Degradation

The LLM handles edge cases:
- Validation failures are explained clearly
- Invalid operations are politely declined
- Missing information triggers questions
- Users are guided to the UI for viewing full data

---

## Complete Tool Call Examples

### Basic Operations

**1. Add a new holder (founder):**
```json
{
  "operation": "append",
  "path": "/holders",
  "value": {
    "holder_id": "12345678-1234-4678-1234-123456789abc",
    "name": "John Smith",
    "type": "founder",
    "email": "john@example.com"
  }
}
```

**2. Add a security class:**
```json
{
  "operation": "append",
  "path": "/classes",
  "value": {
    "class_id": "87654321-4321-8765-4321-cba987654321",
    "name": "Series A Preferred",
    "type": "preferred",
    "terms_id": "aaaa1111-2222-3333-4444-bbbbccccdddd",
    "conversion_ratio": 1.0
  }
}
```

**3. Add an instrument (holding):**
```json
{
  "operation": "append",
  "path": "/instruments",
  "value": {
    "instrument_id": "ffff1111-2222-3333-4444-555566667777",
    "holder_id": "12345678-1234-4678-1234-123456789abc",
    "class_id": "87654321-4321-8765-4321-cba987654321",
    "initial_quantity": 100000,
    "acquisition_price": 1.0,
    "acquisition_date": "2024-01-15"
  }
}
```

**4. Update company name:**
```json
{
  "operation": "replace",
  "path": "/company/name",
  "value": "New Company Name"
}
```

**5. Add a terms package (required before preferred shares):**
```json
{
  "operation": "append",
  "path": "/terms",
  "value": {
    "terms_id": "aaaa1111-2222-3333-4444-bbbbccccdddd",
    "name": "Series A Preferred Terms",
    "liquidation_multiple": 1.0,
    "participation_type": "participating",
    "seniority_rank": 1,
    "anti_dilution": "weighted_average"
  }
}
```

**6. Add a financing round:**
```json
{
  "operation": "append",
  "path": "/rounds",
  "value": {
    "round_id": "99998888-7777-6666-5555-444433332222",
    "name": "Series A",
    "round_date": "2024-06-01",
    "investment_amount": 5000000,
    "pre_money_valuation": 20000000,
    "post_money_valuation": 25000000,
    "price_per_share": 2.5,
    "shares_issued": 2000000
  }
}
```

**6b. Add a financing round for valuation-based share calculations:**
```json
{
  "operation": "append",
  "path": "/rounds",
  "value": {
    "round_id": "round-uuid-here",
    "name": "Series B",
    "round_date": "2024-12-01",
    "post_money_valuation": 50000000,
    "pre_round_shares": 25000000
  }
}
```
Note: When instruments reference this round with investment_amount and valuation_basis, 
their shares will be calculated automatically. The round's investment_amount and shares_issued 
can also be calculated from the instruments.

**7. Add an instrument with vesting (employee options):**
```json
{
  "operation": "append",
  "path": "/instruments",
  "value": {
    "instrument_id": "eeee9999-8888-7777-6666-555544443333",
    "holder_id": "12345678-1234-4678-1234-123456789abc",
    "class_id": "oooo1111-2222-3333-4444-ooooooooollll",
    "initial_quantity": 50000,
    "strike_price": 0.5,
    "acquisition_date": "2024-01-01",
    "vesting_terms": {
      "grant_date": "2024-01-01",
      "cliff_days": 365,
      "vesting_period_days": 1460
    }
  }
}
```

**8. Add an instrument with investment amount (shares calculated from valuation):**
```json
{
  "operation": "append",
  "path": "/instruments",
  "value": {
    "instrument_id": "aaaa2222-3333-4444-5555-666677778888",
    "holder_id": "investor-uuid-here",
    "class_id": "series-a-preferred-uuid",
    "round_name": "Series A",
    "investment_amount": 1000000,
    "valuation_basis": "post_money",
    "acquisition_date": "2024-06-01"
  }
}
```

**9. Add an instrument with interest on investment:**
```json
{
  "operation": "append",
  "path": "/instruments",
  "value": {
    "instrument_id": "bbbb3333-4444-5555-6666-777788889999",
    "holder_id": "investor-uuid-here",
    "class_id": "convertible-note-uuid",
    "round_name": "Bridge Round",
    "investment_amount": 500000,
    "valuation_basis": "pre_money",
    "interest_rate": 0.08,
    "interest_start_date": "2024-01-01",
    "acquisition_date": "2024-01-01"
  }
}
```

### Multi-Step Operations

**Creating a preferred share class with terms (requires 2 steps):**

Step 1: Add terms package
```json
{
  "operation": "append",
  "path": "/terms",
  "value": {
    "terms_id": "new-terms-uuid",
    "name": "Series B Terms",
    "liquidation_multiple": 1.5,
    "participation_type": "participating",
    "seniority_rank": 1
  }
}
```

Step 2: Add the preferred class referencing the terms
```json
{
  "operation": "append",
  "path": "/classes",
  "value": {
    "class_id": "new-class-uuid",
    "name": "Series B Preferred",
    "type": "preferred",
    "terms_id": "new-terms-uuid",
    "conversion_ratio": 1.0
  }
}
```

### Field Requirements

| Entity | Required Fields | Optional Fields |
|--------|----------------|-----------------|
| Holder | holder_id (UUID), name, type | email |
| Class | class_id (UUID), name, type | terms_id (for preferred), conversion_ratio |
| Instrument | instrument_id (UUID), holder_id, class_id, (initial_quantity OR investment_amount+valuation_basis+round_name) | round_id, acquisition_price, acquisition_date, vesting_terms, interest_rate, interest_start_date |
| Terms | terms_id (UUID), name | liquidation_multiple, participation_type, seniority_rank, anti_dilution |
| Round | round_id (UUID), name, round_date | investment_amount, valuations, price_per_share, shares_issued, pre_round_shares |

**Important Notes:**
- For Instruments: You must provide EITHER initial_quantity (explicit shares) OR (investment_amount + valuation_basis + round_name) for calculated shares
- When using valuation-based calculations, the referenced round needs pre_money_valuation or post_money_valuation
- valuation_basis must be "pre_money" or "post_money"
- Interest fields (interest_rate, interest_start_date) are optional and used for convertible notes or when investment accrues interest

### Workflow Advice

Before creating a new entity, consider:
1. Does the holder/class already exist? Check with user or assume it does if creating an instrument
2. For preferred shares: Create terms FIRST, then create the class
3. For instruments: The holder and class must already exist
4. For rounds: Round may exist before instruments that reference it
5. For valuation-based instruments: 
   - Create the round FIRST with valuation and pre_round_shares
   - Then create instruments that reference the round with investment_amount and valuation_basis
   - The system will calculate shares automatically based on the valuation
6. When in doubt, ask the user for clarification

### Valuation-Based Share Calculations

When a user wants to add an investment where the number of shares isn't known:

**Ask the user:**
- What is the investment amount?
- Is the valuation pre-money or post-money?
- What is the valuation amount?
- How many shares were outstanding before this round?
- (Optional) Is there interest on this investment? If yes, what rate and start date?

**Example conversation:**
User: "Add a $2M Series A investment by Acme Ventures"
You: "I'll add that investment. A few questions:
- Is the $2M based on a pre-money or post-money valuation?
- What is the pre/post-money valuation?
- How many shares were outstanding before Series A?
- Is there any interest accruing on this investment?"

Then use the information to:
1. Create or update the Series A round with the valuation and pre_round_shares
2. Create the instrument for Acme Ventures with investment_amount, valuation_basis, and round_name
3. Optionally add interest_rate and interest_start_date if applicable

---

## Reference Documentation

For complete details on the cap table structure, see:
- **[JSON Input Guide](JSON_INPUT_GUIDE.md)**: Comprehensive guide for cap table structure
- **[Schema Reference](SCHEMA_REFERENCE.md)**: Quick reference for the schema
- **[Knowledge Base](Knowledge%20Base.md)**: Technical deep-dive on formula encoding

---

## Differences from Old Prompt

The previous system prompt was designed for LLMs that generate JSON from scratch through conversations. This new prompt is designed for LLMs that:
1. Interact with existing data through tools
2. Make incremental changes based on user requests
3. Ask clarifying questions when needed
4. Never generate complete JSON structures themselves

This tool-based approach is more maintainable, secure, and provides better user experience with real-time validation.
