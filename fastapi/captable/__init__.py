"""
Cap Table Generator Package
A comprehensive system for generating dynamic Excel-based capitalization tables.
"""

from .generator import CapTableGenerator, generate_from_json, generate_from_data
from .validation import validate_cap_table, CapTableValidator
from .excel import ExcelGenerator
from .formulas import FormulaResolver
from .dlm import DeterministicLayoutMap, ExcelReference
from .schema import CAP_TABLE_SCHEMA

# Import new modules (with try/except for backward compatibility)
try:
    from . import constants
    from . import types
    from . import errors
    from . import config
    from . import services
    from . import reporting
    from . import monitoring
    from . import cache
    from . import utils
    NEW_MODULES_AVAILABLE = True
except ImportError:
    NEW_MODULES_AVAILABLE = False

__version__ = "1.0.0"
__all__ = [
    "CapTableGenerator",
    "generate_from_json",
    "generate_from_data",
    "validate_cap_table",
    "CapTableValidator",
    "ExcelGenerator",
    "FormulaResolver",
    "DeterministicLayoutMap",
    "ExcelReference",
    "CAP_TABLE_SCHEMA",
]

if NEW_MODULES_AVAILABLE:
    __all__.extend([
        "constants",
        "types",
        "errors",
        "config",
        "services",
        "reporting",
        "monitoring",
        "cache",
        "utils",
    ])
