"""
Sample Data Generator for Cap Table Generator
Creates example cap table JSON data for testing and demos.
"""

import json
import uuid
from typing import Dict, Any


def generate_simple_captable() -> Dict[str, Any]:
    """
    Generate simple cap table with founders and one seed round.
    
    Returns:
        Cap table data dictionary
    """
    # Fixed UUIDs for reproducibility
    alice_id = "eb71bf51-9903-4f63-806a-feafa08f49a0"
    bob_id = "350ed508-f8e6-4cbd-aae8-57d856a3e5de"
    carol_id = "e6336e91-b794-42f6-80b3-370690670933"
    
    common_class_id = "b28c35e4-deab-430e-b1db-a711c3e6f8e5"
    seed_preferred_class_id = "2c6ef140-3db0-409b-b893-f715f0fed026"
    
    seed_round_id = "53617af7-dc61-4174-802e-e2b4663412be"
    seed_terms_id = "35de1352-08dc-40bb-83c5-e4d7c2f120d7"
    
    alice_instrument_id = "7abf580c-c054-4807-bd0d-570cbda38b3c"
    bob_instrument_id = "ea99646c-6d3b-4ae9-af8a-dc917d9a58bf"
    carol_instrument_id = "12c81058-3f5c-4ad4-b09a-1145ccead824"
    alice_seed_id = "0ba78d91-dee0-415c-98dd-9add1b143551"
    
    scenario_id = "56cd0979-7550-4ed2-81c6-c4aa59686ce4"
    
    return {
        "schema_version": "1.0",
        "company": {
            "name": "SimpleStartup Inc.",
            "incorporation_date": "2023-01-15",
            "current_date": "2024-10-25",
            "current_pps": 1.5
        },
        "holders": [
            {
                "holder_id": alice_id,
                "name": "Alice Johnson",
                "type": "founder",
                "email": "alice@simplestartup.com"
            },
            {
                "holder_id": bob_id,
                "name": "Bob Smith",
                "type": "founder",
                "email": "bob@simplestartup.com"
            },
            {
                "holder_id": carol_id,
                "name": "Carol Martinez",
                "type": "founder",
                "email": "carol@simplestartup.com"
            }
        ],
        "classes": [
            {
                "class_id": common_class_id,
                "name": "Common Stock",
                "type": "common",
                "conversion_ratio": 1.0
            },
            {
                "class_id": seed_preferred_class_id,
                "name": "Seed Preferred",
                "type": "preferred",
                "terms_id": seed_terms_id,
                "conversion_ratio": 1.0
            }
        ],
        "terms": [
            {
                "terms_id": seed_terms_id,
                "name": "Seed Preferred Terms",
                "liquidation_multiple": 1.0,
                "participation_type": "non_participating",
                "seniority_rank": 1,
                "anti_dilution": "weighted_average"
            }
        ],
        "instruments": [
            {
                "instrument_id": alice_instrument_id,
                "holder_id": alice_id,
                "class_id": common_class_id,
                "initial_quantity": 4000000,
                "acquisition_price": 0.001,
                "acquisition_date": "2023-01-15"
            },
            {
                "instrument_id": bob_instrument_id,
                "holder_id": bob_id,
                "class_id": common_class_id,
                "initial_quantity": 3000000,
                "acquisition_price": 0.001,
                "acquisition_date": "2023-01-15"
            },
            {
                "instrument_id": carol_instrument_id,
                "holder_id": carol_id,
                "class_id": common_class_id,
                "initial_quantity": 3000000,
                "acquisition_price": 0.001,
                "acquisition_date": "2023-01-15"
            },
            {
                "instrument_id": alice_seed_id,
                "holder_id": alice_id,
                "class_id": seed_preferred_class_id,
                "round_id": seed_round_id,
                "initial_quantity": 2000000,
                "acquisition_price": 1.0,
                "acquisition_date": "2023-06-01"
            }
        ],
        "rounds": [
            {
                "round_id": seed_round_id,
                "name": "Seed Round",
                "round_date": "2023-06-01",
                "investment_amount": 2000000,
                "pre_money_valuation": 8000000,
                "post_money_valuation": 10000000,
                "price_per_share": 1.0,
                "shares_issued": 2000000
            }
        ],
        "waterfall_scenarios": [
            {
                "scenario_id": scenario_id,
                "name": "Exit at $30M",
                "exit_value": 30000000
            }
        ]
    }


def generate_complex_captable() -> Dict[str, Any]:
    """
    Generate complex cap table with multiple rounds, options, vesting, waterfall.
    
    Returns:
        Cap table data dictionary
    """
    # Fixed UUIDs for reproducibility
    david_id = "b5c77236-6c7f-4811-a3be-119c6af50d45"
    emma_id = "55361742-75ab-45da-86bc-55080b972d89"
    frank_id = "4f73ed1c-49cf-4be7-b997-2d8cbdbeee8a"
    grace_id = "b3d17114-aa56-49ca-a6b7-8d25f76aec96"
    seed_ventures_id = "91a2c80e-3210-46e0-bc32-d3b326fedec7"
    alpha_id = "3c5a661f-ed9c-431d-b76b-9dee096bc423"
    beta_id = "8f0a4bb7-7f12-44ba-8b47-63500e2ae84e"
    pool_id = "2b2d1491-5539-4771-9ea8-056ea41d5c50"
    
    common_class_id = "221af0ec-6f6b-4535-8ace-9ee1c7945563"
    option_class_id = "1c3b53cc-975e-4b93-b9ca-40477cb2907a"
    seed_preferred_class_id = "2140f8bb-239f-45ef-a882-8e3e1fec7863"
    series_a_class_id = "209eeedd-3e28-4bce-abd9-1985227cbdce"
    series_b_class_id = "3ccd35f0-baa8-4a97-baf6-e592978d5115"
    
    seed_terms_id = "00fc791c-3a3d-4af4-9ae9-453733ce83e2"
    series_a_terms_id = "f3e3c41d-3a6c-45d1-b317-ba2cfa154c3c"
    series_b_terms_id = "e413afee-897d-4bcd-b23c-c9062ba55c44"
    
    seed_round_id = "e99459e8-1027-4c73-8966-5fc11ed5f350"
    series_a_round_id = "157bae6a-8482-48e4-857e-05d7e01827d6"
    series_b_round_id = "720ce81e-6d13-4e5f-9234-07ea2db876e2"
    
    david_common_id = "3a1ee839-e71f-4cc2-a74c-65b330dc9586"
    emma_common_id = "c140777e-98be-46ef-948b-413370427ef3"
    pool_option_id = "913321ed-69ce-41de-92ce-da9e56f7aa9a"
    frank_option_id = "60601400-b350-43eb-935b-74b9d8252933"
    grace_option_id = "35335348-00e1-498f-857a-2588177770dd"
    seed_ventures_seed_id = "098d9685-df3d-4826-a177-61546aa50163"
    alpha_series_a_id = "9c833799-52e1-438d-9796-19f2abb4041e"
    beta_series_b_id = "114f23d8-50d9-415b-b917-52bc5846a73f"
    
    scenario_id = "fdcf9901-2b51-4a1b-9abf-43bb5827a520"
    
    return {
        "schema_version": "1.0",
        "company": {
            "name": "TechVenture Corp",
            "incorporation_date": "2022-01-01",
            "current_date": "2024-10-25",
            "current_pps": 7.5
        },
        "holders": [
            {
                "holder_id": david_id,
                "name": "David Chen",
                "type": "founder",
                "email": "david@techventure.com"
            },
            {
                "holder_id": emma_id,
                "name": "Emma Wilson",
                "type": "founder",
                "email": "emma@techventure.com"
            },
            {
                "holder_id": frank_id,
                "name": "Frank Thomas",
                "type": "employee",
                "email": "frank@techventure.com"
            },
            {
                "holder_id": grace_id,
                "name": "Grace Lee",
                "type": "employee",
                "email": "grace@techventure.com"
            },
            {
                "holder_id": seed_ventures_id,
                "name": "Seed Ventures LLC",
                "type": "investor"
            },
            {
                "holder_id": alpha_id,
                "name": "Alpha Capital Partners",
                "type": "investor"
            },
            {
                "holder_id": beta_id,
                "name": "Beta Growth Fund",
                "type": "investor"
            },
            {
                "holder_id": pool_id,
                "name": "Unallocated Option Pool",
                "type": "option_pool"
            }
        ],
        "classes": [
            {
                "class_id": common_class_id,
                "name": "Common Stock",
                "type": "common",
                "conversion_ratio": 1.0
            },
            {
                "class_id": option_class_id,
                "name": "Stock Options",
                "type": "option",
                "conversion_ratio": 1.0
            },
            {
                "class_id": seed_preferred_class_id,
                "name": "Seed Preferred",
                "type": "preferred",
                "terms_id": seed_terms_id,
                "conversion_ratio": 1.0
            },
            {
                "class_id": series_a_class_id,
                "name": "Series A Preferred",
                "type": "preferred",
                "terms_id": series_a_terms_id,
                "conversion_ratio": 1.0
            },
            {
                "class_id": series_b_class_id,
                "name": "Series B Preferred",
                "type": "preferred",
                "terms_id": series_b_terms_id,
                "conversion_ratio": 1.0
            }
        ],
        "terms": [
            {
                "terms_id": seed_terms_id,
                "name": "Seed Preferred Terms",
                "liquidation_multiple": 1.0,
                "participation_type": "non_participating",
                "seniority_rank": 3,
                "anti_dilution": "weighted_average"
            },
            {
                "terms_id": series_a_terms_id,
                "name": "Series A Preferred Terms",
                "liquidation_multiple": 1.0,
                "participation_type": "participating",
                "seniority_rank": 2,
                "anti_dilution": "weighted_average"
            },
            {
                "terms_id": series_b_terms_id,
                "name": "Series B Preferred Terms",
                "liquidation_multiple": 1.5,
                "participation_type": "participating",
                "seniority_rank": 1,
                "anti_dilution": "weighted_average"
            }
        ],
        "instruments": [
            {
                "instrument_id": david_common_id,
                "holder_id": david_id,
                "class_id": common_class_id,
                "initial_quantity": 5000000,
                "acquisition_price": 0.001,
                "acquisition_date": "2022-01-01"
            },
            {
                "instrument_id": emma_common_id,
                "holder_id": emma_id,
                "class_id": common_class_id,
                "initial_quantity": 5000000,
                "acquisition_price": 0.001,
                "acquisition_date": "2022-01-01"
            },
            {
                "instrument_id": pool_option_id,
                "holder_id": pool_id,
                "class_id": option_class_id,
                "initial_quantity": 2000000,
                "strike_price": 0.1,
                "acquisition_date": "2022-01-01"
            },
            {
                "instrument_id": frank_option_id,
                "holder_id": frank_id,
                "class_id": option_class_id,
                "initial_quantity": 400000,
                "strike_price": 0.5,
                "acquisition_date": "2022-06-01",
                "vesting_terms": {
                    "grant_date": "2022-06-01",
                    "cliff_days": 365,
                    "vesting_period_days": 1460
                }
            },
            {
                "instrument_id": grace_option_id,
                "holder_id": grace_id,
                "class_id": option_class_id,
                "initial_quantity": 300000,
                "strike_price": 1.0,
                "acquisition_date": "2023-03-01",
                "vesting_terms": {
                    "grant_date": "2023-03-01",
                    "cliff_days": 365,
                    "vesting_period_days": 1460
                }
            },
            {
                "instrument_id": seed_ventures_seed_id,
                "holder_id": seed_ventures_id,
                "class_id": seed_preferred_class_id,
                "round_id": seed_round_id,
                "initial_quantity": 3000000,
                "acquisition_price": 1.0,
                "acquisition_date": "2022-12-01"
            },
            {
                "instrument_id": alpha_series_a_id,
                "holder_id": alpha_id,
                "class_id": series_a_class_id,
                "round_id": series_a_round_id,
                "initial_quantity": 4000000,
                "acquisition_price": 2.5,
                "acquisition_date": "2023-09-01"
            },
            {
                "instrument_id": beta_series_b_id,
                "holder_id": beta_id,
                "class_id": series_b_class_id,
                "round_id": series_b_round_id,
                "initial_quantity": 3333333,
                "acquisition_price": 6.0,
                "acquisition_date": "2024-06-01"
            }
        ],
        "rounds": [
            {
                "round_id": seed_round_id,
                "name": "Seed Round",
                "round_date": "2022-12-01",
                "investment_amount": 3000000,
                "pre_money_valuation": 12000000,
                "post_money_valuation": 15000000,
                "price_per_share": 1.0,
                "shares_issued": 3000000
            },
            {
                "round_id": series_a_round_id,
                "name": "Series A",
                "round_date": "2023-09-01",
                "investment_amount": 10000000,
                "pre_money_valuation": 40000000,
                "post_money_valuation": 50000000,
                "price_per_share": 2.5,
                "shares_issued": 4000000
            },
            {
                "round_id": series_b_round_id,
                "name": "Series B",
                "round_date": "2024-06-01",
                "investment_amount": 20000000,
                "pre_money_valuation": 100000000,
                "post_money_valuation": 120000000,
                "price_per_share": 6.0,
                "shares_issued": 3333333
            }
        ],
        "waterfall_scenarios": [
            {
                "scenario_id": scenario_id,
                "name": "Exit at $200M",
                "exit_value": 200000000
            }
        ]
    }


def save_sample_data(data: Dict[str, Any], filepath: str):
    """
    Save sample data to JSON file.
    
    Args:
        data: Cap table data dictionary
        filepath: Path to output JSON file
    """
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def main():
    """Generate sample JSON files."""
    simple_data = generate_simple_captable()
    complex_data = generate_complex_captable()
    
    save_sample_data(simple_data, "sample_simple_captable.json")
    save_sample_data(complex_data, "sample_complex_captable.json")
    
    print("Generated sample JSON files:")
    print("  - sample_simple_captable.json")
    print("  - sample_complex_captable.json")


if __name__ == "__main__":
    main()

