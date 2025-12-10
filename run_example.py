#!/usr/bin/env python3
"""
Quick script to run the round-based example and generate Excel output.

Usage:
    python run_example.py [input_file.json] [output_file.xlsx]

Examples:
    python run_example.py examples/anti_dilution_test.json
    python run_example.py examples/chatgpt.json output.xlsx
"""

import sys
from pathlib import Path

# Add fastapi to path so we can import captable
sys.path.insert(0, str(Path(__file__).parent / "fastapi"))

try:
    from captable import generate_from_json

    # Paths - allow command-line argument for input file
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
        if not input_file.is_absolute():
            input_file = Path(__file__).parent / input_file
        if not input_file.exists():
            print(f"❌ ERROR: Input file not found: {input_file}")
            sys.exit(1)
    else:
        input_file = Path(__file__).parent / "examples" / "chatgpt.json"
    
    # Generate output filename from input filename
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
        if not output_file.is_absolute():
            output_file = Path(__file__).parent / output_file
    else:
        output_file = Path(__file__).parent / f"{input_file.stem}_output.xlsx"

    print("🚀 Generating Excel from round-based example...")
    print(f"📄 Input: {input_file}")
    print(f"📊 Output: {output_file}")
    print()

    # Generate
    result = generate_from_json(str(input_file), str(output_file))

    print("✅ SUCCESS!")
    print(f"📊 Excel file created: {output_file}")
    print()
    print("📋 What's in the file:")
    print("   - Rounds Sheet: All rounds with instruments laid out vertically (base shares only)")
    print("   - Pro Rata Allocations: Pro rata share allocations per stakeholder per round")
    print("   - Cap Table: Summary view showing ownership evolution")
    print()
    print("💡 Open the Excel file to see the results!")

except ImportError as e:
    print("❌ ERROR: Missing dependencies")
    print()
    print("Install dependencies with:")
    print("  pip install -r requirements.txt")
    print()
    print("Or if using virtual environment:")
    print("  python3 -m venv venv")
    print("  source venv/bin/activate  # On Mac/Linux")
    print("  # Or: venv\\Scripts\\activate  # On Windows")
    print("  pip install -r requirements.txt")
    print()
    print(f"Missing module: {e}")
    sys.exit(1)

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
