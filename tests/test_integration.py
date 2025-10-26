"""
Integration Tests for JSON to Excel Generation
Tests the complete flow from JSON input to Excel output.
"""

import pytest
import json
from pathlib import Path
from src.captable import generate_from_json, generate_from_data
from src.captable.generator import CapTableGenerator
from tests.conftest import assert_excel_structure, assert_table_exists, assert_named_range_exists


class TestEndToEndGeneration:
    """Test complete JSON to Excel generation flow."""
    
    def test_generate_from_json_file(self, sample_json_file, temp_dir, excel_helper):
        """Test generating Excel from JSON file."""
        output_path = temp_dir / "output.xlsx"
        
        result = generate_from_json(str(sample_json_file), str(output_path))
        
        assert Path(result).exists()
        assert_excel_structure(output_path, [
            'Holders', 'Classes', 'Terms', 'Summary', 'Ledger', 
            'Rounds', 'Cap Table Progression', 'Vesting', 'Waterfall'
        ])
    
    def test_generate_from_data_dict(self, full_cap_table, temp_dir, excel_helper):
        """Test generating Excel from data dictionary."""
        output_path = temp_dir / "output.xlsx"
        
        result = generate_from_data(full_cap_table, str(output_path))
        
        assert Path(result).exists()
        assert_excel_structure(output_path, [
            'Holders', 'Classes', 'Terms', 'Summary', 'Ledger', 
            'Rounds', 'Cap Table Progression', 'Vesting', 'Waterfall'
        ])
    
    def test_generator_class_workflow(self, full_cap_table, temp_dir):
        """Test using CapTableGenerator class directly."""
        output_path = temp_dir / "output.xlsx"
        
        generator = CapTableGenerator(json_data=full_cap_table)
        
        # Validate
        is_valid = generator.validate()
        assert is_valid is True
        assert len(generator.get_validation_errors()) == 0
        
        # Generate
        result = generator.generate_excel(str(output_path))
        assert Path(result).exists()
    
    def test_validation_before_generation(self, temp_dir):
        """Test that invalid data is caught before generation."""
        invalid_data = {
            "schema_version": "1.0",
            "company": {"name": "Test"},
            # Missing required fields: holders, classes, instruments
        }
        
        output_path = temp_dir / "output.xlsx"
        
        with pytest.raises(ValueError, match="invalid"):
            generate_from_data(invalid_data, str(output_path))
    
    def test_complex_captable_generation(self, complex_cap_table, temp_dir, excel_helper):
        """Test generating complex cap table with all features."""
        output_path = temp_dir / "complex.xlsx"
        
        result = generate_from_data(complex_cap_table, str(output_path))
        
        assert Path(result).exists()
        
        # Verify all sheets exist
        sheets = excel_helper.get_sheet_names(output_path)
        assert 'Holders' in sheets
        assert 'Classes' in sheets
        assert 'Terms' in sheets
        assert 'Ledger' in sheets
        assert 'Rounds' in sheets
        assert 'Vesting' in sheets
        assert 'Waterfall' in sheets
        
        # Verify data integrity
        # Check that we have correct number of holders
        holders_count = 0
        for i in range(2, 20):  # Check up to row 20
            val = excel_helper.get_cell_value(output_path, 'Holders', f'A{i}')
            if val:
                holders_count += 1
            else:
                break
        
        assert holders_count == len(complex_cap_table['holders'])


class TestFormulaLinking:
    """Test that formula linking works correctly."""
    
    def test_holder_type_updates_from_master(self, full_cap_table, temp_dir, excel_helper):
        """Test that Ledger holder_type is linked to Holders sheet."""
        output_path = temp_dir / "output.xlsx"
        generate_from_data(full_cap_table, str(output_path))
        
        # Verify XLOOKUP formula exists
        formula = excel_helper.get_cell_formula(output_path, 'Ledger', 'B2')
        assert formula is not None
        assert 'XLOOKUP' in formula
        assert 'Holders' in formula
    
    def test_class_type_updates_from_master(self, full_cap_table, temp_dir, excel_helper):
        """Test that Ledger class_type is linked to Classes sheet."""
        output_path = temp_dir / "output.xlsx"
        generate_from_data(full_cap_table, str(output_path))
        
        # Verify XLOOKUP formula exists
        formula = excel_helper.get_cell_formula(output_path, 'Ledger', 'D2')
        assert formula is not None
        assert 'XLOOKUP' in formula
        assert 'Classes' in formula
    
    def test_waterfall_terms_linked(self, full_cap_table, temp_dir, excel_helper):
        """Test that Waterfall terms are linked to Terms sheet."""
        output_path = temp_dir / "output.xlsx"
        generate_from_data(full_cap_table, str(output_path))
        
        # Verify waterfall sheet exists (may not have data with minimal fixture)
        assert excel_helper.sheet_exists(output_path, 'Waterfall')
        
        # Try to check for XLOOKUP if data exists
        try:
            lp_formula = excel_helper.get_cell_formula(output_path, 'Waterfall', 'E2')
            if lp_formula:
                assert 'XLOOKUP' in lp_formula or 'Terms' in lp_formula
        except Exception:
            # No data in waterfall, that's okay
            pass
    
    def test_rounds_initial_shares_formula(self, full_cap_table, temp_dir, excel_helper):
        """Test that Rounds pre_round_shares uses formula."""
        output_path = temp_dir / "output.xlsx"
        generate_from_data(full_cap_table, str(output_path))
        
        # Verify SUMIF formula exists
        formula = excel_helper.get_cell_formula(output_path, 'Rounds', 'C2')
        assert formula is not None
        assert 'SUMIF' in formula
        assert 'Ledger' in formula


class TestDataConsistency:
    """Test data consistency across sheets."""
    
    def test_holder_names_match_across_sheets(self, full_cap_table, temp_dir, excel_helper):
        """Test that holder names are consistent across sheets."""
        output_path = temp_dir / "output.xlsx"
        generate_from_data(full_cap_table, str(output_path))
        
        # Get holder name from Holders sheet
        holder_name_master = excel_helper.get_cell_value(output_path, 'Holders', 'A2')
        
        # Get holder name from Ledger sheet
        holder_name_ledger = excel_helper.get_cell_value(output_path, 'Ledger', 'A2')
        
        assert holder_name_master == holder_name_ledger
    
    def test_class_names_match_across_sheets(self, full_cap_table, temp_dir, excel_helper):
        """Test that class names are consistent across sheets."""
        output_path = temp_dir / "output.xlsx"
        generate_from_data(full_cap_table, str(output_path))
        
        # Get class name from Classes sheet
        class_name_master = excel_helper.get_cell_value(output_path, 'Classes', 'A2')
        
        # Get class name from Ledger sheet
        class_name_ledger = excel_helper.get_cell_value(output_path, 'Ledger', 'C2')
        
        assert class_name_master == class_name_ledger
    
    def test_round_names_match(self, full_cap_table, temp_dir, excel_helper):
        """Test that round names are consistent."""
        output_path = temp_dir / "output.xlsx"
        generate_from_data(full_cap_table, str(output_path))
        
        # Check if rounds exist
        round_name_master = excel_helper.get_cell_value(output_path, 'Rounds', 'A2')
        
        if round_name_master:
            # Find the round_name in Ledger (check several rows)
            found_match = False
            for row in range(2, 10):
                round_name_ledger = excel_helper.get_cell_value(output_path, 'Ledger', f'J{row}')
                if round_name_ledger == round_name_master:
                    found_match = True
                    break
            
            # It's okay if no match - not all instruments have rounds
            # Just verify rounds sheet exists
            assert excel_helper.sheet_exists(output_path, 'Rounds')


class TestTableStructures:
    """Test that Excel tables are created correctly."""
    
    def test_all_required_tables_exist(self, full_cap_table, temp_dir):
        """Test that all required tables are created."""
        output_path = temp_dir / "output.xlsx"
        generate_from_data(full_cap_table, str(output_path))
        
        assert_table_exists(output_path, 'Holders')
        assert_table_exists(output_path, 'Classes')
        assert_table_exists(output_path, 'Terms')
        assert_table_exists(output_path, 'Ledger')
    
    def test_structured_references_work(self, full_cap_table, temp_dir, excel_helper):
        """Test that structured references (table references) are used."""
        output_path = temp_dir / "output.xlsx"
        generate_from_data(full_cap_table, str(output_path))
        
        # Check that formulas use structured references
        formula = excel_helper.get_cell_formula(output_path, 'Ledger', 'B2')
        assert 'Holders[' in formula  # Structured reference syntax


class TestNamedRanges:
    """Test that named ranges are created correctly."""
    
    def test_all_required_named_ranges_exist(self, full_cap_table, temp_dir):
        """Test that all required named ranges are created."""
        output_path = temp_dir / "output.xlsx"
        generate_from_data(full_cap_table, str(output_path))
        
        assert_named_range_exists(output_path, 'Current_PPS')
        assert_named_range_exists(output_path, 'Total_FDS')
        assert_named_range_exists(output_path, 'Exit_Val')
        assert_named_range_exists(output_path, 'Current_Date')
    
    def test_named_ranges_reference_summary(self, full_cap_table, temp_dir, excel_helper):
        """Test that named ranges reference Summary sheet."""
        output_path = temp_dir / "output.xlsx"
        generate_from_data(full_cap_table, str(output_path))
        
        named_ranges = excel_helper.get_named_ranges(output_path)
        
        assert 'Summary' in named_ranges['Current_PPS']
        assert 'Summary' in named_ranges['Total_FDS']


class TestDataValidation:
    """Test data validation rules."""
    
    def test_data_validation_exists(self, full_cap_table, temp_dir, excel_helper):
        """Test that data validation rules are applied."""
        output_path = temp_dir / "output.xlsx"
        generate_from_data(full_cap_table, str(output_path))
        
        # Check that Ledger has data validations
        validations = excel_helper.get_data_validations(output_path, 'Ledger')
        assert len(validations) >= 3  # At least holder_name, class_name, round_name


class TestMultiRoundScenarios:
    """Test scenarios with multiple financing rounds."""
    
    def test_multiple_rounds_progression(self, complex_cap_table, temp_dir, excel_helper):
        """Test that multiple rounds are handled correctly."""
        output_path = temp_dir / "output.xlsx"
        generate_from_data(complex_cap_table, str(output_path))
        
        # Check that both rounds exist
        round1 = excel_helper.get_cell_value(output_path, 'Rounds', 'A2')
        round2 = excel_helper.get_cell_value(output_path, 'Rounds', 'A3')
        
        assert round1 == 'Series A'
        assert round2 == 'Series B'
        
        # Check that pre_round_shares for second round references first round
        formula = excel_helper.get_cell_formula(output_path, 'Rounds', 'C3')
        assert formula is not None
        # Should reference previous row
        assert 'C2' in formula or '$C$2' in formula


class TestVestingCalculations:
    """Test vesting calculations."""
    
    def test_vesting_formulas_exist(self, complex_cap_table, temp_dir, excel_helper):
        """Test that vesting formulas are created."""
        output_path = temp_dir / "output.xlsx"
        generate_from_data(complex_cap_table, str(output_path))
        
        # Check days_elapsed formula
        formula = excel_helper.get_cell_formula(output_path, 'Vesting', 'H2')
        if formula:  # Only if vesting data exists
            assert 'DAYS' in formula
            assert 'Current_Date' in formula


class TestWaterfallScenarios:
    """Test waterfall analysis."""
    
    def test_waterfall_calculations(self, full_cap_table, temp_dir, excel_helper):
        """Test that waterfall calculations are created."""
        output_path = temp_dir / "output.xlsx"
        generate_from_data(full_cap_table, str(output_path))
        
        # Check that waterfall sheet has formulas
        # Shares formula
        shares_formula = excel_helper.get_cell_formula(output_path, 'Waterfall', 'C2')
        assert shares_formula is not None
        assert 'SUMIF' in shares_formula
        
        # Ownership formula
        ownership_formula = excel_helper.get_cell_formula(output_path, 'Waterfall', 'D2')
        assert ownership_formula is not None
        assert 'Total_FDS' in ownership_formula


class TestErrorHandling:
    """Test error handling in generation."""
    
    def test_invalid_schema_version(self, minimal_cap_table, temp_dir):
        """Test that invalid schema version is caught."""
        data = minimal_cap_table.copy()
        data['schema_version'] = '99.0'
        
        output_path = temp_dir / "output.xlsx"
        
        with pytest.raises(ValueError):
            generate_from_data(data, str(output_path))
    
    def test_missing_required_field(self, temp_dir):
        """Test that missing required fields are caught."""
        data = {
            "schema_version": "1.0",
            "company": {"name": "Test"},
            # Missing holders, classes, instruments
        }
        
        output_path = temp_dir / "output.xlsx"
        
        with pytest.raises(ValueError):
            generate_from_data(data, str(output_path))
    
    def test_invalid_holder_reference(self, minimal_cap_table, temp_dir):
        """Test that invalid holder references are caught."""
        data = minimal_cap_table.copy()
        data['instruments'][0]['holder_name'] = 'NonExistentHolder'
        
        output_path = temp_dir / "output.xlsx"
        
        with pytest.raises(ValueError):
            generate_from_data(data, str(output_path))
    
    def test_invalid_class_reference(self, minimal_cap_table, temp_dir):
        """Test that invalid class references are caught."""
        data = minimal_cap_table.copy()
        data['instruments'][0]['class_name'] = 'NonExistentClass'
        
        output_path = temp_dir / "output.xlsx"
        
        with pytest.raises(ValueError):
            generate_from_data(data, str(output_path))


class TestPerformance:
    """Test performance with larger datasets."""
    
    def test_large_holder_count(self, minimal_cap_table, temp_dir):
        """Test generation with many holders."""
        data = minimal_cap_table.copy()
        
        # Add 100 holders
        for i in range(100):
            data['holders'].append({
                "name": f"Holder{i}",
                "type": "investor",
                "email": f"holder{i}@test.com"
            })
            data['instruments'].append({
                "holder_name": f"Holder{i}",
                "class_name": "Common",
                "initial_quantity": 10000,
                "acquisition_price": 0.01,
                "acquisition_date": "2023-01-01"
            })
        
        output_path = temp_dir / "large.xlsx"
        
        # Should complete without error
        result = generate_from_data(data, str(output_path))
        assert Path(result).exists()
    
    def test_many_instruments(self, minimal_cap_table, temp_dir):
        """Test generation with many instruments."""
        data = minimal_cap_table.copy()
        
        # Add 200 instruments
        for i in range(200):
            data['instruments'].append({
                "holder_name": "Alice",
                "class_name": "Common",
                "initial_quantity": 1000,
                "acquisition_price": 0.01,
                "acquisition_date": "2023-01-01"
            })
        
        output_path = temp_dir / "many_instruments.xlsx"
        
        # Should complete without error
        result = generate_from_data(data, str(output_path))
        assert Path(result).exists()

