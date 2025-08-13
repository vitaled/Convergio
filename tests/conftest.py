"""
🧪 PYTEST CONFIGURATION - CONVERGIO TEST SUITE
==============================================

Central configuration for all tests.
Sets up paths, logging, and common fixtures.
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime
import pytest
import asyncio

# Setup Python paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
TESTS_DIR = PROJECT_ROOT / "tests"
LOGS_DIR = TESTS_DIR / "logs"

# Add backend to Python path
sys.path.insert(0, str(BACKEND_DIR))

# Create logs directory
LOGS_DIR.mkdir(exist_ok=True)

# Configure logging
def setup_logging(test_name: str):
    """Setup logging for a test with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"{test_name}_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ],
        force=True
    )
    
    logger = logging.getLogger()
    logger.info(f"="*60)
    logger.info(f"Test: {test_name}")
    logger.info(f"Started: {datetime.now().isoformat()}")
    logger.info(f"Log file: {log_file}")
    logger.info(f"="*60)
    
    return logger, log_file

# Common fixtures
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_logger(request):
    """Provide a logger for the test."""
    test_name = request.node.name
    logger, log_file = setup_logging(test_name)
    yield logger
    logger.info(f"Test completed: {test_name}")

@pytest.fixture
async def test_client():
    """Provide an async HTTP client for API testing."""
    import httpx
    async with httpx.AsyncClient(base_url="http://localhost:9000") as client:
        yield client

@pytest.fixture
def backend_settings():
    """Get backend settings."""
    from src.core.config import get_settings
    return get_settings()

@pytest.fixture
async def db_session():
    """Provide a database session for testing."""
    from src.core.database import get_db_session
    async for session in get_db_session():
        yield session
        break

# Test markers
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests"
    )
    config.addinivalue_line(
        "markers", "performance: Performance tests"
    )
    config.addinivalue_line(
        "markers", "security: Security tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )

# Environment configuration
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DATABASE_URL", "postgresql://localhost/convergio_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("API_BASE_URL", "http://localhost:9000")
os.environ.setdefault("COST_API_BASE_URL", "http://localhost:9000/api/v1")