# 🧪 Convergio Test Suite Documentation

## Overview

The Convergio test suite has been reorganized for clarity, efficiency, and comprehensive coverage. All tests now follow a consistent structure with proper logging, documentation, and clear output.

## Test Structure

```
tests/
├── backend/           # Backend unit and functional tests
├── frontend/          # Frontend component and UI tests  
├── integration/       # System integration tests
├── e2e/              # End-to-end user journey tests
├── performance/       # Performance and load tests
├── security/         # Security and vulnerability tests
├── logs/             # Test execution logs with timestamps
└── _archive/         # Deprecated/obsolete tests
```

## Main Test Suites

### 1. Backend Core Tests (`backend/test_core_functionality.py`)
**Purpose:** Test core backend functionality

**Coverage:**
- API health and status endpoints
- Agent initialization (Ali CEO, Amy CFO)
- Orchestrator coordination
- Cost tracking and limits
- Database connectivity
- Security framework
- WebSocket streaming

**Run:** `python tests/backend/test_core_functionality.py`

### 2. System Integration Tests (`integration/test_system_integration.py`)
**Purpose:** Test component integration and workflows

**Coverage:**
- Multi-agent conversations
- Ali CEO intelligent responses
- Amy CFO financial analysis
- Vector search integration
- Web search capabilities
- Performance benchmarks
- Error handling and recovery

**Run:** `python tests/integration/test_system_integration.py`

### 3. End-to-End Tests (`e2e/test_end_to_end.py`)
**Purpose:** Test complete user journeys

**Coverage:**
- Complete user workflows from frontend to backend
- WebSocket real-time streaming
- Multi-step conversations with context
- Concurrent user sessions
- Session management
- Error recovery scenarios

**Run:** `python tests/e2e/test_end_to_end.py`

## Running Tests

### Run All Tests
```bash
# From repository root
pytest tests/ -v

# With coverage report
pytest tests/ --cov=backend --cov-report=html
```

### Run Specific Test Suite
```bash
# Backend tests only
pytest tests/backend/ -v

# Integration tests only
pytest tests/integration/ -v

# E2E tests only
pytest tests/e2e/ -v
```

### Run with Detailed Logging
```bash
# Each test automatically creates timestamped logs in tests/logs/
python tests/backend/test_core_functionality.py
```

## Test Output

All tests produce:
1. **Console output** with colored pass/fail indicators
2. **Timestamped log files** in `tests/logs/` with format: `{test_name}_{YYYYMMDD_HHMMSS}.log`
3. **JUnit XML reports** for CI/CD integration
4. **HTML reports** for detailed test results

### Log File Structure
Each log file contains:
- Test suite name and timestamp
- Individual test execution details
- Performance metrics
- Error messages and stack traces
- Summary of results

Example log output:
```
2024-12-28 16:45:23 - INFO - === Starting test_core_functionality Test Suite ===
2024-12-28 16:45:23 - INFO - Environment: development
2024-12-28 16:45:24 - INFO - ✓ Health check passed: healthy
2024-12-28 16:45:25 - INFO - ✓ Ali CEO initialized with model: gpt-4o-mini
...
```

## Test Requirements

### Python Dependencies
```txt
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
pytest-html>=3.1.0
httpx>=0.24.0
websockets>=11.0
playwright>=1.30.0
```

### Environment Setup
1. Backend must be running on `http://localhost:9000`
2. Frontend (for E2E tests) on `http://localhost:5173`
3. Database and Redis should be accessible
4. API keys should be configured in `.env`

## Writing New Tests

### Test Template
```python
#!/usr/bin/env python3
"""
Test description and purpose
"""

import logging
from datetime import datetime
from pathlib import Path

# Setup logging
LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
TEST_NAME = Path(__file__).stem
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"{TEST_NAME}_{TIMESTAMP}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Your test code here
```

### Best Practices
1. **Clear naming:** Test functions should describe what they test
2. **Documentation:** Each test should have a docstring explaining purpose and coverage
3. **Logging:** Use logger.info() for important checkpoints
4. **Assertions:** Include meaningful assertion messages
5. **Cleanup:** Always clean up resources in teardown methods
6. **Isolation:** Tests should not depend on each other

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Run Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests
        run: |
          pytest tests/ --junit-xml=test-results.xml
      - name: Upload test results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: |
            test-results.xml
            tests/logs/
```

## Troubleshooting

### Common Issues

1. **Tests fail with connection errors**
   - Ensure backend is running: `cd backend && python main.py`
   - Check DATABASE_URL and REDIS_URL in `.env`

2. **WebSocket tests fail**
   - Verify WebSocket endpoint is enabled
   - Check firewall/proxy settings

3. **E2E tests timeout**
   - Increase timeout values in test configuration
   - Ensure frontend is built and running

4. **Missing dependencies**
   ```bash
   pip install -r requirements-test.txt
   ```

## Maintenance

### Regular Tasks
- Review and update test coverage monthly
- Archive obsolete tests to `_archive/`
- Update test documentation when adding new features
- Monitor test execution times and optimize slow tests
- Clean old log files: `find tests/logs -mtime +30 -delete`

## Legacy Tests

The following legacy test categories remain for compatibility:
- `test_agents_simple.py` - Basic agent definition validation
- `test_ali_coordination.py` - Ali's coordination capabilities
- `test_multiagent_conversations.py` - Multi-agent scenarios
- `test_performance_simple.py` - Performance benchmarks

These will be gradually migrated into the new structure.

## Contact

For test-related questions or issues:
- Create an issue in the repository
- Check existing test logs in `tests/logs/`
- Review this documentation for updates