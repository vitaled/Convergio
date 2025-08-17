"""
📊 Unit Tests for Cost Analytics Service
Comprehensive tests for analytics, predictions, and optimization features
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import statistics

from backend.src.services.cost_analytics_service import (
    CostAnalyticsService, CostTrend, OptimizationRecommendation
)


class TestCostAnalyticsService:
    """Test suite for cost analytics service"""
    
    @pytest.fixture
    async def analytics_service(self):
        """Create analytics service instance"""
        return CostAnalyticsService()
    
    @pytest.fixture
    def sample_cost_data(self):
        """Sample cost data for testing"""
        base_date = datetime.utcnow() - timedelta(days=30)
        return [
            MagicMock(
                date=base_date + timedelta(days=i),
                total_cost_usd=Decimal(str(10 + i * 0.5)),  # Increasing trend
                total_interactions=50 + i,
                total_tokens=10000 + i * 100
            )
            for i in range(30)
        ]
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        mock_session = AsyncMock()
        return mock_session
    
    @pytest.mark.asyncio
    async def test_generate_comprehensive_analytics_report(self, analytics_service):
        """Test comprehensive analytics report generation"""
        
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        with patch('backend.src.services.cost_analytics_service.get_async_read_session') as mock_session:
            # Mock database responses for all components
            mock_db = mock_session.return_value.__aenter__.return_value
            
            # Mock cost overview data
            mock_db.execute.side_effect = [
                # Total costs query
                AsyncMock(first=lambda: MagicMock(
                    total_cost=Decimal("500.00"),
                    total_interactions=1000,
                    total_tokens=250000,
                    avg_cost=Decimal("0.50"),
                    max_cost=Decimal("5.00"),
                    min_cost=Decimal("0.01")
                )),
                # Daily breakdown query
                AsyncMock(all=lambda: [
                    MagicMock(date=start_date + timedelta(days=i), daily_cost=Decimal(str(15 + i)), daily_interactions=30 + i)
                    for i in range(30)
                ]),
                # Provider performance query
                AsyncMock(all=lambda: [
                    MagicMock(
                        provider="openai",
                        total_cost=Decimal("300.00"),
                        interaction_count=600,
                        avg_cost=Decimal("0.50"),
                        avg_response_time=1200.0,
                        total_tokens=150000,
                        avg_tokens=250.0
                    ),
                    MagicMock(
                        provider="anthropic",
                        total_cost=Decimal("200.00"),
                        interaction_count=400,
                        avg_cost=Decimal("0.50"),
                        avg_response_time=800.0,
                        total_tokens=100000,
                        avg_tokens=250.0
                    )
                ]),
                # Agent efficiency query
                AsyncMock(all=lambda: [
                    MagicMock(
                        agent_id="agent_1",
                        agent_name="Assistant Agent",
                        total_cost=Decimal("150.00"),
                        interaction_count=300,
                        avg_cost=Decimal("0.50"),
                        total_tokens=75000,
                        provider_count=2,
                        session_count=25
                    )
                ]),
                # Model costs query
                AsyncMock(all=lambda: [
                    MagicMock(
                        provider="openai",
                        model="gpt-4o",
                        total_cost=Decimal("200.00"),
                        usage_count=400,
                        avg_cost=Decimal("0.50"),
                        input_tokens=80000,
                        output_tokens=40000,
                        avg_response_time=1000.0
                    )
                ]),
                # Usage patterns - hourly
                AsyncMock(all=lambda: [
                    MagicMock(hour=i, total_cost=Decimal(str(5 + i)), interaction_count=10 + i)
                    for i in range(24)
                ]),
                # Usage patterns - weekly
                AsyncMock(all=lambda: [
                    MagicMock(day_of_week=i, total_cost=Decimal(str(50 + i * 10)), interaction_count=100 + i * 20)
                    for i in range(7)
                ]),
                # Session durations
                AsyncMock(all=lambda: [
                    MagicMock(
                        session_id=f"session_{i}",
                        total_cost_usd=Decimal(str(5 + i)),
                        total_interactions=10 + i,
                        duration_seconds=300 + i * 60
                    )
                    for i in range(10)
                ]),
                # Anomaly detection data
                AsyncMock(all=lambda: [
                    MagicMock(
                        created_at=datetime.utcnow() - timedelta(minutes=i * 10),
                        total_cost_usd=Decimal(str(0.5 + i * 0.1)),
                        session_id=f"session_{i}",
                        agent_id=f"agent_{i % 3}",
                        provider="openai",
                        model="gpt-4o"
                    )
                    for i in range(100)
                ]),
                # Prediction data
                AsyncMock(all=lambda: [
                    MagicMock(date=start_date + timedelta(days=i), daily_cost=Decimal(str(10 + i * 0.2)))
                    for i in range(30)
                ])
            ]
            
            # Mock pricing data
            mock_pricing_result = AsyncMock()
            mock_pricing_result.scalars.return_value.all.return_value = [
                MagicMock(
                    provider="openai",
                    model="gpt-4o",
                    input_price_per_1k=Decimal("0.003"),
                    output_price_per_1k=Decimal("0.015")
                )
            ]
            
            report = await analytics_service.generate_comprehensive_analytics_report(
                start_date, end_date, include_predictions=True, include_optimizations=True
            )
            
            assert "report_metadata" in report
            assert "executive_summary" in report
            assert "cost_overview" in report
            assert "provider_performance" in report
            assert "agent_efficiency" in report
            assert "model_analysis" in report
            assert "usage_patterns" in report
            assert "anomalies" in report
            assert "predictions" in report
            assert "optimization_recommendations" in report
            
            # Verify metadata
            assert report["report_metadata"]["duration_days"] == 30
            assert report["report_metadata"]["includes_predictions"] is True
            assert report["report_metadata"]["includes_optimizations"] is True
    
    @pytest.mark.asyncio
    async def test_cost_overview_generation(self, analytics_service):
        """Test cost overview generation"""
        
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        with patch('backend.src.services.cost_analytics_service.get_async_read_session') as mock_session:
            mock_db = mock_session.return_value.__aenter__.return_value
            
            # Mock total costs query
            mock_db.execute.side_effect = [
                AsyncMock(first=lambda: MagicMock(
                    total_cost=Decimal("100.00"),
                    total_interactions=200,
                    total_tokens=50000,
                    avg_cost=Decimal("0.50"),
                    max_cost=Decimal("2.00"),
                    min_cost=Decimal("0.05")
                )),
                AsyncMock(all=lambda: [
                    MagicMock(date=(start_date + timedelta(days=i)).date(), daily_cost=Decimal(str(10 + i * 2)), daily_interactions=25 + i * 2)
                    for i in range(7)
                ])
            ]
            
            overview = await analytics_service._generate_cost_overview(start_date, end_date)
            
            assert overview["total_cost"] == 100.00
            assert overview["total_interactions"] == 200
            assert overview["total_tokens"] == 50000
            assert overview["average_cost_per_interaction"] == 0.50
            assert overview["max_single_cost"] == 2.00
            assert overview["min_single_cost"] == 0.05
            assert len(overview["daily_breakdown"]) == 7
            assert "trend_analysis" in overview
            assert overview["trend_analysis"]["direction"] in ["increasing", "decreasing", "stable"]
    
    @pytest.mark.asyncio
    async def test_provider_performance_analysis(self, analytics_service):
        """Test provider performance analysis"""
        
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        with patch('backend.src.services.cost_analytics_service.get_async_read_session') as mock_session:
            mock_db = mock_session.return_value.__aenter__.return_value
            
            mock_db.execute.return_value.all.return_value = [
                MagicMock(
                    provider="openai",
                    total_cost=Decimal("60.00"),
                    interaction_count=120,
                    avg_cost=Decimal("0.50"),
                    avg_response_time=1000.0,
                    total_tokens=30000,
                    avg_tokens=250.0
                ),
                MagicMock(
                    provider="anthropic",
                    total_cost=Decimal("40.00"),
                    interaction_count=80,
                    avg_cost=Decimal("0.50"),
                    avg_response_time=800.0,
                    total_tokens=20000,
                    avg_tokens=250.0
                )
            ]
            
            analysis = await analytics_service._analyze_provider_performance(start_date, end_date)
            
            assert "provider_breakdown" in analysis
            assert "efficiency_rankings" in analysis
            assert "cost_optimization_opportunities" in analysis
            assert len(analysis["provider_breakdown"]) == 2
            
            # Check OpenAI provider data
            openai_data = next(p for p in analysis["provider_breakdown"] if p["provider"] == "openai")
            assert openai_data["total_cost"] == 60.00
            assert openai_data["cost_share_percentage"] == 60.0  # 60/100
            assert openai_data["interaction_count"] == 120
            assert openai_data["tokens_per_dollar"] > 0
    
    @pytest.mark.asyncio
    async def test_agent_efficiency_analysis(self, analytics_service):
        """Test agent efficiency analysis"""
        
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        with patch('backend.src.services.cost_analytics_service.get_async_read_session') as mock_session:
            mock_db = mock_session.return_value.__aenter__.return_value
            
            mock_db.execute.return_value.all.return_value = [
                MagicMock(
                    agent_id="agent_1",
                    agent_name="Efficient Agent",
                    total_cost=Decimal("30.00"),
                    interaction_count=100,
                    avg_cost=Decimal("0.30"),
                    total_tokens=25000,
                    provider_count=2,
                    session_count=10
                ),
                MagicMock(
                    agent_id="agent_2", 
                    agent_name="Expensive Agent",
                    total_cost=Decimal("70.00"),
                    interaction_count=100,
                    avg_cost=Decimal("0.70"),
                    total_tokens=25000,
                    provider_count=3,
                    session_count=8
                )
            ]
            
            analysis = await analytics_service._analyze_agent_efficiency(start_date, end_date)
            
            assert "agent_breakdown" in analysis
            assert "top_consumers" in analysis
            assert "efficiency_leaders" in analysis
            assert "optimization_candidates" in analysis
            assert len(analysis["agent_breakdown"]) == 2
            
            # Check that efficiency leaders are sorted by cost
            if analysis["efficiency_leaders"]:
                first_agent = analysis["efficiency_leaders"][0]
                assert first_agent["agent_id"] == "agent_1"  # Lower cost agent
    
    @pytest.mark.asyncio
    async def test_cost_predictions(self, analytics_service):
        """Test cost prediction models"""
        
        # Test data: increasing trend
        daily_costs = [10.0 + i * 0.5 for i in range(14)]  # 14 days of increasing costs
        
        # Test linear prediction
        linear_prediction = await analytics_service._linear_trend_prediction(daily_costs)
        
        assert "next_day" in linear_prediction
        assert "next_7_days" in linear_prediction
        assert "confidence" in linear_prediction
        assert "model_parameters" in linear_prediction
        assert linear_prediction["next_day"] > 0
        assert linear_prediction["next_7_days"] > 0
        assert 0 <= linear_prediction["confidence"] <= 1
        
        # Test seasonal prediction
        seasonal_prediction = await analytics_service._seasonal_prediction(daily_costs)
        
        assert "next_day" in seasonal_prediction
        assert "next_7_days" in seasonal_prediction
        assert seasonal_prediction["confidence"] == 0.7
        
        # Test exponential smoothing
        exp_prediction = await analytics_service._exponential_smoothing(daily_costs)
        
        assert "next_day" in exp_prediction
        assert "next_7_days" in exp_prediction
        assert exp_prediction["confidence"] == 0.6
    
    @pytest.mark.asyncio
    async def test_anomaly_detection(self, analytics_service):
        """Test cost anomaly detection"""
        
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # Create test data with outliers
        normal_costs = [0.5 + i * 0.01 for i in range(90)]  # Normal costs
        outlier_costs = [5.0, 8.0, 12.0]  # Outliers
        all_costs = normal_costs + outlier_costs
        
        cost_data = [
            MagicMock(
                created_at=start_date + timedelta(minutes=i * 10),
                total_cost_usd=Decimal(str(cost)),
                session_id=f"session_{i}",
                agent_id=f"agent_{i % 5}",
                provider="openai",
                model="gpt-4o"
            )
            for i, cost in enumerate(all_costs)
        ]
        
        with patch('backend.src.services.cost_analytics_service.get_async_read_session') as mock_session:
            mock_db = mock_session.return_value.__aenter__.return_value
            mock_db.execute.return_value.all.return_value = cost_data
            
            analysis = await analytics_service._detect_cost_anomalies(start_date, end_date)
            
            assert "anomalies" in analysis
            assert "summary" in analysis
            assert len(analysis["anomalies"]) > 0  # Should detect outliers
            assert analysis["summary"]["total_anomalies"] > 0
            
            # Check that highest cost anomalies are detected
            high_cost_anomalies = [a for a in analysis["anomalies"] if a["cost"] > 10.0]
            assert len(high_cost_anomalies) > 0
    
    def test_trend_calculation(self, analytics_service):
        """Test trend calculation logic"""
        
        # Test increasing trend
        increasing_values = [1.0, 2.0, 3.0, 4.0, 5.0]
        trend = analytics_service._calculate_trend(increasing_values)
        
        assert trend.direction == "increasing"
        assert trend.percentage_change > 0
        assert trend.confidence_score >= 0
        
        # Test decreasing trend
        decreasing_values = [5.0, 4.0, 3.0, 2.0, 1.0]
        trend = analytics_service._calculate_trend(decreasing_values)
        
        assert trend.direction == "decreasing"
        assert trend.percentage_change < 0
        
        # Test stable trend
        stable_values = [2.0, 2.1, 1.9, 2.0, 2.1]
        trend = analytics_service._calculate_trend(stable_values)
        
        assert trend.direction == "stable"
        assert abs(trend.percentage_change) < 10  # Small change
        
        # Test edge case: single value
        single_value = [1.0]
        trend = analytics_service._calculate_trend(single_value)
        
        assert trend.direction == "stable"
        assert trend.percentage_change == 0.0
        assert trend.confidence_score == 0.0
    
    @pytest.mark.asyncio
    async def test_usage_pattern_analysis(self, analytics_service):
        """Test usage pattern analysis"""
        
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        with patch('backend.src.services.cost_analytics_service.get_async_read_session') as mock_session:
            mock_db = mock_session.return_value.__aenter__.return_value
            
            # Mock hourly, weekly, and session data
            mock_db.execute.side_effect = [
                # Hourly patterns
                AsyncMock(all=lambda: [
                    MagicMock(hour=i, total_cost=Decimal(str(1 + i * 0.5)), interaction_count=10 + i)
                    for i in range(24)
                ]),
                # Weekly patterns
                AsyncMock(all=lambda: [
                    MagicMock(day_of_week=i, total_cost=Decimal(str(10 + i * 5)), interaction_count=50 + i * 10)
                    for i in range(7)
                ]),
                # Session durations
                AsyncMock(all=lambda: [
                    MagicMock(
                        session_id=f"session_{i}",
                        total_cost_usd=Decimal(str(2 + i * 0.5)),
                        total_interactions=5 + i,
                        duration_seconds=300 + i * 120
                    )
                    for i in range(20)
                ])
            ]
            
            analysis = await analytics_service._analyze_usage_patterns(start_date, end_date)
            
            assert "hourly_patterns" in analysis
            assert "weekly_patterns" in analysis
            assert "session_analysis" in analysis
            assert "peak_usage_insights" in analysis
            
            assert len(analysis["hourly_patterns"]) == 24
            assert len(analysis["weekly_patterns"]) == 7
            
            # Verify day name mapping
            sunday_data = next(d for d in analysis["weekly_patterns"] if d["day_of_week"] == 0)
            assert sunday_data["day_name"] == "Sunday"
    
    @pytest.mark.asyncio
    async def test_error_handling_in_report_generation(self, analytics_service):
        """Test error handling during report generation"""
        
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        with patch('backend.src.services.cost_analytics_service.get_async_read_session') as mock_session:
            # Mock database error
            mock_session.return_value.__aenter__.side_effect = Exception("Database connection failed")
            
            report = await analytics_service.generate_comprehensive_analytics_report(
                start_date, end_date, include_predictions=True, include_optimizations=True
            )
            
            assert "error" in report
            assert "generated_at" in report
            assert report["error"] == "Database connection failed"
    
    @pytest.mark.asyncio
    async def test_insufficient_data_handling(self, analytics_service):
        """Test handling of insufficient data scenarios"""
        
        start_date = datetime.utcnow() - timedelta(days=2)
        end_date = datetime.utcnow()
        
        with patch('backend.src.services.cost_analytics_service.get_async_read_session') as mock_session:
            mock_db = mock_session.return_value.__aenter__.return_value
            
            # Mock insufficient data for predictions (less than 7 days)
            mock_db.execute.return_value.all.return_value = [
                MagicMock(date=(start_date + timedelta(days=i)).date(), daily_cost=Decimal(str(10 + i)))
                for i in range(2)  # Only 2 days of data
            ]
            
            predictions = await analytics_service._generate_cost_predictions(start_date, end_date)
            
            assert "error" in predictions
            assert "Insufficient data" in predictions["error"]
            assert predictions["required_days"] == 7
            assert predictions["available_days"] == 2
    
    @pytest.mark.asyncio
    async def test_concurrent_analytics_requests(self, analytics_service):
        """Test handling of concurrent analytics requests"""
        
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        with patch('backend.src.services.cost_analytics_service.get_async_read_session') as mock_session:
            # Mock successful database responses
            mock_db = mock_session.return_value.__aenter__.return_value
            mock_db.execute.return_value.first.return_value = MagicMock(
                total_cost=Decimal("100.00"),
                total_interactions=200,
                total_tokens=50000,
                avg_cost=Decimal("0.50"),
                max_cost=Decimal("2.00"),
                min_cost=Decimal("0.05")
            )
            mock_db.execute.return_value.all.return_value = []
            
            # Create multiple concurrent requests
            tasks = []
            for i in range(5):
                task = analytics_service._generate_cost_overview(start_date, end_date)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            assert len(results) == 5
            for result in results:
                if not isinstance(result, Exception):
                    assert "total_cost" in result
                    assert "total_interactions" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])