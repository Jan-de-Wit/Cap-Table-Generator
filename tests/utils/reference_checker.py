"""
Reference Checker

Verify named ranges and references in Excel files.
"""

from typing import List, Dict, Any, Set
from .excel_reader import ExcelReader


class ReferenceChecker:
    """Check Excel references."""
    
    def __init__(self, excel_reader: ExcelReader):
        """
        Initialize reference checker.
        
        Args:
            excel_reader: ExcelReader instance
        """
        self.excel_reader = excel_reader
    
    def check_named_ranges(self) -> Dict[str, Any]:
        """
        Check all named ranges exist and are valid.
        
        Returns:
            Dictionary with check results
        """
        named_ranges = self.excel_reader.get_named_ranges()
        
        results = {
            "total_ranges": len(named_ranges),
            "valid_ranges": [],
            "invalid_ranges": [],
        }
        
        for name, definition in named_ranges.items():
            # Basic validation - check if definition is not empty
            if definition and definition.strip():
                results["valid_ranges"].append({"name": name, "definition": definition})
            else:
                results["invalid_ranges"].append({"name": name, "definition": definition})
        
        return results
    
    def find_circular_references(self) -> List[str]:
        """
        Find potential circular references.
        
        Note: This is a simplified check. Full circular reference
        detection would require more sophisticated analysis.
        
        Returns:
            List of potential circular references
        """
        # This is a placeholder - full implementation would analyze
        # formula dependencies to detect cycles
        return []
    
    def verify_cross_sheet_references(self) -> Dict[str, Any]:
        """
        Verify cross-sheet references are valid.
        
        Returns:
            Dictionary with verification results
        """
        sheet_names = set(self.excel_reader.get_sheet_names())
        results = {
            "valid_references": [],
            "invalid_references": [],
        }
        
        # Check named ranges for cross-sheet references
        named_ranges = self.excel_reader.get_named_ranges()
        for name, definition in named_ranges.items():
            # Extract sheet name from definition (simplified)
            if "!" in definition:
                sheet_name = definition.split("!")[0].strip("'\"")
                if sheet_name in sheet_names:
                    results["valid_references"].append({"name": name, "sheet": sheet_name})
                else:
                    results["invalid_references"].append({"name": name, "sheet": sheet_name})
        
        return results

