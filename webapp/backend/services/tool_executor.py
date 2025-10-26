"""
Tool Executor - Executes cap_table_editor operations with validation.
Handles JSON Pointer operations and generates human-readable diffs.
"""

import sys
import os
import copy
import jsonpointer
import jsonpatch
import logging
from typing import Dict, Any, List, Optional, Tuple

from webapp.backend.utils.color_logger import setup_tool_logging

# Set up logger with color coding
logger = setup_tool_logging(__name__)

# Add parent directory to path to import cap table modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.captable.validation import validate_cap_table
from webapp.backend.services.captable_service import cap_table_service
from webapp.backend.models import (
    CapTableEditorRequest,
    CapTableEditorSuccessResponse,
    CapTableEditorErrorResponse,
    ErrorDetail,
    DiffItem
)

# Import modular operations
from webapp.backend.services.tools.operations import (
    apply_replace,
    apply_append,
    apply_upsert,
    apply_delete,
    apply_bulk_patch
)


class ToolExecutor:
    """Executes cap_table_editor tool operations."""
    
    def execute_cap_table_editor(
        self, 
        request: CapTableEditorRequest,
        preview_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Execute cap_table_editor operation.
        
        Args:
            request: Tool execution request
            preview_mode: If True, don't persist changes to state
            
        Returns:
            Success response with updated cap table, diff, and metrics
            OR error response with validation errors
        """
        if preview_mode:
            logger.info(f"[TOOL_EXEC_START] Starting cap_table_editor operation (PREVIEW MODE)")
        else:
            logger.info(f"[TOOL_EXEC_START] Starting cap_table_editor operation")
        
        logger.info(f"  Operation: {request.operation}")
        logger.info(f"  Path: {request.path}")
        
        # Log value if present
        if request.value is not None:
            if isinstance(request.value, dict):
                # For complex values, show a preview
                value_str = str(request.value)[:300]
                if len(str(request.value)) > 300:
                    value_str += "..."
                logger.info(f"  Value: {value_str}")
            else:
                logger.info(f"  Value: {request.value}")
        
        # Log patch if present
        if request.patch:
            logger.info(f"  Patch operations: {len(request.patch)}")
            for i, patch_op in enumerate(request.patch[:3]):  # Show first 3
                logger.info(f"    {i+1}. {patch_op.get('op', 'N/A')} {patch_op.get('path', 'N/A')}")
            if len(request.patch) > 3:
                logger.info(f"    ... and {len(request.patch) - 3} more")
        
        logger.debug(f"  Full request: operation={request.operation}, path={request.path}, "
                     f"value_type={type(request.value).__name__ if request.value else None}")
        
        # Get current cap table
        current_cap_table = cap_table_service.get_cap_table()
        logger.debug(f"  Current cap table size: {len(current_cap_table)} top-level keys")
        
        # Store original for diff
        original_cap_table = copy.deepcopy(current_cap_table)
        
        # Apply operation
        try:
            logger.info(f"  Applying {request.operation} operation")
            updated_cap_table = self._apply_operation(current_cap_table, request)
            logger.info(f"  Operation applied successfully")
        except Exception as e:
            logger.error(f"[TOOL_EXEC_END] Operation failed with exception: {e}")
            logger.exception(e)
            return CapTableEditorErrorResponse(
                errors=[ErrorDetail(
                    path=request.path or "/",
                    message=str(e),
                    rule="operation_error"
                )]
            ).model_dump(by_alias=True)
        
        # Validate against schema
        logger.info("  Validating against schema")
        is_valid, errors = validate_cap_table(updated_cap_table)
        
        if not is_valid:
            logger.error(f"[TOOL_EXEC_END] Schema validation failed with {len(errors)} error(s)")
            for error in errors:
                logger.error(f"  Validation error: {error}")
            
            error_details = [
                ErrorDetail(
                    path="/",
                    message=error,
                    rule="schema_validation"
                ) for error in errors
            ]
            return CapTableEditorErrorResponse(errors=error_details).model_dump(by_alias=True)
        
        logger.info("  Schema validation passed")
        
        # Update service state (skip in preview mode)
        if not preview_mode:
            cap_table_service.set_cap_table(updated_cap_table)
            logger.debug("  State updated in cap_table_service")
        else:
            logger.debug("  Preview mode - state NOT updated")
        
        # Generate diff
        logger.debug("  Generating diff")
        diff = self._generate_diff(original_cap_table, updated_cap_table)
        logger.info(f"  Generated {len(diff)} diff item(s)")
        
        # Calculate metrics
        logger.debug("  Calculating metrics")
        metrics = cap_table_service.calculate_metrics()
        logger.info(f"  Computed metrics for {len(metrics.get('ownership', []))} holder(s)")
        
        # Return success response
        response = CapTableEditorSuccessResponse(
            capTable=updated_cap_table,
            diff=diff,
            metrics=metrics
        )
        
        logger.info(f"[TOOL_EXEC_END] Operation completed successfully")
        return response.model_dump(by_alias=True)
    
    def _apply_operation(
        self, 
        cap_table: Dict[str, Any], 
        request: CapTableEditorRequest
    ) -> Dict[str, Any]:
        """Apply the requested operation to the cap table."""
        operation = request.operation
        
        if operation == "replace":
            return apply_replace(cap_table, request.path, request.value)
        elif operation == "append":
            return apply_append(cap_table, request.path, request.value)
        elif operation == "upsert":
            return apply_upsert(cap_table, request.path, request.value)
        elif operation == "delete":
            return apply_delete(cap_table, request.path, request.value)
        elif operation == "bulkPatch":
            return apply_bulk_patch(cap_table, request.patch)
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    def _generate_diff(
        self, 
        original: Dict[str, Any], 
        updated: Dict[str, Any]
    ) -> List[DiffItem]:
        """
        Generate human-readable diff between original and updated cap tables.
        """
        diff_items = []
        
        # Compare key sections
        self._diff_company(original, updated, diff_items)
        self._diff_holders(original, updated, diff_items)
        self._diff_classes(original, updated, diff_items)
        self._diff_instruments(original, updated, diff_items)
        self._diff_rounds(original, updated, diff_items)
        
        return diff_items
    
    def _diff_company(
        self, 
        original: Dict[str, Any], 
        updated: Dict[str, Any], 
        diff_items: List[DiffItem]
    ):
        """Compare company section."""
        orig_company = original.get("company", {})
        upd_company = updated.get("company", {})
        
        if orig_company.get("name") != upd_company.get("name"):
            diff_items.append(DiffItem(
                op="replace",
                path="/company/name",
                from_value=orig_company.get("name"),
                to=upd_company.get("name"),
                description=f"Company name changed: {orig_company.get('name', 'None')} → {upd_company.get('name', 'None')}"
            ))
    
    def _diff_holders(
        self, 
        original: Dict[str, Any], 
        updated: Dict[str, Any], 
        diff_items: List[DiffItem]
    ):
        """Compare holders."""
        orig_holders = {h["name"]: h for h in original.get("holders", [])}
        upd_holders = {h["name"]: h for h in updated.get("holders", [])}
        
        # New holders
        for holder_name, holder in upd_holders.items():
            if holder_name not in orig_holders:
                diff_items.append(DiffItem(
                    op="add",
                    path=f"/holders/{holder_name}",
                    to=holder,
                    description=f"Added holder: \"{holder.get('name')}\" (type: {holder.get('type')})"
                ))
        
        # Removed holders
        for holder_name, holder in orig_holders.items():
            if holder_name not in upd_holders:
                diff_items.append(DiffItem(
                    op="remove",
                    path=f"/holders/{holder_name}",
                    from_value=holder,
                    description=f"Removed holder: \"{holder.get('name')}\""
                ))
    
    def _diff_classes(
        self, 
        original: Dict[str, Any], 
        updated: Dict[str, Any], 
        diff_items: List[DiffItem]
    ):
        """Compare security classes."""
        orig_classes = {c["name"]: c for c in original.get("classes", [])}
        upd_classes = {c["name"]: c for c in updated.get("classes", [])}
        
        # New classes
        for class_name, sec_class in upd_classes.items():
            if class_name not in orig_classes:
                diff_items.append(DiffItem(
                    op="add",
                    path=f"/classes/{class_name}",
                    to=sec_class,
                    description=f"Added security class: \"{sec_class.get('name')}\" (type: {sec_class.get('type')})"
                ))
    
    def _diff_instruments(
        self, 
        original: Dict[str, Any], 
        updated: Dict[str, Any], 
        diff_items: List[DiffItem]
    ):
        """Compare instruments."""
        # Use a tuple of (holder_name, class_name, quantity) as key since instruments don't have IDs
        def get_instrument_key(instrument):
            return (
                instrument.get("holder_name"),
                instrument.get("class_name"),
                instrument.get("initial_quantity", 0)
            )
        
        orig_instruments = {get_instrument_key(i): i for i in original.get("instruments", [])}
        upd_instruments = {get_instrument_key(i): i for i in updated.get("instruments", [])}
        
        # New instruments
        for key, instrument in upd_instruments.items():
            if key not in orig_instruments:
                qty = instrument.get("initial_quantity", 0)
                holder = instrument.get("holder_name", "Unknown")
                class_name = instrument.get("class_name", "Unknown")
                diff_items.append(DiffItem(
                    op="add",
                    path=f"/instruments",
                    to=instrument,
                    description=f"Added instrument: {holder} - {qty:,.0f} shares of {class_name}"
                ))
            else:
                # Check for quantity changes
                orig_qty = orig_instruments[key].get("initial_quantity", 0)
                upd_qty = instrument.get("initial_quantity", 0)
                if orig_qty != upd_qty:
                    holder = instrument.get("holder_name", "Unknown")
                    class_name = instrument.get("class_name", "Unknown")
                    diff_items.append(DiffItem(
                        op="replace",
                        path=f"/instruments/quantity",
                        from_value=orig_qty,
                        to=upd_qty,
                        description=f"{holder} {class_name} quantity changed: {orig_qty:,.0f} → {upd_qty:,.0f}"
                    ))
    
    def _diff_rounds(
        self, 
        original: Dict[str, Any], 
        updated: Dict[str, Any], 
        diff_items: List[DiffItem]
    ):
        """Compare financing rounds."""
        orig_rounds = {r["name"]: r for r in original.get("rounds", [])}
        upd_rounds = {r["name"]: r for r in updated.get("rounds", [])}
        
        # New rounds
        for round_name, round_data in upd_rounds.items():
            if round_name not in orig_rounds:
                diff_items.append(DiffItem(
                    op="add",
                    path=f"/rounds/{round_name}",
                    to=round_data,
                    description=f"Added financing round: \"{round_data.get('name')}\""
                ))


# Global executor instance
tool_executor = ToolExecutor()

