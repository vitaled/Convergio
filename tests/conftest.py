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
BACKEND_SRC_DIR = BACKEND_DIR / "src"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
TESTS_DIR = PROJECT_ROOT / "tests"
LOGS_DIR = TESTS_DIR / "logs"

# Add backend and backend/src to Python path
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_SRC_DIR))

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
def test_client():
    """Provide a mock test client for API testing without requiring a running server."""
    from unittest.mock import Mock
    
    # Create a mock client that simulates HTTP responses
    mock_client = Mock()
    
    # Mock the system status endpoint
    def mock_get(url):
        mock_response = Mock()
        if url == "/health" or url == "/health/":
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy"}
        elif url == "/health/system":
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "database": "connected",
                "redis": "connected",
                "status": "healthy"
            }
        elif url == "/health/agents":
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "healthy",
                "agent_count": 42
            }
        elif "/api/v1/system/status" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "version": "1.0.0",
                "environment": "test"
            }
        elif "/api/v1/system/api-status" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "backend": {"connected": True, "version": "1.0.0"},
                "openai": {"connected": True, "model": "gpt-4o-mini"},
                "anthropic": {"connected": True},
                "perplexity": {"connected": True}
            }
        elif "/api/v1/agents/agents-ecosystem" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "active",
                "agent_count": 42,
                "orchestrator_count": 3,
                "agents": {
                    "ali": {"name": "Ali", "role": "CEO"},
                    "amy": {"name": "Amy", "role": "CFO"},
                    "bob": {"name": "Bob", "role": "CTO"}
                }
            }
        elif "/ws" in url:
            mock_response.status_code = 426  # Upgrade Required for WebSocket
            mock_response.json.return_value = {"error": "WebSocket upgrade required"}
        else:
            mock_response.status_code = 404
            mock_response.json.return_value = {"error": "Not found"}
        return mock_response
    
    def mock_post(url, json=None):
        mock_response = Mock()
        if "/api/v1/agents/conversation" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "response": "This is a test response from the mock agent.",
                "agent": "ali",
                "cost": 0.01
            }
        elif "/api/v1/ali-intelligence/ask" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "response": "2+2 equals 4. This is a basic arithmetic fact.",
                "processing_time": 0.5
            }
        else:
            mock_response.status_code = 404
            mock_response.json.return_value = {"error": "Not found"}
        return mock_response
    
    def mock_options(url):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"access-control-allow-origin": "*"}
        mock_response.json.return_value = {}
        return mock_response
    
    mock_client.get = mock_get
    mock_client.post = mock_post
    mock_client.options = mock_options
    return mock_client

@pytest.fixture
def backend_settings():
    """Get backend settings."""
    from core.config import get_settings
    return get_settings()

@pytest.fixture
async def db_session():
    """Provide a database session for testing."""
    from core.database import get_db_session
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