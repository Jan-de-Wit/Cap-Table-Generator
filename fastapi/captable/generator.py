"""
Cap Table Generator - Main Orchestrator
Coordinates JSON validation, DLM creation, and Excel generation.
"""

import json
import sys
from typing import Dict, Any, Optional
from pathlib import Path
from .validation import validate_cap_table, CapTableValidator
from .excel import ExcelGenerator
from .errors import ExcelGenerationError
from .monitoring import PerformanceTracker


class CapTableGenerator:
    """Main orchestrator for cap table generation."""
    
    def __init__(self, json_path: Optional[str] = None, json_data: Optional[Dict[str, Any]] = None):
        """
        Initialize generator with JSON data.
        
        Args:
            json_path: Path to JSON file
            json_data: Direct JSON data (alternative to json_path)
        """
        if json_path:
            self.json_path = Path(json_path)
            with open(self.json_path, 'r') as f:
                self.data = json.load(f)
        elif json_data:
            self.json_path = None
            self.data = json_data
        else:
            raise ValueError("Either json_path or json_data must be provided")
        
        self.validation_errors = []
        self.is_valid = False
        self.performance_tracker = PerformanceTracker()
        
    def validate(self) -> bool:
        """
        Validate the cap table data against schema.
        
        Returns:
            True if valid, False otherwise
        """
        with self.performance_tracker.track("validation"):
            self.is_valid, self.validation_errors = validate_cap_table(self.data)
        return self.is_valid
    
    def generate_excel(self, output_path: str, force: bool = False) -> str:
        """
        Generate Excel workbook from cap table data.
        
        Args:
            output_path: Path for output Excel file
            force: If True, generate even with validation errors (not recommended)
            
        Returns:
            Path to generated Excel file
            
        Raises:
            ValueError: If data is invalid and force=False
        """
        if not self.is_valid and not force:
            if not self.validation_errors:
                # Haven't validated yet
                self.validate()
            
            if not self.is_valid:
                error_msg = "Cap table data is invalid:\n" + "\n".join(self.validation_errors)
                raise ExcelGenerationError(
                    error_msg,
                    details={"validation_errors": self.validation_errors}
                )
        
        # Generate Excel with performance tracking
        with self.performance_tracker.track("excel_generation"):
            generator = ExcelGenerator(self.data, output_path)
            result_path = generator.generate()
        
        return result_path
    
    def get_validation_errors(self) -> list:
        """Get list of validation errors."""
        return self.validation_errors
    
    def export_json(self, output_path: str, indent: int = 2):
        """
        Export the current cap table data to JSON file.
        
        Args:
            output_path: Path for output JSON file
            indent: JSON indentation level
        """
        with open(output_path, 'w') as f:
            json.dump(self.data, f, indent=indent)


def generate_from_json(json_path: str, output_path: str) -> str:
    """
    Convenience function to generate Excel from JSON file.
    
    Args:
        json_path: Path to input JSON file
        output_path: Path for output Excel file
        
    Returns:
        Path to generated Excel file
    """
    generator = CapTableGenerator(json_path=json_path)
    
    if not generator.validate():
        error_msg = "Validation errors found:\n"
        for error in generator.get_validation_errors():
            error_msg += f"  - {error}\n"
        print(error_msg, file=sys.stderr)
        raise ValueError("Cap table data is invalid")
    
    return generator.generate_excel(output_path)


def generate_from_data(data: Dict[str, Any], output_path: str) -> str:
    """
    Convenience function to generate Excel from data dictionary.
    
    Args:
        data: Cap table data dictionary
        output_path: Path for output Excel file
        
    Returns:
        Path to generated Excel file
    """
    generator = CapTableGenerator(json_data=data)
    
    if not generator.validate():
        error_msg = "Validation errors found:\n"
        for error in generator.get_validation_errors():
            error_msg += f"  - {error}\n"
        print(error_msg, file=sys.stderr)
        raise ValueError("Cap table data is invalid")
    
    return generator.generate_excel(output_path)

