"""
Validation Report

Detailed validation reports with error grouping and suggestions.
"""

from typing import List, Dict, Any, Optional
from ..errors import CapTableError, ValidationError
from .error_reporter import ErrorReporter, ErrorSeverity


class ValidationReport:
    """Validation report with detailed information."""
    
    def __init__(self, is_valid: bool, errors: List[CapTableError]):
        """
        Initialize validation report.
        
        Args:
            is_valid: Whether validation passed
            errors: List of validation errors
        """
        self.is_valid = is_valid
        self.errors = errors
        self.error_reporter = ErrorReporter()
        
        # Add all errors to reporter
        for error in errors:
            self.error_reporter.add_error(error)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        return {
            "is_valid": self.is_valid,
            "total_errors": len(self.errors),
            "errors_by_type": self._group_by_type(),
        }
    
    def _group_by_type(self) -> Dict[str, int]:
        """Group errors by type."""
        groups: Dict[str, int] = {}
        for error in self.errors:
            error_type = type(error).__name__
            groups[error_type] = groups.get(error_type, 0) + 1
        return groups
    
    def get_errors_by_field(self) -> Dict[str, List[CapTableError]]:
        """Group errors by field name."""
        by_field: Dict[str, List[CapTableError]] = {}
        for error in self.errors:
            if isinstance(error, ValidationError) and error.details.get("field"):
                field = error.details["field"]
                if field not in by_field:
                    by_field[field] = []
                by_field[field].append(error)
        return by_field
    
    def get_errors_by_round(self) -> Dict[str, List[CapTableError]]:
        """Group errors by round name."""
        by_round: Dict[str, List[CapTableError]] = {}
        for error in self.errors:
            round_name = error.context.get("round_name")
            if round_name:
                if round_name not in by_round:
                    by_round[round_name] = []
                by_round[round_name].append(error)
        return by_round
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "is_valid": self.is_valid,
            "summary": self.get_summary(),
            "errors": [error.to_dict() for error in self.errors],
            "errors_by_field": {
                field: [e.to_dict() for e in errors]
                for field, errors in self.get_errors_by_field().items()
            },
            "errors_by_round": {
                round_name: [e.to_dict() for e in errors]
                for round_name, errors in self.get_errors_by_round().items()
            },
        }


class ValidationReportGenerator:
    """Generate validation reports."""
    
    @staticmethod
    def generate(
        is_valid: bool,
        errors: List[CapTableError],
        include_suggestions: bool = True
    ) -> ValidationReport:
        """
        Generate validation report.
        
        Args:
            is_valid: Whether validation passed
            errors: List of validation errors
            include_suggestions: Whether to include fix suggestions
            
        Returns:
            ValidationReport object
        """
        report = ValidationReport(is_valid, errors)
        
        if include_suggestions:
            # Add suggestions to errors (could be enhanced)
            for error in errors:
                if isinstance(error, ValidationError):
                    suggestion = ValidationReportGenerator._get_suggestion(error)
                    if suggestion:
                        error.details["suggestion"] = suggestion
        
        return report
    
    @staticmethod
    def _get_suggestion(error: ValidationError) -> Optional[str]:
        """Get fix suggestion for error."""
        error_code = error.error_code
        
        suggestions = {
            "VALIDATION_ERROR": "Check the field value and ensure it meets the requirements.",
            "SCHEMA_ERROR": "Verify the data structure matches the expected schema.",
            "RELATIONSHIP_ERROR": "Check that all referenced entities exist.",
            "BUSINESS_RULE_ERROR": "Review the business rule that was violated.",
        }
        
        return suggestions.get(error_code)

