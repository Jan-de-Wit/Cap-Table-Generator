"""
Ownership Validation Rules

Rules for validating ownership percentages and consistency.
"""

from typing import List, Dict, Any
from .base import ValidationRule, RuleResult
from ...errors import BusinessRuleError
# Constants for ownership validation (will be moved to config)
MAX_OWNERSHIP_PERCENTAGE = 100.0
MIN_OWNERSHIP_PERCENTAGE = 0.0


class OwnershipRule(ValidationRule):
    """Base class for ownership-related rules."""
    
    @property
    def rule_name(self) -> str:
        """Rule identifier."""
        return "ownership_base"


class TotalOwnershipRule(OwnershipRule):
    """Validate that total ownership does not exceed 100%."""
    
    @property
    def rule_name(self) -> str:
        """Rule identifier."""
        return "total_ownership"
    
    def validate(self, data: Dict[str, Any]) -> RuleResult:
        """Validate total ownership percentage."""
        errors: List[BusinessRuleError] = []
        
        rounds = data.get("rounds", [])
        if not rounds:
            return RuleResult(is_valid=True, errors=[])
        
        # This is a simplified check - full implementation would calculate
        # actual ownership percentages from the cap table
        # For now, we'll check that pro rata percentages don't exceed 100%
        
        for round_idx, round_data in enumerate(rounds):
            instruments = round_data.get("instruments", [])
            total_pro_rata_pct = 0.0
            
            for inst in instruments:
                pro_rata_pct = inst.get("pro_rata_percentage")
                if pro_rata_pct is not None:
                    total_pro_rata_pct += pro_rata_pct
            
            if total_pro_rata_pct > 1.0:  # 100%
                errors.append(
                    BusinessRuleError(
                        f"Total pro rata percentage ({total_pro_rata_pct * 100:.2f}%) exceeds 100% in round '{round_data.get('name', f'Round {round_idx + 1}')}'",
                        rule_name=self.rule_name,
                        context={"round_name": round_data.get("name"), "round_idx": round_idx}
                    )
                )
        
        return RuleResult(is_valid=len(errors) == 0, errors=errors)


class ProRataPercentageRule(OwnershipRule):
    """Validate pro rata percentages are within valid range."""
    
    @property
    def rule_name(self) -> str:
        """Rule identifier."""
        return "pro_rata_percentage"
    
    def validate(self, data: Dict[str, Any]) -> RuleResult:
        """Validate pro rata percentages."""
        errors: List[BusinessRuleError] = []
        
        rounds = data.get("rounds", [])
        for round_idx, round_data in enumerate(rounds):
            instruments = round_data.get("instruments", [])
            
            for inst_idx, inst in enumerate(instruments):
                pro_rata_pct = inst.get("pro_rata_percentage")
                if pro_rata_pct is not None:
                    if pro_rata_pct < 0 or pro_rata_pct > 1.0:
                        errors.append(
                            BusinessRuleError(
                                f"Pro rata percentage ({pro_rata_pct * 100:.2f}%) must be between 0% and 100%",
                                rule_name=self.rule_name,
                                context={
                                    "round_name": round_data.get("name"),
                                    "round_idx": round_idx,
                                    "instrument_idx": inst_idx,
                                    "holder_name": inst.get("holder_name")
                                }
                            )
                        )
        
        return RuleResult(is_valid=len(errors) == 0, errors=errors)

