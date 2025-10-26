# Cap Table Generator - Testing Suite

Comprehensive testing suite for JSON to Excel cap table generation, including tests for formula linking, validation, and integration flows.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Quick Start](#quick-start)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Writing New Tests](#writing-new-tests)
- [Coverage](#coverage)
- [Continuous Integration](#continuous-integration)

---

## Overview

This testing suite provides comprehensive coverage for:
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end JSON → Excel workflows
- **Validation Tests**: Schema compliance and business rules
- **Formula Tests**: Excel formula generation and linking
- **Edge Cases**: Boundary conditions and error handling

### Test Statistics

| Category | Test Files | Test Count | Coverage |
|----------|-----------|------------|----------|
| Unit Tests | `test_excel_generator.py` | 40+ | Components |
| Integration | `test_integration.py` | 30+ | Full Flow |
| Validation | `test_validation.py` | 35+ | Schema |
| Total | 3 files | 105+ tests | ~85%+ |

---

## Test Structure

```
tests/
├── README.md                    # This file
├── requirements-test.txt        # Testing dependencies
├── conftest.py                  # Shared fixtures and utilities
├── test_excel_generator.py      # Unit tests for Excel generator
├── test_integration.py          # Integration tests
├── test_validation.py           # Validation logic tests
└── __pycache__/                 # Python cache (ignored)
```

### Key Files

**`conftest.py`**
- Shared pytest fixtures
- Helper utilities (`ExcelHelper` class)
- Test data factories
- Common assertions

**`test_excel_generator.py`**
- Unit tests for `ExcelGenerator` class
- Master sheet creation tests
- Formula linking tests
- Data validation tests

**`test_integration.py`**
- End-to-end generation tests
- Multi-sheet consistency tests
- Performance tests
- Error handling tests

**`test_validation.py`**
- Schema validation tests
- Business rule validation
- Referential integrity tests
- Edge case validation

---

## Quick Start

### 1. Install Testing Dependencies

```bash
# From project root
pip install -r tests/requirements-test.txt
```

### 2. Run All Tests

```bash
pytest
```

### 3. Run with Coverage

```bash
pytest --cov=src/captable --cov-report=html
```

### 4. View Coverage Report

```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

---

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_excel_generator.py

# Run specific test class
pytest tests/test_excel_generator.py::TestExcelGeneratorMasterSheets

# Run specific test function
pytest tests/test_excel_generator.py::TestExcelGeneratorMasterSheets::test_holders_sheet_creation

# Run tests matching pattern
pytest -k "formula"
```

### Advanced Commands

```bash
# Run tests in parallel (faster)
pytest -n auto

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l

# Run only failed tests from last run
pytest --lf

# Run failed tests first, then all
pytest --ff

# Run with coverage and missing lines
pytest --cov=src/captable --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=src/captable --cov-report=html

# Run with timeout (300 seconds)
pytest --timeout=300

# Run and show print statements
pytest -s
```

### Test Markers

Tests are categorized with markers for selective execution:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only validation tests
pytest -m validation

# Run only formula tests
pytest -m formula

# Exclude slow tests
pytest -m "not slow"

# Run multiple categories
pytest -m "unit or integration"
```

---

## Test Categories

### 1. Unit Tests (`test_excel_generator.py`)

Tests individual components of the Excel generator.

**Test Classes:**
- `TestExcelGeneratorInit` - Initialization tests
- `TestExcelGeneratorMasterSheets` - Master sheet creation
- `TestExcelGeneratorSummarySheet` - Summary sheet tests
- `TestExcelGeneratorLedgerSheet` - Ledger sheet and formulas
- `TestExcelGeneratorRoundsSheet` - Rounds sheet tests
- `TestExcelGeneratorWaterfallSheet` - Waterfall analysis
- `TestExcelGeneratorCapTableProgression` - Cap table progression
- `TestExcelGeneratorVestingSheet` - Vesting calculations
- `TestExcelGeneratorFormats` - Cell formatting
- `TestExcelGeneratorEdgeCases` - Edge cases

**Example:**
```python
def test_holders_sheet_creation(full_cap_table, temp_dir, excel_helper):
    """Test that Holders sheet is created correctly."""
    output_path = temp_dir / "test.xlsx"
    generator = ExcelGenerator(full_cap_table, str(output_path))
    generator.generate()
    
    assert excel_helper.sheet_exists(output_path, 'Holders')
    assert_table_exists(output_path, 'Holders')
```

### 2. Integration Tests (`test_integration.py`)

Tests complete JSON → Excel workflows.

**Test Classes:**
- `TestEndToEndGeneration` - Full generation flow
- `TestFormulaLinking` - Formula linking verification
- `TestDataConsistency` - Cross-sheet consistency
- `TestTableStructures` - Excel table creation
- `TestNamedRanges` - Named range creation
- `TestDataValidation` - Data validation rules
- `TestMultiRoundScenarios` - Multiple rounds
- `TestVestingCalculations` - Vesting formulas
- `TestWaterfallScenarios` - Waterfall analysis
- `TestErrorHandling` - Error conditions
- `TestPerformance` - Performance with large datasets

**Example:**
```python
def test_generate_from_json_file(sample_json_file, temp_dir):
    """Test generating Excel from JSON file."""
    output_path = temp_dir / "output.xlsx"
    result = generate_from_json(str(sample_json_file), str(output_path))
    
    assert Path(result).exists()
    assert_excel_structure(output_path, [
        'Holders', 'Classes', 'Terms', 'Summary', 'Ledger'
    ])
```

### 3. Validation Tests (`test_validation.py`)

Tests JSON schema and business rule validation.

**Test Classes:**
- `TestSchemaValidation` - JSON schema compliance
- `TestHolderValidation` - Holder validation rules
- `TestClassValidation` - Security class validation
- `TestInstrumentValidation` - Instrument validation
- `TestNameUniqueness` - Name uniqueness checks
- `TestValuationCalculations` - Valuation logic
- `TestTermsValidation` - Terms validation
- `TestVestingTermsValidation` - Vesting rules
- `TestRoundValidation` - Round validation
- `TestEdgeCases` - Edge case validation

**Example:**
```python
def test_invalid_holder_reference(minimal_cap_table):
    """Test that invalid holder_name reference is caught."""
    data = minimal_cap_table.copy()
    data['instruments'][0]['holder_name'] = 'NonExistentHolder'
    
    validator = CapTableValidator()
    is_valid, errors = validator.validate(data)
    
    assert is_valid is False
    assert any('NonExistentHolder' in error for error in errors)
```

---

## Writing New Tests

### Test Template

```python
def test_my_feature(fixture1, fixture2, excel_helper):
    """
    Test description goes here.
    
    This test verifies that [specific behavior].
    """
    # Arrange
    data = fixture1.copy()
    output_path = fixture2 / "test.xlsx"
    
    # Act
    result = do_something(data, output_path)
    
    # Assert
    assert result is not None
    assert excel_helper.sheet_exists(output_path, 'SheetName')
```

### Using Fixtures

Available fixtures (see `conftest.py`):
- `temp_dir` - Temporary directory for test outputs
- `simple_holders` - Simple holder data
- `simple_classes` - Simple class data
- `simple_terms` - Simple terms data
- `simple_instruments` - Simple instrument data
- `simple_rounds` - Simple round data
- `minimal_cap_table` - Minimal valid cap table
- `full_cap_table` - Full cap table with all sections
- `complex_cap_table` - Complex cap table with multiple rounds
- `excel_helper` - Excel file inspection utilities
- `sample_json_file` - Sample JSON file

**Example:**
```python
def test_with_fixtures(full_cap_table, temp_dir, excel_helper):
    # full_cap_table provides complete test data
    # temp_dir provides temporary directory
    # excel_helper provides inspection utilities
    pass
```

### Using ExcelHelper

```python
# Check if sheet exists
excel_helper.sheet_exists(file_path, 'SheetName')

# Get cell value
value = excel_helper.get_cell_value(file_path, 'Sheet', 'A1')

# Get cell formula
formula = excel_helper.get_cell_formula(file_path, 'Sheet', 'B2')

# Check if cell has formula
excel_helper.is_formula(file_path, 'Sheet', 'C3')

# Check if table exists
excel_helper.table_exists(file_path, 'TableName')

# Check if named range exists
excel_helper.named_range_exists(file_path, 'NamedRange')

# Get data validations
validations = excel_helper.get_data_validations(file_path, 'Sheet')
```

### Custom Assertions

```python
# Assert Excel structure
assert_excel_structure(file_path, ['Sheet1', 'Sheet2'])

# Assert formula exists
assert_formula_in_cell(file_path, 'Sheet', 'A1', 'XLOOKUP')

# Assert table exists
assert_table_exists(file_path, 'TableName')

# Assert named range exists
assert_named_range_exists(file_path, 'RangeName')
```

---

## Coverage

### Running Coverage

```bash
# Generate coverage report
pytest --cov=src/captable --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

### Coverage Goals

| Component | Target | Current |
|-----------|--------|---------|
| excel.py | 90%+ | TBD |
| validation.py | 95%+ | TBD |
| formulas.py | 85%+ | TBD |
| generator.py | 90%+ | TBD |
| Overall | 85%+ | TBD |

### Improving Coverage

1. **Identify gaps:**
```bash
pytest --cov=src/captable --cov-report=term-missing
```

2. **Focus on uncovered lines:**
   - Look for lines with `!` in coverage report
   - Write tests specifically for those lines

3. **Test error paths:**
   - Test exception handling
   - Test validation failures
   - Test edge cases

---

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', 3.11]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r tests/requirements-test.txt
    
    - name: Run tests with coverage
      run: |
        pytest --cov=src/captable --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

---

## Troubleshooting

### Common Issues

**Issue: `ModuleNotFoundError: No module named 'src'`**

Solution: Run tests from project root, not from `tests/` directory:
```bash
cd /path/to/project/root
pytest
```

**Issue: `openpyxl` not found**

Solution: Install test requirements:
```bash
pip install -r tests/requirements-test.txt
```

**Issue: Tests fail with "file not found"**

Solution: Ensure you're using `temp_dir` fixture for output files:
```python
def test_example(temp_dir):
    output_path = temp_dir / "test.xlsx"  # Use temp_dir, not hardcoded path
```

**Issue: Formula tests fail**

Solution: Formulas may vary slightly. Test for presence of key functions:
```python
formula = excel_helper.get_cell_formula(path, 'Sheet', 'A1')
assert 'XLOOKUP' in formula  # Don't test exact formula string
```

---

## Best Practices

### 1. Test Independence
- Each test should be independent
- Use fixtures, not global state
- Clean up after tests (automatic with `temp_dir`)

### 2. Descriptive Names
```python
# Good
def test_holder_type_uses_xlookup_formula():
    pass

# Bad
def test_ht():
    pass
```

### 3. Clear Assertions
```python
# Good
assert excel_helper.sheet_exists(path, 'Holders'), \
    "Holders sheet should be created"

# Bad
assert True
```

### 4. Test One Thing
```python
# Good - tests one specific behavior
def test_holders_sheet_has_correct_headers():
    assert header1 == expected1
    assert header2 == expected2

# Bad - tests multiple unrelated things
def test_everything():
    assert sheets_exist
    assert formulas_work
    assert validation_passes
```

### 5. Use Parameterization for Similar Tests
```python
@pytest.mark.parametrize("holder_type", [
    "founder", "investor", "employee", "advisor"
])
def test_valid_holder_types(holder_type):
    # Test all valid holder types with one test function
    pass
```

---

## Contributing

When adding new features:

1. **Write tests first** (TDD approach)
2. **Maintain coverage** above 85%
3. **Add fixtures** to `conftest.py` if reusable
4. **Update documentation** in this README
5. **Run full test suite** before committing

```bash
# Before committing
pytest --cov=src/captable --cov-report=term-missing
```

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [openpyxl Documentation](https://openpyxl.readthedocs.io/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

---

## Questions?

For questions or issues with tests:
1. Check this README
2. Review `conftest.py` for available fixtures
3. Look at existing tests for examples
4. Run with `-vv` for detailed output

---

**Last Updated:** October 26, 2025  
**Test Suite Version:** 1.0  
**Python Version:** 3.8+

