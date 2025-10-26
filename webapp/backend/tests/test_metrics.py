"""
Unit tests for metrics calculation
"""

import sys
import os
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from webapp.backend.services.captable_service import cap_table_service


def setup_function():
    """Reset cap table before each test."""
    cap_table_service.reset()


def test_empty_metrics():
    """Test metrics for empty cap table."""
    metrics = cap_table_service.calculate_metrics()
    
    assert metrics["totals"]["issued"] == 0
    assert metrics["totals"]["fullyDiluted"] == 0
    assert len(metrics["ownership"]) == 0
    assert metrics["pool"]["size"] == 0


def test_simple_ownership():
    """Test ownership calculation with one holder."""
    cap_table = {
        "schema_version": "1.0",
        "company": {"name": "Test Co"},
        "holders": [{
            "holder_id": "holder-1",
            "name": "Alice",
            "type": "founder"
        }],
        "classes": [{
            "class_id": "class-1",
            "name": "Common",
            "type": "common"
        }],
        "instruments": [{
            "instrument_id": "inst-1",
            "holder_id": "holder-1",
            "class_id": "class-1",
            "initial_quantity": 1000000,
            "current_quantity": 1000000
        }]
    }
    
    cap_table_service.set_cap_table(cap_table)
    metrics = cap_table_service.calculate_metrics()
    
    assert metrics["totals"]["issued"] == 1000000
    assert metrics["totals"]["fullyDiluted"] == 1000000
    assert len(metrics["ownership"]) == 1
    assert metrics["ownership"][0]["holder_name"] == "Alice"
    assert metrics["ownership"][0]["percent_issued"] == 100.0
    assert metrics["ownership"][0]["percent_fd"] == 100.0


def test_multiple_holders():
    """Test ownership with multiple holders."""
    cap_table = {
        "schema_version": "1.0",
        "company": {"name": "Test Co"},
        "holders": [
            {"holder_id": "holder-1", "name": "Alice", "type": "founder"},
            {"holder_id": "holder-2", "name": "Bob", "type": "founder"}
        ],
        "classes": [{
            "class_id": "class-1",
            "name": "Common",
            "type": "common"
        }],
        "instruments": [
            {
                "instrument_id": "inst-1",
                "holder_id": "holder-1",
                "class_id": "class-1",
                "initial_quantity": 600000
            },
            {
                "instrument_id": "inst-2",
                "holder_id": "holder-2",
                "class_id": "class-1",
                "initial_quantity": 400000
            }
        ]
    }
    
    cap_table_service.set_cap_table(cap_table)
    metrics = cap_table_service.calculate_metrics()
    
    assert metrics["totals"]["issued"] == 1000000
    assert len(metrics["ownership"]) == 2
    
    alice = next(o for o in metrics["ownership"] if o["holder_name"] == "Alice")
    bob = next(o for o in metrics["ownership"] if o["holder_name"] == "Bob")
    
    assert alice["percent_issued"] == pytest.approx(60.0, rel=0.01)
    assert bob["percent_issued"] == pytest.approx(40.0, rel=0.01)


def test_option_pool():
    """Test option pool calculations."""
    cap_table = {
        "schema_version": "1.0",
        "company": {"name": "Test Co"},
        "holders": [
            {"holder_id": "holder-1", "name": "Alice", "type": "founder"},
            {"holder_id": "pool", "name": "Option Pool", "type": "option_pool"},
            {"holder_id": "holder-2", "name": "Employee 1", "type": "employee"}
        ],
        "classes": [
            {"class_id": "class-1", "name": "Common", "type": "common"},
            {"class_id": "class-2", "name": "Options", "type": "option"}
        ],
        "instruments": [
            {
                "instrument_id": "inst-1",
                "holder_id": "holder-1",
                "class_id": "class-1",
                "initial_quantity": 800000
            },
            {
                "instrument_id": "inst-2",
                "holder_id": "pool",
                "class_id": "class-2",
                "initial_quantity": 200000  # Ungranted
            },
            {
                "instrument_id": "inst-3",
                "holder_id": "holder-2",
                "class_id": "class-2",
                "initial_quantity": 50000  # Granted
            }
        ]
    }
    
    cap_table_service.set_cap_table(cap_table)
    metrics = cap_table_service.calculate_metrics()
    
    assert metrics["pool"]["size"] == 250000  # 200k + 50k
    assert metrics["pool"]["granted"] == 50000
    assert metrics["pool"]["remaining"] == 200000
    
    # FD should include options
    assert metrics["totals"]["fullyDiluted"] == 1050000  # 800k + 250k


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

