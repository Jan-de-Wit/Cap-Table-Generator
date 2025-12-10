"""
Cap Table Service

Main business logic service for cap table operations.
"""

from typing import Dict, Any, Optional
from ..generator import CapTableGenerator
from ..errors import CapTableError, ExcelGenerationError
from ..types import CapTableData


class CapTableService:
    """Service for cap table business logic."""
    
    def __init__(self):
        """Initialize cap table service."""
        pass
    
    def validate_cap_table(self, data: CapTableData) -> tuple[bool, list[str]]:
        """
        Validate cap table data.
        
        Args:
            data: Cap table data dictionary
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        generator = CapTableGenerator(json_data=data)
        is_valid = generator.validate()
        errors = generator.get_validation_errors() if not is_valid else []
        return is_valid, errors
    
    def generate_excel(
        self,
        data: CapTableData,
        output_path: str,
        force: bool = False
    ) -> str:
        """
        Generate Excel file from cap table data.
        
        Args:
            data: Cap table data dictionary
            output_path: Path for output Excel file
            force: If True, generate even with validation errors
            
        Returns:
            Path to generated Excel file
            
        Raises:
            ExcelGenerationError: If generation fails
        """
        try:
            generator = CapTableGenerator(json_data=data)
            
            if not force:
                if not generator.validate():
                    errors = generator.get_validation_errors()
                    error_msg = "Cap table data is invalid:\n" + "\n".join(errors)
                    raise ExcelGenerationError(
                        error_msg,
                        details={"validation_errors": errors}
                    )
            
            result_path = generator.generate_excel(output_path, force=force)
            return result_path
        
        except CapTableError:
            raise
        except Exception as e:
            raise ExcelGenerationError(
                f"Failed to generate Excel: {str(e)}",
                details={"original_error": str(e)}
            ) from e
    
    def export_json(
        self,
        data: CapTableData,
        output_path: str,
        indent: int = 2
    ) -> str:
        """
        Export cap table data to JSON file.
        
        Args:
            data: Cap table data dictionary
            output_path: Path for output JSON file
            indent: JSON indentation level
            
        Returns:
            Path to exported JSON file
        """
        generator = CapTableGenerator(json_data=data)
        generator.export_json(output_path, indent=indent)
        return output_path




