"""
Sample Cap Table Fixtures

Standardized test data for each calculation type and scenario.
"""

# Fixed Shares Round
FIXED_SHARES_ROUND = {
    "name": "Founders Round",
    "calculation_type": "fixed_shares",
    "round_date": "2023-01-01",
    "instruments": [
        {
            "holder_name": "Founder 1",
            "class_name": "Common",
            "initial_quantity": 5000000,
        },
        {
            "holder_name": "Founder 2",
            "class_name": "Common",
            "initial_quantity": 5000000,
        },
    ],
}

# Target Percentage Round
TARGET_PERCENTAGE_ROUND = {
    "name": "ESOP Round",
    "calculation_type": "target_percentage",
    "round_date": "2023-06-01",
    "instruments": [
        {
            "holder_name": "Employee 1",
            "class_name": "Common",
            "target_percentage": 0.05,
        },
        {
            "holder_name": "Employee 2",
            "class_name": "Common",
            "target_percentage": 0.03,
        },
    ],
}

# Valuation-Based Round
VALUATION_BASED_ROUND = {
    "name": "Seed Round",
    "calculation_type": "valuation_based",
    "round_date": "2024-01-01",
    "valuation": 1000000,
    "valuation_basis": "pre_money",
    "instruments": [
        {
            "holder_name": "Investor A",
            "class_name": "Preferred",
            "investment_amount": 200000,
        },
        {
            "holder_name": "Investor B",
            "class_name": "Preferred",
            "investment_amount": 300000,
        },
    ],
}

# Convertible Round
CONVERTIBLE_ROUND = {
    "name": "Convertible Note",
    "calculation_type": "convertible",
    "round_date": "2024-03-01",
    "valuation": 2000000,
    "valuation_basis": "pre_money",
    "instruments": [
        {
            "holder_name": "Investor C",
            "class_name": "Note",
            "investment_amount": 100000,
            "interest_rate": 0.08,
            "discount_rate": 0.20,
            "payment_date": "2024-03-01",
            "expected_conversion_date": "2025-03-01",
            "interest_type": "simple",
        }
    ],
}

# SAFE Round
SAFE_ROUND = {
    "name": "SAFE",
    "calculation_type": "safe",
    "round_date": "2024-06-01",
    "valuation": 3000000,
    "valuation_basis": "pre_money",
    "instruments": [
        {
            "holder_name": "Investor D",
            "class_name": "SAFE",
            "investment_amount": 150000,
            "discount_rate": 0.15,
            "expected_conversion_date": "2025-06-01",
        }
    ],
}

# Complete Cap Table
COMPLETE_CAP_TABLE = {
    "schema_version": "2.0",
    "holders": [
        {"name": "Founder 1", "group": "Founders"},
        {"name": "Founder 2", "group": "Founders"},
        {"name": "Employee 1", "group": "ESOP"},
        {"name": "Employee 2", "group": "ESOP"},
        {"name": "Investor A", "group": "Investors"},
        {"name": "Investor B", "group": "Investors"},
        {"name": "Investor C", "group": "Investors"},
        {"name": "Investor D", "group": "Investors"},
    ],
    "rounds": [
        FIXED_SHARES_ROUND,
        TARGET_PERCENTAGE_ROUND,
        VALUATION_BASED_ROUND,
        CONVERTIBLE_ROUND,
        SAFE_ROUND,
    ],
}





