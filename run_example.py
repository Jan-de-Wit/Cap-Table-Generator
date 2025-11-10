#!/usr/bin/env python3
"""
Quick script to run the round-based example and generate Excel output.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from captable import generate_from_json

    # Paths
    input_file = Path(__file__).parent / "examples" / \
        "chatgpt.json"
    output_file = Path(__file__).parent / "output_v2.xlsx"

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
    print("   - Cap Table Progression: Summary view showing ownership evolution")
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
