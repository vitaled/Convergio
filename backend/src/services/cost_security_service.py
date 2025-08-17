"""
🔒 Cost Security and Anomaly Detection Service
Advanced security features for cost tracking and fraud prevention
"""

import asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import hashlib
import hmac
import secrets

import structlog
from sqlalchemy import and_, func, select, update, desc
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session, get_async_read_session
from models.cost_tracking import (
    CostAlert, CostSession, CostStatus, CostTracking,
    DailyCostSummary, Provider, ProviderPricing
)

logger = structlog.get_logger()


class SecurityLevel(str, Enum):
    """Security alert levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(str, Enum):
    """Types of cost anomalies"""
    UNUSUAL_SPIKE = "unusual_spike"
    RAPID_CONSUMPTION = "rapid_consumption"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    PROVIDER_ABUSE = "provider_abuse"
    TOKEN_EXPLOITATION = "token_exploitation"
    SESSION_ANOMALY = "session_anomaly"


class CostSecurityService:
    """Advanced cost security and anomaly detection"""
    
    def __init__(self):
        """Initialize cost security service"""
        self.anomaly_thresholds = {
            "cost_spike_multiplier": 5.0,  # Cost > 5x normal = anomaly
            "rapid_calls_threshold": 10,   # >10 calls per minute = suspicious
            "session_cost_limit": 100.0,   # >$100 per session = alert
            "hourly_cost_limit": 50.0,     # >$50 per hour = alert
            "token_efficiency_threshold": 0.001,  # <0.1% efficiency = suspicious
        }
        
        # Rate limiting settings
        self.rate_limits = {
            "default": {"calls_per_minute": 60, "cost_per_minute": 10.0},
            "high_volume": {"calls_per_minute": 100, "cost_per_minute": 20.0},
            "restricted": {"calls_per_minute": 10, "cost_per_minute": 2.0}
        }
        
        # Security patterns to detect
        self.security_patterns = {
            "cost_explosion": {"window_minutes": 5, "multiplier": 10},
            "token_farming": {"min_tokens": 1000, "max_cost_per_token": 0.00001},
            "provider_hopping": {"providers_in_window": 3, "window_minutes": 10}
        }
        
        self._security_cache = {}
        
        logger.info("🔒 Cost security service initialized")
    
    async def analyze_request_security(
        self,
        session_id: str,
        agent_id: Optional[str],
        provider: str,
        model: str,
        estimated_tokens: int,
        estimated_cost: float,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive security analysis before processing request
        """
        
        security_result = {
            "allowed": True,
            "security_level": SecurityLevel.LOW,
            "anomalies": [],
            "rate_limit_status": {},
            "risk_score": 0.0,
            "recommendations": []
        }
        
        try:
            # Rate limiting check
            rate_status = await self._check_rate_limits(session_id, agent_id, estimated_cost)
            security_result["rate_limit_status"] = rate_status
            
            if not rate_status["allowed"]:
                security_result["allowed"] = False
                security_result["security_level"] = SecurityLevel.HIGH
                security_result["anomalies"].append({
                    "type": AnomalyType.RAPID_CONSUMPTION,
                    "message": rate_status["reason"],
                    "severity": "high"
                })
            
            # Historical pattern analysis
            pattern_analysis = await self._analyze_historical_patterns(
                session_id, agent_id, provider, estimated_cost
            )
            security_result["risk_score"] += pattern_analysis["risk_score"]
            security_result["anomalies"].extend(pattern_analysis["anomalies"])
            
            # Cost spike detection
            spike_analysis = await self._detect_cost_spikes(
                session_id, agent_id, estimated_cost
            )
            security_result["risk_score"] += spike_analysis["risk_score"]
            security_result["anomalies"].extend(spike_analysis["anomalies"])
            
            # Token efficiency analysis
            efficiency_analysis = await self._analyze_token_efficiency(
                agent_id, estimated_tokens, estimated_cost
            )
            security_result["risk_score"] += efficiency_analysis["risk_score"]
            security_result["anomalies"].extend(efficiency_analysis["anomalies"])
            
            # Provider abuse detection
            abuse_analysis = await self._detect_provider_abuse(
                session_id, provider, estimated_cost
            )
            security_result["risk_score"] += abuse_analysis["risk_score"]
            security_result["anomalies"].extend(abuse_analysis["anomalies"])
            
            # Determine overall security level
            security_result["security_level"] = self._calculate_security_level(
                security_result["risk_score"]
            )
            
            # Generate recommendations
            security_result["recommendations"] = await self._generate_security_recommendations(
                security_result
            )
            
            # Block if high risk
            if security_result["risk_score"] > 80 or security_result["security_level"] == SecurityLevel.CRITICAL:
                security_result["allowed"] = False
            
            # Log security analysis
            logger.info("🔍 Security analysis completed",
                       session_id=session_id,
                       risk_score=security_result["risk_score"],
                       security_level=security_result["security_level"],
                       anomalies_detected=len(security_result["anomalies"]))
            
            return security_result
            
        except Exception as e:
            logger.error("❌ Security analysis failed", error=str(e))
            # Fail secure - block on error
            return {
                "allowed": False,
                "security_level": SecurityLevel.CRITICAL,
                "anomalies": [{"type": "security_check_failed", "message": str(e)}],
                "risk_score": 100.0,
                "error": str(e)
            }
    
    async def _check_rate_limits(
        self,
        session_id: str,
        agent_id: Optional[str],
        estimated_cost: float
    ) -> Dict[str, Any]:
        """Check rate limiting for session/agent"""
        
        current_time = datetime.utcnow()
        window_start = current_time - timedelta(minutes=1)
        
        async with get_async_read_session() as db:
            # Get recent calls for this session
            result = await db.execute(
                select(
                    func.count(CostTracking.id).label("call_count"),
                    func.sum(CostTracking.total_cost_usd).label("total_cost")
                )
                .where(
                    and_(
                        CostTracking.session_id == session_id,
                        CostTracking.created_at >= window_start
                    )
                )
            )
            
            session_stats = result.first()
            call_count = session_stats.call_count or 0
            total_cost = float(session_stats.total_cost or 0)
            
            # Determine rate limit tier (could be based on user subscription)
            rate_limit = self.rate_limits["default"]
            
            # Check limits
            calls_exceeded = call_count >= rate_limit["calls_per_minute"]
            cost_exceeded = (total_cost + estimated_cost) > rate_limit["cost_per_minute"]
            
            if calls_exceeded or cost_exceeded:
                return {
                    "allowed": False,
                    "reason": f"Rate limit exceeded: {call_count}/{rate_limit['calls_per_minute']} calls, ${total_cost:.2f}/${rate_limit['cost_per_minute']:.2f} cost",
                    "current_calls": call_count,
                    "current_cost": total_cost,
                    "limits": rate_limit,
                    "retry_after_seconds": 60
                }
            
            return {
                "allowed": True,
                "current_calls": call_count,
                "current_cost": total_cost,
                "remaining_calls": rate_limit["calls_per_minute"] - call_count,
                "remaining_cost": rate_limit["cost_per_minute"] - total_cost,
                "limits": rate_limit
            }
    
    async def _analyze_historical_patterns(
        self,
        session_id: str,
        agent_id: Optional[str],
        provider: str,
        estimated_cost: float
    ) -> Dict[str, Any]:
        """Analyze historical patterns for anomalies"""
        
        anomalies = []
        risk_score = 0.0
        
        async with get_async_read_session() as db:
            # Get historical data for comparison
            week_ago = datetime.utcnow() - timedelta(days=7)
            
            # Analyze session patterns
            session_result = await db.execute(
                select(
                    func.avg(CostTracking.total_cost_usd).label("avg_cost"),
                    func.stddev(CostTracking.total_cost_usd).label("stddev_cost"),
                    func.count(CostTracking.id).label("total_calls")
                )
                .where(
                    and_(
                        CostTracking.session_id == session_id,
                        CostTracking.created_at >= week_ago
                    )
                )
            )
            
            session_stats = session_result.first()
            
            if session_stats and session_stats.avg_cost:
                avg_cost = float(session_stats.avg_cost)
                stddev_cost = float(session_stats.stddev_cost or 0)
                
                # Check for cost spike
                if estimated_cost > avg_cost + (3 * stddev_cost) and estimated_cost > avg_cost * 5:
                    anomalies.append({
                        "type": AnomalyType.UNUSUAL_SPIKE,
                        "message": f"Cost spike detected: ${estimated_cost:.2f} vs avg ${avg_cost:.2f}",
                        "severity": "high",
                        "estimated_cost": estimated_cost,
                        "average_cost": avg_cost
                    })
                    risk_score += 30.0
            
            # Analyze agent patterns if agent_id provided
            if agent_id:
                agent_result = await db.execute(
                    select(
                        func.avg(CostTracking.total_cost_usd).label("avg_cost"),
                        func.count(func.distinct(CostTracking.provider)).label("provider_count")
                    )
                    .where(
                        and_(
                            CostTracking.agent_id == agent_id,
                            CostTracking.created_at >= week_ago
                        )
                    )
                )
                
                agent_stats = agent_result.first()
                
                if agent_stats and agent_stats.provider_count > 5:
                    anomalies.append({
                        "type": AnomalyType.PROVIDER_ABUSE,
                        "message": f"Agent using {agent_stats.provider_count} different providers",
                        "severity": "medium",
                        "provider_count": agent_stats.provider_count
                    })
                    risk_score += 15.0
        
        return {
            "anomalies": anomalies,
            "risk_score": risk_score
        }
    
    async def _detect_cost_spikes(
        self,
        session_id: str,
        agent_id: Optional[str],
        estimated_cost: float
    ) -> Dict[str, Any]:
        """Detect unusual cost spikes"""
        
        anomalies = []
        risk_score = 0.0
        
        # Check against absolute thresholds
        if estimated_cost > 10.0:  # $10 per call is unusual
            anomalies.append({
                "type": AnomalyType.UNUSUAL_SPIKE,
                "message": f"High-cost API call: ${estimated_cost:.2f}",
                "severity": "high",
                "estimated_cost": estimated_cost
            })
            risk_score += 40.0
        elif estimated_cost > 1.0:  # $1 per call is concerning
            anomalies.append({
                "type": AnomalyType.UNUSUAL_SPIKE,
                "message": f"Elevated-cost API call: ${estimated_cost:.2f}",
                "severity": "medium",
                "estimated_cost": estimated_cost
            })
            risk_score += 15.0
        
        return {
            "anomalies": anomalies,
            "risk_score": risk_score
        }
    
    async def _analyze_token_efficiency(
        self,
        agent_id: Optional[str],
        estimated_tokens: int,
        estimated_cost: float
    ) -> Dict[str, Any]:
        """Analyze token usage efficiency"""
        
        anomalies = []
        risk_score = 0.0
        
        if estimated_tokens > 0 and estimated_cost > 0:
            cost_per_token = estimated_cost / estimated_tokens
            
            # Extremely low cost per token might indicate abuse
            if cost_per_token < self.anomaly_thresholds["token_efficiency_threshold"]:
                anomalies.append({
                    "type": AnomalyType.TOKEN_EXPLOITATION,
                    "message": f"Suspicious token efficiency: ${cost_per_token:.6f} per token",
                    "severity": "medium",
                    "cost_per_token": cost_per_token,
                    "tokens": estimated_tokens
                })
                risk_score += 20.0
            
            # Very high token count for single call
            if estimated_tokens > 100000:  # 100k tokens
                anomalies.append({
                    "type": AnomalyType.TOKEN_EXPLOITATION,
                    "message": f"High token count: {estimated_tokens:,} tokens",
                    "severity": "high",
                    "tokens": estimated_tokens
                })
                risk_score += 25.0
        
        return {
            "anomalies": anomalies,
            "risk_score": risk_score
        }
    
    async def _detect_provider_abuse(
        self,
        session_id: str,
        provider: str,
        estimated_cost: float
    ) -> Dict[str, Any]:
        """Detect potential provider abuse patterns"""
        
        anomalies = []
        risk_score = 0.0
        
        async with get_async_read_session() as db:
            # Check for rapid provider switching
            recent_time = datetime.utcnow() - timedelta(minutes=10)
            
            result = await db.execute(
                select(func.count(func.distinct(CostTracking.provider)))
                .where(
                    and_(
                        CostTracking.session_id == session_id,
                        CostTracking.created_at >= recent_time
                    )
                )
            )
            
            provider_count = result.scalar() or 0
            
            if provider_count >= 3:  # Using 3+ providers in 10 minutes
                anomalies.append({
                    "type": AnomalyType.PROVIDER_ABUSE,
                    "message": f"Rapid provider switching: {provider_count} providers in 10 minutes",
                    "severity": "medium",
                    "provider_count": provider_count
                })
                risk_score += 20.0
        
        return {
            "anomalies": anomalies,
            "risk_score": risk_score
        }
    
    def _calculate_security_level(self, risk_score: float) -> SecurityLevel:
        """Calculate security level based on risk score"""
        
        if risk_score >= 80:
            return SecurityLevel.CRITICAL
        elif risk_score >= 50:
            return SecurityLevel.HIGH
        elif risk_score >= 25:
            return SecurityLevel.MEDIUM
        else:
            return SecurityLevel.LOW
    
    async def _generate_security_recommendations(
        self,
        security_result: Dict[str, Any]
    ) -> List[str]:
        """Generate security recommendations"""
        
        recommendations = []
        
        if security_result["risk_score"] > 50:
            recommendations.append("Consider implementing additional authentication")
            recommendations.append("Enable enhanced monitoring for this session")
        
        if any(a["type"] == AnomalyType.RAPID_CONSUMPTION for a in security_result["anomalies"]):
            recommendations.append("Implement exponential backoff")
            recommendations.append("Review rate limiting settings")
        
        if any(a["type"] == AnomalyType.UNUSUAL_SPIKE for a in security_result["anomalies"]):
            recommendations.append("Investigate usage patterns")
            recommendations.append("Consider cost caps for this session")
        
        if any(a["type"] == AnomalyType.PROVIDER_ABUSE for a in security_result["anomalies"]):
            recommendations.append("Monitor cross-provider usage")
            recommendations.append("Consider provider-specific limits")
        
        return recommendations
    
    async def generate_security_audit_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate comprehensive security audit report"""
        
        async with get_async_read_session() as db:
            # Get security-related alerts
            alerts_result = await db.execute(
                select(CostAlert)
                .where(
                    and_(
                        CostAlert.created_at >= start_date,
                        CostAlert.created_at <= end_date,
                        CostAlert.severity.in_(["warning", "critical"])
                    )
                )
                .order_by(desc(CostAlert.created_at))
                .limit(100)
            )
            alerts = alerts_result.scalars().all()
            
            # Analyze high-cost sessions
            high_cost_sessions = await db.execute(
                select(CostSession)
                .where(
                    and_(
                        CostSession.started_at >= start_date,
                        CostSession.started_at <= end_date,
                        CostSession.total_cost_usd > 50.0
                    )
                )
                .order_by(desc(CostSession.total_cost_usd))
                .limit(20)
            )
            expensive_sessions = high_cost_sessions.scalars().all()
            
            # Analyze provider usage patterns
            provider_analysis = await db.execute(
                select(
                    CostTracking.provider,
                    func.sum(CostTracking.total_cost_usd).label("total_cost"),
                    func.count(CostTracking.id).label("call_count"),
                    func.avg(CostTracking.total_cost_usd).label("avg_cost"),
                    func.max(CostTracking.total_cost_usd).label("max_cost")
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
            provider_stats = provider_analysis.all()
            
            # Security metrics
            total_cost = sum(float(session.total_cost_usd) for session in expensive_sessions)
            critical_alerts = [a for a in alerts if a.severity == "critical"]
            
            return {
                "audit_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "duration_days": (end_date - start_date).days
                },
                "security_summary": {
                    "total_alerts": len(alerts),
                    "critical_alerts": len(critical_alerts),
                    "expensive_sessions": len(expensive_sessions),
                    "total_high_cost": total_cost,
                    "security_incidents": len([a for a in alerts if "security" in a.alert_type.lower()])
                },
                "alerts": [
                    {
                        "id": alert.id,
                        "type": alert.alert_type,
                        "severity": alert.severity,
                        "message": alert.message,
                        "timestamp": alert.created_at.isoformat(),
                        "is_resolved": alert.is_resolved
                    }
                    for alert in alerts[:10]  # Top 10 recent alerts
                ],
                "expensive_sessions": [
                    {
                        "session_id": session.session_id,
                        "total_cost": float(session.total_cost_usd),
                        "interactions": session.total_interactions,
                        "started_at": session.started_at.isoformat(),
                        "status": session.status,
                        "cost_per_interaction": float(session.total_cost_usd) / session.total_interactions if session.total_interactions > 0 else 0
                    }
                    for session in expensive_sessions[:10]
                ],
                "provider_analysis": [
                    {
                        "provider": stat.provider,
                        "total_cost": float(stat.total_cost),
                        "call_count": stat.call_count,
                        "avg_cost": float(stat.avg_cost),
                        "max_cost": float(stat.max_cost),
                        "cost_per_call": float(stat.total_cost) / stat.call_count if stat.call_count > 0 else 0
                    }
                    for stat in provider_stats
                ],
                "security_recommendations": await self._generate_audit_recommendations(alerts, expensive_sessions),
                "generated_at": datetime.utcnow().isoformat()
            }
    
    async def _generate_audit_recommendations(
        self,
        alerts: List[Any],
        expensive_sessions: List[Any]
    ) -> List[str]:
        """Generate audit-specific recommendations"""
        
        recommendations = []
        
        if len(alerts) > 10:
            recommendations.append("High alert volume detected - review alert thresholds")
        
        if any(alert.severity == "critical" for alert in alerts):
            recommendations.append("Critical security alerts require immediate investigation")
        
        if len(expensive_sessions) > 5:
            recommendations.append("Multiple high-cost sessions detected - implement stricter limits")
        
        if any(float(session.total_cost_usd) > 100 for session in expensive_sessions):
            recommendations.append("Sessions exceeding $100 require manual approval")
        
        recommendations.extend([
            "Implement real-time anomaly detection",
            "Enable automatic cost capping",
            "Add multi-factor authentication for high-cost operations",
            "Set up automated security monitoring"
        ])
        
        return recommendations


# Global security service instance
cost_security_service = CostSecurityService()