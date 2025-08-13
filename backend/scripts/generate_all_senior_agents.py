#!/usr/bin/env python3
"""
🚀 Generate All Senior-Level Agents for Convergio
==================================================

This script:
1. Runs the senior job description filter to extract senior positions
2. Uses AI to generate agent definitions from those positions
3. Places agents directly in the definitions folder for auto-discovery
"""

import sys
import subprocess
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main execution function."""
    base_dir = Path(__file__).resolve().parents[2]  # convergio root
    
    print("="*60)
    print("🚀 CONVERGIO SENIOR AGENT GENERATION PIPELINE")
    print("="*60)
    
    # Step 1: Filter senior job descriptions
    print("\n📋 Step 1: Extracting senior-level positions...")
    print("-"*40)
    
    filter_script = base_dir / "backend" / "src" / "services" / "job_description_senior_filter.py"
    result = subprocess.run([sys.executable, str(filter_script)], capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"Failed to filter job descriptions: {result.stderr}")
        return 1
    
    print(result.stdout)
    
    # Step 2: Generate agents using AI
    print("\n🤖 Step 2: Generating agents with AI...")
    print("-"*40)
    
    generator_script = base_dir / "backend" / "src" / "services" / "job_description_to_agent_ai.py"
    
    # Set output directly to definitions folder
    output_dir = base_dir / "backend" / "src" / "agents" / "definitions"
    
    result = subprocess.run(
        [sys.executable, str(generator_script), 
         "--output-dir", str(output_dir)],
        capture_output=True, 
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"Failed to generate agents: {result.stderr}")
        return 1
    
    print(result.stdout)
    
    # Step 3: Summary
    print("\n✅ Step 3: Pipeline Complete!")
    print("-"*40)
    print(f"📁 Senior job descriptions: {base_dir / 'jobDescriptions' / 'senior'}")
    print(f"📁 Generated agents: {output_dir}")
    print("\n🎉 New agents are automatically discoverable by the DynamicAgentLoader!")
    print("   They will be loaded next time the system starts.")
    print("="*60)
    
    return 0

if __name__ == "__main__":
    exit(main())