#!/usr/bin/env python3
"""
Quick Setup Script - Install dependencies and run pipeline
Handles compatibility issues and provides better error messages
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and report results"""
    print(f"\n{'='*70}")
    print(f"▶ {description}")
    print(f"{'='*70}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=False)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            return True
        else:
            print(f"❌ {description} - FAILED")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║    CONVERSATION EVALUATION BENCHMARK - QUICK SETUP              ║
    ║                                                                  ║
    ║    This script will:                                            ║
    ║    1. Install Python dependencies                               ║
    ║    2. Run the complete evaluation pipeline                      ║
    ║    3. Generate all evaluation data                              ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Step 1: Check Python version
    print(f"\n📋 Python Version Check")
    print(f"Python {sys.version}")
    if sys.version_info < (3, 10):
        print("⚠️  WARNING: Python 3.10+ recommended")
    
    # Step 2: Install dependencies
    print(f"\n📦 Installing Dependencies")
    print("This may take a few minutes...")
    
    if not run_command(
        f"{sys.executable} -m pip install --upgrade pip",
        "Upgrading pip"
    ):
        print("Warning: pip upgrade failed, continuing anyway...")
    
    if not run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing project dependencies"
    ):
        print("\n⚠️  Note: Some dependencies may have failed to install")
        print("Trying alternative installation...")
        
        # Try installing without optional dependencies
        run_command(
            f"{sys.executable} -m pip install pandas numpy pydantic python-dotenv fastapi uvicorn",
            "Installing core dependencies (minimal set)"
        )
    
    # Step 3: Run pipeline
    print(f"\n🚀 Running Evaluation Pipeline")
    if run_command(
        f"{sys.executable} run_pipeline.py",
        "Executing pipeline"
    ):
        print("\n" + "="*70)
        print("✅ PIPELINE COMPLETED SUCCESSFULLY!")
        print("="*70)
        print("""
        📊 Output Files Generated:
        
        data/
        ├── facets_processed.json
        ├── conversations/
        └── evaluations/
        
        output/
        └── evaluation_report.json
        
        Next Steps:
        1. Start Streamlit UI: streamlit run ui_app.py
        2. Start API: uvicorn api_main:app --reload
        3. Check output files in data/ directory
        """)
    else:
        print("\n❌ Pipeline failed. Check error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
