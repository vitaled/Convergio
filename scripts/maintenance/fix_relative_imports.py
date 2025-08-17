#!/usr/bin/env python3
"""
Script to fix relative imports in the Convergio backend code.
Converts relative imports to absolute imports for proper module resolution.
"""

import os
import re
from pathlib import Path

def fix_relative_imports_in_file(file_path):
    """Fix relative imports in a single Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix relative imports that go beyond top-level package
        # Convert ... to absolute imports
        content = re.sub(r'from \.\.\.([a-zA-Z_][a-zA-Z0-9_]*)', r'from \1', content)
        
        # Convert .. to absolute imports (agents.services.*)
        content = re.sub(r'from \.\.([a-zA-Z_][a-zA-Z0-9_]*)', r'from agents.\1', content)
        
        # Convert . to absolute imports (current package)
        # This is more complex, so we'll handle specific cases
        content = re.sub(r'from \.([a-zA-Z_][a-zA-Z0-9_]*)', r'from \1', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed imports in {file_path}")
            return True
        else:
            print(f"⏭️  No changes needed in {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix all Python files in the backend directory."""
    backend_dir = Path("backend/src")
    
    if not backend_dir.exists():
        print(f"❌ Backend directory not found: {backend_dir}")
        return
    
    print(f"🔍 Scanning for Python files in {backend_dir}")
    
    python_files = list(backend_dir.rglob("*.py"))
    print(f"📁 Found {len(python_files)} Python files")
    
    fixed_count = 0
    for file_path in python_files:
        if fix_relative_imports_in_file(file_path):
            fixed_count += 1
    
    print(f"\n🎉 Import fixing complete!")
    print(f"📊 Files processed: {len(python_files)}")
    print(f"🔧 Files fixed: {fixed_count}")

if __name__ == "__main__":
    main()
