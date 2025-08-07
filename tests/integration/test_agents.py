#!/usr/bin/env python3
"""
Simple Agent Test Suite - Tests that all 41 AI agents exist and are loadable
"""

import os
from pathlib import Path

def test_agent_files_exist():
    """Test that all agent definition files exist"""
    project_root = Path(__file__).parent.parent.parent
    agents_dir = project_root / "backend" / "src" / "agents" / "definitions"
    
    if not agents_dir.exists():
        print(f"❌ Agents directory not found: {agents_dir}")
        return False
    
    agent_files = list(agents_dir.glob("*.md"))
    excluded_files = {"CommonValuesAndPrinciples.md", "MICROSOFT_VALUES.md"}
    valid_files = [f for f in agent_files if f.name not in excluded_files]
    
    print(f"📁 Found {len(valid_files)} agent definition files")
    
    if len(valid_files) < 41:
        print(f"❌ Expected at least 41 agents, found {len(valid_files)}")
        return False
    
    # Check that files are readable and non-empty
    valid_count = 0
    for file_path in valid_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            if len(content) > 100:  # Minimum content check
                valid_count += 1
                print(f"✅ {file_path.stem}")
            else:
                print(f"❌ {file_path.stem}: File too short")
        except Exception as e:
            print(f"❌ {file_path.stem}: Error reading file - {e}")
    
    print(f"\n📊 Results:")
    print(f"   Total files: {len(valid_files)}")
    print(f"   Valid agents: {valid_count}")
    
    if valid_count >= 41:
        print("✅ AGENT FILES TEST: PASSED")
        return True
    else:
        print("❌ AGENT FILES TEST: FAILED")
        return False

def main():
    """Main test function"""
    print("🚀 SIMPLE AGENT TEST SUITE")
    print("=" * 50)
    
    try:
        success = test_agent_files_exist()
        return success
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)