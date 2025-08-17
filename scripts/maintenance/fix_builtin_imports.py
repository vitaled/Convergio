#!/usr/bin/env python3
"""
Script to fix incorrect imports from local modules that should be from built-in Python modules.
"""

import os
import re
from pathlib import Path

def fix_builtin_imports_in_file(file_path):
    """Fix incorrect imports from local modules that should be from built-in modules."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix imports that should be from built-in modules
        content = re.sub(r'from \.dataclasses import', r'from dataclasses import', content)
        content = re.sub(r'from \.typing import', r'from typing import', content)
        content = re.sub(r'from \.json import', r'from json import', content)
        content = re.sub(r'from \.datetime import', r'from datetime import', content)
        content = re.sub(r'from \.os import', r'from os import', content)
        content = re.sub(r'from \.pathlib import', r'from pathlib import', content)
        content = re.sub(r'from \.logging import', r'from logging import', content)
        content = re.sub(r'from \.structlog import', r'from structlog import', content)
        content = re.sub(r'from \.asyncio import', r'from asyncio import', content)
        content = re.sub(r'from \.httpx import', r'from httpx import', content)
        content = re.sub(r'from \.pydantic import', r'from pydantic import', content)
        content = re.sub(r'from \.redis import', r'from redis import', content)
        content = re.sub(r'from \.sqlalchemy import', r'from sqlalchemy import', content)
        content = re.sub(r'from \.fastapi import', r'from fastapi import', content)
        content = re.sub(r'from \.uvicorn import', r'from uvicorn import', content)
        content = re.sub(r'from \.enum import', r'from enum import', content)
        content = re.sub(r'from \.collections import', r'from collections import', content)
        content = re.sub(r'from \.threading import', r'from threading import', content)
        content = re.sub(r'from \.time import', r'from time import', content)
        content = re.sub(r'from \.uuid import', r'from uuid import', content)
        content = re.sub(r'from \.hashlib import', r'from hashlib import', content)
        content = re.sub(r'from \.base64 import', r'from base64 import', content)
        content = re.sub(r'from \.pickle import', r'from pickle import', content)
        content = re.sub(r'from \.copy import', r'from copy import', content)
        content = re.sub(r'from \.itertools import', r'from itertools import', content)
        content = re.sub(r'from \.functools import', r'from functools import', content)
        content = re.sub(r'from \.abc import', r'from abc import', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed builtin imports in {file_path}")
            return True
        else:
            print(f"⏭️  No changes needed in {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix all incorrect builtin imports."""
    backend_dir = Path("backend/src")
    
    if not backend_dir.exists():
        print(f"❌ Backend directory not found: {backend_dir}")
        return
    
    print(f"🔍 Scanning for Python files with incorrect builtin imports in {backend_dir}")
    
    python_files = list(backend_dir.rglob("*.py"))
    print(f"📁 Found {len(python_files)} Python files")
    
    fixed_count = 0
    for file_path in python_files:
        if fix_builtin_imports_in_file(file_path):
            fixed_count += 1
    
    print(f"\n🎉 Builtin import fixing complete!")
    print(f"📊 Files processed: {len(python_files)}")
    print(f"🔧 Files fixed: {fixed_count}")

if __name__ == "__main__":
    main()
