# Cap Table Generator - Refactoring Implementation Guide

This guide provides step-by-step instructions for refactoring the codebase according to the approved plan.

## Current Status

✅ **Completed**:
- Created base modules for excel package
- Created master_sheets.py generator
- Created summary_sheet.py generator
- Started architecture documentation

## Implementation Phases

### Phase 1: Core Library - Excel Module (In Progress)

**Goal**: Split `excel.py` (1172 lines) into modular sheet generators

#### Step 1.1.1: Complete Sheet Generator Stubs ⏳

**Create the following files** (already started):
- ✅ `src/captable/excel/__init__.py` - Done
- ✅ `src/captable/excel/base.py` - Done
- ✅ `src/captable/excel/formatters.py` - Done
- ✅ `src/captable/excel/table_builder.py` - Done
- ✅ `src/captable/excel/sheet_generators/__init__.py` - Done
- ✅ `src/captable/excel/sheet_generators/master_sheets.py` - Done
- ✅ `src/captable/excel/sheet_generators/summary_sheet.py` - Done
- ⏳ `src/captable/excel/sheet_generators/ledger_sheet.py` - TODO
- ⏳ `src/captable/excel/sheet_generators/rounds_sheet.py` - TODO
- ⏳ `src/captable/excel/sheet_generators/progression_sheet.py` - TODO
- ⏳ `src/captable/excel/sheet_generators/vesting_sheet.py` - TODO
- ⏳ `src/captable/excel/sheet_generators/waterfall_sheet.py` - TODO

**Action Items**:
1. Extract `_create_ledger_sheet()` from `excel.py` lines 302-523
2. Extract `_create_rounds_sheet()` from `excel.py` lines 553-649
3. Extract `_create_cap_table_progression_sheet()` from `excel.py` lines 651-914
4. Extract `_create_vesting_sheet()` from `excel.py` lines 916-977
5. Extract `_create_waterfall_sheet()` from `excel.py` lines 979-1114

Each should:
- Inherit from `BaseSheetGenerator`
- Implement `_get_sheet_name()` and `generate()` methods
- Use `self.formats`, `self.dlm`, `self.formula_resolver`
- Import utilities from `..base`, `..table_builder`

#### Step 1.1.2: Create Refactored Excel Generator

**File**: `src/captable/excel/generator_new.py`

**Purpose**: Orchestrate sheet generation using new modular structure

**Structure**:
```python
from typing import Dict, Any
import xlsxwriter
from .formatters import ExcelFormatters
from .sheet_generators import (
    MasterSheetsGenerator,
    SummarySheetGenerator,
    LedgerSheetGenerator,
    # ... etc
)

class ExcelGenerator:
    def __init__(self, data: Dict[str, Any], output_path: str):
        self.data = data
        self.output_path = output_path
        self.workbook = None
        self.formats = {}
        self.dlm = DeterministicLayoutMap()
        self.formula_resolver = FormulaResolver(self.dlm)
    
    def generate(self) -> str:
        # Create workbook
        # Create formats
        # Generate sheets in order
        # Close and save
```

#### Step 1.1.3: Update Excel Generator Orchestrator

**Modify**: `src/captable/excel.py`

**Changes**:
1. Keep `ExcelGenerator` class but make it use sheet generators
2. Import from new generators
3. Call generators in sequence
4. Maintain backward compatibility

#### Step 1.1.4: Testing and Verification

**Test Steps**:
1. Run existing tests: `pytest tests/test_excel_generator.py -v`
2. Generate sample Excel files
3. Verify formulas are correct
4. Check named ranges work
5. Verify table structured references

**Files to Update**:
- `tests/test_excel_generator.py` - Add tests for new structure
- `demo.py` - Verify it still works

**Success Criteria**:
- ✅ All tests pass
- ✅ Generated Excel files are identical to before
- ✅ No regressions in functionality
- ✅ Each new file < 500 lines

---

### Phase 1.2: Formula Resolution Enhancement

**Goal**: Split `formulas.py` (417 lines) into specialized modules

#### Step 1.2.1: Create Formulas Package Structure

**Create directory**: `src/captable/formulas/`

**Files to Create**:
1. `__init__.py` - Package exports
2. `base.py` - FormulaResolver base class
3. `ownership.py` - Ownership and dilution formulas
4. `tsm.py` - Treasury Stock Method
5. `vesting.py` - Vesting schedules
6. `valuation.py` - Valuation-based calculations
7. `waterfall.py` - Liquidation preferences
8. `interest.py` - Interest accrual

#### Step 1.2.2: Extract Formula Methods

**From `formulas.py` extract**:

**ownership.py**:
- `create_ownership_formula()` (line 155)
- Related ownership calculations

**tsm.py**:
- `create_tsm_gross_itm_formula()` (line 168)
- `create_tsm_proceeds_formula()` (line 183)
- `create_tsm_repurchase_formula()` (line 187)
- `create_tsm_net_dilution_formula()` (line 192)

**vesting.py**:
- `create_vesting_formula()` (line 196)
- Vesting-related calculations

**valuation.py**:
- `create_shares_from_investment_premoney_formula()` (line 320)
- `create_shares_from_investment_postmoney_formula()` (line 344)
- `create_price_per_share_from_valuation_formula()` (line 371)
- `create_post_money_from_pre_money_formula()` (line 385)
- `create_pre_money_from_post_money_formula()` (line 401)

**waterfall.py**:
- `create_waterfall_nonparticipating_formula()` (line 240)
- `create_waterfall_participating_formula()` (line 257)
- Waterfall-related calculations

**interest.py**:
- `create_accrued_interest_formula()` (line 293)
- Interest calculations

**base.py**:
- Main `FormulaResolver` class
- `resolve_feo()` (line 21)
- `_resolve_path()` (line 65)
- `_replace_placeholders()` (line 101)
- `_wrap_divisions_in_iferror()` (line 126)

#### Step 1.2.3: Update Imports

**Files to Update**:
- `excel/generator.py` - Import from new formulas package
- `excel/sheet_generators/*.py` - Update formula references
- `generator.py` - Update imports

#### Step 1.2.4: Testing

**Test Steps**:
1. Run existing tests that use formulas
2. Verify formula generation still works
3. Check that specialized modules are used correctly

**Success Criteria**:
- ✅ All tests pass
- ✅ Each formula module < 200 lines
- ✅ Clear separation of concerns

---

### Phase 1.3: Validation System Improvement

**Goal**: Split `validation.py` into specialized validators

#### Step 1.3.1: Create Validation Package

**Directory**: `src/captable/validation/`

**Files to Create**:
1. `__init__.py`
2. `schema_validator.py` - JSON Schema validation
3. `relationship_validator.py` - Foreign key checks
4. `business_rules.py` - Business logic validation
5. `feo_validator.py` - Formula Encoding Object validation
6. `validator.py` - Main orchestrator

#### Step 1.3.2: Extract Validation Methods

**From `validation.py` extract**:

**schema_validator.py**:
- Schema compliance checking using jsonschema
- Use existing `Draft201909Validator`

**relationship_validator.py**:
- `_validate_relationships()` (line 53)
- Check foreign keys for instruments, classes, scenarios

**business_rules.py**:
- `_validate_name_uniqueness()` (line 142)
- `_validate_valuation_calculations()` (line 174)
- Business logic specific to cap tables

**feo_validator.py**:
- `_validate_feo_objects()` (line 106)
- Check FEO structure and dependencies

**validator.py**:
- Main `CapTableValidator` class
- Orchestrate all validators
- Return combined results

#### Step 1.3.3: Update Main Validator

**File**: `src/captable/validation.py`

**Changes**:
1. Import from new validators
2. Keep `validate_cap_table()` function for backward compatibility
3. Delegate to validator package

#### Step 1.3.4: Testing

**Test Steps**:
1. Run `tests/test_validation.py`
2. Verify all validation rules still work
3. Test each validator independently

**Success Criteria**:
- ✅ All validation tests pass
- ✅ Each validator < 300 lines
- ✅ Clear separation of concerns

---

### Phase 1.4: Additional Excel Functionality

**Goal**: Complete ledger, rounds, progression, vesting, waterfall generators

#### Step 1.4.1: Complete Ledger Sheet Generator

**File**: `src/captable/excel/sheet_generators/ledger_sheet.py`

**Extract from `excel.py` lines 302-523**:
- Complex valuation-based calculations
- XLOOKUP formulas for holder/class types
- Data validation for foreign keys
- TSM calculations

**Implementation Notes**:
- Handle valuation-based instruments
- Support both explicit and calculated shares
- Add proper error handling

#### Step 1.4.2: Complete Remaining Generators

Follow same pattern for:
- `rounds_sheet.py`
- `progression_sheet.py`
- `vesting_sheet.py`
- `waterfall_sheet.py`

#### Step 1.4.3: Integration Testing

**Test all generators together**:
```bash
pytest tests/test_excel_generator.py::test_full_generation
```

---

### Phase 2: Web Application Refactoring

**Goal**: Refactor web application for maintainability

#### Step 2.1: LLM Service Decomposition

**Directory**: `webapp/backend/services/llm/`

**Files to Create**:
1. `__init__.py`
2. `client.py` - OpenAI client wrapper
3. `tool_definitions.py` - Tool schemas
4. `prompt_manager.py` - System prompts
5. `message_formatter.py` - Message formatting
6. `stream_handler.py` - SSE streaming
7. `llm_service.py` - Main orchestrator

**Current File**: `webapp/backend/services/llm_service.py` (1002 lines)

**Extraction Strategy**:
1. Extract tool definitions (lines 33-600+)
2. Extract prompt management
3. Extract streaming logic
4. Keep orchestrator minimal

#### Step 2.2: Tool Execution System

**Directory**: `webapp/backend/services/tools/`

**Files to Create**:
1. `__init__.py`
2. `executor.py` - Core execution
3. `orchestrator.py` - Tool call management
4. `validator.py` - Parameter validation
5. `operations/__init__.py`
6. `operations/replace.py`
7. `operations/append.py`
8. `operations/upsert.py`
9. `operations/delete.py`
10. `operations/bulk_patch.py`

#### Step 2.3: API Route Organization

**Directory**: `webapp/backend/routers/`

**Files to Create**:
1. `__init__.py`
2. `chat.py` - Chat endpoints
3. `captable.py` - Cap table CRUD
4. `tools.py` - Tool execution
5. `conversation.py` - Conversation management
6. `export.py` - Download endpoints

**Update**: `webapp/backend/main.py`
- Import routers
- Include router modules

---

### Phase 3: Frontend Refactoring

**Goal**: Improve frontend organization

#### Step 3.1: Component Reorganization

**Directory**: `webapp/frontend/src/components/`

**New Structure**:
```
components/
├── Layout/
│   ├── Header.tsx
│   ├── Sidebar.tsx
│   └── MainLayout.tsx
├── Chat/
│   ├── ChatPane.tsx ✅
│   ├── MessageList.tsx ✅
│   ├── MessageInput.tsx ✅
│   └── StatusMessage.tsx ✅
├── CapTable/
│   ├── CapTablePreview.tsx ✅
│   └── CapTableSummary.tsx
├── Tools/
│   ├── ToolCallApproval.tsx ✅
│   └── ToolCallStatus.tsx ✅
├── Export/
│   └── ExportButtons.tsx ✅
└── Common/
    ├── ModelDisplay.tsx ✅
    └── DiffViewer.tsx ✅
```

#### Step 3.2: State Management Refactoring

**Directory**: `webapp/frontend/src/store/`

**Create**:
1. `slices/chatSlice.ts`
2. `slices/captableSlice.ts`
3. `slices/uiSlice.ts`
4. `slices/toolsSlice.ts`
5. `index.ts` - Combined store

**Update**: `appStore.ts` to use slices

#### Step 3.3: API Service Refactoring

**Directory**: `webapp/frontend/src/services/`

**Create**:
1. `chatApi.ts`
2. `captableApi.ts`
3. `toolsApi.ts`
4. `exportApi.ts`

**Keep**: `api.ts` for shared utilities

---

### Phase 4: Documentation

#### Step 4.1: Architecture Documentation ✅ STARTED

**Directory**: `docs/architecture/`

**Files**:
- ✅ `ARCHITECTURE_OVERVIEW.md` - Created
- ✅ `CORE_LIBRARY.md` - Created
- ⏳ `WEB_APPLICATION.md` - TODO
- ⏳ `DATA_FLOW.md` - TODO
- ⏳ `FORMULA_SYSTEM.md` - TODO
- ⏳ `EXCEL_GENERATION.md` - TODO
- ⏳ `API_REFERENCE.md` - TODO

#### Step 4.2: Developer Guides

**Directory**: `docs/guides/`

**Create**:
1. `DEVELOPMENT_SETUP.md`
2. `CONTRIBUTING.md`
3. `TESTING_GUIDE.md`
4. `DEBUGGING.md`
5. `ADDING_FEATURES.md`
6. `CODE_STYLE.md`

#### Step 4.3: Update Existing Docs

**Files to Update**:
- `README.md` - New structure
- `QUICKSTART.md` - Updated paths
- Archive redundant files to `docs/archive/`

#### Step 4.4: Add Inline Documentation

**Files to Document**:
- All new modules
- All public functions
- All classes
- Complex logic sections

---

### Phase 5: Testing Infrastructure

#### Step 5.1: Reorganize Tests

**Directory**: `tests/`

**New Structure**:
```
tests/
├── unit/
│   ├── captable/
│   ├── services/
│   └── validators/
├── integration/
├── e2e/
├── fixtures/
└── helpers/
```

#### Step 5.2: Improve Coverage

**Target**: >80% coverage on core library

**Focus Areas**:
- Formula resolution
- Validation logic
- Excel generation
- API endpoints

---

### Phase 6: Code Quality

#### Step 6.1: Add Type Hints

**Files to Update**:
- All Python modules
- Frontend TypeScript

**Enable**:
- `mypy strict mode`
- `tsc strict`

#### Step 6.2: Custom Exceptions

**File**: `src/captable/exceptions.py`

**Create**:
- `CapTableError` - Base
- `ValidationError`
- `FormulaError`
- `ExcelGenerationError`

#### Step 6.3: Configuration Management

**Directory**: `webapp/backend/config/`

**Create**:
- `settings.py` - Centralized config
- Validation for env vars

---

## Execution Order

**Recommended Sequence**:

1. **Complete Phase 1.1** (Excel Module) - Already started
2. **Phase 1.2** (Formulas) - Builds on Excel
3. **Phase 1.3** (Validation) - Independent
4. **Phase 4.1** (Architecture Docs) - Document as we go
5. **Phase 2** (Web App) - Can parallel with 1
6. **Phase 3** (Frontend) - After 2
7. **Phase 4** (Complete Docs) - Final
8. **Phase 5 & 6** (Quality) - Ongoing

## Verification Checklist

After each phase:

- ✅ All tests pass
- ✅ No linter errors
- ✅ Documentation updated
- ✅ Backward compatibility maintained (where possible)
- ✅ Code review completed
- ✅ Module size < 500 lines

## Next Steps

**Immediate Actions**:

1. Complete remaining Excel generators (ledger, rounds, progression, vesting, waterfall)
2. Extract formulas into specialized modules
3. Update imports throughout codebase
4. Run tests and fix any issues

**Estimated Time**: 2-3 days for Phase 1 completion

**Blockers**: None

**Dependencies**: None (can work in parallel)

