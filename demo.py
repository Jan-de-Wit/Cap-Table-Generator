"""
Demo Script for Cap Table Generator
Demonstrates usage by generating sample cap tables.
"""

from sample_data_generator import generate_simple_captable, generate_complex_captable, save_sample_data
from cap_table_generator import generate_from_data


def main():
    """Generate demo cap tables."""
    print("=" * 70)
    print("Cap Table Generator - Demo")
    print("=" * 70)
    print()
    
    # Generate simple cap table
    print("1. Generating Simple Cap Table...")
    print("-" * 70)
    simple_data = generate_simple_captable()
    
    # Save JSON
    simple_json_path = "demo_simple.json"
    save_sample_data(simple_data, simple_json_path)
    
    # Generate Excel
    simple_excel_path = "demo_simple.xlsx"
    try:
        generate_from_data(simple_data, simple_excel_path)
        print(f"✓ Excel file generated: {simple_excel_path}")
    except Exception as e:
        print(f"✗ Error generating Excel: {e}")
    
    print()
    
    # Generate complex cap table
    print("2. Generating Complex Cap Table...")
    print("-" * 70)
    complex_data = generate_complex_captable()
    
    # Save JSON
    complex_json_path = "demo_complex.json"
    save_sample_data(complex_data, complex_json_path)
    
    # Generate Excel
    complex_excel_path = "demo_complex.xlsx"
    try:
        generate_from_data(complex_data, complex_excel_path)
        print(f"✓ Excel file generated: {complex_excel_path}")
    except Exception as e:
        print(f"✗ Error generating Excel: {e}")
    
    print()
    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print()
    print("Generated files:")
    print(f"  - {simple_json_path}")
    print(f"  - {simple_excel_path}")
    print(f"  - {complex_json_path}")
    print(f"  - {complex_excel_path}")
    print()
    print("Open the Excel files to see dynamic formulas in action!")
    print()


if __name__ == "__main__":
    main()

