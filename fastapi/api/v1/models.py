"""
API v1 Models

Request and response models for API v1.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi.captable.constants import CALCULATION_TYPES, CURRENT_SCHEMA_VERSION


class CapTableRequest(BaseModel):
    """Request model for cap table generation."""
    schema_version: str = Field(..., description="Schema version")
    holders: List[Dict[str, Any]] = Field(..., description="List of holders")
    rounds: List[Dict[str, Any]] = Field(..., description="List of rounds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema_version": "2.0",
                "holders": [
                    {"name": "Founder 1", "group": "Founders"}
                ],
                "rounds": [
                    {
                        "name": "Seed Round",
                        "calculation_type": "valuation_based",
                        "valuation": 1000000,
                        "instruments": []
                    }
                ]
            }
        }


class CapTableResponse(BaseModel):
    """Response model for cap table generation."""
    success: bool = Field(..., description="Whether generation was successful")
    message: str = Field(..., description="Response message")
    filename: Optional[str] = Field(None, description="Generated filename")


class ValidationRequest(BaseModel):
    """Request model for validation."""
    schema_version: str = Field(..., description="Schema version")
    holders: List[Dict[str, Any]] = Field(..., description="List of holders")
    rounds: List[Dict[str, Any]] = Field(..., description="List of rounds")


class ValidationErrorDetail(BaseModel):
    """Detailed validation error."""
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    field: Optional[str] = Field(None, description="Field name if applicable")
    context: Optional[Dict[str, Any]] = Field(None, description="Error context")


class ValidationResponse(BaseModel):
    """Response model for validation."""
    is_valid: bool = Field(..., description="Whether data is valid")
    validation_errors: List[str] = Field(default_factory=list, description="List of error messages")
    error_details: List[ValidationErrorDetail] = Field(default_factory=list, description="Detailed error information")
    summary: Optional[Dict[str, Any]] = Field(None, description="Validation summary")


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    traceback: Optional[str] = Field(None, description="Traceback (only in debug mode)")


class SchemaResponse(BaseModel):
    """Response model for schema information."""
    schema_version: str = Field(..., description="Current schema version")
    schema_url: Optional[str] = Field(None, description="URL to schema definition")
    supported_versions: List[str] = Field(..., description="List of supported schema versions")


class CalculationTypeInfo(BaseModel):
    """Information about a calculation type."""
    name: str = Field(..., description="Calculation type name")
    description: str = Field(..., description="Description of calculation type")
    required_fields: List[str] = Field(..., description="Required fields for this type")


class CalculationTypesResponse(BaseModel):
    """Response model for calculation types."""
    calculation_types: List[CalculationTypeInfo] = Field(..., description="List of calculation types")


class CalculateSharesRequest(BaseModel):
    """Request model for calculating shares."""
    calculation_type: str = Field(..., description="Type of calculation")
    round_data: Dict[str, Any] = Field(..., description="Round data")
    instrument_data: Dict[str, Any] = Field(..., description="Instrument data")


class CalculateSharesResponse(BaseModel):
    """Response model for share calculation."""
    shares: int = Field(..., description="Calculated number of shares")
    formula: Optional[str] = Field(None, description="Excel formula used")
    explanation: Optional[str] = Field(None, description="Explanation of calculation")


class TemplateInfo(BaseModel):
    """Information about a template."""
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    schema_version: str = Field(..., description="Schema version")
    data: Dict[str, Any] = Field(..., description="Template data")


class TemplateResponse(BaseModel):
    """Response model for templates."""
    templates: List[TemplateInfo] = Field(..., description="List of available templates")


class CompareRequest(BaseModel):
    """Request model for comparing cap tables."""
    cap_table_1: Dict[str, Any] = Field(..., description="First cap table")
    cap_table_2: Dict[str, Any] = Field(..., description="Second cap table")


class ComparisonDifference(BaseModel):
    """A difference between two cap tables."""
    type: str = Field(..., description="Type of difference (added, removed, changed)")
    path: str = Field(..., description="JSON path to the difference")
    value_1: Optional[Any] = Field(None, description="Value in first cap table")
    value_2: Optional[Any] = Field(None, description="Value in second cap table")


class CompareResponse(BaseModel):
    """Response model for comparison."""
    are_identical: bool = Field(..., description="Whether cap tables are identical")
    differences: List[ComparisonDifference] = Field(default_factory=list, description="List of differences")
    summary: Optional[Dict[str, Any]] = Field(None, description="Comparison summary")

