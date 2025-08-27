# Import Path Consistency Guide

## ⚠️ CRITICAL: Import Path Standards for Convergio Backend

This document addresses the recurring import path inconsistency issues that occur when different LLMs modify the codebase.

## The Problem

Different AI assistants often change import paths inconsistently, leading to:
- `ModuleNotFoundError: No module named 'core'`
- `ImportError: attempted relative import beyond top-level package`
- SQLAlchemy table redefinition errors
- Backend startup failures
- Test failures

## Root Cause Analysis

The Convergio backend uses a specific module structure where:
- Main entry point: `backend/src/main.py`
- Module root: `backend/src/`
- Package structure: `src.main:app` (as defined in start.sh)
- PYTHONPATH must be set to: `/path/to/convergio/backend/src`

## 🔒 MANDATORY Import Path Standards

### 1. Main Application (`backend/src/main.py`)
**ALWAYS use relative imports:**
```python
# ✅ CORRECT
from .core.database import init_db, close_db
from .api.agents import router as agents_router
from .agents.orchestrator import initialize_agents

# ❌ WRONG - WILL BREAK
from core.database import init_db, close_db
from api.agents import router as agents_router
from agents.orchestrator import initialize_agents
```

### 2. API Modules (`backend/src/api/*.py`)
**ALWAYS use relative imports for internal modules:**
```python
# ✅ CORRECT
from ..core.database import get_db_session
from ..models.talent import Talent
from ..agents.services.agent_intelligence import AgentIntelligence

# ❌ WRONG - WILL BREAK
from core.database import get_db_session
from models.talent import Talent
from agents.services.agent_intelligence import AgentIntelligence
```

### 3. Agent Services (`backend/src/agents/services/*.py`)
**Use appropriate relative imports:**
```python
# ✅ CORRECT (from agents/services/ to core/)
from ...services.unified_cost_tracker import unified_cost_tracker
from ..observability.otel_integration import initialize_otel

# ❌ WRONG - WILL BREAK
from services.unified_cost_tracker import unified_cost_tracker
```

### 4. Benchmark Files (`backend/src/agents/benchmarks/*.py`)
**Special case - mixed imports:**
```python
# ✅ CORRECT
from ..services.autogen_groupchat_orchestrator import ModernGroupChatOrchestrator
from ..services.redis_state_manager import RedisStateManager
from services.unified_cost_tracker import unified_cost_tracker  # Note: absolute for services/
from ..observability.otel_integration import initialize_otel

# ❌ WRONG
from ...services.unified_cost_tracker import unified_cost_tracker  # Too many ..
```

### 5. Models (`backend/src/models/*.py`)
**ALWAYS use relative imports + extend_existing:**
```python
# ✅ CORRECT
from ..core.database import Base

class Document(Base):
    __tablename__ = "documents"
    __table_args__ = {'extend_existing': True}  # CRITICAL: Prevents redefinition errors

# ❌ WRONG
from core.database import Base
# Missing __table_args__ = {'extend_existing': True}
```

## 🛡️ Preventive Measures

### 1. Environment Setup Validation
Before making changes, ALWAYS verify:
```bash
cd /path/to/convergio/backend
export PYTHONPATH=$PWD/src
python -c "from src.main import app; print('✅ Import paths working')"
```

### 2. Test Suite Validation
Run tests with proper PYTHONPATH:
```bash
cd /path/to/convergio
PYTHONPATH=$PWD/backend/src ./test.sh
```

### 3. Common Failure Points to Check

#### SQLAlchemy Models
- ALL models MUST have `__table_args__ = {'extend_existing': True}`
- This prevents "Table 'X' is already defined" errors

#### Orchestrator Imports
- `backend/src/agents/orchestrator.py` should use absolute imports for core modules:
```python
# ✅ CORRECT
from core.redis import init_redis

# ❌ WRONG
from ..core.redis import init_redis  # Causes "attempted relative import beyond top-level package"
```

## 🚨 Emergency Fix Checklist

When import errors occur:

1. **Check main.py imports:**
   ```bash
   grep -n "from [^.]" backend/src/main.py
   # Should return NO matches - all imports should be relative (from .)
   ```

2. **Fix main.py if needed:**
   ```python
   # Change any absolute imports to relative
   sed -i 's/from core\./from .core./g' backend/src/main.py
   sed -i 's/from api\./from .api./g' backend/src/main.py
   sed -i 's/from agents\./from .agents./g' backend/src/main.py
   ```

3. **Check models for table redefinition:**
   ```bash
   grep -L "extend_existing" backend/src/models/*.py
   # Add __table_args__ = {'extend_existing': True} to any missing
   ```

4. **Verify orchestrator imports:**
   ```bash
   grep "from \.\." backend/src/agents/orchestrator.py
   # Should be minimal - most core imports should be absolute
   ```

5. **Test import validation:**
   ```bash
   cd backend/src && python -c "import main; print('✅ OK')"
   ```

## 🔧 Quick Fix Script

Create this as `/backend/fix_imports.py`:
```python
#!/usr/bin/env python3
import re
import glob

def fix_main_imports():
    """Fix main.py imports to be relative"""
    with open('src/main.py', 'r') as f:
        content = f.read()
    
    # Fix imports
    content = re.sub(r'^from (core|api|agents|models|services)\.', r'from .\1.', content, flags=re.MULTILINE)
    
    with open('src/main.py', 'w') as f:
        f.write(content)
    print("✅ Fixed main.py imports")

def fix_model_tables():
    """Add extend_existing to all models"""
    for model_file in glob.glob('src/models/*.py'):
        with open(model_file, 'r') as f:
            content = f.read()
        
        if '__table_args__' not in content and '__tablename__' in content:
            content = content.replace(
                '__tablename__ = ',
                '__tablename__ = '
            ).replace(
                '__tablename__ = "', 
                '__tablename__ = "\n    __table_args__ = {\'extend_existing\': True}\n    "'
            )
            
            with open(model_file, 'w') as f:
                f.write(content)
            print(f"✅ Fixed {model_file}")

if __name__ == "__main__":
    fix_main_imports()
    fix_model_tables()
```

## 📋 Validation Commands

After any LLM changes, run these commands:

```bash
# 1. Test backend startup
cd /path/to/convergio/backend
PYTHONPATH=$PWD/src python -c "from src.main import app; print('✅ Backend imports OK')"

# 2. Run tests
cd /path/to/convergio
PYTHONPATH=$PWD/backend/src ./test.sh

# 3. Check for common issues
cd backend/src
grep -r "from [^.].*core\." . | grep -v "__pycache__" | grep -v ".pyc"
grep -r "attempted relative import" . 2>/dev/null || echo "No relative import errors found"
```

## ⚡ Quick Reference

| File Location | Import Style | Example |
|---------------|-------------|---------|
| `src/main.py` | Relative only | `from .core.database import init_db` |
| `src/api/*.py` | Relative for internal | `from ..core.database import get_db` |
| `src/agents/services/*.py` | Mixed relative | `from ..utils.config import get_settings` |
| `src/agents/benchmarks/*.py` | Mixed (special) | `from services.unified_cost_tracker import x` |
| `src/models/*.py` | Relative + extend_existing | `from ..core.database import Base` |
| `src/agents/orchestrator.py` | Absolute for core | `from core.redis import init_redis` |

---

**🚨 REMEMBER: When in doubt, test the import with:**
```bash
PYTHONPATH=/path/to/convergio/backend/src python -c "from src.main import app"
```

This document should be consulted by ANY AI assistant before modifying import statements!