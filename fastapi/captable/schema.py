"""
JSON Schema Definition for Cap Table Generator
Follows Draft 2019-09 specification with formula-driven calculations.
"""

import json
from pathlib import Path

def load_schema_from_file():
    """Load schema from JSON file."""
    schema_file = Path(__file__).parent / "schemas" / "cap_table_schema.json"
    with open(schema_file) as f:
        return json.load(f)

# Load the schema from the JSON file
CAP_TABLE_SCHEMA = load_schema_from_file()


def get_schema():
    """Return the cap table JSON schema."""
    return CAP_TABLE_SCHEMA
