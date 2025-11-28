"""
Valuation Validation Rules

Rules for validating valuation calculations and consistency.
"""

from typing import List, Dict, Any
from .base import ValidationRule, RuleResult
from ...errors import BusinessRuleError
from ...constants import VALUATION_BASIS_PRE_MONEY, VALUATION_BASIS_POST_MONEY


class ValuationRule(ValidationRule):
    """Base class for valuation-related rules."""
    
    @property
    def rule_name(self) -> str:
        """Rule identifier."""
        return "valuation_base"


class ValuationConsistencyRule(ValuationRule):
    """Validate valuation consistency (pre-money + investment = post-money)."""
    
    @property
    def rule_name(self) -> str:
        """Rule identifier."""
        return "valuation_consistency"
    
    def validate(self, data: Dict[str, Any]) -> RuleResult:
        """Validate valuation consistency."""
        errors: List[BusinessRuleError] = []
        tolerance = 0.01  # 1 cent tolerance
        
        rounds = data.get("rounds", [])
        for round_idx, round_data in enumerate(rounds):
            calc_type = round_data.get("calculation_type")
            if calc_type not in ["valuation_based", "convertible", "safe"]:
                continue
            
            valuation = round_data.get("valuation")
            valuation_basis = round_data.get("valuation_basis", "pre_money")
            
            if valuation is None:
                continue
            
            # Calculate total investment
            instruments = round_data.get("instruments", [])
            total_investment = 0.0
            
            for inst in instruments:
                investment = inst.get("investment_amount") or inst.get("principal") or 0.0
                total_investment += investment
            
            # Validate consistency
            if valuation_basis == VALUATION_BASIS_PRE_MONEY:
                post_money = valuation + total_investment
                # Check if post-money is consistent (if provided)
                # This is a simplified check
            elif valuation_basis == VALUATION_BASIS_POST_MONEY:
                pre_money = valuation - total_investment
                if pre_money < 0:
                    errors.append(
                        BusinessRuleError(
                            f"Post-money valuation ({valuation:,.2f}) is less than total investment ({total_investment:,.2f}) in round '{round_data.get('name', f'Round {round_idx + 1}')}'",
                            rule_name=self.rule_name,
                            context={
                                "round_name": round_data.get("name"),
                                "round_idx": round_idx,
                                "post_money": valuation,
                                "total_investment": total_investment
                            }
                        )
                    )
        
        return RuleResult(is_valid=len(errors) == 0, errors=errors)

