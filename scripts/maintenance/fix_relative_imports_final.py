#!/usr/bin/env python3
"""
Script to fix missing relative imports in the Convergio backend code.
Fixes imports that should be relative within the same package.
"""

import os
import re
from pathlib import Path

def fix_relative_imports_in_file(file_path):
    """Fix missing relative imports in a single Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix imports that should be relative within the same package
        # These are typically imports from the same directory level
        
        # Fix imports that are missing the . prefix for same-directory imports
        content = re.sub(r'from ([a-zA-Z_][a-zA-Z0-9_]*) import', r'from .\1 import', content)
        
        # But be careful not to double-dot imports that are already correct
        content = re.sub(r'from \.\.([a-zA-Z_][a-zA-Z0-9_]*) import', r'from ..\1 import', content)
        
        # Fix specific common patterns
        content = re.sub(r'from agent_', r'from .agent_', content)
        content = re.sub(r'from selection_', r'from .selection_', content)
        content = re.sub(r'from context import', r'from .context import', content)
        content = re.sub(r'from types import', r'from .types import', content)
        content = re.sub(r'from setup import', r'from .setup import', content)
        content = re.sub(r'from runner import', r'from .runner import', content)
        content = re.sub(r'from rag import', r'from .rag import', content)
        content = re.sub(r'from initializer import', r'from .initializer import', content)
        content = re.sub(r'from intelligent_router import', r'from .intelligent_router import', content)
        content = re.sub(r'from message_classifier import', r'from .message_classifier import', content)
        content = re.sub(r'from selection_metrics_enhanced import', r'from .selection_metrics_enhanced import', content)
        content = re.sub(r'from token_optimizer import', r'from .token_optimizer import', content)
        content = re.sub(r'from conflict_detector import', r'from .conflict_detector import', content)
        content = re.sub(r'from turn_by_turn_selector import', r'from .turn_by_turn_selector import', content)
        content = re.sub(r'from tool_executor import', r'from .tool_executor import', content)
        content = re.sub(r'from rag_enhancements import', r'from .rag_enhancements import', content)
        content = re.sub(r'from orchestrator_conversation import', r'from .orchestrator_conversation import', content)
        content = re.sub(r'from multi_agent_fix import', r'from .multi_agent_fix import', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed relative imports in {file_path}")
            return True
        else:
            print(f"⏭️  No changes needed in {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix all missing relative imports."""
    backend_dir = Path("backend/src")
    
    if not backend_dir.exists():
        print(f"❌ Backend directory not found: {backend_dir}")
        return
    
    print(f"🔍 Scanning for Python files with missing relative imports in {backend_dir}")
    
    # Focus on specific directories that are likely to have relative import issues
    target_dirs = [
        "agents/services/groupchat",
        "agents/services/graphflow", 
        "agents/services/hitl",
        "agents/services/observability",
        "agents/services/streaming"
    ]
    
    python_files = []
    for target_dir in target_dirs:
        target_path = backend_dir / target_dir
        if target_path.exists():
            python_files.extend(list(target_path.rglob("*.py")))
    
    print(f"📁 Found {len(python_files)} Python files in target directories")
    
    fixed_count = 0
    for file_path in python_files:
        if fix_relative_imports_in_file(file_path):
            fixed_count += 1
    
    print(f"\n🎉 Relative import fixing complete!")
    print(f"📊 Files processed: {len(python_files)}")
    print(f"🔧 Files fixed: {fixed_count}")

if __name__ == "__main__":
    main()
