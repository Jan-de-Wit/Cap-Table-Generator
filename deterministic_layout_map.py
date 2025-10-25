"""
Deterministic Layout Map (DLM)
Maps JSON entities/UUIDs to Excel cell addresses, Named Ranges, and Structured References.
Provides the bridge between abstract JSON data and physical Excel coordinates.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ExcelReference:
    """Represents an Excel reference with metadata."""
    reference_type: str  # 'named_range', 'structured_reference', 'cell_reference'
    address: str  # The actual Excel reference (e.g., 'Summary!Total_FDS', 'Ledger[@[shares]]')
    sheet_name: str
    row: Optional[int] = None
    col: Optional[int] = None
    table_name: Optional[str] = None
    column_name: Optional[str] = None


class DeterministicLayoutMap:
    """
    Tracks the mapping between JSON data and Excel locations during workbook generation.
    Provides methods to resolve symbolic references and UUIDs to Excel addresses.
    """
    
    def __init__(self):
        # UUID to Excel reference mapping
        self.uuid_map: Dict[str, ExcelReference] = {}
        
        # Named ranges (global constants on Summary sheet)
        self.named_ranges: Dict[str, ExcelReference] = {}
        
        # Structured table references
        self.tables: Dict[str, Dict[str, Any]] = {}  # table_name -> metadata
        
        # Sheet structure tracking
        self.sheet_rows: Dict[str, int] = {}  # sheet_name -> current_row
        self.sheet_cols: Dict[str, Dict[str, int]] = {}  # sheet_name -> {col_name: col_idx}
        
        # JSON Pointer to Excel reference mapping
        self.pointer_map: Dict[str, ExcelReference] = {}
        
    def register_named_range(self, name: str, sheet: str, row: int, col: int) -> str:
        """
        Register a Named Range for a global constant.
        
        Args:
            name: Named range identifier (e.g., 'Total_FDS')
            sheet: Sheet name
            row: Row index (0-based)
            col: Column index (0-based)
            
        Returns:
            Excel reference string (e.g., 'Summary!Total_FDS' or just 'Total_FDS')
        """
        ref = ExcelReference(
            reference_type='named_range',
            address=name,
            sheet_name=sheet,
            row=row,
            col=col
        )
        self.named_ranges[name] = ref
        return name
    
    def register_table(self, table_name: str, sheet: str, start_row: int, 
                      start_col: int, columns: List[str]) -> None:
        """
        Register an Excel Table with column headers.
        
        Args:
            table_name: Name of the Excel Table
            sheet: Sheet name
            start_row: Starting row (0-based)
            start_col: Starting column (0-based)
            columns: List of column header names
        """
        self.tables[table_name] = {
            'sheet': sheet,
            'start_row': start_row,
            'start_col': start_col,
            'columns': {col: idx for idx, col in enumerate(columns)},
            'column_list': columns
        }
    
    def register_table_row(self, table_name: str, row_idx: int, 
                          uuid: Optional[str] = None, 
                          json_pointer: Optional[str] = None) -> None:
        """
        Register a row in an Excel Table, mapping it to a UUID or JSON pointer.
        
        Args:
            table_name: Name of the Excel Table
            row_idx: Row index within the table (data rows, 0-based)
            uuid: Optional UUID for this row's entity
            json_pointer: Optional JSON Pointer path
        """
        if table_name not in self.tables:
            raise ValueError(f"Table '{table_name}' not registered")
        
        table = self.tables[table_name]
        actual_row = table['start_row'] + 1 + row_idx  # +1 for header row
        
        if uuid:
            # Register reference for each column in this row
            for col_name, col_idx in table['columns'].items():
                ref = ExcelReference(
                    reference_type='structured_reference',
                    address=f"{table_name}[@[{col_name}]]",
                    sheet_name=table['sheet'],
                    row=actual_row,
                    col=table['start_col'] + col_idx,
                    table_name=table_name,
                    column_name=col_name
                )
                # Store with UUID and column name as key
                self.uuid_map[f"{uuid}.{col_name}"] = ref
        
        if json_pointer:
            # Similar registration for JSON pointer
            for col_name, col_idx in table['columns'].items():
                ref = ExcelReference(
                    reference_type='structured_reference',
                    address=f"{table_name}[@[{col_name}]]",
                    sheet_name=table['sheet'],
                    row=actual_row,
                    col=table['start_col'] + col_idx,
                    table_name=table_name,
                    column_name=col_name
                )
                self.pointer_map[f"{json_pointer}.{col_name}"] = ref
    
    def register_cell(self, identifier: str, sheet: str, row: int, col: int,
                     is_absolute: bool = True) -> str:
        """
        Register a cell reference.
        
        Args:
            identifier: UUID or JSON pointer
            sheet: Sheet name
            row: Row index (0-based)
            col: Column index (0-based)
            is_absolute: Whether to use absolute reference ($A$1) or relative (A1)
            
        Returns:
            Excel reference string
        """
        col_letter = self._col_index_to_letter(col)
        if is_absolute:
            address = f"${col_letter}${row + 1}"
        else:
            address = f"{col_letter}{row + 1}"
        
        if sheet:
            full_address = f"{sheet}!{address}"
        else:
            full_address = address
        
        ref = ExcelReference(
            reference_type='cell_reference',
            address=full_address,
            sheet_name=sheet,
            row=row,
            col=col
        )
        
        self.uuid_map[identifier] = ref
        self.pointer_map[identifier] = ref
        
        return full_address
    
    def resolve_reference(self, identifier: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Resolve a symbolic identifier (UUID, JSON pointer, or named range) to Excel reference.
        
        Args:
            identifier: UUID, JSON pointer, or symbolic name
            context: Optional context for structured references (current row)
            
        Returns:
            Excel reference string or None if not found
        """
        # Check named ranges first
        if identifier in self.named_ranges:
            return self.named_ranges[identifier].address
        
        # Check UUID map
        if identifier in self.uuid_map:
            return self.uuid_map[identifier].address
        
        # Check pointer map
        if identifier in self.pointer_map:
            return self.pointer_map[identifier].address
        
        return None
    
    def get_structured_reference(self, table_name: str, column_name: str, 
                                 current_row: bool = True) -> Optional[str]:
        """
        Generate a structured reference for an Excel Table column.
        
        Args:
            table_name: Name of the Excel Table
            column_name: Column header name
            current_row: If True, use [@[column]] syntax for current row
            
        Returns:
            Structured reference string
        """
        if table_name not in self.tables:
            return None
        
        if column_name not in self.tables[table_name]['columns']:
            return None
        
        if current_row:
            return f"{table_name}[@[{column_name}]]"
        else:
            return f"{table_name}[[{column_name}]]"
    
    def get_table_column_range(self, table_name: str, column_name: str) -> Optional[str]:
        """
        Get the entire column range reference for a table column.
        
        Args:
            table_name: Name of the Excel Table
            column_name: Column header name
            
        Returns:
            Column range reference (e.g., 'Ledger[shares]')
        """
        if table_name not in self.tables:
            return None
        
        if column_name not in self.tables[table_name]['columns']:
            return None
        
        return f"{table_name}[[{column_name}]]"
    
    def _col_index_to_letter(self, col_idx: int) -> str:
        """Convert 0-based column index to Excel column letter(s)."""
        result = []
        col_idx += 1  # Convert to 1-based
        while col_idx > 0:
            col_idx -= 1
            result.append(chr(col_idx % 26 + ord('A')))
            col_idx //= 26
        return ''.join(reversed(result))
    
    def get_cell_address(self, sheet: str, row: int, col: int, absolute: bool = True) -> str:
        """
        Generate a cell address string.
        
        Args:
            sheet: Sheet name (empty string for no sheet prefix)
            row: Row index (0-based)
            col: Column index (0-based)
            absolute: Use absolute reference ($A$1)
            
        Returns:
            Cell address string
        """
        col_letter = self._col_index_to_letter(col)
        if absolute:
            address = f"${col_letter}${row + 1}"
        else:
            address = f"{col_letter}{row + 1}"
        
        if sheet:
            return f"{sheet}!{address}"
        return address

