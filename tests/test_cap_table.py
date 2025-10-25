"""
Test Suite for Cap Table Generator
Comprehensive tests for validation, formula generation, and Excel output.
"""

import pytest
import json
import os
from pathlib import Path
from src.captable import (
    validate_cap_table, CapTableValidator,
    DeterministicLayoutMap, ExcelReference,
    FormulaResolver,
    CapTableGenerator, generate_from_data
)
from sample_data_generator import generate_simple_captable, generate_complex_captable


class TestSchemaValidation:
    """Test JSON schema validation."""
    
    def test_valid_simple_captable(self):
        """Test that simple cap table passes validation."""
        data = generate_simple_captable()
        is_valid, errors = validate_cap_table(data)
        assert is_valid, f"Validation failed: {errors}"
        assert len(errors) == 0
    
    def test_valid_complex_captable(self):
        """Test that complex cap table passes validation."""
        data = generate_complex_captable()
        is_valid, errors = validate_cap_table(data)
        assert is_valid, f"Validation failed: {errors}"
        assert len(errors) == 0
    
    def test_missing_required_field(self):
        """Test that missing required fields are caught."""
        data = {
            "schema_version": "1.0",
            "company": {"name": "Test"},
            "holders": [],
            "classes": []
            # Missing 'instruments' - required field
        }
        is_valid, errors = validate_cap_table(data)
        assert not is_valid
        assert len(errors) > 0
    
    def test_invalid_uuid_format(self):
        """Test that invalid UUID format is caught."""
        data = generate_simple_captable()
        data['holders'][0]['holder_id'] = "not-a-valid-uuid"
        is_valid, errors = validate_cap_table(data)
        assert not is_valid
        # Just verify we got an error, the specific message format may vary
        assert len(errors) > 0
    
    def test_broken_foreign_key(self):
        """Test that broken foreign key relationships are caught."""
        data = generate_simple_captable()
        # Reference non-existent holder
        data['instruments'][0]['holder_id'] = "00000000-0000-0000-0000-000000000000"
        is_valid, errors = validate_cap_table(data)
        assert not is_valid
        assert any('not found' in error for error in errors)
    
    def test_duplicate_uuid(self):
        """Test that duplicate UUIDs are caught."""
        data = generate_simple_captable()
        # Duplicate holder ID
        data['holders'][1]['holder_id'] = data['holders'][0]['holder_id']
        is_valid, errors = validate_cap_table(data)
        assert not is_valid
        assert any('Duplicate' in error for error in errors)


class TestDeterministicLayoutMap:
    """Test Deterministic Layout Map functionality."""
    
    def test_named_range_registration(self):
        """Test named range registration and resolution."""
        dlm = DeterministicLayoutMap()
        name = dlm.register_named_range('Total_FDS', 'Summary', 5, 1)
        assert name == 'Total_FDS'
        
        ref = dlm.resolve_reference('Total_FDS')
        assert ref == 'Total_FDS'
    
    def test_table_registration(self):
        """Test Excel table registration."""
        dlm = DeterministicLayoutMap()
        columns = ['col1', 'col2', 'col3']
        dlm.register_table('TestTable', 'Sheet1', 0, 0, columns)
        
        assert 'TestTable' in dlm.tables
        assert dlm.tables['TestTable']['columns'] == {'col1': 0, 'col2': 1, 'col3': 2}
    
    def test_structured_reference_generation(self):
        """Test structured reference generation."""
        dlm = DeterministicLayoutMap()
        columns = ['shares', 'price']
        dlm.register_table('Ledger', 'Ledger', 0, 0, columns)
        
        ref = dlm.get_structured_reference('Ledger', 'shares', current_row=True)
        assert ref == 'Ledger[@[shares]]'
        
        ref = dlm.get_structured_reference('Ledger', 'shares', current_row=False)
        assert ref == 'Ledger[[shares]]'
    
    def test_column_letter_conversion(self):
        """Test column index to letter conversion."""
        dlm = DeterministicLayoutMap()
        assert dlm._col_index_to_letter(0) == 'A'
        assert dlm._col_index_to_letter(25) == 'Z'
        assert dlm._col_index_to_letter(26) == 'AA'
        assert dlm._col_index_to_letter(701) == 'ZZ'
    
    def test_cell_address_generation(self):
        """Test cell address generation."""
        dlm = DeterministicLayoutMap()
        
        addr = dlm.get_cell_address('Summary', 5, 1, absolute=True)
        assert addr == 'Summary!$B$6'
        
        addr = dlm.get_cell_address('', 0, 0, absolute=False)
        assert addr == 'A1'


class TestFormulaResolver:
    """Test formula resolution functionality."""
    
    def test_ownership_formula_generation(self):
        """Test ownership percentage formula."""
        dlm = DeterministicLayoutMap()
        dlm.register_named_range('Total_FDS', 'Summary', 5, 1)
        
        resolver = FormulaResolver(dlm)
        formula = resolver.create_ownership_formula('B5', 'Total_FDS')
        
        assert formula.startswith('=')
        assert 'IFERROR' in formula
        assert 'B5' in formula
        assert 'Total_FDS' in formula
    
    def test_tsm_formula_generation(self):
        """Test Treasury Stock Method formulas."""
        dlm = DeterministicLayoutMap()
        dlm.register_named_range('Current_PPS', 'Summary', 2, 1)
        
        resolver = FormulaResolver(dlm)
        
        # Gross ITM formula
        formula = resolver.create_tsm_gross_itm_formula('B5', 'C5', 'Current_PPS')
        assert formula.startswith('=IF')
        assert 'Current_PPS' in formula
        assert 'B5' in formula
        
        # Proceeds formula
        formula = resolver.create_tsm_proceeds_formula('D5', 'C5')
        assert '=' in formula
        assert '*' in formula
        
        # Repurchase formula
        formula = resolver.create_tsm_repurchase_formula('E5', 'Current_PPS')
        assert 'IFERROR' in formula
        assert '/' in formula
        
        # Net dilution formula
        formula = resolver.create_tsm_net_dilution_formula('D5', 'F5')
        assert '-' in formula
    
    def test_vesting_formula_generation(self):
        """Test vesting schedule formula."""
        dlm = DeterministicLayoutMap()
        dlm.register_named_range('Current_Date', 'Summary', 3, 1)
        
        resolver = FormulaResolver(dlm)
        formula = resolver.create_vesting_formula('B5', 'C5', 'D5', 'E5', 'Current_Date')
        
        assert formula.startswith('=')
        assert 'MIN' in formula
        assert 'MAX' in formula
        assert 'DAYS' in formula
        assert 'Current_Date' in formula
    
    def test_waterfall_formula_generation(self):
        """Test liquidation waterfall formulas."""
        dlm = DeterministicLayoutMap()
        resolver = FormulaResolver(dlm)
        
        # Non-participating
        formula = resolver.create_waterfall_nonparticipating_formula('B5', 'Exit_Val', 'C5')
        assert 'MAX' in formula
        assert 'Exit_Val' in formula
        
        # Participating
        formula = resolver.create_waterfall_participating_formula('B5', 'Exit_Val', 'D5', 'C5')
        assert '+' in formula
        assert 'Exit_Val' in formula
    
    def test_safe_conversion_formula(self):
        """Test SAFE conversion formulas."""
        dlm = DeterministicLayoutMap()
        resolver = FormulaResolver(dlm)
        
        # Conversion price
        formula = resolver.create_safe_conversion_price_formula('B5', 'C5', 'D5', 'E5')
        assert 'MIN' in formula
        assert '/' in formula
        
        # Conversion shares
        formula = resolver.create_safe_conversion_shares_formula('F5', 'G5')
        assert 'IFERROR' in formula
        assert '/' in formula
    
    def test_option_pool_topup_formula(self):
        """Test option pool top-up formula."""
        dlm = DeterministicLayoutMap()
        resolver = FormulaResolver(dlm)
        
        formula = resolver.create_option_pool_topup_formula('B5', 'C5')
        assert 'IFERROR' in formula
        assert '/' in formula
        assert '(1' in formula


class TestCapTableGenerator:
    """Test end-to-end cap table generation."""
    
    def test_generator_initialization_with_data(self):
        """Test generator can be initialized with data."""
        data = generate_simple_captable()
        generator = CapTableGenerator(json_data=data)
        assert generator.data == data
    
    def test_generator_validation(self):
        """Test generator validation."""
        data = generate_simple_captable()
        generator = CapTableGenerator(json_data=data)
        
        is_valid = generator.validate()
        assert is_valid
        assert len(generator.get_validation_errors()) == 0
    
    def test_generator_fails_invalid_data(self):
        """Test generator fails on invalid data."""
        data = {"schema_version": "1.0"}  # Incomplete
        generator = CapTableGenerator(json_data=data)
        
        is_valid = generator.validate()
        assert not is_valid
        assert len(generator.get_validation_errors()) > 0
    
    def test_excel_generation_simple(self, tmp_path):
        """Test Excel generation for simple cap table."""
        data = generate_simple_captable()
        output_path = tmp_path / "test_simple.xlsx"
        
        result = generate_from_data(data, str(output_path))
        
        assert result == str(output_path)
        assert output_path.exists()
        assert output_path.stat().st_size > 0
    
    def test_excel_generation_complex(self, tmp_path):
        """Test Excel generation for complex cap table."""
        data = generate_complex_captable()
        output_path = tmp_path / "test_complex.xlsx"
        
        result = generate_from_data(data, str(output_path))
        
        assert result == str(output_path)
        assert output_path.exists()
        assert output_path.stat().st_size > 0
    
    def test_generator_refuses_invalid_without_force(self):
        """Test generator refuses to generate from invalid data without force."""
        data = {"schema_version": "1.0"}  # Incomplete
        generator = CapTableGenerator(json_data=data)
        
        with pytest.raises(ValueError) as exc_info:
            generator.generate_excel("output.xlsx", force=False)
        
        assert "invalid" in str(exc_info.value).lower()


def run_tests():
    """Run all tests."""
    pytest.main([__file__, '-v'])


if __name__ == "__main__":
    run_tests()

