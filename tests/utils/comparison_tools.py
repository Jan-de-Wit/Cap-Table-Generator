"""
Comparison Tools

Compare generated Excel files with expected outputs.
"""

from typing import Dict, Any, List
from pathlib import Path
from .excel_reader import ExcelReader


class ComparisonTools:
    """Tools for comparing Excel files."""
    
    @staticmethod
    def compare_sheets(
        reader1: ExcelReader,
        reader2: ExcelReader,
        sheet_name: str
    ) -> Dict[str, Any]:
        """
        Compare two sheets from different workbooks.
        
        Args:
            reader1: First Excel reader
            reader2: Second Excel reader
            sheet_name: Name of sheet to compare
            
        Returns:
            Dictionary with comparison results
        """
        sheet1 = reader1.get_sheet(sheet_name)
        sheet2 = reader2.get_sheet(sheet_name)
        
        if not sheet1 or not sheet2:
            return {
                "match": False,
                "error": f"Sheet {sheet_name} not found in one or both workbooks"
            }
        
        differences = []
        max_row = max(sheet1.max_row, sheet2.max_row)  # type: ignore
        max_col = max(sheet1.max_column, sheet2.max_column)  # type: ignore
        
        for row in range(1, max_row + 1):
            for col in range(1, max_col + 1):
                cell1 = sheet1.cell(row, col).value
                cell2 = sheet2.cell(row, col).value
                
                if cell1 != cell2:
                    cell_address = f"{sheet1.cell(row, col).column_letter}{row}"
                    differences.append({
                        "cell": cell_address,
                        "expected": cell1,
                        "actual": cell2
                    })
        
        return {
            "match": len(differences) == 0,
            "differences": differences,
            "total_cells": max_row * max_col,
            "different_cells": len(differences)
        }
    
    @staticmethod
    def compare_named_ranges(
        reader1: ExcelReader,
        reader2: ExcelReader
    ) -> Dict[str, Any]:
        """
        Compare named ranges between two workbooks.
        
        Args:
            reader1: First Excel reader
            reader2: Second Excel reader
            
        Returns:
            Dictionary with comparison results
        """
        ranges1 = reader1.get_named_ranges()
        ranges2 = reader2.get_named_ranges()
        
        only_in_1 = set(ranges1.keys()) - set(ranges2.keys())
        only_in_2 = set(ranges2.keys()) - set(ranges1.keys())
        common = set(ranges1.keys()) & set(ranges2.keys())
        
        differences = []
        for name in common:
            if ranges1[name] != ranges2[name]:
                differences.append({
                    "name": name,
                    "expected": ranges1[name],
                    "actual": ranges2[name]
                })
        
        return {
            "match": len(only_in_1) == 0 and len(only_in_2) == 0 and len(differences) == 0,
            "only_in_expected": list(only_in_1),
            "only_in_actual": list(only_in_2),
            "differences": differences,
            "common_ranges": len(common)
        }

