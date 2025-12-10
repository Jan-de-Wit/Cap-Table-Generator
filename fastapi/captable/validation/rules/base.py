"""
Base Validation Rule

Base class for all validation rules.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass
from ...errors import ValidationError


@dataclass
class RuleResult:
    """Result of a validation rule check."""
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError] = None
    
    def __post_init__(self):
        """Initialize warnings if not provided."""
        if self.warnings is None:
            self.warnings = []


class ValidationRule(ABC):
    """Base class for validation rules."""
    
    @property
    @abstractmethod
    def rule_name(self) -> str:
        """Rule identifier."""
        pass
    
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> RuleResult:
        """
        Validate data and return result.
        
        Args:
            data: Cap table data dictionary
            
        Returns:
            RuleResult object
        """
        pass
    
    def is_enabled(self, config: Any = None) -> bool:
        """
        Check if rule is enabled.
        
        Args:
            config: Optional validation configuration
            
        Returns:
            True if enabled, False otherwise
        """
        # Default implementation - can be overridden
        if config and hasattr(config, 'disabled_rules'):
            return self.rule_name not in config.disabled_rules
        return True




