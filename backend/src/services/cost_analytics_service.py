"""
📊 Advanced Cost Analytics and Intelligence Service
Comprehensive cost analysis, predictions, and optimization insights
"""

import asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
import statistics
import numpy as np
from dataclasses import dataclass

import structlog
from sqlalchemy import and_, func, select, text, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session, get_async_read_session
from models.cost_tracking import (
    CostAlert, CostSession, CostStatus, CostTracking,
    DailyCostSummary, Provider, ProviderPricing
)

logger = structlog.get_logger()


@dataclass
class CostTrend:
    """Cost trend analysis result"""
    direction: str  # increasing, decreasing, stable
    percentage_change: float
    confidence_score: float
    prediction_accuracy: float


@dataclass
class OptimizationRecommendation:
    """Cost optimization recommendation"""
    type: str
    priority: str  # high, medium, low
    potential_savings: float
    description: str
    implementation_effort: str  # easy, medium, hard
    affected_components: List[str]


class CostAnalyticsService:
    """Advanced cost analytics and business intelligence"""
    
    def __init__(self):
        """Initialize cost analytics service"""
        self.prediction_models = {
            "linear": self._linear_trend_prediction,
            "seasonal": self._seasonal_prediction,
            "exponential": self._exponential_smoothing
        }
        
        # Analytics settings
        self.trend_analysis_days = 30
        self.prediction_horizon_days = 7
        self.optimization_threshold = 0.1  # 10% potential savings
        
        logger.info("📊 Cost analytics service initialized")
    
    async def generate_comprehensive_analytics_report(
        self,
        start_date: datetime,
        end_date: datetime,
        include_predictions: bool = True,
        include_optimizations: bool = True
    ) -> Dict[str, Any]:
        """
        Generate comprehensive cost analytics report
        """
        
        try:
            logger.info("📊 Generating comprehensive analytics report",
                       start_date=start_date,
                       end_date=end_date)
            
            # Gather all analytics concurrently
            analytics_tasks = await asyncio.gather(
                self._generate_cost_overview(start_date, end_date),
                self._analyze_provider_performance(start_date, end_date),
                self._analyze_agent_efficiency(start_date, end_date),
                self._analyze_model_costs(start_date, end_date),
                self._analyze_usage_patterns(start_date, end_date),
                self._detect_cost_anomalies(start_date, end_date),
                return_exceptions=True
            )
            
            cost_overview, provider_performance, agent_efficiency, model_costs, usage_patterns, anomalies = analytics_tasks
            
            report = {
                "report_metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "period": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat(),
                        "duration_days": (end_date - start_date).days
                    },
                    "report_version": "2.0",
                    "includes_predictions": include_predictions,
                    "includes_optimizations": include_optimizations
                },
                "executive_summary": await self._generate_executive_summary(cost_overview, provider_performance),
                "cost_overview": cost_overview if not isinstance(cost_overview, Exception) else {"error": str(cost_overview)},
                "provider_performance": provider_performance if not isinstance(provider_performance, Exception) else {"error": str(provider_performance)},
                "agent_efficiency": agent_efficiency if not isinstance(agent_efficiency, Exception) else {"error": str(agent_efficiency)},
                "model_analysis": model_costs if not isinstance(model_costs, Exception) else {"error": str(model_costs)},
                "usage_patterns": usage_patterns if not isinstance(usage_patterns, Exception) else {"error": str(usage_patterns)},
                "anomalies": anomalies if not isinstance(anomalies, Exception) else {"error": str(anomalies)}
            }
            
            # Add predictions if requested
            if include_predictions:
                try:
                    predictions = await self._generate_cost_predictions(start_date, end_date)
                    report["predictions"] = predictions
                except Exception as e:
                    report["predictions"] = {"error": str(e)}
            
            # Add optimization recommendations if requested
            if include_optimizations:
                try:
                    optimizations = await self._generate_optimization_recommendations(report)
                    report["optimization_recommendations"] = optimizations
                except Exception as e:
                    report["optimization_recommendations"] = {"error": str(e)}
            
            logger.info("✅ Analytics report generated successfully")
            return report
            
        except Exception as e:
            logger.error("❌ Failed to generate analytics report", error=str(e))
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }
    
    async def _generate_cost_overview(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate high-level cost overview"""
        
        async with get_async_read_session() as db:
            # Total costs and statistics
            total_result = await db.execute(
                select(
                    func.sum(CostTracking.total_cost_usd).label("total_cost"),
                    func.count(CostTracking.id).label("total_interactions"),
                    func.sum(CostTracking.total_tokens).label("total_tokens"),
                    func.avg(CostTracking.total_cost_usd).label("avg_cost"),
                    func.max(CostTracking.total_cost_usd).label("max_cost"),
                    func.min(CostTracking.total_cost_usd).label("min_cost")
                )
                .where(
                    and_(
                        CostTracking.created_at >= start_date,
                        CostTracking.created_at <= end_date
                    )
                )
            )
            
            totals = total_result.first()
            
            # Daily breakdown
            daily_result = await db.execute(
                select(
                    func.date(CostTracking.created_at).label("date"),
                    func.sum(CostTracking.total_cost_usd).label("daily_cost"),
                    func.count(CostTracking.id).label("daily_interactions")
                )
                .where(
                    and_(
                        CostTracking.created_at >= start_date,
                        CostTracking.created_at <= end_date
                    )
                )
                .group_by(func.date(CostTracking.created_at))
                .order_by("date")
            )
            
            daily_data = daily_result.all()
            
            # Calculate trends
            daily_costs = [float(row.daily_cost) for row in daily_data]
            trend_analysis = self._calculate_trend(daily_costs)
            
            return {
                "total_cost": float(totals.total_cost or 0),
                "total_interactions": totals.total_interactions or 0,
                "total_tokens": totals.total_tokens or 0,
                "average_cost_per_interaction": float(totals.avg_cost or 0),
                "max_single_cost": float(totals.max_cost or 0),
                "min_single_cost": float(totals.min_cost or 0),
                "daily_breakdown": [
                    {
                        "date": row.date.isoformat() if row.date else None,
                        "cost": float(row.daily_cost or 0),
                        "interactions": row.daily_interactions or 0
                    }
                    for row in daily_data
                ],
                "trend_analysis": {
                    "direction": trend_analysis.direction,
                    "percentage_change": trend_analysis.percentage_change,
                    "confidence_score": trend_analysis.confidence_score
                },
                "cost_distribution": await self._analyze_cost_distribution(db, start_date, end_date)
            }
    
    async def _analyze_provider_performance(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze performance across providers"""
        
        async with get_async_read_session() as db:
            provider_result = await db.execute(
                select(
                    CostTracking.provider,
                    func.sum(CostTracking.total_cost_usd).label("total_cost"),
                    func.count(CostTracking.id).label("interaction_count"),
                    func.avg(CostTracking.total_cost_usd).label("avg_cost"),
                    func.avg(CostTracking.response_time_ms).label("avg_response_time"),
                    func.sum(CostTracking.total_tokens).label("total_tokens"),
                    func.avg(CostTracking.total_tokens).label("avg_tokens")
                )
                .where(
                    and_(
                        CostTracking.created_at >= start_date,
                        CostTracking.created_at <= end_date
                    )
                )
                .group_by(CostTracking.provider)
                .order_by(desc("total_cost"))
            )
            
            provider_stats = provider_result.all()
            
            # Calculate efficiency metrics
            provider_analysis = []
            total_cost = sum(float(stat.total_cost) for stat in provider_stats)
            
            for stat in provider_stats:
                cost_share = (float(stat.total_cost) / total_cost * 100) if total_cost > 0 else 0
                tokens_per_dollar = (stat.total_tokens / float(stat.total_cost)) if stat.total_cost and float(stat.total_cost) > 0 else 0
                
                provider_analysis.append({
                    "provider": stat.provider,
                    "total_cost": float(stat.total_cost),
                    "cost_share_percentage": cost_share,
                    "interaction_count": stat.interaction_count,
                    "average_cost_per_interaction": float(stat.avg_cost or 0),
                    "average_response_time_ms": float(stat.avg_response_time or 0),
                    "total_tokens": stat.total_tokens or 0,
                    "average_tokens_per_interaction": float(stat.avg_tokens or 0),
                    "tokens_per_dollar": tokens_per_dollar,
                    "efficiency_score": await self._calculate_provider_efficiency(stat)
                })
            
            return {
                "provider_breakdown": provider_analysis,
                "efficiency_rankings": sorted(
                    provider_analysis,
                    key=lambda x: x["efficiency_score"],
                    reverse=True
                ),
                "cost_optimization_opportunities": await self._identify_provider_optimizations(provider_analysis)
            }
    
    async def _analyze_agent_efficiency(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze agent cost efficiency"""
        
        async with get_async_read_session() as db:
            agent_result = await db.execute(
                select(
                    CostTracking.agent_id,
                    CostTracking.agent_name,
                    func.sum(CostTracking.total_cost_usd).label("total_cost"),
                    func.count(CostTracking.id).label("interaction_count"),
                    func.avg(CostTracking.total_cost_usd).label("avg_cost"),
                    func.sum(CostTracking.total_tokens).label("total_tokens"),
                    func.count(func.distinct(CostTracking.provider)).label("provider_count"),
                    func.count(func.distinct(CostTracking.session_id)).label("session_count")
                )
                .where(
                    and_(
                        CostTracking.created_at >= start_date,
                        CostTracking.created_at <= end_date,
                        CostTracking.agent_id.isnot(None)
                    )
                )
                .group_by(CostTracking.agent_id, CostTracking.agent_name)
                .order_by(desc("total_cost"))
            )
            
            agent_stats = agent_result.all()
            
            agent_analysis = []
            total_cost = sum(float(stat.total_cost) for stat in agent_stats)
            
            for stat in agent_stats:
                cost_share = (float(stat.total_cost) / total_cost * 100) if total_cost > 0 else 0
                cost_per_session = float(stat.total_cost) / stat.session_count if stat.session_count > 0 else 0
                
                agent_analysis.append({
                    "agent_id": stat.agent_id,
                    "agent_name": stat.agent_name,
                    "total_cost": float(stat.total_cost),
                    "cost_share_percentage": cost_share,
                    "interaction_count": stat.interaction_count,
                    "session_count": stat.session_count,
                    "average_cost_per_interaction": float(stat.avg_cost or 0),
                    "average_cost_per_session": cost_per_session,
                    "total_tokens": stat.total_tokens or 0,
                    "provider_diversity": stat.provider_count or 0,
                    "efficiency_metrics": await self._calculate_agent_efficiency_metrics(stat)
                })
            
            return {
                "agent_breakdown": agent_analysis,
                "top_consumers": agent_analysis[:10],
                "efficiency_leaders": sorted(
                    [a for a in agent_analysis if a["interaction_count"] >= 5],  # Min 5 interactions
                    key=lambda x: x["average_cost_per_interaction"]
                )[:5],
                "optimization_candidates": await self._identify_agent_optimizations(agent_analysis)
            }
    
    async def _analyze_model_costs(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze costs by model"""
        
        async with get_async_read_session() as db:
            model_result = await db.execute(
                select(
                    CostTracking.provider,
                    CostTracking.model,
                    func.sum(CostTracking.total_cost_usd).label("total_cost"),
                    func.count(CostTracking.id).label("usage_count"),
                    func.avg(CostTracking.total_cost_usd).label("avg_cost"),
                    func.sum(CostTracking.input_tokens).label("input_tokens"),
                    func.sum(CostTracking.output_tokens).label("output_tokens"),
                    func.avg(CostTracking.response_time_ms).label("avg_response_time")
                )
                .where(
                    and_(
                        CostTracking.created_at >= start_date,
                        CostTracking.created_at <= end_date
                    )
                )
                .group_by(CostTracking.provider, CostTracking.model)
                .order_by(desc("total_cost"))
            )
            
            model_stats = model_result.all()
            
            # Get current pricing for cost analysis
            pricing_result = await db.execute(
                select(ProviderPricing)
                .where(ProviderPricing.is_active == True)
            )
            current_pricing = {
                f"{p.provider}:{p.model}": p
                for p in pricing_result.scalars().all()
            }
            
            model_analysis = []
            total_cost = sum(float(stat.total_cost) for stat in model_stats)
            
            for stat in model_stats:
                model_key = f"{stat.provider}:{stat.model}"
                pricing = current_pricing.get(model_key)
                
                cost_share = (float(stat.total_cost) / total_cost * 100) if total_cost > 0 else 0
                total_tokens = (stat.input_tokens or 0) + (stat.output_tokens or 0)
                
                # Calculate theoretical vs actual cost
                theoretical_cost = 0
                if pricing and total_tokens > 0:
                    theoretical_cost = (
                        float(pricing.input_price_per_1k) * (stat.input_tokens or 0) / 1000 +
                        float(pricing.output_price_per_1k) * (stat.output_tokens or 0) / 1000
                    )
                
                cost_variance = float(stat.total_cost) - theoretical_cost if theoretical_cost > 0 else 0
                
                model_analysis.append({
                    "provider": stat.provider,
                    "model": stat.model,
                    "total_cost": float(stat.total_cost),
                    "cost_share_percentage": cost_share,
                    "usage_count": stat.usage_count,
                    "average_cost_per_use": float(stat.avg_cost or 0),
                    "total_tokens": total_tokens,
                    "input_tokens": stat.input_tokens or 0,
                    "output_tokens": stat.output_tokens or 0,
                    "average_response_time_ms": float(stat.avg_response_time or 0),
                    "theoretical_cost": theoretical_cost,
                    "cost_variance": cost_variance,
                    "cost_efficiency_score": await self._calculate_model_efficiency(stat, pricing)
                })
            
            return {
                "model_breakdown": model_analysis,
                "most_expensive": model_analysis[:5],
                "most_used": sorted(model_analysis, key=lambda x: x["usage_count"], reverse=True)[:5],
                "most_efficient": sorted(
                    [m for m in model_analysis if m["usage_count"] >= 3],
                    key=lambda x: x["cost_efficiency_score"],
                    reverse=True
                )[:5],
                "cost_variance_analysis": [
                    m for m in model_analysis
                    if abs(m["cost_variance"]) > 0.1  # Variance > $0.10
                ]
            }
    
    async def _analyze_usage_patterns(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze usage patterns over time"""
        
        async with get_async_read_session() as db:
            # Hourly patterns
            hourly_result = await db.execute(
                select(
                    func.extract('hour', CostTracking.created_at).label("hour"),
                    func.sum(CostTracking.total_cost_usd).label("total_cost"),
                    func.count(CostTracking.id).label("interaction_count")
                )
                .where(
                    and_(
                        CostTracking.created_at >= start_date,
                        CostTracking.created_at <= end_date
                    )
                )
                .group_by(func.extract('hour', CostTracking.created_at))
                .order_by("hour")
            )
            
            hourly_data = hourly_result.all()
            
            # Weekly patterns
            weekly_result = await db.execute(
                select(
                    func.extract('dow', CostTracking.created_at).label("day_of_week"),
                    func.sum(CostTracking.total_cost_usd).label("total_cost"),
                    func.count(CostTracking.id).label("interaction_count")
                )
                .where(
                    and_(
                        CostTracking.created_at >= start_date,
                        CostTracking.created_at <= end_date
                    )
                )
                .group_by(func.extract('dow', CostTracking.created_at))
                .order_by("day_of_week")
            )
            
            weekly_data = weekly_result.all()
            
            # Session duration analysis
            session_duration_result = await db.execute(
                select(
                    CostSession.session_id,
                    CostSession.total_cost_usd,
                    CostSession.total_interactions,
                    func.extract('epoch', CostSession.ended_at - CostSession.started_at).label("duration_seconds")
                )
                .where(
                    and_(
                        CostSession.started_at >= start_date,
                        CostSession.started_at <= end_date,
                        CostSession.ended_at.isnot(None)
                    )
                )
            )
            
            session_durations = session_duration_result.all()
            
            return {
                "hourly_patterns": [
                    {
                        "hour": int(row.hour),
                        "total_cost": float(row.total_cost),
                        "interaction_count": row.interaction_count,
                        "average_cost": float(row.total_cost) / row.interaction_count if row.interaction_count > 0 else 0
                    }
                    for row in hourly_data
                ],
                "weekly_patterns": [
                    {
                        "day_of_week": int(row.day_of_week),  # 0=Sunday, 6=Saturday
                        "day_name": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][int(row.day_of_week)],
                        "total_cost": float(row.total_cost),
                        "interaction_count": row.interaction_count
                    }
                    for row in weekly_data
                ],
                "session_analysis": {
                    "average_session_duration_minutes": statistics.mean([
                        float(s.duration_seconds) / 60 for s in session_durations if s.duration_seconds
                    ]) if session_durations else 0,
                    "average_cost_per_session": statistics.mean([
                        float(s.total_cost_usd) for s in session_durations
                    ]) if session_durations else 0,
                    "cost_vs_duration_correlation": await self._calculate_session_correlation(session_durations)
                },
                "peak_usage_insights": await self._identify_peak_usage_patterns(hourly_data, weekly_data)
            }
    
    async def _detect_cost_anomalies(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Detect cost anomalies and unusual patterns"""
        
        async with get_async_read_session() as db:
            # Get all costs in chronological order
            cost_result = await db.execute(
                select(
                    CostTracking.created_at,
                    CostTracking.total_cost_usd,
                    CostTracking.session_id,
                    CostTracking.agent_id,
                    CostTracking.provider,
                    CostTracking.model
                )
                .where(
                    and_(
                        CostTracking.created_at >= start_date,
                        CostTracking.created_at <= end_date
                    )
                )
                .order_by(CostTracking.created_at)
            )
            
            cost_data = cost_result.all()
            
            if not cost_data:
                return {"anomalies": [], "summary": "No data available for anomaly detection"}
            
            costs = [float(row.total_cost_usd) for row in cost_data]
            mean_cost = statistics.mean(costs)
            std_cost = statistics.stdev(costs) if len(costs) > 1 else 0
            
            anomalies = []
            
            # Statistical outliers (3 standard deviations)
            outlier_threshold = mean_cost + (3 * std_cost)
            
            for row in cost_data:
                cost = float(row.total_cost_usd)
                
                if cost > outlier_threshold and cost > 1.0:  # $1 minimum for anomaly
                    anomalies.append({
                        "type": "statistical_outlier",
                        "severity": "high" if cost > outlier_threshold * 2 else "medium",
                        "cost": cost,
                        "timestamp": row.created_at.isoformat(),
                        "session_id": row.session_id,
                        "agent_id": row.agent_id,
                        "provider": row.provider,
                        "model": row.model,
                        "deviation_from_mean": cost - mean_cost,
                        "standard_deviations": (cost - mean_cost) / std_cost if std_cost > 0 else 0
                    })
            
            # Time-based anomalies (spikes in short periods)
            time_anomalies = await self._detect_time_based_anomalies(cost_data)
            anomalies.extend(time_anomalies)
            
            return {
                "anomalies": sorted(anomalies, key=lambda x: x["cost"], reverse=True),
                "summary": {
                    "total_anomalies": len(anomalies),
                    "high_severity": len([a for a in anomalies if a.get("severity") == "high"]),
                    "medium_severity": len([a for a in anomalies if a.get("severity") == "medium"]),
                    "statistical_baseline": {
                        "mean_cost": mean_cost,
                        "standard_deviation": std_cost,
                        "outlier_threshold": outlier_threshold
                    }
                }
            }
    
    async def _generate_cost_predictions(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate cost predictions using multiple models"""
        
        async with get_async_read_session() as db:
            # Get daily cost data for prediction
            daily_result = await db.execute(
                select(
                    func.date(CostTracking.created_at).label("date"),
                    func.sum(CostTracking.total_cost_usd).label("daily_cost")
                )
                .where(
                    and_(
                        CostTracking.created_at >= start_date,
                        CostTracking.created_at <= end_date
                    )
                )
                .group_by(func.date(CostTracking.created_at))
                .order_by("date")
            )
            
            daily_data = daily_result.all()
            
            if len(daily_data) < 7:  # Need at least a week of data
                return {
                    "error": "Insufficient data for predictions",
                    "required_days": 7,
                    "available_days": len(daily_data)
                }
            
            daily_costs = [float(row.daily_cost) for row in daily_data]
            
            # Generate predictions using different models
            predictions = {}
            
            for model_name, model_func in self.prediction_models.items():
                try:
                    prediction = await model_func(daily_costs)
                    predictions[model_name] = prediction
                except Exception as e:
                    predictions[model_name] = {"error": str(e)}
            
            # Ensemble prediction (average of all models)
            valid_predictions = [
                p["next_7_days"] for p in predictions.values()
                if isinstance(p, dict) and "next_7_days" in p
            ]
            
            ensemble_prediction = {
                "next_day": statistics.mean([p["next_day"] for p in predictions.values() if isinstance(p, dict) and "next_day" in p]) if valid_predictions else 0,
                "next_7_days": statistics.mean(valid_predictions) if valid_predictions else 0,
                "confidence": min([p.get("confidence", 0) for p in predictions.values() if isinstance(p, dict)], default=0)
            }
            
            return {
                "individual_models": predictions,
                "ensemble_prediction": ensemble_prediction,
                "prediction_metadata": {
                    "data_points_used": len(daily_costs),
                    "prediction_horizon": self.prediction_horizon_days,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
    
    async def _generate_optimization_recommendations(self, analytics_report: Dict[str, Any]) -> List[OptimizationRecommendation]:
        """Generate cost optimization recommendations"""
        
        recommendations = []
        
        try:
            # Provider optimization
            if "provider_performance" in analytics_report:
                provider_recs = await self._analyze_provider_optimization_opportunities(
                    analytics_report["provider_performance"]
                )
                recommendations.extend(provider_recs)
            
            # Model optimization
            if "model_analysis" in analytics_report:
                model_recs = await self._analyze_model_optimization_opportunities(
                    analytics_report["model_analysis"]
                )
                recommendations.extend(model_recs)
            
            # Agent optimization
            if "agent_efficiency" in analytics_report:
                agent_recs = await self._analyze_agent_optimization_opportunities(
                    analytics_report["agent_efficiency"]
                )
                recommendations.extend(agent_recs)
            
            # Usage pattern optimization
            if "usage_patterns" in analytics_report:
                pattern_recs = await self._analyze_usage_pattern_optimization(
                    analytics_report["usage_patterns"]
                )
                recommendations.extend(pattern_recs)
            
            # Sort by potential savings
            recommendations.sort(key=lambda x: x.potential_savings, reverse=True)
            
            return recommendations[:10]  # Top 10 recommendations
            
        except Exception as e:
            logger.error("❌ Failed to generate optimization recommendations", error=str(e))
            return []
    
    # Helper methods for calculations and analysis
    
    def _calculate_trend(self, values: List[float]) -> CostTrend:
        """Calculate trend analysis for a series of values"""
        
        if len(values) < 2:
            return CostTrend("stable", 0.0, 0.0, 0.0)
        
        # Simple linear regression
        x = list(range(len(values)))
        n = len(values)
        
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x_i * y_i for x_i, y_i in zip(x, values))
        sum_x2 = sum(x_i * x_i for x_i in x)
        
        if (n * sum_x2 - sum_x * sum_x) == 0:
            return CostTrend("stable", 0.0, 0.0, 0.0)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Calculate percentage change
        if values[0] != 0:
            percentage_change = ((values[-1] - values[0]) / values[0]) * 100
        else:
            percentage_change = 0.0
        
        # Determine direction
        if abs(slope) < 0.01:
            direction = "stable"
        elif slope > 0:
            direction = "increasing"
        else:
            direction = "decreasing"
        
        # Calculate confidence (R-squared)
        y_mean = sum_y / n
        ss_tot = sum((y - y_mean) ** 2 for y in values)
        y_pred = [slope * x_i + (sum_y - slope * sum_x) / n for x_i in x]
        ss_res = sum((y - y_p) ** 2 for y, y_p in zip(values, y_pred))
        
        confidence = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        return CostTrend(direction, percentage_change, max(0, confidence), confidence)
    
    async def _linear_trend_prediction(self, daily_costs: List[float]) -> Dict[str, Any]:
        """Linear trend prediction model"""
        
        x = list(range(len(daily_costs)))
        n = len(daily_costs)
        
        sum_x = sum(x)
        sum_y = sum(daily_costs)
        sum_xy = sum(x_i * y_i for x_i, y_i in zip(x, daily_costs))
        sum_x2 = sum(x_i * x_i for x_i in x)
        
        if (n * sum_x2 - sum_x * sum_x) == 0:
            return {"error": "Cannot calculate linear trend"}
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n
        
        # Predictions
        next_day = intercept + slope * n
        next_7_days = sum(intercept + slope * (n + i) for i in range(1, 8))
        
        # Calculate confidence based on R-squared
        y_mean = sum_y / n
        ss_tot = sum((y - y_mean) ** 2 for y in daily_costs)
        y_pred = [slope * x_i + intercept for x_i in x]
        ss_res = sum((y - y_p) ** 2 for y, y_p in zip(daily_costs, y_pred))
        
        confidence = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        return {
            "next_day": max(0, next_day),
            "next_7_days": max(0, next_7_days),
            "confidence": max(0, min(1, confidence)),
            "model_parameters": {"slope": slope, "intercept": intercept}
        }
    
    async def _seasonal_prediction(self, daily_costs: List[float]) -> Dict[str, Any]:
        """Seasonal prediction model (simplified)"""
        
        if len(daily_costs) < 7:
            return {"error": "Insufficient data for seasonal analysis"}
        
        # Simple weekly seasonality
        weekly_avg = statistics.mean(daily_costs[-7:])  # Last week average
        
        return {
            "next_day": weekly_avg,
            "next_7_days": weekly_avg * 7,
            "confidence": 0.7,  # Moderate confidence for seasonal
            "model_parameters": {"weekly_average": weekly_avg}
        }
    
    async def _exponential_smoothing(self, daily_costs: List[float]) -> Dict[str, Any]:
        """Exponential smoothing prediction"""
        
        alpha = 0.3  # Smoothing parameter
        
        # Calculate exponentially smoothed values
        smoothed = [daily_costs[0]]
        for i in range(1, len(daily_costs)):
            smoothed.append(alpha * daily_costs[i] + (1 - alpha) * smoothed[i-1])
        
        next_day = smoothed[-1]
        next_7_days = next_day * 7
        
        return {
            "next_day": max(0, next_day),
            "next_7_days": max(0, next_7_days),
            "confidence": 0.6,
            "model_parameters": {"alpha": alpha, "last_smoothed": smoothed[-1]}
        }
    
    # Additional helper methods would continue here...
    # (Implementing remaining methods for brevity)

# Global analytics service instance
cost_analytics_service = CostAnalyticsService()