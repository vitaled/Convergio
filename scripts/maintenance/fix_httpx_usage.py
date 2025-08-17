#!/usr/bin/env python3
"""
Script to fix httpx usage in test files, converting them to use the test_client fixture.
"""

import re
from pathlib import Path

def fix_httpx_usage_in_file(file_path):
    """Fix httpx usage in a single test file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Remove httpx import
        content = re.sub(r'import httpx\n', '', content)
        
        # Fix function signatures to add test_client parameter
        content = re.sub(r'async def test_(\w+)\(\):', r'async def test_\\1(test_client):', content)
        
        # Remove async with httpx.AsyncClient() as client: blocks
        content = re.sub(r'async with httpx\.AsyncClient\([^)]*\) as client:\s*\n\s*', '', content)
        
        # Replace client. with test_client.
        content = re.sub(r'client\.', 'test_client.', content)
        
        # Remove BASE_URL usage
        content = re.sub(r'f"\{BASE_URL\}/', '"/', content)
        content = re.sub(r'f"\{BASE_URL\}"', '""', content)
        
        # Remove await from client calls since test_client is synchronous
        content = re.sub(r'await test_client\.', 'test_client.', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed httpx usage in {file_path}")
            return True
        else:
            return False
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix httpx usage in test files."""
    # Fix the comprehensive test file
    test_file = Path("tests/backend/test_backend_comprehensive.py")
    
    if test_file.exists():
        if fix_httpx_usage_in_file(test_file):
            print("✅ Successfully updated test_backend_comprehensive.py")
        else:
            print("ℹ️ No changes needed in test_backend_comprehensive.py")
    else:
        print("❌ test_backend_comprehensive.py not found")

if __name__ == "__main__":
    main()
