"""
Error Handling

Structured error types with context and error codes for better error reporting.
"""

from typing import Dict, Any, Optional, List
from .constants import (
    ERROR_CODE_VALIDATION,
    ERROR_CODE_FORMULA_GENERATION,
    ERROR_CODE_REFERENCE_RESOLUTION,
    ERROR_CODE_EXCEL_GENERATION,
    ERROR_CODE_SCHEMA,
    ERROR_CODE_RELATIONSHIP,
    ERROR_CODE_BUSINESS_RULE,
)


class CapTableError(Exception):
    """Base exception for cap table errors."""
    
    def __init__(
        self,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize cap table error.
        
        Args:
            error_code: Unique error code identifier
            message: Human-readable error message
            details: Additional error details
            context: Context information (round, instrument, holder, etc.)
        """
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.context = context or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON serialization."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "context": self.context
        }
    
    def __str__(self) -> str:
        """String representation of error."""
        context_str = ""
        if self.context:
            context_parts = [f"{k}={v}" for k, v in self.context.items()]
            context_str = f" ({', '.join(context_parts)})"
        return f"[{self.error_code}] {self.message}{context_str}"


class ValidationError(CapTableError):
    """Validation-related errors."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Any = None,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Initialize validation error."""
        error_code = ERROR_CODE_VALIDATION
        if field:
            details = details or {}
            details["field"] = field
            if value is not None:
                details["value"] = value
        
        super().__init__(error_code, message, details, context)


class SchemaError(ValidationError):
    """Schema validation errors."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Any = None,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Initialize schema error."""
        error_code = ERROR_CODE_SCHEMA
        super().__init__(message, field, value, details, context)
        self.error_code = error_code


class RelationshipError(ValidationError):
    """Relationship validation errors."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Any = None,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Initialize relationship error."""
        error_code = ERROR_CODE_RELATIONSHIP
        super().__init__(message, field, value, details, context)
        self.error_code = error_code


class BusinessRuleError(ValidationError):
    """Business rule validation errors."""
    
    def __init__(
        self,
        message: str,
        rule_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Initialize business rule error."""
        error_code = ERROR_CODE_BUSINESS_RULE
        if rule_name:
            details = details or {}
            details["rule_name"] = rule_name
        
        super().__init__(message, None, None, details, context)
        self.error_code = error_code


class FormulaGenerationError(CapTableError):
    """Formula generation errors."""
    
    def __init__(
        self,
        message: str,
        calculation_type: Optional[str] = None,
        instrument: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Initialize formula generation error."""
        error_code = ERROR_CODE_FORMULA_GENERATION
        if calculation_type:
            details = details or {}
            details["calculation_type"] = calculation_type
        if instrument:
            context = context or {}
            context["instrument"] = instrument
        
        super().__init__(error_code, message, details, context)


class ReferenceResolutionError(CapTableError):
    """Reference resolution errors."""
    
    def __init__(
        self,
        message: str,
        reference: Optional[str] = None,
        reference_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Initialize reference resolution error."""
        error_code = ERROR_CODE_REFERENCE_RESOLUTION
        if reference:
            details = details or {}
            details["reference"] = reference
        if reference_type:
            details = details or {}
            details["reference_type"] = reference_type
        
        super().__init__(error_code, message, details, context)


class ExcelGenerationError(CapTableError):
    """Excel generation errors."""
    
    def __init__(
        self,
        message: str,
        sheet_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Initialize Excel generation error."""
        error_code = ERROR_CODE_EXCEL_GENERATION
        if sheet_name:
            details = details or {}
            details["sheet_name"] = sheet_name
        
        super().__init__(error_code, message, details, context)


def aggregate_errors(errors: List[CapTableError]) -> Dict[str, Any]:
    """
    Aggregate multiple errors into a structured response.
    
    Args:
        errors: List of error objects
        
    Returns:
        Dictionary with aggregated error information
    """
    error_dicts = [error.to_dict() for error in errors]
    
    # Group by error code
    by_code: Dict[str, List[Dict[str, Any]]] = {}
    for error_dict in error_dicts:
        code = error_dict["error_code"]
        if code not in by_code:
            by_code[code] = []
        by_code[code].append(error_dict)
    
    return {
        "total_errors": len(errors),
        "errors_by_code": by_code,
        "all_errors": error_dicts
    }





