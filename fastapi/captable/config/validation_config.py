"""
Validation Configuration

Validation rules and settings configuration.
"""

from typing import Dict, Set
from pydantic import BaseModel, Field


class ValidationConfig(BaseModel):
    """Validation configuration."""
    
    # Rule enablement
    enable_schema_validation: bool = Field(default=True, description="Enable schema validation")
    enable_relationship_validation: bool = Field(default=True, description="Enable relationship validation")
    enable_business_rules: bool = Field(default=True, description="Enable business rules")
    
    # Ownership rules
    enable_ownership_validation: bool = Field(default=True, description="Enable ownership validation")
    max_ownership_percentage: float = Field(default=100.0, description="Maximum ownership percentage")
    min_ownership_percentage: float = Field(default=0.0, description="Minimum ownership percentage")
    
    # Valuation rules
    enable_valuation_validation: bool = Field(default=True, description="Enable valuation validation")
    valuation_tolerance: float = Field(default=0.01, description="Valuation calculation tolerance")
    
    # Financial rules
    enable_financial_validation: bool = Field(default=True, description="Enable financial validation")
    min_investment_amount: float = Field(default=0.0, description="Minimum investment amount")
    max_interest_rate: float = Field(default=100.0, description="Maximum interest rate (%)")
    max_discount_rate: float = Field(default=100.0, description="Maximum discount rate (%)")
    
    # Pro rata rules
    enable_pro_rata_validation: bool = Field(default=True, description="Enable pro rata validation")
    max_pro_rata_percentage: float = Field(default=100.0, description="Maximum pro rata percentage sum")
    
    # Performance
    parallel_validation: bool = Field(default=False, description="Enable parallel validation")
    early_exit_on_critical: bool = Field(default=True, description="Exit early on critical errors")
    cache_validation_results: bool = Field(default=True, description="Cache validation results")
    
    # Disabled rules (for flexibility)
    disabled_rules: Set[str] = Field(default_factory=set, description="Set of disabled rule names")
    
    class Config:
        frozen = True


_validation_config: ValidationConfig = ValidationConfig()


def get_validation_config() -> ValidationConfig:
    """Get validation configuration (singleton)."""
    return _validation_config


def update_validation_config(**kwargs: Dict) -> ValidationConfig:
    """Update validation configuration."""
    global _validation_config
    _validation_config = _validation_config.model_copy(update=kwargs)
    return _validation_config

