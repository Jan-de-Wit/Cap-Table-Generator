

# **Expert Technical Report: Designing a Dynamic JSON Schema for Capitalization Table Generation**

## **I. Conceptual and Structural Architecture of Capitalization Tables**

This technical report establishes the necessary data model, entity hierarchy, and structural mandates for generating a dynamic Excel-based capitalization table (cap table) from structured JSON data. The architecture focuses on decoupling core data from calculated outputs, ensuring all metrics are derived via embedded, referential Excel formulas.

### **1.1. Core Entities and Data Modeling Prerequisites**

A comprehensive cap table tracks the entirety of a company’s equity ownership, security types, transaction history, and associated legal terms, which are typically utilized by venture capital firms and startups for reporting and strategic decision-making.1 To capture this complexity dynamically, the data model requires five interdependent entities, linked by universally unique identifiers (UUIDs) for stability and referential integrity.3

#### **Core Entity Definitions:**

1. **Shareholder/Holder (Entity):** Represents the stakeholder (e.g., Founder, VC Fund, Employee). Key attributes include a mandatory UUID (holder\_id), Name, and Type.  
2. **Security Class (Class):** Defines the legal instrument (e.g., Common Stock, Series A Preferred). Attributes include class\_id (UUID), Name, and default conversion\_ratio.  
3. **Terms Package (Terms):** Crucially, this entity defines the specific financial and legal rights associated with a Security Class, such as liquidation\_multiple, participation\_rights (Boolean or Capped), seniority\_rank, and dividend\_rate.  
4. **Instrument (Holding):** This represents a specific grant or tranche of shares or options held by a Shareholder. Attributes include instrument\_id (UUID), initial\_quantity, acquisition\_price (Original Issue Price, or OIP), and mandatory foreign keys linking it to the holder\_id and class\_id.  
5. **Transaction/Round (Event):** Represents the historical change event, such as a Series A financing or a stock split. Attributes include round\_id (UUID), investment\_amount, pre\_money\_valuation, and total\_new\_shares.

The architecture mandates the strategic decoupling of the Terms Package from the generic Security Class definition. In professional financial modeling, liquidation preferences are complex, involving multiples, participation rights, and seniority.4 By modeling Terms as a separate, referential object, the equity stack can evolve, and the simulation capabilities are significantly enhanced. For instance, testing a scenario (e.g., 2x vs. 3x preference) only requires updating a single terms\_id reference on a scenario object, without restructuring the entire Security Class data set. The AI agent must utilize this chained reference (Instrument $\\rightarrow$ Security Class $\\rightarrow$ Terms) when compiling inputs for the complex conditional formulas required during exit waterfall analysis.

Table 1: Cap Table Entity Hierarchy and Relationships

| Entity | Role | Primary Key | Key Relationships | Purpose of FEO Integration |
| :---- | :---- | :---- | :---- | :---- |
| Shareholder (Entity) | The ultimate owner (e.g., Founder, Fund). | holder\_id (UUID) | One-to-many relationship with Instrument. | Calculates current ownership percentages. |
| Security Class (Class) | Defines the type of share (Common, Preferred A, Option). | class\_id (UUID) | One-to-one relationship with Terms Package. | Aggregates shares for totals and dilution calculations. |
| Terms Package (Terms) | Legal and financial rights (LP multiple, participation). | terms\_id (UUID) | Linked by class\_id to ensure correct application during Waterfall analysis. | Provides inputs for conditional formulas (e.g., IF, MAX). |
| Instrument (Holding) | A specific grant of shares or options to a holder. | instrument\_id (UUID) | Links holder\_id and class\_id. | Source data for shares, strike price, grant date, and vesting calculations. |
| Transaction (Event/Round) | A financing or administrative action. | round\_id (UUID) | Links to all instruments created in that round. | Calculates Price Per Share and Pre/Post-money valuations dynamically. |

### **1.2. The Equity Stack: Relationships and Dependencies**

The primary challenge in generating a dynamic cap table is enforcing relationships not through explicit data computation, but through formula references. This system requires strict adherence to JSON Schema standards, utilizing IDs ($id) and JSON Pointers ($ref) to define relationships and inputs, thereby replacing the inherent volatility of hard-coded cell addresses.3

#### **Dynamic Metric Generation**

The schema dictates that critical financial metrics, such as Fully Diluted Shares (FDS), Price Per Share (PPS), and ownership percentages, must be treated as calculated properties. These properties are identified by the presence of a nested structure referencing the **Formula Encoding Object (FEO)**, which houses the Excel syntax and its dependent inputs.

#### **Standard Excel Organization Mapping**

To ensure the reliability of cross-sheet references and the feasibility of formula automation, the AI agent must enforce a standardized Excel workbook structure:

1. **"Summary" Sheet:** This sheet contains global constants (e.g., the current market Price Per Share, Current\_PPS, or a simulated Exit\_Val) and calculated dynamic totals (e.g., Total FDS). These global references must be designated as Excel Named Ranges (e.g., Total\_FDS) for clean, readable formula referencing across the workbook.  
2. **"Shareholders" / "Ledger" Sheet:** This sheet serves as the transactional master list, where each row represents an Instrument (Holding). This data set must be generated as an Excel Table, allowing the formulas to utilize highly resilient Structured References (e.g., Ledger).7  
3. **"Waterfall" / "Scenarios" Sheet:** This sheet performs complex conditional logic, referencing inputs from the Summary sheet and the aggregated share counts from the Ledger.

### **1.3. Common Metrics and Calculation Prerequisites**

Accurate financial analysis relies on dynamically calculated metrics that reflect the true economic ownership of the company.

* **Shares Outstanding (Basic vs. FDS):** The critical metric for determining true ownership and dilution is the Fully Diluted Shares (FDS). This calculation must incorporate the net dilutive effect of options, warrants, and convertible notes.8 FDS is the required denominator for all percentage ownership calculations.  
* **Valuation Metrics:** The Price Per Share (PPS) and Pre/Post-Money Valuations are transactional outputs tied to specific funding rounds (Event). The PPS is dynamically calculated based on the investment amount and the resulting share counts for that round.9 The system must be capable of calculating these values using dynamic arithmetic based on input parameters provided within the Transaction entity.

## **II. Dynamic Equity Modeling: Comprehensive Use Cases**

This section provides the technical specifications and required Excel formula logic for the AI agent to implement standard and advanced cap table functionalities.

### **2.1. Foundational Calculation Registry**

The foundational calculations are dependent on aggregating data from the Ledger sheet and referencing global constants from the Summary sheet.

| Use Case | Description | Required Data Fields | Sample Excel Formula Logic (FEO Placeholder) | Dependencies |
| :---- | :---- | :---- | :---- | :---- |
| **Ownership % per Shareholder** | Calculates current ownership based on the FDS total. | Instrument.shares\_held, Summary.Total\_FDS | \=\] / Summary\!Total\_FDS (Structured Ref \+ Named Range) | Cross-Sheet Linking |
| **Share Class Totals** | Aggregates the total number of shares/options for a specific legal class. | Ledger, Ledger | \= SUMIF(Ledger,\], Ledger) | Structured Ref |
| **Fully Diluted Total (FDS)** | Sum of all outstanding shares plus the net dilutive effect of options/warrants (via TSM). | All Common/Preferred Shares, All Net Dilution (TSM) | \= SUM(Common\_Shares) \+ SUM(Preferred\_Shares) \+ SUM(Net\_Dilution) | Cumulative, Cross-Sheet Linking |

### **2.2. Transactional Event Modeling**

#### **A. SAFE and Convertible Note Conversion**

SAFEs (Simple Agreement for Future Equity) and convertible notes convert based on either a Price Cap or a Discount Rate applied to the new round’s Price Per Share (PPS). The calculation must determine the share count using the lowest possible price (most favorable to the investor).

* **Required Data Fields:** Investment Amount, Round PPS, Price Cap, Discount Rate, Shares Pre-Round.  
* **Conversion Shares Calculation (Logic):** The formula must calculate the price based on the Price Cap $\\text{($\\text{PriceCap} / \\text{Shares\_PreRound}$)}$ and the discounted price $\\text{($\\text{Round\_PPS} \\times (1 \- \\text{Discount})$)}$, selecting the minimum of the two prices, and then dividing the investment amount by that minimum price.  
* **Formula Logic (FEO):** $\\text{= \[@\[Investment\\\_Amount\]\] / MIN( (Round\\\_PPS \* (1 \- Discount\\\_Rate)), (Price\\\_Cap / Shares\\\_PreRound) )}$

Standard professional modeling avoids using iterative calculations (circular references) where the SAFE conversion affects the round's final PPS. Instead, the deterministic approach uses the stated PPS of the new round as the firm reference point. The AI agent is mandated to implement this simplified, deterministic formula structure to maintain high performance and avoid complex calculation dependencies.

#### **B. Vesting Schedules and Option Grants**

Vesting calculations rely on date arithmetic to determine the number of available shares at any point in time, critical for employee reporting and legal compliance.

* **Vested Shares Calculation:** This involves checking the number of days elapsed since the grant date against the specified cliff and total vesting period. The result must be capped at the total shares granted.  
* **Required Data Fields:** Total Shares Granted, Grant Date, Cliff Days, Vesting Period Days, Summary.Current\_Date (global date constant).  
* **Formula Logic (FEO):** $\\text{=\] \* MIN(1, MAX(0, (DAYS(Summary\!Current\_Date,\]) \-\]) /\] ) )}$. The use of $\\text{MAX}(0, \\ldots)$ prevents reporting negative vested shares before the cliff date has passed.

### **2.3. Valuation and Dilution Mechanics**

#### **A. Fully Diluted Shares (FDS) using Treasury Stock Method (TSM)**

The Treasury Stock Method (TSM) must be implemented to accurately calculate the net dilutive effect of in-the-money (ITM) options, warrants, and similar instruments.10 This requires dynamic conditional checking against a fluctuating global share price.

* **Conditional Check:** An option is considered dilutive only if it is 'in-the-money', meaning the Instrument.strike\_price is less than the current market price (Summary\!Current\_PPS).10  
* **Calculation Sequence:** TSM involves three steps: determining the gross shares issued from exercise, calculating the theoretical shares repurchased using the proceeds, and finding the net dilution.11  
  * $\\text{Net Dilution} \= \\text{Gross "In-the-Money" Dilutive Securities} \- \\text{Shares Repurchased}$.10

The ability to isolate the Summary\!Current\_PPS as a single, easily modifiable input cell via a Named Range is critical. This approach allows the user to immediately perform "instant scenario modeling," observing the impact on FDS and ownership across a spectrum of potential exit valuations. The TSM formulas must strictly reference this Named Range to ensure the required dynamic capability.

Table 2: Treasury Stock Method (TSM) Dynamic Calculation Mapping

| TSM Calculation Step | Required Data Inputs (JSON Ref) | Formula Logic (Symbolic FEO) | Dependency Type |
| :---- | :---- | :---- | :---- |
| 1\. Gross In-The-Money Shares | Instrument.initial\_quantity, Summary.current\_pps, Instrument.strike\_price | \=IF(Summary\!Current\_PPS \> Instrument.strike\_price, Instrument.initial\_quantity, 0\) | Named Range / Structured Ref |
| 2\. Proceeds from Exercise | Step 1 Result, Instrument.strike\_price | \=\] \*\] | Structured Ref |
| 3\. Shares Repurchased | Step 2 Result, Summary.current\_pps | \=IFERROR(\[@\[Proceeds\]\] / Summary\!Current\_PPS, 0\) | Named Range / Structured Ref |
| 4\. Net Dilution (TSM) | Step 1 Result, Step 3 Result | \=\] \-\] | Structured Ref |
| 5\. Total Fully Diluted Shares (FDS) | Sum of Common Shares \+ Total Net Dilution | \=SUMIF(Ledger, "Common", Ledger) \+ SUM(Ledger) | Structured Ref / Cross-Sheet |

### **2.4. Advanced Scenario and Exit Modeling (Waterfall)**

The Exit Waterfall analysis determines the distribution of proceeds based on the liquidation preferences (LP) and seniority of each share class. This requires highly conditional, sequential calculation logic, often involving nested IF and MAX functions.12

#### **A. Non-Participating Preferred Payout**

Non-participating preferred investors are entitled to the greater of their total Liquidation Preference (LP) amount or what they would receive if they converted their shares to common stock (pro-rata conversion).4

* **Formula Logic (Simplified):** $\\text{=IF}(\\text{Exit\\\_Val} \\le \\text{Total\\\_Preference}, \\text{LP\\\_Amount}, \\text{MAX}(\\text{LP\\\_Amount}, \\text{Exit\\\_Val} \\times \\text{\]}))$

#### **B. Participating Preferred Payout**

Participating preferred investors "double dip" by receiving their LP amount first, and then participating pro-rata in the remaining proceeds alongside common shareholders.4

* **Formula Logic (Partial Proceeds):** $\\text{= LP\\\_Amount} \+ ( (\\text{Exit\\\_Val} \- \\text{Total\\\_LP\\\_Paid\\\_Prior}) \\times \\text{\]} )$

#### **Cascading Calculation Flow**

The core requirement of the Waterfall sheet is adherence to seniority. The payout to any class is determined by the *remaining proceeds* after all senior classes have been fully paid.4 This requires a defined processing order. The JSON schema must include a WaterfallScenario entity that defines the processing order using Terms.seniority\_rank. The AI agent must use the internal Deterministic Layout Map (DLM) to ensure the generated Excel formulas refer correctly to the payout results of the preceding, senior classes, establishing a dynamic dependency chain.

Table 3: Liquidation Waterfall Logic (IF/MAX Conditional Mapping)

| Preference Type | Exit Value Check | Calculation (Symbolic FEO) | Required Function |
| :---- | :---- | :---- | :---- |
| Non-Participating LP | Exit Payout \> LP Amount? | \= MAX(\[@\[LP\_Amount\]\], Exit\_Val \*\]) | MAX / IF |
| Participating LP | Remaining Proceeds \> 0? | \= \[@\[LP\_Amount\]\] \+ ( (Exit\_Val \- SUM(Precedent\_Payments)) \*\] ) | SUM / Arithmetic |
| Common Stock | All Preferred LP Paid? | \= Exit\_Val \- SUM(All\_LP\_Payments) \*\] | Arithmetic / Cross-Sheet |

### **2.5. Investor-Focused and Compliance Logic**

* **Option Pool Top-Up:** Calculating the number of new shares required to establish a specific post-money option pool percentage requires a specialized reverse-dilution formula.9 This calculation is crucial for fundraising scenario forecasting.  
  * **Formula Logic (FEO):** $\\text{= (FDS\\\_PreRound} \\times \\text{Target\\\_Pool\\\_Percent) / (1 \- Target\\\_Pool\\\_Percent)}$.

## **III. JSON Schema Specification and Referential Integrity**

The proposed schema utilizes a Draft 2019-09 compliant structure to ensure robust definition and support for internal referencing. The architecture emphasizes the explicit modeling of calculated properties via a Formula Encoding Object (FEO).

### **3.1. Schema Blueprint: Modular Design and Naming Conventions**

The schema mandates the use of snake\_case for all property keys. All identifying attributes must be UUIDs. Reusable components, such as Instrument and VestingTerms, are defined within the top-level $defs structure.

The critical design decision is how to define attributes that are Excel-calculated rather than hard-coded inputs. Standard JSON Reference rules state that properties cannot exist alongside a $ref.15 Therefore, a property like Instrument.ownership\_percent\_fds cannot simply be a numerical field. Instead, it must reference the FEO structure defined in the $defs block.

* *Schema Example for a Calculated Property:*  
  JSON  
  "ownership\_percent\_fds": {  
      "$ref": "\#/$defs/FormulaEncodingObject",  
      "description": "Calculates ownership based on current shares / Total FDS."  
  }

### **3.2. Formula Encoding Object (FEO) Structure**

The FEO is a custom object designed to encapsulate all necessary information for the AI agent to inject a dynamic Excel formula into the generated workbook, effectively decoupling the calculation logic from the physical cell location.

| Property Key | Type | Description | Mandate |
| :---- | :---- | :---- | :---- |
| is\_calculated | Boolean | Flag indicating that this field requires formula injection. | TRUE |
| formula\_string | String | The Excel formula using symbolic placeholders (e.g., "=SharesHeld / TotalFDS"). | Must use US English syntax and comma separators.17 |
| dependency\_refs | Array of Objects | List of symbolic references that the AI agent must resolve to physical Excel addresses or ranges. | Defines data inputs required by the formula using JSON Pointer notation. |
| output\_type | String | Specifies the required Excel reference style (structured\_reference, named\_range, cell\_reference). | Guides the AI agent on syntax rules and addressing.7 |

### **3.3. Hierarchical and Cross-Referencing Mechanisms (Task 3\)**

The AI agent must translate the symbolic FEO placeholders into functional Excel addresses. This translation relies entirely on robust referencing protocols.

1. **Symbolic References and Pointers:** The symbolic placeholders (e.g., TotalFDS) used in the formula\_string must correspond precisely to an entry in the dependency\_refs array. Each entry must utilize JSON Pointer notation (e.g., $\\text{path: "\\\#/rounds/R102/investment\\\_amount"}$) to pinpoint the input data within the JSON structure.6  
2. **Prioritizing Resilient References:** The AI agent must be directed to prioritize Named Ranges and Structured References over absolute cell addressing.  
   * **Named Ranges:** These are mandatory for referencing single, unchanging constants defined in the Summary sheet (e.g., Summary\!Total\_FDS). They are clean and maintain integrity even if the Summary sheet layout changes.  
   * **Structured References:** These are mandatory for referencing data within the Ledger Excel Table (e.g., Ledger). They provide automatic adjustment capabilities if rows or columns are added, moved, or deleted within the table, significantly enhancing the generated Excel file’s robustness.7

## **IV. Excel Formula Representation and Encoding Best Practices**

The integrity of the dynamic cap table hinges on strict adherence to Excel formula encoding standards and a reliable translation pipeline.

### **4.1. The Formula Encoding Standard**

To guarantee file compatibility across all versions and locales of Microsoft Excel, formulas must adhere to two strict rules during injection:

1. **Syntax and Locale:** All function names within the formula\_string must be in US English (e.g., SUM, IF, MAX), and the list separator must be the comma (,).17 If a non-English locale is used during generation, Excel will automatically translate the US English functions upon file opening, maintaining functionality.  
2. **Error Handling:** To prevent visual disruption and calculation failure, especially in valuation contexts where division is common (e.g., Price Per Share, TSM share repurchase), all dividing calculations must be wrapped in the $\\text{IFERROR}$ function (e.g., $\\text{"=IFERROR(A1/B1, 0)"}$). This ensures the dynamic model handles zero denominators gracefully.

### **4.2. Translating JSON References to Excel Addresses (The DLM)**

The AI agent requires an internal, ephemeral data structure—the **Deterministic Layout Map (DLM)**—to bridge the gap between abstract JSON references and physical Excel coordinates. The DLM is generated during the initial sheet construction phase.

#### **Translation Process:**

1. **FEO Reading:** The AI Agent reads the FEO, extracting the symbolic formula\_string (e.g., $\\text{"= SharesHeld / TotalFDS"}$).  
2. **Dependency Query:** The Agent consults the FEO's dependency\_refs array to identify the JSON Pointers associated with the symbolic placeholders.  
3. **DLM Lookup:** The Agent queries the DLM to resolve the JSON Pointer paths (or UUIDs) into their predetermined Excel reference addresses (e.g., TotalFDS resolves to the Named Range Summary\!Total\_FDS).  
4. **Syntax Selection and Injection:** Based on the FEO's output\_type property, the Agent formats the reference string into the appropriate syntax (e.g., Structured Reference) and injects the final formula: $\\text{=\[@\[current\\\_quantity\]\] / Summary\!Total\\\_FDS}$.

Table 4: Formula Encoding Object (FEO) Translation Protocol

| JSON FEO Component | Excel Synthesis Role | Excel Syntax Target | Justification |
| :---- | :---- | :---- | :---- |
| formula\_string (e.g., SharesHeld / TotalFDS) | Core logic injection. | US English functions and comma separators. | Ensures universal compatibility across Excel environments.17 |
| dependency\_refs (JSON Pointer Path) | Data lookup and address resolution via DLM. | Target Address (e.g., B2, C:C) or Structured Reference. | Replaces volatile hard-coded addresses with stable UUID/path links.6 |
| output\_type: "named\_range" | Target single cell lookup. | Summary\!Named\_Range (e.g., Summary\!Total\_FDS). | Improves formula readability and maintains cross-sheet integrity for constants. |
| output\_type: "structured\_reference" | Target table data lookup. | Table\_Name\[@\[Column\_Header\]\] (e.g., Ledger). | Formulas automatically adjust if rows/columns are inserted or moved.7 |

## **V. Conversion Concepts and Implementation Blueprint**

The choice of conversion tool profoundly impacts the preservation of formula integrity, particularly regarding the display of calculated results upon file opening.

### **5.1. Evaluation of Formula Writing Libraries**

Non-native Python and JavaScript libraries are essential for server-side generation but share a critical limitation regarding dynamic calculation results.

| Library | Platform | Formula Handling | Cross-Sheet Support | Critical Limitation |
| :---- | :---- | :---- | :---- | :---- |
| **xlsxwriter** | Python | High fidelity for writing formulas, strictly enforcing US English syntax.17 | Full support for cross-sheet and external references. | **Does not calculate results;** stores 0 as the formula result and relies on Excel to recalculate upon opening.17 |
| **openpyxl** | Python | Robust formula writing supported.18 | Full support. | Similar constraint to xlsxwriter; calculation results are not computed by the library. |
| **exceljs** | JavaScript | Supports reading and writing formula values and types.19 | Supports standard cross-sheet linking. | Requires setting a flag to trigger recalculation upon file opening. |

The fact that these libraries only write the formula string, and not the computed result, means the generated XLSX file will display stale data (often zeros or the last static value) until the user initiates a manual calculation in Excel.17 This compromises the dynamic nature of the cap table. Therefore, the AI agent's implementation strategy must include a mandatory step: regardless of the library chosen, the agent must explicitly set the workbook property flag to **force full recalculation upon file opening**.

### **5.2. Native Office Automation Tools**

Tools such as Office Scripts (TypeScript for Excel on the web) and Microsoft Graph offer native, scriptable access to Excel's calculation engine and structure.20 While they could potentially perform the calculations server-side, their primary strategic role lies in post-generation automation.

* **Role in Ecosystem:** Office Scripts are ideal for implementing future features like automated auditing, scheduled data validation, or using Power Automate to cross-reference data validation across multiple generated workbooks in a flow.21 For the initial high-volume backend generation, the cross-platform libraries (xlsxwriter, exceljs) are preferable, with native tools reserved for high-level maintenance and verification.

### **5.3. Blueprint for Formula Preservation**

The AI agent must execute a precise five-stage sequence to guarantee formula preservation and dynamic integrity:

1. **Structure Generation:** Create all necessary worksheets ("Summary," "Ledger," "Waterfall," etc.) and define the key data sets as official Excel Tables (Ledger).  
2. **DLM Creation & Static Data Write:** Iterate through the JSON data, generate the Deterministic Layout Map (DLM) mapping UUIDs/paths to physical addresses, and write all raw input data (e.g., shares held, strike prices) into the corresponding cells.  
3. **Named Range Definition:** Define all global constants located on the Summary sheet as Named Ranges.  
4. **FEO Resolution and Injection:** Iterate through all JSON calculated attributes, utilize the FEO and DLM to resolve symbolic placeholders into Structured References and Named Ranges, and inject the final US English formula string into the designated cells.  
5. **Finalization:** Set the workbook's "force recalculation on load" flag and save the XLSX file. This step is non-negotiable for preserving the perceived accuracy and dynamism of the output.

## **VI. Conclusion and Future Extensibility**

The research confirms that generating dynamic, formula-driven cap tables requires a strict, opinionated architectural approach centered on the decoupling of inputs, logic, and location. The success of the AI coding agent’s implementation is entirely contingent upon two key technical mandates:

1. **Referential Integrity via FEO and DLM:** The Formula Encoding Object (FEO) provides the necessary structural abstraction to represent Excel formulas using symbolic references and JSON Pointers, while the Deterministic Layout Map (DLM) provides the essential runtime service to translate these abstract references into robust Excel syntax (Structured References and Named Ranges).  
2. **Adherence to Financial and Technical Standards:** The agent must rigorously implement industry-standard logic, including the conditional calculation of Fully Diluted Shares using the Treasury Stock Method (TSM) against a variable share price, and the sequential, conditional payout logic required for the Liquidation Waterfall (using IF, MAX, and SUMIF functions). All formulas must adhere to the US English function syntax standard.

The modular design, particularly the separation of Security Class and Terms Package, ensures that the system is highly extensible. New instruments, such as tokenized equity or future convertible structures, can be incorporated simply by defining a new Terms Package or Security Class without necessitating a fundamental change to the core entity schema or the logic used for calculating ownership and dilution.

#### **Geciteerd werk**

1. Cap Table | Startup Template \+ Calculation Example \- Wall Street Prep, geopend op oktober 25, 2025, [https://www.wallstreetprep.com/knowledge/the-ultimate-guide-to-capitalization-tables/](https://www.wallstreetprep.com/knowledge/the-ultimate-guide-to-capitalization-tables/)  
2. Cap Table Analytics: Gaining Strategic Insights \- Astrella, geopend op oktober 25, 2025, [https://astrella.com/blogs/cap-table-analytics-gaining-strategic-insights/](https://astrella.com/blogs/cap-table-analytics-gaining-strategic-insights/)  
3. Verifiable Credentials JSON Schema Specification \- W3C, geopend op oktober 25, 2025, [https://www.w3.org/TR/vc-json-schema/](https://www.w3.org/TR/vc-json-schema/)  
4. Modelling Liquidation Preferences in Cap Tables — Allied Venture ..., geopend op oktober 25, 2025, [https://www.allied.vc/guides/modelling-liquidation-preferences-in-cap-tables](https://www.allied.vc/guides/modelling-liquidation-preferences-in-cap-tables)  
5. JSON: referencing json schema with id \- Stack Overflow, geopend op oktober 25, 2025, [https://stackoverflow.com/questions/19564212/json-referencing-json-schema-with-id](https://stackoverflow.com/questions/19564212/json-referencing-json-schema-with-id)  
6. How to use JSON references ($refs) \- Redocly, geopend op oktober 25, 2025, [https://redocly.com/learn/openapi/ref-guide](https://redocly.com/learn/openapi/ref-guide)  
7. Using structured references with Excel tables \- Microsoft Support, geopend op oktober 25, 2025, [https://support.microsoft.com/en-us/office/using-structured-references-with-excel-tables-f5ed2452-2337-4f71-bed3-c8ae6d2b276e](https://support.microsoft.com/en-us/office/using-structured-references-with-excel-tables-f5ed2452-2337-4f71-bed3-c8ae6d2b276e)  
8. Diluted EPS Formula and Calculation \- Example, Sample \- Corporate Finance Institute, geopend op oktober 25, 2025, [https://corporatefinanceinstitute.com/resources/valuation/diluted-eps-formula-calculation/](https://corporatefinanceinstitute.com/resources/valuation/diluted-eps-formula-calculation/)  
9. The Capitalization Table (Cap Table): Full Guide \+ Excel Examples, geopend op oktober 25, 2025, [https://breakingintowallstreet.com/kb/venture-capital/capitalization-table/](https://breakingintowallstreet.com/kb/venture-capital/capitalization-table/)  
10. Treasury Stock Method (TSM) | Formula \+ Calculator \- Wall Street Prep, geopend op oktober 25, 2025, [https://www.wallstreetprep.com/knowledge/treasury-stock-method/](https://www.wallstreetprep.com/knowledge/treasury-stock-method/)  
11. Treasury Stock Method Calculator \- Download Free Excel Template, geopend op oktober 25, 2025, [https://corporatefinanceinstitute.com/resources/financial-modeling/treasury-stock-method-calculator/](https://corporatefinanceinstitute.com/resources/financial-modeling/treasury-stock-method-calculator/)  
12. The Liquidation Preference in Venture Capital: Full Tutorial and Excel Examples, geopend op oktober 25, 2025, [https://breakingintowallstreet.com/kb/venture-capital/liquidation-preference/](https://breakingintowallstreet.com/kb/venture-capital/liquidation-preference/)  
13. Building a Waterfall | Ali Rahimtula, geopend op oktober 25, 2025, [https://rahimtula.com/2024/10/22/building-a-waterfall/](https://rahimtula.com/2024/10/22/building-a-waterfall/)  
14. How to calculate your startup option pool size \- The Long-Term Stock Exchange, geopend op oktober 25, 2025, [https://ltse.com/insights/calculate-startup-option-pool-size](https://ltse.com/insights/calculate-startup-option-pool-size)  
15. json schema property description and "$ref" usage \- Stack Overflow, geopend op oktober 25, 2025, [https://stackoverflow.com/questions/33565090/json-schema-property-description-and-ref-usage](https://stackoverflow.com/questions/33565090/json-schema-property-description-and-ref-usage)  
16. Schema references with $ref \- Difference between Draft 5 and Draft 6 · json-schema-org · Discussion \#526 \- GitHub, geopend op oktober 25, 2025, [https://github.com/orgs/json-schema-org/discussions/526](https://github.com/orgs/json-schema-org/discussions/526)  
17. Working with Formulas \- XlsxWriter \- Read the Docs, geopend op oktober 25, 2025, [https://xlsxwriter.readthedocs.io/working\_with\_formulas.html](https://xlsxwriter.readthedocs.io/working_with_formulas.html)  
18. A Guide to Excel Spreadsheets in Python With openpyxl, geopend op oktober 25, 2025, [https://realpython.com/openpyxl-excel-spreadsheets-python/](https://realpython.com/openpyxl-excel-spreadsheets-python/)  
19. exceljs/exceljs: Excel Workbook Manager \- GitHub, geopend op oktober 25, 2025, [https://github.com/exceljs/exceljs](https://github.com/exceljs/exceljs)  
20. Introduction to Office Scripts in Excel \- Microsoft Support, geopend op oktober 25, 2025, [https://support.microsoft.com/en-us/office/introduction-to-office-scripts-in-excel-9fbe283d-adb8-4f13-a75b-a81c6baf163a](https://support.microsoft.com/en-us/office/introduction-to-office-scripts-in-excel-9fbe283d-adb8-4f13-a75b-a81c6baf163a)  
21. Office Scripts samples and scenarios \- Microsoft Learn, geopend op oktober 25, 2025, [https://learn.microsoft.com/en-us/office/dev/scripts/resources/samples/samples-overview](https://learn.microsoft.com/en-us/office/dev/scripts/resources/samples/samples-overview)