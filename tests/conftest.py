"""
Pytest Configuration and Fixtures

Shared fixtures and configuration for all tests.
"""

import pytest
import tempfile
import os
from pathlib import Path
from typing import Dict, Any


@pytest.fixture
def temp_dir():
    """Create temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_cap_table_data() -> Dict[str, Any]:
    """Sample cap table data for testing."""
    return {
        "schema_version": "2.0",
        "holders": [
            {"name": "Founder 1", "group": "Founders"},
            {"name": "Founder 2", "group": "Founders"},
            {"name": "Investor A", "group": "Investors"},
        ],
        "rounds": [
            {
                "name": "Seed Round",
                "calculation_type": "valuation_based",
                "round_date": "2024-01-01",
                "valuation": 1000000,
                "valuation_basis": "pre_money",
                "instruments": [
                    {
                        "holder_name": "Investor A",
                        "class_name": "Common",
                        "investment_amount": 100000,
                    }
                ],
            }
        ],
    }


@pytest.fixture
def fixed_shares_round() -> Dict[str, Any]:
    """Sample fixed shares round."""
    return {
        "name": "Fixed Shares Round",
        "calculation_type": "fixed_shares",
        "round_date": "2024-01-01",
        "instruments": [
            {
                "holder_name": "Founder 1",
                "class_name": "Common",
                "initial_quantity": 1000000,
            }
        ],
    }


@pytest.fixture
def target_percentage_round() -> Dict[str, Any]:
    """Sample target percentage round."""
    return {
        "name": "Target % Round",
        "calculation_type": "target_percentage",
        "round_date": "2024-01-01",
        "instruments": [
            {
                "holder_name": "Investor A",
                "class_name": "Common",
                "target_percentage": 0.20,
            }
        ],
    }


@pytest.fixture
def valuation_based_round() -> Dict[str, Any]:
    """Sample valuation-based round."""
    return {
        "name": "Series A",
        "calculation_type": "valuation_based",
        "round_date": "2024-01-01",
        "valuation": 5000000,
        "valuation_basis": "pre_money",
        "instruments": [
            {
                "holder_name": "Investor A",
                "class_name": "Preferred",
                "investment_amount": 1000000,
            }
        ],
    }


@pytest.fixture
def convertible_round() -> Dict[str, Any]:
    """Sample convertible round."""
    return {
        "name": "Convertible Note",
        "calculation_type": "convertible",
        "round_date": "2024-01-01",
        "valuation": 2000000,
        "valuation_basis": "pre_money",
        "instruments": [
            {
                "holder_name": "Investor A",
                "class_name": "Note",
                "investment_amount": 50000,
                "interest_rate": 0.08,
                "discount_rate": 0.20,
                "payment_date": "2024-01-01",
                "expected_conversion_date": "2025-01-01",
                "interest_type": "simple",
            }
        ],
    }


@pytest.fixture
def safe_round() -> Dict[str, Any]:
    """Sample SAFE round."""
    return {
        "name": "SAFE",
        "calculation_type": "safe",
        "round_date": "2024-01-01",
        "valuation": 2000000,
        "valuation_basis": "pre_money",
        "instruments": [
            {
                "holder_name": "Investor A",
                "class_name": "SAFE",
                "investment_amount": 100000,
                "discount_rate": 0.20,
                "expected_conversion_date": "2025-01-01",
            }
        ],
    }





