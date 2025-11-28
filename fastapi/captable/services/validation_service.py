"""
Validation Service

Validation orchestration service.
"""

from typing import Dict, Any, List
from ..validation import validate_cap_table, CapTableValidator
from ..errors import ValidationError, CapTableError, BusinessRuleError
from ..reporting import ValidationReportGenerator, ValidationReport
from ..types import CapTableData


class ValidationService:
    """Service for validation operations."""
    
    def __init__(self):
        """Initialize validation service."""
        pass
    
    def validate(
        self,
        data: CapTableData,
        include_suggestions: bool = True
    ) -> ValidationReport:
        """
        Validate cap table data and generate report.
        
        Args:
            data: Cap table data dictionary
            include_suggestions: Whether to include fix suggestions
            
        Returns:
            ValidationReport object
        """
        # Use the validator which now includes enhanced rules
        validator = CapTableValidator()
        is_valid, error_messages = validator.validate(data)
        
        # Convert error messages to ValidationError objects
        # Try to extract context from error messages
        errors: List[CapTableError] = []
        for error_msg in error_messages:
            # Check if it's a business rule error (starts with rule name)
            if ":" in error_msg:
                parts = error_msg.split(":", 1)
                rule_name = parts[0].strip()
                message = parts[1].strip() if len(parts) > 1 else error_msg
                
                # Try to create appropriate error type
                if "ownership" in rule_name.lower() or "pro rata" in rule_name.lower():
                    error = BusinessRuleError(
                        message=message,
                        rule_name=rule_name,
                        details={"original_message": error_msg}
                    )
                else:
                    error = ValidationError(
                        message=message,
                        details={"original_message": error_msg, "rule_name": rule_name}
                    )
            else:
                error = ValidationError(
                    message=error_msg,
                    details={"original_message": error_msg}
                )
            errors.append(error)
        
        return ValidationReportGenerator.generate(
            is_valid,
            errors,
            include_suggestions=include_suggestions
        )
    
    def validate_field(
        self,
        data: CapTableData,
        field_path: str
    ) -> List[str]:
        """
        Validate specific field in cap table data.
        
        Args:
            data: Cap table data dictionary
            field_path: JSON path to field (e.g., "rounds[0].name")
            
        Returns:
            List of validation error messages for this field
        """
        # Full validation and filter by field
        report = self.validate(data, include_suggestions=False)
        field_errors = report.get_errors_by_field()
        
        # Extract field name from path
        field_name = field_path.split(".")[-1].split("[")[0]
        
        if field_name in field_errors:
            return [str(e) for e in field_errors[field_name]]
        
        return []

