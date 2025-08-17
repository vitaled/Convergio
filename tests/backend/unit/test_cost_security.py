"""
🔒 Unit Tests for Cost Security Service
Comprehensive tests for security features and anomaly detection
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from services.cost_security_service import (
    CostSecurityService, SecurityLevel, AnomalyType
)


class TestCostSecurityService:
    """Test suite for cost security service"""
    
    @pytest.fixture
    async def security_service(self):
        """Create security service instance"""
        return CostSecurityService()
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.first.return_value = MagicMock(
            call_count=5,
            total_cost=Decimal("2.50")
        )
        mock_session.execute.return_value = mock_result
        return mock_session
    
    @pytest.mark.asyncio
    async def test_analyze_request_security_normal_request(self, security_service):
        """Test security analysis for normal request"""
        
        with patch('services.cost_security_service.get_async_read_session') as mock_session:
            # Mock normal usage patterns
            mock_session.return_value.__aenter__.return_value.execute.return_value.first.return_value = MagicMock(
                call_count=5,
                total_cost=Decimal("1.50")
            )
            
            result = await security_service.analyze_request_security(
                session_id="test_session",
                agent_id="test_agent",
                provider="openai",
                model="gpt-4o",
                estimated_tokens=1000,
                estimated_cost=0.10,
                user_context={}
            )
            
            assert result["allowed"] is True
            assert result["security_level"] in [SecurityLevel.LOW, SecurityLevel.MEDIUM]
            assert result["risk_score"] >= 0
            assert isinstance(result["anomalies"], list)
            assert isinstance(result["recommendations"], list)
    
    @pytest.mark.asyncio
    async def test_analyze_request_security_high_cost_spike(self, security_service):
        """Test security analysis for high cost spike"""
        
        with patch('services.cost_security_service.get_async_read_session') as mock_session:
            mock_session.return_value.__aenter__.return_value.execute.return_value.first.return_value = MagicMock(
                call_count=2,
                total_cost=Decimal("0.50")
            )
            
            result = await security_service.analyze_request_security(
                session_id="test_session",
                agent_id="test_agent",
                provider="openai",
                model="gpt-4o",
                estimated_tokens=1000,
                estimated_cost=15.0,  # High cost
                user_context={}
            )
            
            assert result["security_level"] in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]
            assert result["risk_score"] > 30
            assert any(
                anomaly["type"] == AnomalyType.UNUSUAL_SPIKE 
                for anomaly in result["anomalies"]
            )
    
    @pytest.mark.asyncio
    async def test_rate_limiting_exceeded(self, security_service):
        """Test rate limiting when limits are exceeded"""
        
        with patch('services.cost_security_service.get_async_read_session') as mock_session:
            # Mock rate limit exceeded
            mock_session.return_value.__aenter__.return_value.execute.return_value.first.return_value = MagicMock(
                call_count=70,  # Exceeds default 60 calls/minute
                total_cost=Decimal("5.00")
            )
            
            result = await security_service.analyze_request_security(
                session_id="test_session",
                agent_id="test_agent",
                provider="openai",
                model="gpt-4o",
                estimated_tokens=1000,
                estimated_cost=0.10,
                user_context={}
            )
            
            assert result["allowed"] is False
            assert result["security_level"] in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]
            assert result["rate_limit_status"]["allowed"] is False
            assert any(
                anomaly["type"] == AnomalyType.RAPID_CONSUMPTION 
                for anomaly in result["anomalies"]
            )
    
    @pytest.mark.asyncio
    async def test_token_efficiency_analysis(self, security_service):
        """Test token efficiency anomaly detection"""
        
        with patch('services.cost_security_service.get_async_read_session') as mock_session:
            mock_session.return_value.__aenter__.return_value.execute.return_value.first.return_value = MagicMock(
                call_count=5,
                total_cost=Decimal("1.00")
            )
            
            result = await security_service.analyze_request_security(
                session_id="test_session",
                agent_id="test_agent",
                provider="openai",
                model="gpt-4o",
                estimated_tokens=150000,  # Very high token count
                estimated_cost=0.01,     # Very low cost
                user_context={}
            )
            
            assert any(
                anomaly["type"] == AnomalyType.TOKEN_EXPLOITATION 
                for anomaly in result["anomalies"]
            )
    
    @pytest.mark.asyncio
    async def test_provider_abuse_detection(self, security_service):
        """Test provider abuse pattern detection"""
        
        with patch('services.cost_security_service.get_async_read_session') as mock_session:
            # Mock multiple providers used recently
            mock_session.return_value.__aenter__.return_value.execute.return_value.scalar.return_value = 4
            
            result = await security_service.analyze_request_security(
                session_id="test_session",
                agent_id="test_agent",
                provider="openai",
                model="gpt-4o",
                estimated_tokens=1000,
                estimated_cost=0.10,
                user_context={}
            )
            
            assert any(
                anomaly["type"] == AnomalyType.PROVIDER_ABUSE 
                for anomaly in result["anomalies"]
            )
    
    @pytest.mark.asyncio
    async def test_security_analysis_error_handling(self, security_service):
        """Test security analysis error handling"""
        
        with patch('services.cost_security_service.get_async_read_session') as mock_session:
            # Mock database error
            mock_session.return_value.__aenter__.side_effect = Exception("Database connection failed")
            
            result = await security_service.analyze_request_security(
                session_id="test_session",
                agent_id="test_agent",
                provider="openai",
                model="gpt-4o",
                estimated_tokens=1000,
                estimated_cost=0.10,
                user_context={}
            )
            
            # Should fail secure - block request on error
            assert result["allowed"] is False
            assert result["security_level"] == SecurityLevel.CRITICAL
            assert result["risk_score"] == 100.0
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_generate_security_audit_report(self, security_service):
        """Test security audit report generation"""
        
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        with patch('services.cost_security_service.get_async_read_session') as mock_session:
            # Mock audit data
            mock_db = mock_session.return_value.__aenter__.return_value
            
            # Mock alerts
            mock_alerts_result = AsyncMock()
            mock_alerts_result.scalars.return_value.all.return_value = [
                MagicMock(
                    id=1,
                    alert_type="security_violation",
                    severity="critical",
                    message="Suspicious activity detected",
                    created_at=datetime.utcnow(),
                    is_resolved=False
                )
            ]
            
            # Mock expensive sessions
            mock_sessions_result = AsyncMock()
            mock_sessions_result.scalars.return_value.all.return_value = [
                MagicMock(
                    session_id="expensive_session",
                    total_cost_usd=Decimal("75.50"),
                    total_interactions=10,
                    started_at=datetime.utcnow(),
                    status="completed"
                )
            ]
            
            # Mock provider analysis
            mock_provider_result = AsyncMock()
            mock_provider_result.all.return_value = [
                MagicMock(
                    provider="openai",
                    total_cost=Decimal("100.00"),
                    call_count=50,
                    avg_cost=Decimal("2.00"),
                    max_cost=Decimal("15.00")
                )
            ]
            
            mock_db.execute.side_effect = [
                mock_alerts_result,
                mock_sessions_result,
                mock_provider_result
            ]
            
            report = await security_service.generate_security_audit_report(start_date, end_date)
            
            assert "audit_period" in report
            assert "security_summary" in report
            assert "alerts" in report
            assert "expensive_sessions" in report
            assert "provider_analysis" in report
            assert "security_recommendations" in report
            assert report["audit_period"]["duration_days"] == 7
            assert report["security_summary"]["total_alerts"] == 1
            assert report["security_summary"]["critical_alerts"] == 1
    
    def test_security_level_calculation(self, security_service):
        """Test security level calculation based on risk score"""
        
        assert security_service._calculate_security_level(10) == SecurityLevel.LOW
        assert security_service._calculate_security_level(30) == SecurityLevel.MEDIUM
        assert security_service._calculate_security_level(60) == SecurityLevel.HIGH
        assert security_service._calculate_security_level(90) == SecurityLevel.CRITICAL
    
    @pytest.mark.asyncio
    async def test_generate_security_recommendations(self, security_service):
        """Test security recommendations generation"""
        
        security_result = {
            "risk_score": 70,
            "anomalies": [
                {"type": AnomalyType.RAPID_CONSUMPTION, "severity": "high"},
                {"type": AnomalyType.UNUSUAL_SPIKE, "severity": "medium"},
                {"type": AnomalyType.PROVIDER_ABUSE, "severity": "low"}
            ]
        }
        
        recommendations = await security_service._generate_security_recommendations(security_result)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert any("authentication" in rec.lower() for rec in recommendations)
        assert any("rate limiting" in rec.lower() for rec in recommendations)
        assert any("monitoring" in rec.lower() for rec in recommendations)
    
    def test_anomaly_thresholds_configuration(self, security_service):
        """Test anomaly threshold configuration"""
        
        assert security_service.anomaly_thresholds["cost_spike_multiplier"] > 0
        assert security_service.anomaly_thresholds["rapid_calls_threshold"] > 0
        assert security_service.anomaly_thresholds["session_cost_limit"] > 0
        assert security_service.anomaly_thresholds["hourly_cost_limit"] > 0
        assert security_service.anomaly_thresholds["token_efficiency_threshold"] > 0
    
    def test_rate_limits_configuration(self, security_service):
        """Test rate limits configuration"""
        
        assert "default" in security_service.rate_limits
        assert "high_volume" in security_service.rate_limits
        assert "restricted" in security_service.rate_limits
        
        for tier, limits in security_service.rate_limits.items():
            assert "calls_per_minute" in limits
            assert "cost_per_minute" in limits
            assert limits["calls_per_minute"] > 0
            assert limits["cost_per_minute"] > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_security_analysis(self, security_service):
        """Test concurrent security analysis requests"""
        
        with patch('services.cost_security_service.get_async_read_session') as mock_session:
            mock_session.return_value.__aenter__.return_value.execute.return_value.first.return_value = MagicMock(
                call_count=5,
                total_cost=Decimal("1.50")
            )
            
            # Simulate concurrent requests
            tasks = []
            for i in range(10):
                task = security_service.analyze_request_security(
                    session_id=f"session_{i}",
                    agent_id=f"agent_{i}",
                    provider="openai",
                    model="gpt-4o",
                    estimated_tokens=1000,
                    estimated_cost=0.10,
                    user_context={}
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 10
            for result in results:
                assert "allowed" in result
                assert "security_level" in result
                assert "risk_score" in result
    
    @pytest.mark.asyncio
    async def test_edge_case_zero_cost_request(self, security_service):
        """Test security analysis for zero-cost request"""
        
        with patch('services.cost_security_service.get_async_read_session') as mock_session:
            mock_session.return_value.__aenter__.return_value.execute.return_value.first.return_value = MagicMock(
                call_count=1,
                total_cost=Decimal("0.00")
            )
            
            result = await security_service.analyze_request_security(
                session_id="test_session",
                agent_id="test_agent",
                provider="openai",
                model="gpt-4o",
                estimated_tokens=0,
                estimated_cost=0.0,
                user_context={}
            )
            
            assert result["allowed"] is True
            assert result["security_level"] == SecurityLevel.LOW
            assert result["risk_score"] == 0.0
    
    @pytest.mark.asyncio
    async def test_large_session_analysis(self, security_service):
        """Test security analysis for large session with many interactions"""
        
        with patch('services.cost_security_service.get_async_read_session') as mock_session:
            mock_session.return_value.__aenter__.return_value.execute.return_value.first.return_value = MagicMock(
                call_count=500,  # Very high call count
                total_cost=Decimal("200.00")  # High total cost
            )
            
            result = await security_service.analyze_request_security(
                session_id="large_session",
                agent_id="power_user",
                provider="openai",
                model="gpt-4o",
                estimated_tokens=50000,
                estimated_cost=5.0,
                user_context={"user_tier": "enterprise"}
            )
            
            assert result["allowed"] is False  # Should be blocked due to rate limits
            assert result["security_level"] in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]
            assert result["risk_score"] > 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])