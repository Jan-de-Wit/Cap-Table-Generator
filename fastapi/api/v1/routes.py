"""
API v1 Routes

Version 1 API endpoints.
"""

import tempfile
import os
from pathlib import Path
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from fastapi.responses import FileResponse, JSONResponse

from ..v1.models import (
    CapTableRequest,
    CapTableResponse,
    ValidationRequest,
    ValidationResponse,
    ValidationErrorDetail,
    ErrorResponse,
    SchemaResponse,
    CalculationTypesResponse,
    CalculationTypeInfo,
    CalculateSharesRequest,
    CalculateSharesResponse,
    TemplateResponse,
    TemplateInfo,
    CompareRequest,
    CompareResponse,
    ComparisonDifference,
)

# Import services and utilities
# Import with fallback for different paths
import sys
from pathlib import Path

# Determine captable path relative to this file
# fastapi/api/v1/routes.py -> fastapi/captable
current_file = Path(__file__).resolve()
captable_path = current_file.parent.parent.parent / "captable"

# Add fastapi to path if needed
if captable_path.exists():
    fastapi_path = captable_path.parent
    if str(fastapi_path) not in sys.path:
        sys.path.insert(0, str(fastapi_path))

# Now import
from captable.services import CapTableService, ValidationService, ExportService
from captable.errors import CapTableError, ExcelGenerationError
from captable.constants import (
    CALCULATION_TYPES,
    CURRENT_SCHEMA_VERSION,
    CALC_TYPE_FIXED_SHARES,
    CALC_TYPE_TARGET_PERCENTAGE,
    CALC_TYPE_VALUATION_BASED,
    CALC_TYPE_CONVERTIBLE,
    CALC_TYPE_SAFE,
)
from captable.monitoring import PerformanceTracker
from captable.reporting import ValidationReportGenerator
from fastapi.captable.constants import (
    CALCULATION_TYPES,
    CURRENT_SCHEMA_VERSION,
    CALC_TYPE_FIXED_SHARES,
    CALC_TYPE_TARGET_PERCENTAGE,
    CALC_TYPE_VALUATION_BASED,
    CALC_TYPE_CONVERTIBLE,
    CALC_TYPE_SAFE,
)
from fastapi.captable.monitoring import PerformanceTracker
from fastapi.captable.reporting import ValidationReportGenerator

router = APIRouter(prefix="/api/v1", tags=["v1"])

# Initialize services
cap_table_service = CapTableService()
validation_service = ValidationService()
export_service = ExportService()
performance_tracker = PerformanceTracker()


def cleanup_file(file_path: str):
    """Background task to clean up temporary file."""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        print(f"Warning: Failed to cleanup file {file_path}: {e}", file=__import__("sys").stderr)


@router.post("/generate-excel", response_model=CapTableResponse)
async def generate_excel(
    request: CapTableRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate Excel file from cap table JSON data.
    
    Args:
        request: Cap table data in JSON format
        
    Returns:
        Excel file as binary response
    """
    try:
        with performance_tracker.track("excel_generation"):
            data = request.model_dump()
            
            # Validate the data
            validation_report = validation_service.validate(data, include_suggestions=True)
            if not validation_report.is_valid:
                error_details = [
                    ValidationErrorDetail(
                        error_code=error.error_code,
                        message=error.message,
                        field=error.details.get("field"),
                        context=error.context
                    )
                    for error in validation_report.errors
                ]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "Validation failed",
                        "validation_errors": [str(e) for e in validation_report.errors],
                        "error_details": [detail.dict() for detail in error_details],
                        "summary": validation_report.get_summary()
                    }
                )
            
            # Create temporary file for Excel output
            excel_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
                    excel_path = tmp_file.name
                
                # Generate Excel file using service
                result_path = cap_table_service.generate_excel(data, excel_path)
                
                # Schedule cleanup after response is sent
                background_tasks.add_task(cleanup_file, excel_path)
                
                # Return the Excel file
                return FileResponse(
                    result_path,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    filename="cap-table.xlsx",
                    headers={
                        "Content-Disposition": 'attachment; filename="cap-table.xlsx"'
                    }
                )
            except Exception as e:
                # Clean up on error
                if excel_path and os.path.exists(excel_path):
                    try:
                        os.unlink(excel_path)
                    except:
                        pass
                raise
    
    except HTTPException:
        raise
    except CapTableError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error=e.message,
                error_code=e.error_code,
                details=e.details
            ).dict()
        )
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        print(f"ERROR: {error_msg}", file=__import__("sys").stderr)
        print(traceback_str, file=__import__("sys").stderr)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error=error_msg,
                traceback=traceback_str if os.environ.get("DEBUG") else None
            ).dict()
        )


@router.post("/validate", response_model=ValidationResponse)
async def validate_cap_table_endpoint(request: ValidationRequest):
    """
    Validate cap table JSON data without generating Excel.
    
    Args:
        request: Cap table data in JSON format
        
    Returns:
        Validation result with errors if any
    """
    try:
        with performance_tracker.track("validation"):
            data = request.model_dump()
            validation_report = validation_service.validate(data, include_suggestions=True)
            
            error_details = [
                ValidationErrorDetail(
                    error_code=error.error_code,
                    message=error.message,
                    field=error.details.get("field"),
                    context=error.context
                )
                for error in validation_report.errors
            ]
            
            return ValidationResponse(
                is_valid=validation_report.is_valid,
                validation_errors=[str(e) for e in validation_report.errors],
                error_details=error_details,
                summary=validation_report.get_summary()
            )
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        print(f"ERROR: {error_msg}", file=__import__("sys").stderr)
        print(traceback_str, file=__import__("sys").stderr)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error=error_msg,
                traceback=traceback_str if os.environ.get("DEBUG") else None
            ).dict()
        )


@router.get("/schema", response_model=SchemaResponse)
async def get_schema():
    """
    Get current schema information.
    
    Returns:
        Schema version and supported versions
    """
    return SchemaResponse(
        schema_version=CURRENT_SCHEMA_VERSION,
        supported_versions=[CURRENT_SCHEMA_VERSION]
    )


@router.get("/calculation-types", response_model=CalculationTypesResponse)
async def get_calculation_types():
    """
    Get list of supported calculation types.
    
    Returns:
        List of calculation types with descriptions
    """
    calculation_type_info = {
        CALC_TYPE_FIXED_SHARES: {
            "description": "Direct share allocation with fixed quantities",
            "required_fields": ["initial_quantity"]
        },
        CALC_TYPE_TARGET_PERCENTAGE: {
            "description": "Calculate shares to achieve target ownership percentage",
            "required_fields": ["target_percentage"]
        },
        CALC_TYPE_VALUATION_BASED: {
            "description": "Calculate shares based on investment amount and valuation",
            "required_fields": ["investment_amount", "valuation"]
        },
        CALC_TYPE_CONVERTIBLE: {
            "description": "Convertible note with interest and discount",
            "required_fields": ["investment_amount", "interest_rate", "discount_rate"]
        },
        CALC_TYPE_SAFE: {
            "description": "SAFE (Simple Agreement for Future Equity)",
            "required_fields": ["investment_amount", "discount_rate"]
        },
    }
    
    types = [
        CalculationTypeInfo(
            name=calc_type,
            description=calculation_type_info.get(calc_type, {}).get("description", ""),
            required_fields=calculation_type_info.get(calc_type, {}).get("required_fields", [])
        )
        for calc_type in CALCULATION_TYPES
    ]
    
    return CalculationTypesResponse(calculation_types=types)


@router.post("/calculate-shares", response_model=CalculateSharesResponse)
async def calculate_shares(request: CalculateSharesRequest):
    """
    Calculate shares for a specific instrument.
    
    Args:
        request: Calculation request with instrument and round data
        
    Returns:
        Calculated shares and formula
    """
    try:
        # This is a simplified implementation
        # Full implementation would use the formula modules
        calc_type = request.calculation_type
        instrument = request.instrument_data
        round_data = request.round_data
        
        if calc_type == CALC_TYPE_FIXED_SHARES:
            shares = instrument.get("initial_quantity", 0)
            formula = f"={shares}"
            explanation = "Fixed shares: direct quantity allocation"
        elif calc_type == CALC_TYPE_VALUATION_BASED:
            investment = instrument.get("investment_amount", 0)
            valuation = round_data.get("valuation", 1)
            # Simplified calculation
            shares = int((investment / valuation) * 1000000)  # Simplified
            formula = f"=ROUND(({investment} / {valuation}) * pre_round_shares, 0)"
            explanation = "Valuation-based: investment / valuation * pre-round shares"
        else:
            shares = 0
            formula = "=0"
            explanation = "Calculation not yet implemented for this type"
        
        return CalculateSharesResponse(
            shares=shares,
            formula=formula,
            explanation=explanation
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(error=str(e)).dict()
        )


@router.get("/templates", response_model=TemplateResponse)
async def get_templates():
    """
    Get example cap table templates.
    
    Returns:
        List of available templates
    """
    # Load templates from examples directory
    examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
    templates = []
    
    if examples_dir.exists():
        for json_file in examples_dir.glob("*.json"):
            try:
                import json
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                templates.append(
                    TemplateInfo(
                        name=json_file.stem.replace("_", " ").title(),
                        description=f"Example cap table from {json_file.name}",
                        schema_version=data.get("schema_version", CURRENT_SCHEMA_VERSION),
                        data=data
                    )
                )
            except Exception:
                continue
    
    return TemplateResponse(templates=templates)


@router.post("/compare", response_model=CompareResponse)
async def compare_cap_tables(request: CompareRequest):
    """
    Compare two cap tables and identify differences.
    
    Args:
        request: Two cap tables to compare
        
    Returns:
        Comparison result with differences
    """
    try:
        import json
        
        # Simple comparison - convert to JSON strings and compare
        data1_str = json.dumps(request.cap_table_1, sort_keys=True)
        data2_str = json.dumps(request.cap_table_2, sort_keys=True)
        
        are_identical = data1_str == data2_str
        
        differences = []
        if not are_identical:
            # Simplified difference detection
            # Full implementation would do deep comparison
            differences.append(
                ComparisonDifference(
                    type="changed",
                    path="root",
                    value_1="Cap Table 1",
                    value_2="Cap Table 2"
                )
            )
        
        return CompareResponse(
            are_identical=are_identical,
            differences=differences,
            summary={
                "total_differences": len(differences)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(error=str(e)).dict()
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}

