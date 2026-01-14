"""
Type Definitions

Type aliases, Protocol definitions, and TypedDict structures for type safety.
"""

from typing import Dict, List, Any, Optional, Union, TypedDict, Protocol
from typing_extensions import NotRequired


# Type Aliases
CapTableData = Dict[str, Any]
RoundData = Dict[str, Any]
InstrumentData = Dict[str, Any]
HolderData = Dict[str, Any]
ValidationErrors = List[str]
ExcelReference = str


# TypedDict Definitions
class RoundDict(TypedDict):
    """Type definition for round data structure."""
    name: str
    calculation_type: str
    round_date: NotRequired[str]
    valuation: NotRequired[float]
    valuation_basis: NotRequired[str]
    price_per_share: NotRequired[float]
    instruments: List[InstrumentData]
    conversion_round_ref: NotRequired[str]


class InstrumentDict(TypedDict):
    """Type definition for instrument data structure."""
    holder_name: str
    class_name: str
    initial_quantity: NotRequired[int]
    target_percentage: NotRequired[float]
    target_is_top_up: NotRequired[bool]
    investment_amount: NotRequired[float]
    interest_rate: NotRequired[float]
    discount_rate: NotRequired[float]
    payment_date: NotRequired[str]
    expected_conversion_date: NotRequired[str]
    interest_type: NotRequired[str]
    valuation_cap_type: NotRequired[str]
    valuation_cap: NotRequired[float]
    pro_rata_rights: NotRequired[str]
    pro_rata_percentage: NotRequired[float]
    exercise_type: NotRequired[str]
    partial_exercise_amount: NotRequired[float]
    partial_exercise_percentage: NotRequired[float]


class HolderDict(TypedDict):
    """Type definition for holder data structure."""
    name: str
    group: NotRequired[str]
    description: NotRequired[str]


class CapTableDict(TypedDict):
    """Type definition for complete cap table structure."""
    schema_version: str
    holders: List[HolderDict]
    rounds: List[RoundDict]


# Protocol Definitions
class CalculationType(Protocol):
    """Protocol for calculation type implementations."""
    
    def calculate_shares(
        self, 
        instrument: InstrumentData, 
        round_data: RoundData
    ) -> str:
        """Generate Excel formula for shares calculation."""
        ...
    
    def get_columns(self) -> List[str]:
        """Get required columns for this calculation type."""
        ...
    
    def validate_instrument(self, instrument: InstrumentData) -> List[str]:
        """Validate instrument data."""
        ...


class ValidationRule(Protocol):
    """Protocol for validation rule implementations."""
    
    def validate(self, data: CapTableData) -> List[str]:
        """Validate and return error messages."""
        ...
    
    @property
    def rule_name(self) -> str:
        """Rule identifier."""
        ...


class Exporter(Protocol):
    """Protocol for export format implementations."""
    
    def export(self, data: CapTableData, output_path: str) -> str:
        """Export cap table to file."""
        ...
    
    def validate_format(self, data: CapTableData) -> bool:
        """Validate data for this format."""
        ...


# Union Types
CalculationTypeName = Union[
    str  # Will be one of the CALC_TYPE_* constants
]

ProRataTypeName = Union[
    str  # Will be one of the PRO_RATA_* constants
]

ValuationBasisName = Union[
    str  # Will be one of the VALUATION_BASIS_* constants
]





