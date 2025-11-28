"""
Export Service

Export orchestration service.
"""

from typing import Dict, Any, Optional, List
from ..services.cap_table_service import CapTableService
from ..types import CapTableData


class ExportService:
    """Service for export operations."""
    
    def __init__(self):
        """Initialize export service."""
        self.cap_table_service = CapTableService()
    
    def export_excel(
        self,
        data: CapTableData,
        output_path: str,
        force: bool = False
    ) -> str:
        """
        Export cap table to Excel format.
        
        Args:
            data: Cap table data dictionary
            output_path: Path for output Excel file
            force: If True, generate even with validation errors
            
        Returns:
            Path to generated Excel file
        """
        return self.cap_table_service.generate_excel(data, output_path, force=force)
    
    def export_json(
        self,
        data: CapTableData,
        output_path: str,
        indent: int = 2
    ) -> str:
        """
        Export cap table to JSON format.
        
        Args:
            data: Cap table data dictionary
            output_path: Path for output JSON file
            indent: JSON indentation level
            
        Returns:
            Path to exported JSON file
        """
        return self.cap_table_service.export_json(data, output_path, indent=indent)
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported export formats.
        
        Returns:
            List of format names
        """
        return ["excel", "json"]  # Will be expanded with additional formats

