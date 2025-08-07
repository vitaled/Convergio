#!/usr/bin/env python3
"""
Unit tests for core configuration management
"""

import os
import pytest
from pathlib import Path
from src.core.config import Settings, get_settings, ensure_directories


class TestSettings:
    """Test configuration settings validation"""
    
    def test_settings_defaults(self):
        """Test default configuration values"""
        settings = Settings()
        assert settings.ENVIRONMENT == "development"
        assert settings.PORT == 9000
        assert settings.POSTGRES_DB == "convergio_db"
        assert settings.JWT_ALGORITHM == "RS256"
    
    def test_database_url_generation(self):
        """Test DATABASE_URL property generation"""
        settings = Settings(
            POSTGRES_USER="test",
            POSTGRES_PASSWORD="test",
            POSTGRES_HOST="localhost",
            POSTGRES_PORT=5432,
            POSTGRES_DB="test_db"
        )
        expected = "postgresql+asyncpg://test:test@localhost:5432/test_db"
        assert settings.DATABASE_URL == expected
    
    def test_redis_url_generation(self):
        """Test REDIS_URL property generation"""
        settings = Settings(
            REDIS_HOST="localhost",
            REDIS_PORT=6379,
            REDIS_DB=1
        )
        expected = "redis://localhost:6379/1"
        assert settings.REDIS_URL == expected
    
    def test_redis_url_with_password(self):
        """Test REDIS_URL with password"""
        settings = Settings(
            REDIS_HOST="localhost",
            REDIS_PORT=6379,
            REDIS_DB=1,
            REDIS_PASSWORD="secret"
        )
        expected = "redis://:secret@localhost:6379/1"
        assert settings.REDIS_URL == expected
    
    def test_cors_origins_list(self):
        """Test CORS origins string to list conversion"""
        settings = Settings(
            CORS_ALLOWED_ORIGINS="http://localhost:4000,http://localhost:3000"
        )
        expected = ["http://localhost:4000", "http://localhost:3000"]
        assert settings.cors_origins_list == expected
    
    def test_environment_validation(self):
        """Test environment name validation"""
        # Valid environments
        for env in ["development", "staging", "production"]:
            settings = Settings(ENVIRONMENT=env)
            assert settings.ENVIRONMENT == env
        
        # Invalid environment should raise ValueError
        with pytest.raises(ValueError, match="Environment must be one of"):
            Settings(ENVIRONMENT="invalid")
    
    def test_log_level_validation(self):
        """Test log level validation"""
        # Valid log levels
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = Settings(LOG_LEVEL=level)
            assert settings.LOG_LEVEL == level.upper()
        
        # Invalid log level should raise ValueError
        with pytest.raises(ValueError, match="Log level must be one of"):
            Settings(LOG_LEVEL="INVALID")
    
    def test_jwt_algorithm_validation(self):
        """Test JWT algorithm validation"""
        # Valid algorithm
        settings = Settings(JWT_ALGORITHM="RS256")
        assert settings.JWT_ALGORITHM == "RS256"
        
        # Invalid algorithm should raise ValueError
        with pytest.raises(ValueError, match="Only RS256 algorithm is supported"):
            Settings(JWT_ALGORITHM="HS256")
    
    def test_settings_caching(self):
        """Test that get_settings() returns cached instance"""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
    
    def test_ensure_directories(self, tmp_path):
        """Test directory creation"""
        # Create temporary settings with custom paths
        test_settings = Settings()
        test_settings.SECRETS_DIR = tmp_path / "secrets"
        test_settings.LOGS_DIR = tmp_path / "logs"
        test_settings.UPLOADS_DIR = tmp_path / "uploads"
        
        ensure_directories(test_settings)
        
        assert (tmp_path / "secrets").exists()
        assert (tmp_path / "logs").exists()
        assert (tmp_path / "uploads").exists()