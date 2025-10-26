# Testing Guide

## Test Structure

```
tests/
├── test_cap_table.py           # Core library tests
├── test_excel_generator.py      # Excel generation tests
├── test_integration.py          # Integration tests
└── test_validation.py           # Validation tests
```

## Running Tests

### All Tests

```bash
pytest tests/
```

### Specific Test File

```bash
pytest tests/test_cap_table.py -v
```

### Specific Test

```bash
pytest tests/test_cap_table.py::TestSchemaValidation -v
```

### With Coverage

```bash
pytest tests/ --cov=src --cov=webapp --cov-report=html
```

### Quick Tests

```bash
pytest tests/ -v -x  # Stop on first failure
pytest tests/ -v -k "test_excel"  # Run tests matching pattern
```

## Test Types

### Unit Tests

Test individual components in isolation:

```python
def test_ownership_formula():
    resolver = FormulaResolver()
    formula = resolver.create_ownership_formula(
        current_shares=1000,
        fully_diluted=2000
    )
    assert formula == "=1000/2000"
```

### Integration Tests

Test component interactions:

```python
def test_excel_generation_end_to_end():
    data = load_test_data("simple_captable.json")
    generator = CapTableGenerator(data)
    result = generator.generate()
    assert result is not None
    assert "Summary" in result.sheets
```

### Performance Tests

```python
def test_excel_generation_performance(benchmark):
    data = load_test_data("complex_captable.json")
    result = benchmark(generate_from_data, data, temp_path)
    assert result
```

## Writing Tests

### Test Structure

```python
import pytest
from src.captable.generator import CapTableGenerator

class TestCapTableGenerator:
    """Test suite for CapTableGenerator."""
    
    def test_initialization_with_data(self, test_data):
        """Test generator initialization with valid data."""
        generator = CapTableGenerator(test_data)
        assert generator.data == test_data
    
    def test_validation_requires_data(self):
        """Test that validation fails without data."""
        with pytest.raises(ValueError):
            CapTableGenerator(None)
```

### Using Fixtures

```python
@pytest.fixture
def sample_captable():
    return {
        "schema_version": "1.0",
        "company": {"name": "Test Corp"},
        "holders": [...],
        ...
    }

def test_with_fixture(sample_captable):
    generator = CapTableGenerator(sample_captable)
    # Use sample_captable in test
```

### Testing Exceptions

```python
def test_handles_invalid_data():
    data = {"invalid": "data"}
    with pytest.raises(ValidationError) as exc_info:
        validate_cap_table(data)
    assert "schema_version" in str(exc_info.value)
```

## Test Data

### Loading Test Data

```python
import json
from pathlib import Path

def load_test_json(filename):
    """Load test data from examples/ directory."""
    path = Path("examples") / filename
    with open(path) as f:
        return json.load(f)

def test_with_example_data():
    data = load_test_json("sample_simple_captable.json")
    generator = CapTableGenerator(data)
    # Test with real-world data
```

## Best Practices

1. **Isolate Tests**: Each test should be independent
2. **Clear Names**: Test names should describe what they test
3. **AAA Pattern**: Arrange, Act, Assert
4. **Fast Tests**: Keep unit tests fast (<1s)
5. **Real Data**: Use real-world data when possible
6. **Edge Cases**: Test boundaries and error conditions
7. **Mock External**: Mock external services and APIs

## Coverage Goals

- Core Library: >90%
- Web App: >80%
- Critical Paths: 100%

Check coverage:
```bash
pytest --cov=src --cov-report=term-missing
```

## Continuous Integration

Tests run automatically on:
- Every commit
- Pull requests
- Nightly builds

See `.github/workflows/` for CI configuration.

