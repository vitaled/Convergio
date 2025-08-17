#!/usr/bin/env python3
"""
Script to fix incorrect api.agents.* imports that should be agents.*
"""

import os
import re
from pathlib import Path

def fix_incorrect_imports_in_file(file_path):
    """Fix incorrect api.agents.* imports in a single Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix incorrect api.agents.* imports that should be agents.*
        content = re.sub(r'from api\.agents\.', r'from agents.', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed incorrect imports in {file_path}")
            return True
        else:
            print(f"⏭️  No changes needed in {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix all incorrect api.agents.* imports."""
    backend_dir = Path("backend/src")
    
    if not backend_dir.exists():
        print(f"❌ Backend directory not found: {backend_dir}")
        return
    
    print(f"🔍 Scanning for Python files with incorrect api.agents.* imports in {backend_dir}")
    
    python_files = list(backend_dir.rglob("*.py"))
    print(f"📁 Found {len(python_files)} Python files")
    
    fixed_count = 0
    for file_path in python_files:
        if fix_incorrect_imports_in_file(file_path):
            fixed_count += 1
    
    print(f"\n🎉 Import fixing complete!")
    print(f"📊 Files processed: {len(python_files)}")
    print(f"🔧 Files fixed: {fixed_count}")

if __name__ == "__main__":
    main()
