"""
JSON Schema Definition for Cap Table Generator
Follows Draft 2019-09 specification with UUID-based relationships
and Formula Encoding Object (FEO) structure.
"""

CAP_TABLE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2019-09/schema",
    "$id": "https://captable.schema/v1",
    "title": "Cap Table Schema",
    "description": "Dynamic capitalization table with formula-driven calculations",
    "type": "object",
    "required": ["schema_version", "company", "holders", "classes", "instruments"],
    "properties": {
        "schema_version": {
            "type": "string",
            "const": "1.0"
        },
        "company": {
            "$ref": "#/$defs/Company"
        },
        "holders": {
            "type": "array",
            "items": {"$ref": "#/$defs/Holder"}
        },
        "classes": {
            "type": "array",
            "items": {"$ref": "#/$defs/SecurityClass"}
        },
        "terms": {
            "type": "array",
            "items": {"$ref": "#/$defs/TermsPackage"}
        },
        "instruments": {
            "type": "array",
            "items": {"$ref": "#/$defs/Instrument"}
        },
        "rounds": {
            "type": "array",
            "items": {"$ref": "#/$defs/Round"}
        },
        "waterfall_scenarios": {
            "type": "array",
            "items": {"$ref": "#/$defs/WaterfallScenario"}
        }
    },
    "$defs": {
        "UUID": {
            "type": "string",
            "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            "description": "UUID v4 format"
        },
        "FormulaEncodingObject": {
            "type": "object",
            "required": ["is_calculated", "formula_string", "dependency_refs", "output_type"],
            "properties": {
                "is_calculated": {
                    "type": "boolean",
                    "const": True,
                    "description": "Flag indicating this field requires formula injection"
                },
                "formula_string": {
                    "type": "string",
                    "description": "Excel formula using symbolic placeholders (US English syntax)"
                },
                "dependency_refs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["placeholder", "path"],
                        "properties": {
                            "placeholder": {
                                "type": "string",
                                "description": "Symbolic name used in formula_string"
                            },
                            "path": {
                                "type": "string",
                                "description": "JSON Pointer to data or UUID reference"
                            },
                            "reference_type": {
                                "type": "string",
                                "enum": ["named_range", "structured_reference", "cell_reference", "uuid_lookup"],
                                "description": "Type of Excel reference to generate"
                            }
                        }
                    },
                    "description": "List of symbolic references to resolve"
                },
                "output_type": {
                    "type": "string",
                    "enum": ["named_range", "structured_reference", "cell_reference"],
                    "description": "Required Excel reference style for output"
                }
            }
        },
        "Company": {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "incorporation_date": {"type": "string", "format": "date"},
                "current_date": {"type": "string", "format": "date"},
                "current_pps": {
                    "type": "number",
                    "description": "Current price per share for TSM calculations"
                }
            }
        },
        "Holder": {
            "type": "object",
            "required": ["holder_id", "name", "type"],
            "properties": {
                "holder_id": {"$ref": "#/$defs/UUID"},
                "name": {"type": "string"},
                "type": {
                    "type": "string",
                    "enum": ["founder", "employee", "investor", "advisor", "option_pool"]
                },
                "email": {"type": "string", "format": "email"}
            }
        },
        "SecurityClass": {
            "type": "object",
            "required": ["class_id", "name", "type"],
            "properties": {
                "class_id": {"$ref": "#/$defs/UUID"},
                "name": {"type": "string"},
                "type": {
                    "type": "string",
                    "enum": ["common", "preferred", "option", "warrant", "safe", "convertible_note"]
                },
                "terms_id": {
                    "$ref": "#/$defs/UUID",
                    "description": "Reference to Terms Package"
                },
                "conversion_ratio": {
                    "type": "number",
                    "default": 1.0,
                    "description": "Default conversion ratio to common"
                }
            }
        },
        "TermsPackage": {
            "type": "object",
            "required": ["terms_id", "name"],
            "properties": {
                "terms_id": {"$ref": "#/$defs/UUID"},
                "name": {"type": "string"},
                "liquidation_multiple": {
                    "type": "number",
                    "default": 1.0
                },
                "participation_type": {
                    "type": "string",
                    "enum": ["non_participating", "participating", "capped_participating"],
                    "default": "non_participating"
                },
                "participation_cap": {
                    "type": "number",
                    "description": "Cap multiple for capped participating (e.g., 2.0 for 2x)"
                },
                "seniority_rank": {
                    "type": "integer",
                    "description": "Determines payout order in waterfall (lower = more senior)"
                },
                "dividend_rate": {
                    "type": "number",
                    "description": "Annual dividend rate (as decimal)"
                },
                "anti_dilution": {
                    "type": "string",
                    "enum": ["none", "weighted_average", "full_ratchet"]
                }
            }
        },
        "Instrument": {
            "type": "object",
            "required": ["instrument_id", "holder_id", "class_id", "initial_quantity"],
            "properties": {
                "instrument_id": {"$ref": "#/$defs/UUID"},
                "holder_id": {"$ref": "#/$defs/UUID"},
                "class_id": {"$ref": "#/$defs/UUID"},
                "round_id": {"$ref": "#/$defs/UUID"},
                "initial_quantity": {
                    "type": "number",
                    "minimum": 0
                },
                "current_quantity": {
                    "oneOf": [
                        {"type": "number"},
                        {"$ref": "#/$defs/FormulaEncodingObject"}
                    ],
                    "description": "Current shares (may be calculated for vesting)"
                },
                "strike_price": {
                    "type": "number",
                    "description": "Exercise price for options/warrants"
                },
                "acquisition_price": {
                    "type": "number",
                    "description": "Original issue price paid"
                },
                "acquisition_date": {
                    "type": "string",
                    "format": "date"
                },
                "vesting_terms": {
                    "$ref": "#/$defs/VestingTerms"
                },
                "convertible_terms": {
                    "$ref": "#/$defs/ConvertibleTerms"
                }
            }
        },
        "VestingTerms": {
            "type": "object",
            "required": ["grant_date", "cliff_days", "vesting_period_days"],
            "properties": {
                "grant_date": {
                    "type": "string",
                    "format": "date"
                },
                "cliff_days": {
                    "type": "integer",
                    "minimum": 0
                },
                "vesting_period_days": {
                    "type": "integer",
                    "minimum": 1
                },
                "vested_quantity": {
                    "$ref": "#/$defs/FormulaEncodingObject",
                    "description": "Calculated vested shares"
                }
            }
        },
        "ConvertibleTerms": {
            "type": "object",
            "properties": {
                "investment_amount": {
                    "type": "number",
                    "minimum": 0
                },
                "discount_rate": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Discount on conversion price (e.g., 0.20 for 20%)"
                },
                "price_cap": {
                    "type": "number",
                    "description": "Valuation cap for conversion"
                },
                "conversion_shares": {
                    "$ref": "#/$defs/FormulaEncodingObject",
                    "description": "Calculated shares on conversion"
                }
            }
        },
        "Round": {
            "type": "object",
            "required": ["round_id", "name", "round_date"],
            "properties": {
                "round_id": {"$ref": "#/$defs/UUID"},
                "name": {"type": "string"},
                "round_date": {
                    "type": "string",
                    "format": "date"
                },
                "investment_amount": {
                    "type": "number",
                    "minimum": 0
                },
                "pre_money_valuation": {
                    "oneOf": [
                        {"type": "number"},
                        {"$ref": "#/$defs/FormulaEncodingObject"}
                    ]
                },
                "post_money_valuation": {
                    "oneOf": [
                        {"type": "number"},
                        {"$ref": "#/$defs/FormulaEncodingObject"}
                    ]
                },
                "price_per_share": {
                    "oneOf": [
                        {"type": "number"},
                        {"$ref": "#/$defs/FormulaEncodingObject"}
                    ]
                },
                "shares_issued": {
                    "oneOf": [
                        {"type": "number"},
                        {"$ref": "#/$defs/FormulaEncodingObject"}
                    ]
                },
                "option_pool_increase": {
                    "type": "object",
                    "properties": {
                        "target_pool_percent": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1
                        },
                        "shares_added": {
                            "$ref": "#/$defs/FormulaEncodingObject"
                        }
                    }
                }
            }
        },
        "WaterfallScenario": {
            "type": "object",
            "required": ["scenario_id", "name", "exit_value"],
            "properties": {
                "scenario_id": {"$ref": "#/$defs/UUID"},
                "name": {"type": "string"},
                "exit_value": {
                    "type": "number",
                    "minimum": 0
                },
                "payouts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["class_id"],
                        "properties": {
                            "class_id": {"$ref": "#/$defs/UUID"},
                            "payout_amount": {
                                "$ref": "#/$defs/FormulaEncodingObject"
                            }
                        }
                    }
                }
            }
        }
    }
}


def get_schema():
    """Returns the cap table JSON schema."""
    return CAP_TABLE_SCHEMA

