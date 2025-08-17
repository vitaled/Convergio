# Maintenance scripts (archived)

This folder contains one-off maintenance helpers that were used during the August refactors to normalize imports and test code.

Status: archived. These scripts are not part of the normal build/test workflows. Keep for reference; delete later if no longer needed.

Included utilities:
- fix_builtin_imports.py — replace mistakenly relative imports of stdlib/third-party modules
- fix_incorrect_imports.py — adjust `from api.agents.*` to `from agents.*`
- fix_relative_imports.py — rewrite relative imports to absolute
- fix_relative_imports_final.py — enforce missing leading dots for same-package imports
- fix_remaining_imports.py — catch miscellaneous import namespace issues
- fix_httpx_usage.py — convert httpx AsyncClient usage in tests to test_client fixture
- fix_unit_test_imports.py — update tests from `src.*` to new package layout

Use at your own risk. Prefer targeted refactors and linters over repo-wide regex replacements.
