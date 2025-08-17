# Convergio Comprehensive Test Runner Usage Guide

## Overview

The enhanced `test.sh` script runs **ALL** possible tests in the Convergio repository, including:

- 🐍 **Backend Tests**: Unit, integration, e2e, security, performance
- 🟢 **Frontend Tests**: Vitest, Playwright, Storybook
- 🎯 **Master Test Runner**: Comprehensive agent testing suite
- 🔒 **Security Tests**: Backend security + frontend npm audit
- ⚡ **Performance Tests**: Load testing and benchmarks
- 📊 **Coverage Reports**: Code coverage analysis

## Basic Usage

```bash
# Run all tests with default settings
./test.sh

# Run with custom configuration
FAIL_FAST=false RUN_COVERAGE=true ./test.sh
```

## Environment Variables

Configure the test execution behavior:

| Variable | Default | Description |
|----------|---------|-------------|
| `FAIL_FAST` | `true` | Stop at first test failure |
| `RUN_COVERAGE` | `false` | Generate coverage reports |
| `RUN_PERFORMANCE` | `true` | Include performance tests |
| `RUN_SECURITY` | `true` | Include security tests |
| `RUN_MASTER_RUNNER` | `true` | Run comprehensive agent tests |
| `VERBOSE` | `false` | Show detailed test output |
| `BACKEND_PORT` | `9000` | Backend API port for tests |
| `FRONTEND_PORT` | `4000` | Frontend port for tests |

## Test Categories

### 1. Backend Tests (Python)

#### Unit Tests
- **Location**: `tests/backend/unit/`
- **Coverage**: Individual component testing
- **Speed**: Fast execution

#### Core Functionality Tests
- **Location**: `tests/backend/`
- **Coverage**: Core system functionality
- **Speed**: Medium execution

#### Integration Tests
- **Location**: `tests/integration/`
- **Coverage**: Component interaction testing
- **Speed**: Medium execution

#### End-to-End Tests
- **Location**: `tests/e2e/`
- **Coverage**: Full system workflow testing
- **Speed**: Slow execution

#### Security Tests
- **Location**: `tests/security/`
- **Coverage**: Security validation
- **Speed**: Medium execution

#### Performance Tests
- **Location**: `tests/performance/`
- **Coverage**: Load testing and benchmarks
- **Speed**: Slow execution

### 2. Frontend Tests (Node.js)

#### Unit Tests (Vitest)
- **Command**: `npm run test`
- **Coverage**: Component and utility testing
- **Speed**: Fast execution

#### Storybook Tests
- **Command**: `npm run test:ui`
- **Coverage**: Component story testing
- **Speed**: Medium execution

#### E2E Tests (Playwright)
- **Command**: `npm run test:e2e`
- **Coverage**: Full user journey testing
- **Speed**: Slow execution

#### Security Audit
- **Command**: `npm run security:scan`
- **Coverage**: Dependency vulnerability scanning
- **Speed**: Fast execution

### 3. Master Test Runner

- **Location**: `tests/master_test_runner.py`
- **Coverage**: Comprehensive agent testing (48+ agents)
- **Features**: Multi-agent workflows, proactive intelligence
- **Speed**: Very slow execution (15-30 minutes)

## Usage Examples

### Run All Tests (Default)
```bash
./test.sh
```

### Run Without Fail-Fast (Continue on Errors)
```bash
FAIL_FAST=false ./test.sh
```

### Run with Coverage Reports
```bash
RUN_COVERAGE=true ./test.sh
```

### Run Only Backend Tests
```bash
RUN_MASTER_RUNNER=false ./test.sh
```

### Run Only Frontend Tests
```bash
cd frontend
npm run test
npm run test:e2e
```

### Run Specific Test Categories
```bash
# Only unit tests
cd tests/backend/unit
pytest -v

# Only integration tests
cd tests/integration
pytest -v

# Only security tests
cd tests/security
pytest -v
```

### Run Master Test Runner Separately
```bash
cd tests
python master_test_runner.py
```

## Test Output and Logs

### Backend Logs
- **Location**: `tests/logs/`
- **Format**: Timestamped log files
- **Content**: Test execution details, errors, performance metrics

### Frontend Results
- **Vitest**: Console output + coverage reports
- **Playwright**: `frontend/test-results/` directory
- **Storybook**: Component story validation

### Coverage Reports
- **Location**: `htmlcov/` (when enabled)
- **Format**: HTML + terminal output
- **View**: Open `htmlcov/index.html` in browser

## Troubleshooting

### Common Issues

#### Python Environment
```bash
# Ensure Python 3.11 is installed
python3.11 --version

# Recreate virtual environment
rm -rf backend/venv
python3.11 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
```

#### Node.js Dependencies
```bash
# Clear and reinstall frontend deps
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### Test Failures
```bash
# Run specific failing test for debugging
cd tests/backend/unit
pytest test_specific_file.py::test_specific_function -v -s

# Run with verbose output
VERBOSE=true ./test.sh
```

### Performance Considerations

- **Unit Tests**: ~1-5 minutes
- **Integration Tests**: ~5-15 minutes  
- **E2E Tests**: ~10-30 minutes
- **Master Test Runner**: ~15-30 minutes
- **Full Suite**: ~30-60 minutes

### Memory Requirements

- **Backend**: 2-4GB RAM
- **Frontend**: 1-2GB RAM
- **Total**: 4-8GB RAM recommended

## Advanced Configuration

### Custom Test Paths
```bash
# Run specific test directories
pytest tests/backend/unit/ tests/integration/ -v

# Run specific test files
pytest tests/backend/unit/test_specific.py -v

# Run specific test functions
pytest tests/backend/unit/test_specific.py::test_function -v
```

### Parallel Execution
```bash
# Run tests in parallel (if supported)
pytest -n auto tests/ -v

# Run specific number of workers
pytest -n 4 tests/ -v
```

### Test Markers
```bash
# Run only fast tests
pytest -m "not slow" tests/ -v

# Run only slow tests
pytest -m "slow" tests/ -v

# Run specific marker
pytest -m "unit" tests/ -v
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Run Comprehensive Tests
  run: |
    FAIL_FAST=false RUN_COVERAGE=true ./test.sh
  env:
    BACKEND_PORT: 9000
    FRONTEND_PORT: 4000
```

### Docker Example
```dockerfile
# Install dependencies
RUN pip install -r backend/requirements.txt
RUN cd frontend && npm install

# Run tests
CMD ["./test.sh"]
```

## Best Practices

1. **Regular Execution**: Run tests before commits and PRs
2. **Fail-Fast**: Use `FAIL_FAST=true` for development, `false` for CI
3. **Coverage**: Enable coverage for release builds
4. **Performance**: Run performance tests periodically, not every build
5. **Security**: Always run security tests in CI/CD pipeline
6. **Logging**: Check logs for detailed failure information

## Support

For test-related issues:
1. Check the test logs in `tests/logs/`
2. Run individual test categories for isolation
3. Verify environment setup (Python 3.11, Node.js 18+)
4. Check dependency versions in requirements.txt and package.json
