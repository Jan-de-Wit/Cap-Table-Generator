"""
End-to-end test for cap table generation flow
"""

import sys
import os
import pytest
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from webapp.backend.services.captable_service import cap_table_service
from webapp.backend.services.tool_executor import tool_executor
from webapp.backend.models import CapTableEditorRequest
from src.captable.generator import generate_from_data


def test_e2e_cap_table_creation():
    """
    End-to-end test simulating a full cap table creation flow.
    
    Simulates:
    1. Create company
    2. Add founders
    3. Add common stock class
    4. Issue founder shares
    5. Add Series A round
    6. Export to Excel
    """
    # Reset
    cap_table_service.reset()
    
    # Step 1: Set company name
    result = tool_executor.execute_cap_table_editor(
        CapTableEditorRequest(
            operation="replace",
            path="/company/name",
            value="TechCo Inc"
        )
    )
    assert result["ok"] is True
    
    # Step 2: Add founders
    founders = [
        {
            "holder_id": "founder-1",
            "name": "Alice Founder",
            "type": "founder",
            "email": "alice@techco.com"
        },
        {
            "holder_id": "founder-2",
            "name": "Bob Cofounder",
            "type": "founder",
            "email": "bob@techco.com"
        }
    ]
    
    for founder in founders:
        result = tool_executor.execute_cap_table_editor(
            CapTableEditorRequest(
                operation="append",
                path="/holders",
                value=founder
            )
        )
        assert result["ok"] is True
    
    # Step 3: Add common stock class
    result = tool_executor.execute_cap_table_editor(
        CapTableEditorRequest(
            operation="append",
            path="/classes",
            value={
                "class_id": "class-common",
                "name": "Common Stock",
                "type": "common"
            }
        )
    )
    assert result["ok"] is True
    
    # Step 4: Issue founder shares
    result = tool_executor.execute_cap_table_editor(
        CapTableEditorRequest(
            operation="bulkPatch",
            patch=[
                {
                    "op": "add",
                    "path": "/instruments/0",
                    "value": {
                        "instrument_id": "inst-1",
                        "holder_id": "founder-1",
                        "class_id": "class-common",
                        "initial_quantity": 5000000,
                        "acquisition_date": "2023-01-01"
                    }
                },
                {
                    "op": "add",
                    "path": "/instruments/1",
                    "value": {
                        "instrument_id": "inst-2",
                        "holder_id": "founder-2",
                        "class_id": "class-common",
                        "initial_quantity": 5000000,
                        "acquisition_date": "2023-01-01"
                    }
                }
            ]
        )
    )
    assert result["ok"] is True
    
    # Step 5: Add Series A round
    result = tool_executor.execute_cap_table_editor(
        CapTableEditorRequest(
            operation="append",
            path="/rounds",
            value={
                "round_id": "round-series-a",
                "name": "Series A",
                "round_date": "2024-01-01",
                "investment_amount": 5000000,
                "pre_money_valuation": 20000000
            }
        )
    )
    assert result["ok"] is True
    
    # Verify final state
    cap_table = cap_table_service.get_cap_table()
    assert cap_table["company"]["name"] == "TechCo Inc"
    assert len(cap_table["holders"]) == 2
    assert len(cap_table["classes"]) == 1
    assert len(cap_table["instruments"]) == 2
    assert len(cap_table["rounds"]) == 1
    
    # Verify metrics
    metrics = cap_table_service.calculate_metrics()
    assert metrics["totals"]["issued"] == 10000000
    assert len(metrics["ownership"]) == 2
    
    # Step 6: Export to Excel
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        temp_path = tmp.name
    
    try:
        output_path = generate_from_data(cap_table, temp_path)
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

