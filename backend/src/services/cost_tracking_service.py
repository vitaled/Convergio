"""
💰 Enhanced Cost Tracking Service with Database Integration
Real-time cost tracking for all AI providers with persistent storage
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import structlog
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from agents.services.redis_state_manager import RedisStateManager
from core.database import get_async_session, get_async_read_session
from models.cost_tracking import (
    CostAlert, CostSession, CostStatus, CostTracking,
    DailyCostSummary, Provider, ProviderPricing
)

logger = structlog.get_logger()


class EnhancedCostTracker:
    """Enhanced cost tracking with database persistence and real-time updates"""
    
    def __init__(self, state_manager: Optional[RedisStateManager] = None):
        """Initialize enhanced cost tracker"""
        self.state_manager = state_manager
        self.cost_limit_usd = 50.0  # Default daily limit
        self._pricing_cache = {}  # Cache for pricing data
        self._session_cache = {}  # Cache for active sessions
        
    async def track_api_call(
        self,
        session_id: str,
        conversation_id: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        turn_id: Optional[str] = None,
        request_type: str = "chat",
        response_time_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track a single API call with full cost calculation and persistence
        """
        try:
            # Get current pricing
            pricing = await self._get_model_pricing(provider, model)
            
            # Calculate costs
            input_cost = Decimal(str(input_tokens / 1000.0)) * pricing["input_price"]
            output_cost = Decimal(str(output_tokens / 1000.0)) * pricing["output_price"]
            total_cost = input_cost + output_cost
            
            # Add per-request cost if applicable (e.g., Perplexity search)
            if pricing.get("price_per_request"):
                total_cost += pricing["price_per_request"]
            
            async with get_async_session() as db:
                # Create cost tracking record
                cost_record = CostTracking(
                    session_id=session_id,
                    conversation_id=conversation_id,
                    turn_id=turn_id,
                    agent_id=agent_id,
                    agent_name=agent_name,
                    provider=provider,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=input_tokens + output_tokens,
                    input_cost_usd=input_cost,
                    output_cost_usd=output_cost,
                    total_cost_usd=total_cost,
                    request_type=request_type,
                    response_time_ms=response_time_ms,
                    request_metadata=metadata or {}
                )
                
                db.add(cost_record)
                await db.commit()
                
                # Update session totals
                await self._update_session_totals(
                    db, session_id, provider, model, agent_id,
                    total_cost, input_tokens + output_tokens
                )
                
                # Update daily summary
                await self._update_daily_summary(
                    db, provider, model, agent_id,
                    total_cost, input_tokens + output_tokens
                )
                
                # Check for alerts
                alerts = await self._check_cost_alerts(
                    db, session_id, agent_id, total_cost
                )
                
                # Store in Redis for real-time access
                if self.state_manager:
                    await self._update_redis_cache(
                        session_id, conversation_id, total_cost, 
                        input_tokens + output_tokens
                    )
                
                logger.info(
                    "💰 API call tracked",
                    session_id=session_id,
                    provider=provider,
                    model=model,
                    cost_usd=float(total_cost),
                    tokens=input_tokens + output_tokens
                )
                
                return {
                    "success": True,
                    "cost_breakdown": {
                        "input_cost_usd": float(input_cost),
                        "output_cost_usd": float(output_cost),
                        "total_cost_usd": float(total_cost),
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": input_tokens + output_tokens
                    },
                    "session_total": await self._get_session_total(db, session_id),
                    "daily_total": await self._get_daily_total(db),
                    "alerts": alerts
                }
                
        except Exception as e:
            logger.error("Failed to track API call", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_model_pricing(self, provider: str, model: str) -> Dict[str, Decimal]:
        """Get current pricing for a model from database"""
        
        cache_key = f"{provider}:{model}"
        
        # Check cache first
        if cache_key in self._pricing_cache:
            cached = self._pricing_cache[cache_key]
            if cached["expires"] > datetime.utcnow():
                return cached["pricing"]
        
        async with get_async_read_session() as db:
            result = await db.execute(
                select(ProviderPricing)
                .where(
                    and_(
                        ProviderPricing.provider == provider,
                        ProviderPricing.model == model,
                        ProviderPricing.is_active == True,
                        ProviderPricing.effective_from <= func.now(),
                        func.coalesce(ProviderPricing.effective_to > func.now(), True)
                    )
                )
                .order_by(ProviderPricing.effective_from.desc())
                .limit(1)
            )
            
            pricing_record = result.scalar_one_or_none()
            
            if pricing_record:
                pricing = {
                    "input_price": pricing_record.input_price_per_1k,
                    "output_price": pricing_record.output_price_per_1k,
                    "price_per_request": pricing_record.price_per_request
                }
            else:
                # Fallback pricing if not found
                logger.warning(f"Pricing not found for {provider}:{model}, using defaults")
                pricing = {
                    "input_price": Decimal("0.001"),
                    "output_price": Decimal("0.002"),
                    "price_per_request": None
                }
            
            # Cache for 1 hour
            self._pricing_cache[cache_key] = {
                "pricing": pricing,
                "expires": datetime.utcnow() + timedelta(hours=1)
            }
            
            return pricing
    
    async def _update_session_totals(
        self,
        db: AsyncSession,
        session_id: str,
        provider: str,
        model: str,
        agent_id: Optional[str],
        cost: Decimal,
        tokens: int
    ):
        """Update or create session totals"""
        
        result = await db.execute(
            select(CostSession).where(CostSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if session:
            # Update existing session
            session.total_cost_usd += cost
            session.total_tokens += tokens
            session.total_interactions += 1
            
            # Update provider breakdown
            provider_breakdown = session.provider_breakdown or {}
            provider_breakdown[provider] = float(
                Decimal(str(provider_breakdown.get(provider, 0))) + cost
            )
            session.provider_breakdown = provider_breakdown
            
            # Update model breakdown
            model_breakdown = session.model_breakdown or {}
            model_breakdown[model] = float(
                Decimal(str(model_breakdown.get(model, 0))) + cost
            )
            session.model_breakdown = model_breakdown
            
            # Update agent breakdown
            if agent_id:
                agent_breakdown = session.agent_breakdown or {}
                agent_breakdown[agent_id] = float(
                    Decimal(str(agent_breakdown.get(agent_id, 0))) + cost
                )
                session.agent_breakdown = agent_breakdown
            
            # Update status
            session.status = self._calculate_status(float(session.total_cost_usd))
            
        else:
            # Create new session
            session = CostSession(
                session_id=session_id,
                total_cost_usd=cost,
                total_tokens=tokens,
                total_interactions=1,
                provider_breakdown={provider: float(cost)},
                model_breakdown={model: float(cost)},
                agent_breakdown={agent_id: float(cost)} if agent_id else {},
                status=CostStatus.HEALTHY.value
            )
            db.add(session)
        
        await db.commit()
    
    async def _update_daily_summary(
        self,
        db: AsyncSession,
        provider: str,
        model: str,
        agent_id: Optional[str],
        cost: Decimal,
        tokens: int
    ):
        """Update or create daily summary"""
        
        today = datetime.utcnow().date()
        
        result = await db.execute(
            select(DailyCostSummary).where(
                func.date(DailyCostSummary.date) == today
            )
        )
        summary = result.scalar_one_or_none()
        
        if summary:
            # Update existing summary
            summary.total_cost_usd += cost
            summary.total_tokens += tokens
            summary.total_interactions += 1
            
            # Update provider costs
            if provider == "openai":
                summary.openai_cost_usd += cost
            elif provider == "anthropic":
                summary.anthropic_cost_usd += cost
            elif provider == "perplexity":
                summary.perplexity_cost_usd += cost
            else:
                summary.other_cost_usd += cost
            
            # Update breakdowns
            provider_breakdown = summary.provider_breakdown or {}
            provider_breakdown[provider] = float(
                Decimal(str(provider_breakdown.get(provider, 0))) + cost
            )
            summary.provider_breakdown = provider_breakdown
            
            model_breakdown = summary.model_breakdown or {}
            model_breakdown[model] = float(
                Decimal(str(model_breakdown.get(model, 0))) + cost
            )
            summary.model_breakdown = model_breakdown
            
            if agent_id:
                agent_breakdown = summary.agent_breakdown or {}
                agent_breakdown[agent_id] = float(
                    Decimal(str(agent_breakdown.get(agent_id, 0))) + cost
                )
                summary.agent_breakdown = agent_breakdown
            
            # Update hourly breakdown
            hour = datetime.utcnow().hour
            hourly_breakdown = summary.hourly_breakdown or {}
            hourly_breakdown[str(hour)] = float(
                Decimal(str(hourly_breakdown.get(str(hour), 0))) + cost
            )
            summary.hourly_breakdown = hourly_breakdown
            
            # Update statistics
            summary.avg_cost_per_interaction = summary.total_cost_usd / summary.total_interactions
            summary.avg_tokens_per_interaction = summary.total_tokens / summary.total_interactions
            
            # Check peak hour
            if cost > summary.peak_hour_cost:
                summary.peak_hour_cost = cost
                summary.peak_hour = hour
            
            # Update budget utilization
            summary.budget_utilization_percent = float(
                (summary.total_cost_usd / summary.daily_budget_usd) * 100
            )
            summary.status = self._calculate_status(float(summary.total_cost_usd))
            
        else:
            # Create new daily summary
            hour = datetime.utcnow().hour
            summary = DailyCostSummary(
                date=datetime.utcnow(),
                total_cost_usd=cost,
                total_tokens=tokens,
                total_interactions=1,
                total_sessions=1,
                openai_cost_usd=cost if provider == "openai" else Decimal("0"),
                anthropic_cost_usd=cost if provider == "anthropic" else Decimal("0"),
                perplexity_cost_usd=cost if provider == "perplexity" else Decimal("0"),
                other_cost_usd=cost if provider not in ["openai", "anthropic", "perplexity"] else Decimal("0"),
                provider_breakdown={provider: float(cost)},
                model_breakdown={model: float(cost)},
                agent_breakdown={agent_id: float(cost)} if agent_id else {},
                hourly_breakdown={str(hour): float(cost)},
                avg_cost_per_interaction=cost,
                avg_tokens_per_interaction=float(tokens),
                peak_hour_cost=cost,
                peak_hour=hour,
                budget_utilization_percent=float((cost / Decimal("50.0")) * 100),
                status=CostStatus.HEALTHY.value
            )
            db.add(summary)
        
        await db.commit()
    
    async def _check_cost_alerts(
        self,
        db: AsyncSession,
        session_id: str,
        agent_id: Optional[str],
        cost: Decimal
    ) -> List[Dict[str, Any]]:
        """Check for cost alerts and create if necessary"""
        
        alerts = []
        
        # Get daily total
        daily_total = await self._get_daily_total(db)
        
        # Check daily limit
        if daily_total > self.cost_limit_usd * 0.8:
            severity = "critical" if daily_total > self.cost_limit_usd else "warning"
            
            alert = CostAlert(
                alert_type="daily_limit",
                severity=severity,
                session_id=session_id,
                agent_id=agent_id,
                current_value=Decimal(str(daily_total)),
                threshold_value=Decimal(str(self.cost_limit_usd)),
                message=f"Daily cost at {daily_total:.2f} USD ({(daily_total/self.cost_limit_usd)*100:.1f}% of limit)"
            )
            db.add(alert)
            
            alerts.append({
                "type": "daily_limit",
                "severity": severity,
                "message": alert.message,
                "current": float(daily_total),
                "threshold": self.cost_limit_usd
            })
        
        # Check for cost spike (single call > $1)
        if cost > 1.0:
            alert = CostAlert(
                alert_type="cost_spike",
                severity="warning",
                session_id=session_id,
                agent_id=agent_id,
                current_value=cost,
                threshold_value=Decimal("1.0"),
                message=f"High cost API call: ${cost:.4f} USD"
            )
            db.add(alert)
            
            alerts.append({
                "type": "cost_spike",
                "severity": "warning",
                "message": alert.message,
                "current": float(cost),
                "threshold": 1.0
            })
        
        if alerts:
            await db.commit()
        
        return alerts
    
    async def _get_session_total(self, db: AsyncSession, session_id: str) -> float:
        """Get total cost for a session"""
        
        result = await db.execute(
            select(CostSession.total_cost_usd)
            .where(CostSession.session_id == session_id)
        )
        total = result.scalar_one_or_none()
        return float(total) if total else 0.0
    
    async def _get_daily_total(self, db: AsyncSession) -> float:
        """Get total cost for today"""
        
        today = datetime.utcnow().date()
        result = await db.execute(
            select(DailyCostSummary.total_cost_usd)
            .where(func.date(DailyCostSummary.date) == today)
        )
        total = result.scalar_one_or_none()
        return float(total) if total else 0.0
    
    async def _update_redis_cache(
        self,
        session_id: str,
        conversation_id: str,
        cost: Decimal,
        tokens: int
    ):
        """Update Redis cache for real-time access"""
        
        if not self.state_manager:
            return
        
        try:
            # Update session cache
            session_key = f"cost:session:{session_id}"
            session_data = await self.state_manager.redis_client.get(session_key)
            
            if session_data:
                data = json.loads(session_data)
                data["total_cost"] = float(Decimal(str(data.get("total_cost", 0))) + cost)
                data["total_tokens"] = data.get("total_tokens", 0) + tokens
                data["last_updated"] = datetime.utcnow().isoformat()
            else:
                data = {
                    "session_id": session_id,
                    "total_cost": float(cost),
                    "total_tokens": tokens,
                    "started_at": datetime.utcnow().isoformat(),
                    "last_updated": datetime.utcnow().isoformat()
                }
            
            await self.state_manager.redis_client.setex(
                session_key,
                3600,  # 1 hour TTL
                json.dumps(data)
            )
            
            # Update daily total cache
            daily_key = f"cost:daily:{datetime.utcnow().strftime('%Y-%m-%d')}"
            daily_data = await self.state_manager.redis_client.get(daily_key)
            
            if daily_data:
                daily_total = float(Decimal(daily_data.decode()) + cost)
            else:
                daily_total = float(cost)
            
            await self.state_manager.redis_client.setex(
                daily_key,
                86400,  # 24 hours TTL
                str(daily_total)
            )
            
        except Exception as e:
            logger.warning("Failed to update Redis cache", error=str(e))
    
    def _calculate_status(self, cost: float) -> str:
        """Calculate status based on cost"""
        
        percentage = (cost / self.cost_limit_usd) * 100
        
        if percentage >= 100:
            return CostStatus.EXCEEDED.value
        elif percentage >= 80:
            return CostStatus.WARNING.value
        elif percentage >= 50:
            return CostStatus.MODERATE.value
        else:
            return CostStatus.HEALTHY.value
    
    async def get_realtime_overview(self) -> Dict[str, Any]:
        """Get real-time cost overview for display"""
        
        try:
            async with get_async_read_session() as db:
                # Get today's summary
                today = datetime.utcnow().date()
                result = await db.execute(
                    select(DailyCostSummary)
                    .where(func.date(DailyCostSummary.date) == today)
                )
                today_summary = result.scalar_one_or_none()
                
                # Get total across all days
                total_result = await db.execute(
                    select(func.sum(DailyCostSummary.total_cost_usd))
                )
                total_all_time = total_result.scalar() or Decimal("0")
                
                # Get active sessions count
                sessions_result = await db.execute(
                    select(func.count(CostSession.id))
                    .where(CostSession.ended_at.is_(None))
                )
                active_sessions = sessions_result.scalar() or 0
                
                if today_summary:
                    return {
                        "total_cost_usd": float(total_all_time),
                        "today_cost_usd": float(today_summary.total_cost_usd),
                        "total_interactions": today_summary.total_interactions,
                        "total_tokens": today_summary.total_tokens,
                        "active_sessions": active_sessions,
                        "status": today_summary.status,
                        "budget_utilization": today_summary.budget_utilization_percent,
                        "provider_breakdown": today_summary.provider_breakdown,
                        "model_breakdown": today_summary.model_breakdown,
                        "hourly_breakdown": today_summary.hourly_breakdown,
                        "last_updated": datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        "total_cost_usd": float(total_all_time),
                        "today_cost_usd": 0.0,
                        "total_interactions": 0,
                        "total_tokens": 0,
                        "active_sessions": active_sessions,
                        "status": "healthy",
                        "budget_utilization": 0.0,
                        "provider_breakdown": {},
                        "model_breakdown": {},
                        "hourly_breakdown": {},
                        "last_updated": datetime.utcnow().isoformat()
                    }
                    
        except Exception as e:
            logger.error("Failed to get realtime overview", error=str(e))
            return {
                "total_cost_usd": 0.0,
                "today_cost_usd": 0.0,
                "total_interactions": 0,
                "total_tokens": 0,
                "active_sessions": 0,
                "status": "error",
                "error": str(e),
                "last_updated": datetime.utcnow().isoformat()
            }
    
    async def get_session_details(self, session_id: str) -> Dict[str, Any]:
        """Get detailed cost breakdown for a session"""
        
        try:
            async with get_async_read_session() as db:
                # Get session summary
                session_result = await db.execute(
                    select(CostSession)
                    .where(CostSession.session_id == session_id)
                )
                session = session_result.scalar_one_or_none()
                
                if not session:
                    return {"error": "Session not found"}
                
                # Get individual API calls
                calls_result = await db.execute(
                    select(CostTracking)
                    .where(CostTracking.session_id == session_id)
                    .order_by(CostTracking.created_at.desc())
                    .limit(100)
                )
                calls = calls_result.scalars().all()
                
                return {
                    "session_id": session.session_id,
                    "total_cost_usd": float(session.total_cost_usd),
                    "total_tokens": session.total_tokens,
                    "total_interactions": session.total_interactions,
                    "status": session.status,
                    "started_at": session.started_at.isoformat(),
                    "provider_breakdown": session.provider_breakdown,
                    "model_breakdown": session.model_breakdown,
                    "agent_breakdown": session.agent_breakdown,
                    "api_calls": [
                        {
                            "conversation_id": call.conversation_id,
                            "agent": call.agent_name or call.agent_id,
                            "provider": call.provider,
                            "model": call.model,
                            "cost_usd": float(call.total_cost_usd),
                            "tokens": call.total_tokens,
                            "timestamp": call.created_at.isoformat()
                        }
                        for call in calls
                    ]
                }
                
        except Exception as e:
            logger.error("Failed to get session details", error=str(e))
            return {"error": str(e)}
    
    async def get_agent_costs(self, agent_id: str, days: int = 7) -> Dict[str, Any]:
        """Get cost breakdown for a specific agent"""
        
        try:
            async with get_async_read_session() as db:
                start_date = datetime.utcnow() - timedelta(days=days)
                
                result = await db.execute(
                    select(
                        func.sum(CostTracking.total_cost_usd).label("total_cost"),
                        func.sum(CostTracking.total_tokens).label("total_tokens"),
                        func.count(CostTracking.id).label("total_calls"),
                        func.avg(CostTracking.total_cost_usd).label("avg_cost"),
                        CostTracking.provider,
                        CostTracking.model
                    )
                    .where(
                        and_(
                            CostTracking.agent_id == agent_id,
                            CostTracking.created_at >= start_date
                        )
                    )
                    .group_by(CostTracking.provider, CostTracking.model)
                )
                
                breakdown = []
                total_cost = Decimal("0")
                total_tokens = 0
                total_calls = 0
                
                for row in result.all():
                    breakdown.append({
                        "provider": row.provider,
                        "model": row.model,
                        "total_cost": float(row.total_cost or 0),
                        "total_tokens": row.total_tokens or 0,
                        "total_calls": row.total_calls or 0,
                        "avg_cost": float(row.avg_cost or 0)
                    })
                    total_cost += row.total_cost or Decimal("0")
                    total_tokens += row.total_tokens or 0
                    total_calls += row.total_calls or 0
                
                return {
                    "agent_id": agent_id,
                    "period_days": days,
                    "total_cost_usd": float(total_cost),
                    "total_tokens": total_tokens,
                    "total_calls": total_calls,
                    "avg_cost_per_call": float(total_cost / total_calls) if total_calls > 0 else 0,
                    "model_breakdown": breakdown
                }
                
        except Exception as e:
            logger.error("Failed to get agent costs", error=str(e))
            return {"error": str(e)}