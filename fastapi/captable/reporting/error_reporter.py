"""
Error Reporter

Structured error reporting with severity levels and aggregation.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from ..errors import CapTableError, aggregate_errors


class ErrorSeverity(Enum):
    """Error severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ErrorReporter:
    """Structured error reporting."""
    
    def __init__(self):
        """Initialize error reporter."""
        self.errors: List[CapTableError] = []
        self.warnings: List[CapTableError] = []
        self.info: List[CapTableError] = []
    
    def add_error(self, error: CapTableError) -> None:
        """Add an error."""
        self.errors.append(error)
    
    def add_warning(self, error: CapTableError) -> None:
        """Add a warning."""
        self.warnings.append(error)
    
    def add_info(self, error: CapTableError) -> None:
        """Add an info message."""
        self.info.append(error)
    
    def add(self, error: CapTableError, severity: ErrorSeverity = ErrorSeverity.ERROR) -> None:
        """Add error with specified severity."""
        if severity == ErrorSeverity.ERROR:
            self.add_error(error)
        elif severity == ErrorSeverity.WARNING:
            self.add_warning(error)
        elif severity == ErrorSeverity.INFO:
            self.add_info(error)
    
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    def get_all_errors(self) -> List[CapTableError]:
        """Get all errors (errors, warnings, info)."""
        return self.errors + self.warnings + self.info
    
    def get_summary(self) -> Dict[str, Any]:
        """Get error summary."""
        return {
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "total_info": len(self.info),
            "has_errors": self.has_errors(),
            "has_warnings": self.has_warnings(),
        }
    
    def get_report(self) -> Dict[str, Any]:
        """Get complete error report."""
        return {
            "summary": self.get_summary(),
            "errors": aggregate_errors(self.errors),
            "warnings": aggregate_errors(self.warnings),
            "info": aggregate_errors(self.info),
        }
    
    def clear(self) -> None:
        """Clear all errors."""
        self.errors.clear()
        self.warnings.clear()
        self.info.clear()
    
    def export_json(self) -> Dict[str, Any]:
        """Export errors as JSON-serializable dictionary."""
        return self.get_report()
    
    def export_text(self) -> str:
        """Export errors as human-readable text."""
        lines = []
        
        if self.errors:
            lines.append("ERRORS:")
            for error in self.errors:
                lines.append(f"  - {error}")
        
        if self.warnings:
            lines.append("\nWARNINGS:")
            for warning in self.warnings:
                lines.append(f"  - {warning}")
        
        if self.info:
            lines.append("\nINFO:")
            for info in self.info:
                lines.append(f"  - {info}")
        
        if not lines:
            lines.append("No errors, warnings, or info messages.")
        
        return "\n".join(lines)

