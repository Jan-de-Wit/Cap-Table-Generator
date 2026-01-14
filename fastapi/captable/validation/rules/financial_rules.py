"""
Financial Validation Rules

Rules for validating financial data consistency.
"""

from typing import List, Dict, Any
from .base import ValidationRule, RuleResult
from ...errors import BusinessRuleError
from ...utils.date_utils import parse_date, validate_date_range


class FinancialRule(ValidationRule):
    """Base class for financial-related rules."""

    @property
    def rule_name(self) -> str:
        """Rule identifier."""
        return "financial_base"


class InvestmentAmountRule(FinancialRule):
    """Validate investment amounts are positive."""

    @property
    def rule_name(self) -> str:
        """Rule identifier."""
        return "investment_amount"

    def validate(self, data: Dict[str, Any]) -> RuleResult:
        """Validate investment amounts."""
        errors: List[BusinessRuleError] = []

        rounds = data.get("rounds", [])
        for round_idx, round_data in enumerate(rounds):
            instruments = round_data.get("instruments", [])

            for inst_idx, inst in enumerate(instruments):
                investment = inst.get(
                    "investment_amount") or inst.get("principal")
                if investment is not None and investment <= 0:
                    errors.append(
                        BusinessRuleError(
                            f"Investment amount must be positive, got {investment}",
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


class RateRule(FinancialRule):
    """Validate interest and discount rates are within valid range."""

    @property
    def rule_name(self) -> str:
        """Rule identifier."""
        return "rate_validation"

    def validate(self, data: Dict[str, Any]) -> RuleResult:
        """Validate rates."""
        errors: List[BusinessRuleError] = []

        rounds = data.get("rounds", [])
        for round_idx, round_data in enumerate(rounds):
            instruments = round_data.get("instruments", [])

            for inst_idx, inst in enumerate(instruments):
                # Check interest rate
                interest_rate = inst.get("interest_rate")
                if interest_rate is not None:
                    if interest_rate < 0 or interest_rate > 1.0:
                        errors.append(
                            BusinessRuleError(
                                f"Interest rate ({interest_rate * 100:.2f}%) must be between 0% and 100%",
                                rule_name=self.rule_name,
                                context={
                                    "round_name": round_data.get("name"),
                                    "round_idx": round_idx,
                                    "instrument_idx": inst_idx,
                                    "holder_name": inst.get("holder_name")
                                }
                            )
                        )

                # Check discount rate
                discount_rate = inst.get("discount_rate")
                if discount_rate is not None:
                    if discount_rate < 0 or discount_rate > 1.0:
                        errors.append(
                            BusinessRuleError(
                                f"Discount rate ({discount_rate * 100:.2f}%) must be between 0% and 100%",
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


class DateOrderRule(FinancialRule):
    """Validate dates are in chronological order."""

    @property
    def rule_name(self) -> str:
        """Rule identifier."""
        return "date_order"

    def validate(self, data: Dict[str, Any]) -> RuleResult:
        """Validate date ordering."""
        errors: List[BusinessRuleError] = []

        rounds = data.get("rounds", [])
        for round_idx, round_data in enumerate(rounds):
            round_date = round_data.get("round_date")
            instruments = round_data.get("instruments", [])

            for inst_idx, inst in enumerate(instruments):
                payment_date = inst.get("payment_date")
                conversion_date = inst.get("expected_conversion_date")

                # Check payment_date <= conversion_date
                if payment_date and conversion_date:
                    if not validate_date_range(payment_date, conversion_date):
                        errors.append(
                            BusinessRuleError(
                                f"Payment date ({payment_date}) must be before or equal to conversion date ({conversion_date})",
                                rule_name=self.rule_name,
                                context={
                                    "round_name": round_data.get("name"),
                                    "round_idx": round_idx,
                                    "instrument_idx": inst_idx,
                                    "holder_name": inst.get("holder_name")
                                }
                            )
                        )

                # TODO: reanable Check round_date <= payment_date (if both exist)
                # if round_date and payment_date:
                    # if not validate_date_range(round_date, payment_date):
                    #     errors.append(
                    #         BusinessRuleError(
                    #             f"Round date ({round_date}) must be before or equal to payment date ({payment_date})",
                    #             rule_name=self.rule_name,
                    #             context={
                    #                 "round_name": round_data.get("name"),
                    #                 "round_idx": round_idx,
                    #                 "instrument_idx": inst_idx,
                    #                 "holder_name": inst.get("holder_name")
                    #             }
                    #         )
                    #     )

        return RuleResult(is_valid=len(errors) == 0, errors=errors)
