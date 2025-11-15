#!/usr/bin/env python3
"""
Script to generate Excel from JSON cap table data.
Called from Next.js API route.
"""

import sys
import json
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from captable import generate_from_data

    if len(sys.argv) != 3:
        print("Usage: generate_excel.py <input_json_path> <output_excel_path>", file=sys.stderr)
        sys.exit(1)

    json_path = sys.argv[1]
    excel_path = sys.argv[2]

    # Read JSON data
    with open(json_path, "r") as f:
        data = json.load(f)

    # Generate Excel
    generate_from_data(data, excel_path)

    sys.exit(0)

except ImportError as e:
    print(f"ERROR: Missing dependencies: {e}", file=sys.stderr)
    print("Install dependencies with: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

