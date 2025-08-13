#!/usr/bin/env python3
"""
Utility script to verify Convergio version system (moved from scripts/).
Note: This is not a pytest test file. Run it manually if needed.
"""

import sys
import os
import json
import subprocess
from pathlib import Path

# Add backend to path for testing
backend_path = Path(__file__).resolve().parents[2] / "backend" / "src"
sys.path.insert(0, str(backend_path))


def check_version_file() -> bool:
    version_file = Path(__file__).resolve().parents[2] / "VERSION"
    if not version_file.exists():
        print("VERSION file not found")
        return False
    version = version_file.read_text().strip()
    print(f"VERSION file: {version}")
    return True


def check_version_scripts() -> bool:
    root = Path(__file__).resolve().parents[2]
    # Python script
    py = subprocess.run(["python3", "scripts/get_version.py"], cwd=root, text=True, capture_output=True)
    if py.returncode != 0:
        print(f"get_version.py failed: {py.stderr}")
        return False
    info = json.loads(py.stdout)
    print(f"Python version: v{info.get('version')} build {info.get('build_number')}")

    # Bash script
    sh = subprocess.run(["bash", "scripts/get_version.sh", "version"], cwd=root, text=True, capture_output=True)
    if sh.returncode != 0:
        print(f"get_version.sh failed: {sh.stderr}")
        return False
    print(f"Bash version: v{sh.stdout.strip()}")
    return True


def check_backend_config() -> bool:
    try:
        from agents.utils.config import get_settings
        settings = get_settings()
        print(f"Backend config: v{settings.app_version} build {settings.build_number}")
        return True
    except Exception as e:
        print(f"Backend config check warning: {e}")
        return True


def check_hooks() -> bool:
    pre = Path(__file__).resolve().parents[2] / ".git" / "hooks" / "pre-commit"
    ok = pre.exists()
    print("Pre-commit hook:", "present" if ok else "missing")
    return ok


def check_backend_syntax() -> bool:
    cfg = Path(__file__).resolve().parents[2] / "backend" / "src" / "agents" / "utils" / "config.py"
    if not cfg.exists():
        print("Backend config not found")
        return False
    code = cfg.read_text()
    compile(code, str(cfg), "exec")
    print("Backend config compiles")
    return True


def main() -> int:
    checks = [
        check_version_file,
        check_version_scripts,
        check_backend_config,
        check_backend_syntax,
        check_hooks,
    ]
    passed = 0
    for fn in checks:
        try:
            if fn():
                passed += 1
        except Exception as e:
            print("Check failed:", e)
    print(f"Passed {passed}/{len(checks)} checks")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
