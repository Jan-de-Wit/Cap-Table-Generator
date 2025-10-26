"""
Formula Resolution Module

This module provides formula resolution capabilities for cap tables, organizing
formula creation methods by domain (ownership, TSM, valuation, interest).
"""

from .resolver import FormulaResolver

# Re-export specialized formula functions for backward compatibility
from . import ownership, tsm, valuation, interest

__all__ = ['FormulaResolver']

# Enhance FormulaResolver with specialized methods
def _add_formula_methods_to_resolver():
    """Add convenience methods to FormulaResolver for backward compatibility."""
    
    # Ownership formulas
    FormulaResolver.create_ownership_formula = lambda self, shares_ref, total_fds_ref="Total_FDS": ownership.create_ownership_formula(shares_ref, total_fds_ref)
    FormulaResolver.create_option_pool_topup_formula = lambda self, fds_preround_ref, target_percent_ref: ownership.create_option_pool_topup_formula(fds_preround_ref, target_percent_ref)
    
    # TSM formulas
    FormulaResolver.create_tsm_gross_itm_formula = lambda self, quantity_ref, strike_ref, current_pps_ref="Current_PPS": tsm.create_tsm_gross_itm_formula(quantity_ref, strike_ref, current_pps_ref)
    FormulaResolver.create_tsm_proceeds_formula = lambda self, gross_itm_ref, strike_ref: tsm.create_tsm_proceeds_formula(gross_itm_ref, strike_ref)
    FormulaResolver.create_tsm_repurchase_formula = lambda self, proceeds_ref, current_pps_ref="Current_PPS": tsm.create_tsm_repurchase_formula(proceeds_ref, current_pps_ref)
    FormulaResolver.create_tsm_net_dilution_formula = lambda self, gross_itm_ref, repurchase_ref: tsm.create_tsm_net_dilution_formula(gross_itm_ref, repurchase_ref)
    
    # Valuation formulas
    FormulaResolver.create_safe_conversion_price_formula = lambda self, round_pps_ref, discount_rate_ref, price_cap_ref, shares_preround_ref: valuation.create_safe_conversion_price_formula(round_pps_ref, discount_rate_ref, price_cap_ref, shares_preround_ref)
    FormulaResolver.create_safe_conversion_shares_formula = lambda self, investment_ref, conversion_price_ref: valuation.create_safe_conversion_shares_formula(investment_ref, conversion_price_ref)
    FormulaResolver.create_shares_from_investment_premoney_formula = lambda self, investment_ref, interest_ref, pre_money_val_ref, pre_round_shares_ref: valuation.create_shares_from_investment_premoney_formula(investment_ref, interest_ref, pre_money_val_ref, pre_round_shares_ref)
    FormulaResolver.create_shares_from_investment_postmoney_formula = lambda self, investment_ref, interest_ref, post_money_val_ref, pre_round_shares_ref: valuation.create_shares_from_investment_postmoney_formula(investment_ref, interest_ref, post_money_val_ref, pre_round_shares_ref)
    FormulaResolver.create_shares_from_percentage_formula = lambda self, percentage_ownership_ref, pre_round_shares_ref: valuation.create_shares_from_percentage_formula(percentage_ownership_ref, pre_round_shares_ref)
    FormulaResolver.create_price_per_share_from_valuation_formula = lambda self, valuation_ref, shares_outstanding_ref: valuation.create_price_per_share_from_valuation_formula(valuation_ref, shares_outstanding_ref)
    FormulaResolver.create_post_money_from_pre_money_formula = lambda self, pre_money_ref, investment_ref, interest_ref="0": valuation.create_post_money_from_pre_money_formula(pre_money_ref, investment_ref, interest_ref)
    FormulaResolver.create_pre_money_from_post_money_formula = lambda self, post_money_ref, investment_ref, interest_ref="0": valuation.create_pre_money_from_post_money_formula(post_money_ref, investment_ref, interest_ref)
    
    # Interest formulas
    FormulaResolver.create_accrued_interest_formula = lambda self, principal_ref, interest_rate_ref, start_date_ref, end_date_ref="Current_Date", interest_type="simple": interest.create_accrued_interest_formula(principal_ref, interest_rate_ref, start_date_ref, end_date_ref, interest_type)

# Add methods to FormulaResolver class
_add_formula_methods_to_resolver()
