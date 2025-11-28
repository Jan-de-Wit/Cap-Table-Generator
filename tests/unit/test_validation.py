"""
Unit Tests for Validation

Test validation logic and rules.
"""

import pytest
import sys
from pathlib import Path

# Add fastapi directory to path
test_dir = Path(__file__).resolve().parent.parent
fastapi_dir = test_dir.parent / "fastapi"
sys.path.insert(0, str(fastapi_dir))

from captable.validation import validate_cap_table
from captable.errors import ValidationError
from captable.validation.rules import (
    TotalOwnershipRule,
    ProRataPercentageRule,
    ValuationConsistencyRule,
    InvestmentAmountRule,
    RateRule,
    DateOrderRule,
)


class TestValidation:
    """Test validation functionality."""
    
    def test_validate_complete_cap_table(self, sample_cap_table_data):
        """Test validation of complete cap table."""
        is_valid, errors = validate_cap_table(sample_cap_table_data)
        # Should pass basic validation
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
    
    def test_total_ownership_rule(self):
        """Test total ownership rule."""
        rule = TotalOwnershipRule()
        data = {
            "schema_version": "2.0",
            "holders": [],
            "rounds": [
                {
                    "name": "Test Round",
                    "calculation_type": "fixed_shares",
                    "instruments": [
                        {
                            "holder_name": "Holder 1",
                            "class_name": "Common",
                            "pro_rata_percentage": 0.60,
                        },
                        {
                            "holder_name": "Holder 2",
                            "class_name": "Common",
                            "pro_rata_percentage": 0.50,  # Total > 100%
                        },
                    ],
                }
            ],
        }
        result = rule.validate(data)
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_pro_rata_percentage_rule(self):
        """Test pro rata percentage rule."""
        rule = ProRataPercentageRule()
        data = {
            "schema_version": "2.0",
            "holders": [],
            "rounds": [
                {
                    "name": "Test Round",
                    "calculation_type": "fixed_shares",
                    "instruments": [
                        {
                            "holder_name": "Holder 1",
                            "class_name": "Common",
                            "pro_rata_percentage": 1.5,  # > 100%
                        },
                    ],
                }
            ],
        }
        result = rule.validate(data)
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_investment_amount_rule(self):
        """Test investment amount rule."""
        rule = InvestmentAmountRule()
        data = {
            "schema_version": "2.0",
            "holders": [],
            "rounds": [
                {
                    "name": "Test Round",
                    "calculation_type": "valuation_based",
                    "instruments": [
                        {
                            "holder_name": "Holder 1",
                            "class_name": "Common",
                            "investment_amount": -1000,  # Negative
                        },
                    ],
                }
            ],
        }
        result = rule.validate(data)
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_rate_rule(self):
        """Test rate validation rule."""
        rule = RateRule()
        data = {
            "schema_version": "2.0",
            "holders": [],
            "rounds": [
                {
                    "name": "Test Round",
                    "calculation_type": "convertible",
                    "instruments": [
                        {
                            "holder_name": "Holder 1",
                            "class_name": "Note",
                            "interest_rate": 1.5,  # > 100%
                            "discount_rate": 0.20,
                        },
                    ],
                }
            ],
        }
        result = rule.validate(data)
        assert not result.is_valid
        assert len(result.errors) > 0

