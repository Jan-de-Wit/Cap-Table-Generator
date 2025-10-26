"""
Tests for Cap Table Validation
Tests the validation logic for JSON schema compliance and business rules.
"""

import pytest
from src.captable.validation import CapTableValidator


class TestSchemaValidation:
    """Test JSON schema validation."""
    
    def test_valid_minimal_captable(self, minimal_cap_table):
        """Test that minimal valid cap table passes validation."""
        validator = CapTableValidator()
        is_valid, errors = validator.validate(minimal_cap_table)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_valid_full_captable(self, full_cap_table):
        """Test that full cap table passes validation."""
        validator = CapTableValidator()
        is_valid, errors = validator.validate(full_cap_table)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_missing_schema_version(self, minimal_cap_table):
        """Test that missing schema_version is caught."""
        data = minimal_cap_table.copy()
        del data['schema_version']
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('schema_version' in error for error in errors)
    
    def test_invalid_schema_version(self, minimal_cap_table):
        """Test that invalid schema_version is caught."""
        data = minimal_cap_table.copy()
        data['schema_version'] = '99.0'
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
    
    def test_missing_company(self, minimal_cap_table):
        """Test that missing company is caught."""
        data = minimal_cap_table.copy()
        del data['company']
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('company' in error for error in errors)
    
    def test_missing_holders(self, minimal_cap_table):
        """Test that missing holders is caught."""
        data = minimal_cap_table.copy()
        del data['holders']
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('holders' in error for error in errors)
    
    def test_missing_classes(self, minimal_cap_table):
        """Test that missing classes is caught."""
        data = minimal_cap_table.copy()
        del data['classes']
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('classes' in error for error in errors)
    
    def test_missing_instruments(self, minimal_cap_table):
        """Test that missing instruments is caught."""
        data = minimal_cap_table.copy()
        del data['instruments']
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('instruments' in error for error in errors)


class TestHolderValidation:
    """Test holder validation."""
    
    def test_holder_without_name(self, minimal_cap_table):
        """Test that holder without name is caught."""
        data = minimal_cap_table.copy()
        data['holders'][0] = {"type": "founder"}  # Missing name
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('name' in error for error in errors)
    
    def test_holder_without_type(self, minimal_cap_table):
        """Test that holder without type is caught."""
        data = minimal_cap_table.copy()
        data['holders'][0] = {"name": "Test"}  # Missing type
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('type' in error for error in errors)
    
    def test_holder_invalid_type(self, minimal_cap_table):
        """Test that invalid holder type is caught."""
        data = minimal_cap_table.copy()
        data['holders'][0]['type'] = 'invalid_type'
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False


class TestClassValidation:
    """Test security class validation."""
    
    def test_class_without_name(self, minimal_cap_table):
        """Test that class without name is caught."""
        data = minimal_cap_table.copy()
        data['classes'][0] = {"type": "common"}  # Missing name
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('name' in error for error in errors)
    
    def test_class_without_type(self, minimal_cap_table):
        """Test that class without type is caught."""
        data = minimal_cap_table.copy()
        data['classes'][0] = {"name": "Test"}  # Missing type
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('type' in error for error in errors)
    
    def test_class_invalid_type(self, minimal_cap_table):
        """Test that invalid class type is caught."""
        data = minimal_cap_table.copy()
        data['classes'][0]['type'] = 'invalid_type'
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False


class TestInstrumentValidation:
    """Test instrument validation."""
    
    def test_instrument_without_holder_name(self, minimal_cap_table):
        """Test that instrument without holder_name is caught."""
        data = minimal_cap_table.copy()
        del data['instruments'][0]['holder_name']
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('holder_name' in error for error in errors)
    
    def test_instrument_without_class_name(self, minimal_cap_table):
        """Test that instrument without class_name is caught."""
        data = minimal_cap_table.copy()
        del data['instruments'][0]['class_name']
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('class_name' in error for error in errors)
    
    def test_instrument_invalid_holder_reference(self, minimal_cap_table):
        """Test that invalid holder_name reference is caught."""
        data = minimal_cap_table.copy()
        data['instruments'][0]['holder_name'] = 'NonExistentHolder'
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('NonExistentHolder' in error for error in errors)
    
    def test_instrument_invalid_class_reference(self, minimal_cap_table):
        """Test that invalid class_name reference is caught."""
        data = minimal_cap_table.copy()
        data['instruments'][0]['class_name'] = 'NonExistentClass'
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('NonExistentClass' in error for error in errors)
    
    def test_instrument_invalid_round_reference(self, full_cap_table):
        """Test that invalid round_name reference is caught."""
        data = full_cap_table.copy()
        data['instruments'][1]['round_name'] = 'NonExistentRound'
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('NonExistentRound' in error for error in errors)


class TestNameUniqueness:
    """Test name uniqueness validation."""
    
    def test_duplicate_holder_names(self, minimal_cap_table):
        """Test that duplicate holder names are caught."""
        data = minimal_cap_table.copy()
        data['holders'].append(data['holders'][0].copy())  # Duplicate
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('duplicate' in error.lower() or 'unique' in error.lower() for error in errors)
    
    def test_duplicate_class_names(self, minimal_cap_table):
        """Test that duplicate class names are caught."""
        data = minimal_cap_table.copy()
        data['classes'].append(data['classes'][0].copy())  # Duplicate
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('duplicate' in error.lower() or 'unique' in error.lower() for error in errors)
    
    def test_duplicate_round_names(self, full_cap_table):
        """Test that duplicate round names are caught."""
        data = full_cap_table.copy()
        data['rounds'].append(data['rounds'][0].copy())  # Duplicate
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('duplicate' in error.lower() or 'unique' in error.lower() for error in errors)


class TestValuationCalculations:
    """Test valuation-based calculation validation."""
    
    def test_instrument_with_investment_amount(self):
        """Test that instrument with investment_amount and valuation_basis is valid."""
        data = {
            "schema_version": "1.0",
            "company": {"name": "Test", "current_date": "2024-01-01"},
            "holders": [
                {"name": "Alice", "type": "founder"},
                {"name": "Bob", "type": "investor"}
            ],
            "classes": [
                {"name": "Common", "type": "common"},
                {"name": "Preferred", "type": "preferred"}
            ],
            "rounds": [
                {
                    "name": "Seed",
                    "round_date": "2023-06-01",
                    "pre_money_valuation": 1000000
                }
            ],
            "instruments": [
                {
                    "holder_name": "Alice",
                    "class_name": "Common",
                    "initial_quantity": 1000000,
                    "acquisition_date": "2023-01-01"
                },
                {
                    "holder_name": "Bob",
                    "class_name": "Preferred",
                    "round_name": "Seed",
                    "investment_amount": 100000,
                    "valuation_basis": "pre_money",
                    "acquisition_date": "2023-06-01"
                }
            ]
        }
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is True, f"Validation failed: {errors}"
    
    def test_instrument_missing_quantity_and_investment(self, minimal_cap_table):
        """Test that instrument without initial_quantity or investment_amount is caught."""
        data = minimal_cap_table.copy()
        # Remove initial_quantity, don't provide investment_amount
        del data['instruments'][0]['initial_quantity']
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
    
    def test_investment_without_valuation_basis(self, full_cap_table):
        """Test that investment_amount without valuation_basis is caught."""
        data = full_cap_table.copy()
        data['instruments'].append({
            "holder_name": "Bob",
            "class_name": "Preferred",
            "round_name": "Seed",
            "investment_amount": 100000,
            # Missing valuation_basis
            "acquisition_date": "2023-06-01"
        })
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False


class TestTermsValidation:
    """Test terms validation."""
    
    def test_terms_without_name(self, full_cap_table):
        """Test that terms without name is caught."""
        data = full_cap_table.copy()
        del data['terms'][0]['name']
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
    
    def test_class_references_nonexistent_terms(self):
        """Test that class referencing nonexistent terms is caught."""
        data = {
            "schema_version": "1.0",
            "company": {"name": "Test", "current_date": "2024-01-01"},
            "holders": [
                {"name": "Alice", "type": "founder"}
            ],
            "classes": [
                {"name": "Common", "type": "common", "terms_name": "NonExistentTerms"}
            ],
            "terms": [
                {"name": "StandardTerms", "class_name": "Preferred"}
            ],
            "instruments": [
                {
                    "holder_name": "Alice",
                    "class_name": "Common",
                    "initial_quantity": 1000000,
                    "acquisition_date": "2023-01-01"
                }
            ]
        }
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
        assert any('NonExistentTerms' in error for error in errors)


class TestVestingTermsValidation:
    """Test vesting terms validation."""
    
    def test_valid_vesting_terms(self, complex_cap_table):
        """Test that valid vesting terms pass validation."""
        validator = CapTableValidator()
        is_valid, errors = validator.validate(complex_cap_table)
        
        assert is_valid is True
    
    def test_vesting_terms_missing_grant_date(self, complex_cap_table):
        """Test that vesting terms without grant_date is caught."""
        data = complex_cap_table.copy()
        # Find instrument with vesting terms
        for inst in data['instruments']:
            if 'vesting_terms' in inst:
                del inst['vesting_terms']['grant_date']
                break
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False
    
    def test_vesting_terms_negative_cliff(self, complex_cap_table):
        """Test that negative cliff_days is caught."""
        data = complex_cap_table.copy()
        # Find instrument with vesting terms
        for inst in data['instruments']:
            if 'vesting_terms' in inst:
                inst['vesting_terms']['cliff_days'] = -1
                break
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False


class TestRoundValidation:
    """Test round validation."""
    
    def test_valid_round(self, full_cap_table):
        """Test that valid round passes validation."""
        validator = CapTableValidator()
        is_valid, errors = validator.validate(full_cap_table)
        
        assert is_valid is True
    
    def test_round_without_name(self, full_cap_table):
        """Test that round without name is caught."""
        data = full_cap_table.copy()
        del data['rounds'][0]['name']
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is False


class TestEdgeCases:
    """Test edge cases in validation."""
    
    def test_empty_holders_list(self):
        """Test that empty holders list passes validation."""
        data = {
            "schema_version": "1.0",
            "company": {"name": "Test"},
            "holders": [],
            "classes": [{"name": "Common", "type": "common"}],
            "instruments": []
        }
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        # Empty lists are valid
        assert is_valid is True
    
    def test_special_characters_in_names(self, minimal_cap_table):
        """Test that special characters in names are handled."""
        data = minimal_cap_table.copy()
        data['holders'][0]['name'] = "O'Brien & Associates"
        data['instruments'][0]['holder_name'] = "O'Brien & Associates"
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is True
    
    def test_unicode_in_names(self, minimal_cap_table):
        """Test that unicode characters in names are handled."""
        data = minimal_cap_table.copy()
        data['holders'][0]['name'] = "José García"
        data['instruments'][0]['holder_name'] = "José García"
        
        validator = CapTableValidator()
        is_valid, errors = validator.validate(data)
        
        assert is_valid is True

