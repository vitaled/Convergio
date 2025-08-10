#!/usr/bin/env python3
"""Test environment loading to see if quotes are being stripped"""

import os
import sys
from pathlib import Path

# Add parent to path to import our config
sys.path.insert(0, str(Path(__file__).parent))

# Test manual loading like our config does
def test_manual_load():
    env_file = Path(__file__).parent / ".env"
    
    print("Testing manual .env loading:")
    print(f"Reading from: {env_file}")
    print("-" * 60)
    
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                if 'DEFAULT_AI_MODEL' in line:
                    key, value = line.split('=', 1)
                    print(f"Raw line: {repr(line)}")
                    print(f"Raw value: {repr(value)}")
                    
                    # Strip quotes
                    value = value.strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    print(f"After stripping: {repr(value)}")
                    os.environ[key] = value
                    break

# Now test with our actual config
print("\n" + "="*60)
print("Testing with our config module:")

from src.agents.utils.config import get_settings

settings = get_settings()
print(f"Model from settings: {repr(settings.default_ai_model)}")
print(f"Model value: [{settings.default_ai_model}]")

# Also check direct env var
print(f"Direct from os.environ: {repr(os.environ.get('DEFAULT_AI_MODEL'))}")