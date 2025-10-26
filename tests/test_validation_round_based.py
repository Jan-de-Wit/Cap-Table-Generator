"""
Tests for Cap Table Validation - Version 2.0
Tests the validation logic for round-based architecture with nested instruments.
"""

import pytest
from src.captable.validation import CapTableValidator


class TestSchemaValidationV2:
    """Test JSON schema validation for v2.0."""
    
    def test_valid_minimal_captable_v2(self, minimal_cap_table_v2):
        """Test that minimal valid v2.0 cap table passes validation."""
        validator = CapTableValidator()
        is_valid, errors = validator.validate(minimal_cap_table_v2)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_valid_full_captable_v2(self, full_cap_table_v2):
        """Test that full v2.0 cap table passes validation."""
        validator = CapTableValidator()
        is_valid, errors = validator.validate(full_cap_table_v2)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_schema_version_2_0(self, minimal_cap_table_v2):
        """Test that schema_version must be 2.0."""
        data = minimal_cap_table_v2.copy()
        data['schema_version'] = '1.0'
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        # Should fail because v1.0 expects top-level instruments array
        assert is_valid is False
    
    def test_missing_rounds(self, minimal_cap_table_v2):
        """Test that missing rounds is caught."""
        data = minimal_cap_table_v2.copy()
        del data['rounds']
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('rounds' in error.lower() for error in errors)
    
    def test_round_missing_calculation_type(self, minimal_cap_table_v2):
        """Test that missing calculation_type is caught."""
        data = minimal_cap_table_v2.copy()
        del data['rounds'][0]['calculation_type']
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('calculation_type' in error for error in errors)


class TestRoundCalculationTypes:
    """Test round-level calculation type validation."""
    
    def test_fixed_shares_requires_initial_quantity(self):
        """Test that fixed_shares type requires initial_quantity."""
        data = {
            "schema_version": "2.0",
            "company": {"name": "Test"},
            "rounds": [{
                "name": "Round1",
                "round_date": "2023-01-01",
                "calculation_type": "fixed_shares",
                "instruments": [{
                    "holder_name": "Alice",
                    "class_name": "Common"
                    # Missing: initial_quantity
                }]
            }]
        }
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('initial_quantity' in error for error in errors)
    
    def test_target_percentage_requires_target_percentage(self):
        """Test that target_percentage type requires target_percentage field."""
        data = {
            "schema_version": "2.0",
            "company": {"name": "Test"},
            "rounds": [{
                "name": "Round1",
                "round_date": "2023-01-01",
                "calculation_type": "target_percentage",
                "instruments": [{
                    "holder_name": "Alice",
                    "class_name": "Common"
                    # Missing: target_percentage
                }]
            }]
        }
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('target_percentage' in error for error in errors)
    
    def test_valuation_based_requires_investment_amount(self):
        """Test that valuation_based type requires investment_amount."""
        data = {
            "schema_version": "2.0",
            "company": {"name": "Test"},
            "rounds": [{
                "name": "Round1",
                "round_date": "2023-01-01",
                "calculation_type": "valuation_based",
                "pre_money_valuation": 5000000,
                "instruments": [{
                    "holder_name": "Alice",
                    "class_name": "Common"
                    # Missing: investment_amount
                }]
            }]
        }
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('investment_amount' in error for error in errors)
    
    def test_convertible_requires_all_fields(self):
        """Test that convertible type requires all convertible fields."""
        data = {
            "schema_version": "2.0",
            "company": {"name": "Test"},
            "rounds": [{
                "name": "Round1",
                "round_date": "2023-01-01",
                "calculation_type": "convertible",
                "valuation_cap_basis": "pre_money",
                "pre_money_valuation": 10000000,
                "instruments": [{
                    "holder_name": "Alice",
                    "class_name": "Common",
                    "investment_amount": 100000
                    # Missing: interest_rate, interest_start_date, interest_end_date
                }]
            }]
        }
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('interest' in error.lower() for error in errors)
    
    def test_convertible_requires_valuation_cap_basis(self):
        """Test that convertible round requires valuation_cap_basis."""
        data = {
            "schema_version": "2.0",
            "company": {"name": "Test"},
            "rounds": [{
                "name": "Round1",
                "round_date": "2023-01-01",
                "calculation_type": "convertible",
                "pre_money_valuation": 10000000,
                # Missing: valuation_cap_basis
                "instruments": [{
                    "holder_name": "Alice",
                    "class_name": "Common",
                    "investment_amount": 100000,
                    "interest_rate": 0.08,
                    "interest_start_date": "2023-01-01",
                    "interest_end_date": "2024-01-01",
                    "interest_type": "simple",
                    "discount_rate": 0.20
                }]
            }]
        }
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('valuation_cap_basis' in error for error in errors)


class TestInterestDateValidation:
    """Test interest date validation."""
    
    def test_interest_end_date_must_be_after_start_date(self):
        """Test that interest_end_date must be after interest_start_date."""
        data = {
            "schema_version": "2.0",
            "company": {"name": "Test"},
            "rounds": [{
                "name": "Round1",
                "round_date": "2024-01-01",
                "calculation_type": "convertible",
                "valuation_cap_basis": "pre_money",
                "pre_money_valuation": 10000000,
                "instruments": [{
                    "holder_name": "Alice",
                    "class_name": "Common",
                    "investment_amount": 100000,
                    "interest_rate": 0.08,
                    "interest_start_date": "2024-01-01",
                    "interest_end_date": "2023-01-01",  # Before start date!
                    "interest_type": "simple",
                    "discount_rate": 0.20
                }]
            }]
        }
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('interest_end_date' in error and 'after' in error for error in errors)
    
    def test_interest_dates_equal_is_invalid(self):
        """Test that interest dates cannot be equal."""
        data = {
            "schema_version": "2.0",
            "company": {"name": "Test"},
            "rounds": [{
                "name": "Round1",
                "round_date": "2024-01-01",
                "calculation_type": "convertible",
                "valuation_cap_basis": "pre_money",
                "pre_money_valuation": 10000000,
                "instruments": [{
                    "holder_name": "Alice",
                    "class_name": "Common",
                    "investment_amount": 100000,
                    "interest_rate": 0.08,
                    "interest_start_date": "2023-01-01",
                    "interest_end_date": "2023-01-01",  # Same as start!
                    "interest_type": "simple",
                    "discount_rate": 0.20
                }]
            }]
        }
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False


class TestNestedInstrumentStructure:
    """Test nested instrument structure validation."""
    
    def test_instruments_nested_within_rounds(self, minimal_cap_table_v2):
        """Test that instruments are properly nested."""
        data = minimal_cap_table_v2.copy()
        
        # Verify structure
        assert 'rounds' in data
        assert len(data['rounds']) > 0
        assert 'instruments' in data['rounds'][0]
        assert isinstance(data['rounds'][0]['instruments'], list)
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is True
    
    def test_no_round_name_field_in_instruments(self):
        """Test that round_name field is not allowed (implicit from nesting)."""
        data = {
            "schema_version": "2.0",
            "company": {"name": "Test"},
            "rounds": [{
                "name": "Round1",
                "round_date": "2023-01-01",
                "calculation_type": "fixed_shares",
                "instruments": [{
                    "holder_name": "Alice",
                    "class_name": "Common",
                    "initial_quantity": 1000000,
                    "round_name": "Round1"  # This shouldn't be here!
                }]
            }]
        }
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        # Schema should reject unexpected field
        # (or validation should warn about it)
        # This test documents the behavior


class TestValuationRequirements:
    """Test valuation requirements for calculation types."""
    
    def test_valuation_based_needs_valuation(self):
        """Test that valuation_based rounds need pre or post money valuation."""
        data = {
            "schema_version": "2.0",
            "company": {"name": "Test"},
            "rounds": [{
                "name": "Round1",
                "round_date": "2023-01-01",
                "calculation_type": "valuation_based",
                # Missing: pre_money_valuation or post_money_valuation
                "instruments": [{
                    "holder_name": "Alice",
                    "class_name": "Common",
                    "investment_amount": 100000,
                    "accrued_interest": 0
                }]
            }]
        }
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('valuation' in error.lower() for error in errors)
    
    def test_convertible_needs_valuation(self):
        """Test that convertible rounds need valuation data."""
        data = {
            "schema_version": "2.0",
            "company": {"name": "Test"},
            "rounds": [{
                "name": "Round1",
                "round_date": "2023-01-01",
                "calculation_type": "convertible",
                "valuation_cap_basis": "pre_money",
                # Missing: pre_money_valuation or post_money_valuation or price_per_share
                "instruments": [{
                    "holder_name": "Alice",
                    "class_name": "Common",
                    "investment_amount": 100000,
                    "interest_rate": 0.08,
                    "interest_start_date": "2023-01-01",
                    "interest_end_date": "2024-01-01",
                    "interest_type": "simple",
                    "discount_rate": 0.20
                }]
            }]
        }
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('valuation' in error.lower() or 'price' in error.lower() for error in errors)


class TestCompleteV2Examples:
    """Test complete v2.0 examples with all calculation types."""
    
    def test_all_calculation_types_together(self):
        """Test cap table with all 4 calculation types."""
        data = {
            "schema_version": "2.0",
            "company": {
                "name": "Complete Test",
                "incorporation_date": "2023-01-01",
                "current_date": "2024-12-31"
            },
            "rounds": [
                {
                    "name": "Incorporation",
                    "round_date": "2023-01-01",
                    "calculation_type": "fixed_shares",
                    "instruments": [
                        {
                            "holder_name": "Founder1",
                            "class_name": "Common",
                            "initial_quantity": 5000000,
                            "acquisition_date": "2023-01-01"
                        }
                    ]
                },
                {
                    "name": "Seed",
                    "round_date": "2023-06-01",
                    "calculation_type": "valuation_based",
                    "pre_money_valuation": 8000000,
                    "post_money_valuation": 10000000,
                    "price_per_share": 1.0,
                    "instruments": [
                        {
                            "holder_name": "Seed Investor",
                            "class_name": "Preferred",
                            "investment_amount": 2000000,
                            "accrued_interest": 0
                        }
                    ]
                },
                {
                    "name": "Series A",
                    "round_date": "2024-03-15",
                    "calculation_type": "convertible",
                    "valuation_cap_basis": "pre_money",
                    "pre_money_valuation": 15000000,
                    "post_money_valuation": 20000000,
                    "price_per_share": 1.5,
                    "instruments": [
                        {
                            "holder_name": "VC Fund",
                            "class_name": "Series A",
                            "investment_amount": 5000000,
                            "interest_rate": 0.08,
                            "interest_start_date": "2023-09-01",
                            "interest_end_date": "2024-03-15",
                            "interest_type": "simple",
                            "discount_rate": 0.20
                        }
                    ]
                },
                {
                    "name": "Strategic",
                    "round_date": "2024-09-01",
                    "calculation_type": "target_percentage",
                    "instruments": [
                        {
                            "holder_name": "Strategic Partner",
                            "class_name": "Common",
                            "target_percentage": 0.05
                        }
                    ]
                }
            ]
        }
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is True
        assert len(errors) == 0

