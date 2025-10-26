"""
Unit tests for tool executor
"""

import sys
import os
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from webapp.backend.services.tool_executor import tool_executor
from webapp.backend.services.captable_service import cap_table_service
from webapp.backend.models import CapTableEditorRequest


def setup_function():
    """Reset cap table before each test."""
    cap_table_service.reset()


def test_replace_operation():
    """Test replace operation."""
    # Set company name
    request = CapTableEditorRequest(
        operation="replace",
        path="/company/name",
        value="New Company Name"
    )
    
    result = tool_executor.execute_cap_table_editor(request)
    
    assert result["ok"] is True
    assert result["capTable"]["company"]["name"] == "New Company Name"
    assert len(result["diff"]) > 0


def test_append_operation():
    """Test append operation to add holder."""
    holder = {
        "holder_id": "12345678-1234-1234-1234-123456789012",
        "name": "John Doe",
        "type": "founder"
    }
    
    request = CapTableEditorRequest(
        operation="append",
        path="/holders",
        value=holder
    )
    
    result = tool_executor.execute_cap_table_editor(request)
    
    assert result["ok"] is True
    assert len(result["capTable"]["holders"]) == 1
    assert result["capTable"]["holders"][0]["name"] == "John Doe"


def test_upsert_operation():
    """Test upsert operation."""
    request = CapTableEditorRequest(
        operation="upsert",
        path="/company/current_pps",
        value=1.50
    )
    
    result = tool_executor.execute_cap_table_editor(request)
    
    assert result["ok"] is True
    assert result["capTable"]["company"]["current_pps"] == 1.50


def test_bulk_patch_operation():
    """Test bulk patch operation."""
    patch = [
        {"op": "replace", "path": "/company/name", "value": "Acme Corp"},
        {"op": "add", "path": "/holders", "value": []},
        {"op": "add", "path": "/holders/0", "value": {
            "holder_id": "12345678-1234-1234-1234-123456789012",
            "name": "Jane Smith",
            "type": "founder"
        }}
    ]
    
    request = CapTableEditorRequest(
        operation="bulkPatch",
        patch=patch
    )
    
    result = tool_executor.execute_cap_table_editor(request)
    
    assert result["ok"] is True
    assert result["capTable"]["company"]["name"] == "Acme Corp"
    assert len(result["capTable"]["holders"]) == 1


def test_validation_error():
    """Test that invalid data returns validation errors."""
    holder = {
        "holder_id": "invalid-uuid",  # Invalid UUID
        "name": "John Doe",
        "type": "founder"
    }
    
    request = CapTableEditorRequest(
        operation="append",
        path="/holders",
        value=holder
    )
    
    result = tool_executor.execute_cap_table_editor(request)
    
    assert result["ok"] is False
    assert len(result["errors"]) > 0


def test_diff_generation():
    """Test that diffs are generated correctly."""
    # First operation
    request1 = CapTableEditorRequest(
        operation="replace",
        path="/company/name",
        value="Test Company"
    )
    
    result1 = tool_executor.execute_cap_table_editor(request1)
    assert len(result1["diff"]) > 0
    
    # Second operation
    holder = {
        "holder_id": "12345678-1234-1234-1234-123456789012",
        "name": "Alice",
        "type": "founder"
    }
    
    request2 = CapTableEditorRequest(
        operation="append",
        path="/holders",
        value=holder
    )
    
    result2 = tool_executor.execute_cap_table_editor(request2)
    assert len(result2["diff"]) > 0
    assert any("holder" in str(d).lower() for d in result2["diff"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

