"""
Unit tests for cap table validation
"""

import sys
import os
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.captable.validation import validate_cap_table


def test_valid_minimal_cap_table():
    """Test that a minimal valid cap table passes validation."""
    cap_table = {
        "schema_version": "1.0",
        "company": {
            "name": "Test Company"
        },
        "holders": [],
        "classes": [],
        "instruments": []
    }
    
    is_valid, errors = validate_cap_table(cap_table)
    assert is_valid, f"Validation failed: {errors}"
    assert len(errors) == 0


def test_missing_required_fields():
    """Test that missing required fields are caught."""
    cap_table = {
        "schema_version": "1.0",
        "company": {
            "name": "Test Company"
        }
        # Missing holders, classes, instruments
    }
    
    is_valid, errors = validate_cap_table(cap_table)
    assert not is_valid
    assert len(errors) > 0


def test_invalid_holder_type():
    """Test that invalid holder types are caught."""
    cap_table = {
        "schema_version": "1.0",
        "company": {
            "name": "Test Company"
        },
        "holders": [{
            "holder_id": "12345678-1234-1234-1234-123456789012",
            "name": "John Doe",
            "type": "invalid_type"  # Invalid
        }],
        "classes": [],
        "instruments": []
    }
    
    is_valid, errors = validate_cap_table(cap_table)
    assert not is_valid
    assert any("type" in str(error).lower() for error in errors)


def test_valid_cap_table_with_data():
    """Test a valid cap table with actual data."""
    cap_table = {
        "schema_version": "1.0",
        "company": {
            "name": "Test Company",
            "current_pps": 1.0
        },
        "holders": [{
            "holder_id": "12345678-1234-1234-1234-123456789012",
            "name": "John Doe",
            "type": "founder"
        }],
        "classes": [{
            "class_id": "87654321-4321-4321-4321-210987654321",
            "name": "Common Stock",
            "type": "common"
        }],
        "instruments": [{
            "instrument_id": "11111111-1111-1111-1111-111111111111",
            "holder_id": "12345678-1234-1234-1234-123456789012",
            "class_id": "87654321-4321-4321-4321-210987654321",
            "initial_quantity": 1000000
        }]
    }
    
    is_valid, errors = validate_cap_table(cap_table)
    assert is_valid, f"Validation failed: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

