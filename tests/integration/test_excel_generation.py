"""
Integration Tests for Excel Generation

Test complete Excel generation workflow.
"""

from captable.generator import CapTableGenerator
import pytest
import sys
from pathlib import Path

# Add fastapi directory to path
test_dir = Path(__file__).resolve().parent.parent
fastapi_dir = test_dir.parent / "fastapi"
if str(fastapi_dir) not in sys.path:
    sys.path.insert(0, str(fastapi_dir))


class TestExcelGeneration:
    """Test Excel generation."""

    def test_generate_excel_complete_cap_table(self, temp_dir, sample_cap_table_data):
        """Test generating Excel from complete cap table."""
        output_path = temp_dir / "test_output.xlsx"

        generator = CapTableGenerator(json_data=sample_cap_table_data)
        assert generator.validate()

        result_path = generator.generate_excel(str(output_path))
        assert Path(result_path).exists()
        assert result_path == str(output_path)

    def test_generate_excel_all_calculation_types(self, temp_dir):
        """Test generating Excel with all calculation types."""
        from tests.fixtures.sample_cap_tables import (
            FIXED_SHARES_ROUND,
            TARGET_PERCENTAGE_ROUND,
            VALUATION_BASED_ROUND,
            CONVERTIBLE_ROUND,
            SAFE_ROUND,
        )

        data = {
            "schema_version": "2.0",
            "holders": [
                {"name": "Founder 1", "group": "Founders"},
                {"name": "Investor A", "group": "Investors"},
            ],
            "rounds": [
                FIXED_SHARES_ROUND,
                TARGET_PERCENTAGE_ROUND,
                VALUATION_BASED_ROUND,
                CONVERTIBLE_ROUND,
                SAFE_ROUND,
            ],
        }

        output_path = temp_dir / "test_all_types.xlsx"
        generator = CapTableGenerator(json_data=data)

        if generator.validate():
            result_path = generator.generate_excel(str(output_path))
            assert Path(result_path).exists()
