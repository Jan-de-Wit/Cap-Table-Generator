#!/usr/bin/env python3
"""
Simple script to run the Streamlit wizard for the Cap Table Generator.
"""

import subprocess
import sys
import os

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))
wizard_path = os.path.join(script_dir, "src", "server", "wizard.py")

if __name__ == "__main__":
    print("Starting Cap Table Generator Wizard...")
    print(f"Wizard file: {wizard_path}")
    print("\nThe wizard will open in your browser.")
    print("Press Ctrl+C to stop the server.\n")
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", wizard_path], check=True)
    except KeyboardInterrupt:
        print("\n\nWizard stopped.")
    except subprocess.CalledProcessError as e:
        print(f"\nError running wizard: {e}")
        sys.exit(1)

