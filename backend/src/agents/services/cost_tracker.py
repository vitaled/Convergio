"""
CONVERGIO 2029 - COST TRACKER
Tracking costi OpenAI integrato con AutoGen
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog

from .redis_state_manager import RedisStateManager

logger = structlog.get_logger()

# OpenAI pricing per 1K tokens (as of 2025)
OPENAI_PRICING = {
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "text-embedding-3-small": {"input": 0.00002, "output": 0.0},
    "text-embedding-3-large": {"input": 0.00013, "output": 0.0},
}

# Anthropic pricing per 1K tokens
ANTHROPIC_PRICING = {
    "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
    "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
    "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
}


class CostTracker:
    """Cost tracking service for AI model usage."""
    
    def __init__(self, state_manager: RedisStateManager):
        """Initialize cost tracker."""
        self.state_manager = state_manager
        self.cost_limit_usd = 50.0  # Default daily limit
        
    def set_cost_limit(self, limit_usd: float) -> None:
        """Set daily cost limit."""
        self.cost_limit_usd = limit_usd
        logger.info("Cost limit updated", limit_usd=limit_usd)
    
    async def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        provider: str = "openai"
    ) -> Dict[str, Any]:
        """Calculate cost for token usage."""
        try:
            pricing_table = OPENAI_PRICING if provider == "openai" else ANTHROPIC_PRICING
            
            if model not in pricing_table:
                logger.warning("Unknown model for cost calculation", model=model, provider=provider)
                # Use default pricing for unknown models
                input_cost_per_1k = 0.001
                output_cost_per_1k = 0.002
            else:
                pricing = pricing_table[model]
                input_cost_per_1k = pricing["input"]
                output_cost_per_1k = pricing["output"]
            
            # Calculate costs
            input_cost = (input_tokens / 1000) * input_cost_per_1k
            output_cost = (output_tokens / 1000) * output_cost_per_1k
            total_cost = input_cost + output_cost
            
            cost_breakdown = {
                "model": model,
                "provider": provider,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "input_cost_usd": round(input_cost, 6),
                "output_cost_usd": round(output_cost, 6),
                "total_cost_usd": round(total_cost, 6),
                "pricing": {
                    "input_per_1k": input_cost_per_1k,
                    "output_per_1k": output_cost_per_1k
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.debug(
                "Cost calculated",
                model=model,
                total_tokens=input_tokens + output_tokens,
                total_cost_usd=total_cost
            )
            
            return cost_breakdown
            
        except Exception as e:
            logger.error("Failed to calculate cost", error=str(e), model=model)
            return {
                "model": model,
                "provider": provider,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "input_cost_usd": 0.0,
                "output_cost_usd": 0.0,
                "total_cost_usd": 0.0,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def track_conversation_cost(
        self,
        conversation_id: str,
        cost_breakdown: Dict[str, Any]
    ) -> None:
        """Track cost for a specific conversation."""
        try:
            # Store cost in Redis via state manager
            await self.state_manager.track_cost(
                conversation_id=conversation_id,
                model=cost_breakdown["model"],
                tokens_used=cost_breakdown["total_tokens"],
                cost_usd=cost_breakdown["total_cost_usd"]
            )
            
            # Check if we're approaching daily limit
            daily_summary = await self.state_manager.get_daily_cost_summary()
            daily_cost = daily_summary["total_cost_usd"]
            
            if daily_cost > self.cost_limit_usd * 0.8:  # 80% of limit
                logger.warning(
                    "Approaching daily cost limit",
                    daily_cost_usd=daily_cost,
                    limit_usd=self.cost_limit_usd,
                    percentage=round((daily_cost / self.cost_limit_usd) * 100, 1)
                )
            
            if daily_cost > self.cost_limit_usd:
                logger.error(
                    "Daily cost limit exceeded",
                    daily_cost_usd=daily_cost,
                    limit_usd=self.cost_limit_usd
                )
                # Note: In production, you might want to disable or throttle the service
            
        except Exception as e:
            logger.error("Failed to track conversation cost", error=str(e))
    
    async def get_conversation_costs(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all costs for a conversation."""
        try:
            # Get conversation to extract cost data from messages
            conversation = await self.state_manager.get_conversation(conversation_id)
            if not conversation:
                return []
            
            costs = []
            for message in conversation.get("messages", []):
                if message.get("role") == "assistant" and "cost_breakdown" in message.get("metadata", {}):
                    costs.append(message["metadata"]["cost_breakdown"])
            
            return costs
            
        except Exception as e:
            logger.error("Failed to get conversation costs", error=str(e))
            return []
    
    async def get_daily_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get daily cost summary."""
        try:
            summary = await self.state_manager.get_daily_cost_summary(date)
            
            # Add additional metrics
            summary.update({
                "daily_limit_usd": self.cost_limit_usd,
                "limit_usage_percentage": round(
                    (summary["total_cost_usd"] / self.cost_limit_usd) * 100, 1
                ) if self.cost_limit_usd > 0 else 0,
                "remaining_budget_usd": max(0, self.cost_limit_usd - summary["total_cost_usd"]),
                "status": self._get_budget_status(summary["total_cost_usd"])
            })
            
            return summary
            
        except Exception as e:
            logger.error("Failed to get daily summary", error=str(e))
            return {
                "date": date or datetime.utcnow().strftime("%Y-%m-%d"),
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "error": str(e)
            }
    
    async def get_weekly_summary(self) -> Dict[str, Any]:
        """Get weekly cost summary."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)
            
            daily_summaries = []
            total_cost = 0.0
            total_tokens = 0
            
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                daily_summary = await self.get_daily_summary(date_str)
                daily_summaries.append(daily_summary)
                total_cost += daily_summary["total_cost_usd"]
                total_tokens += daily_summary["total_tokens"]
                current_date += timedelta(days=1)
            
            weekly_limit = self.cost_limit_usd * 7
            
            return {
                "period": {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")
                },
                "total_cost_usd": round(total_cost, 2),
                "total_tokens": total_tokens,
                "weekly_limit_usd": weekly_limit,
                "average_daily_cost_usd": round(total_cost / 7, 2),
                "daily_summaries": daily_summaries,
                "status": self._get_budget_status(total_cost, weekly_limit)
            }
            
        except Exception as e:
            logger.error("Failed to get weekly summary", error=str(e))
            return {"error": str(e)}
    
    async def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive cost summary."""
        try:
            daily = await self.get_daily_summary()
            weekly = await self.get_weekly_summary()
            
            return {
                "daily": daily,
                "weekly": weekly,
                "pricing_tables": {
                    "openai": OPENAI_PRICING,
                    "anthropic": ANTHROPIC_PRICING
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to get cost summary", error=str(e))
            return {"error": str(e)}
    
    def _get_budget_status(self, current_cost: float, limit: Optional[float] = None) -> str:
        """Get budget status based on current cost."""
        if limit is None:
            limit = self.cost_limit_usd
        
        if limit <= 0:
            return "no_limit"
        
        percentage = (current_cost / limit) * 100
        
        if percentage >= 100:
            return "exceeded"
        elif percentage >= 80:
            return "warning"
        elif percentage >= 50:
            return "moderate"
        else:
            return "healthy"
    
    async def check_budget_limits(self, conversation_id: str) -> Dict[str, Any]:
        """Check if conversation can proceed based on budget limits."""
        try:
            daily_summary = await self.get_daily_summary()
            
            can_proceed = daily_summary["total_cost_usd"] < self.cost_limit_usd
            
            return {
                "can_proceed": can_proceed,
                "current_cost_usd": daily_summary["total_cost_usd"],
                "daily_limit_usd": self.cost_limit_usd,
                "remaining_budget_usd": daily_summary["remaining_budget_usd"],
                "status": daily_summary["status"],
                "reason": "Daily budget limit exceeded" if not can_proceed else "Budget OK"
            }
            
        except Exception as e:
            logger.error("Failed to check budget limits", error=str(e))
            return {
                "can_proceed": True,  # Default to allowing if check fails
                "error": str(e)
            }
    
    async def track_turn_cost(
        self,
        conversation_id: str,
        turn_id: str,
        agent_name: str,
        cost_breakdown: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track cost for individual conversation turn with detailed analytics.
        This is the per-turn callback system for WS7 implementation.
        """
        try:
            turn_cost_data = {
                "conversation_id": conversation_id,
                "turn_id": turn_id,
                "agent_name": agent_name,
                "timestamp": datetime.utcnow().isoformat(),
                "cost_breakdown": cost_breakdown,
                "context": context or {},
                "cumulative_conversation_cost": 0.0,
                "turn_sequence": await self._get_turn_sequence(conversation_id),
                "efficiency_metrics": await self._calculate_turn_efficiency(cost_breakdown, context)
            }
            
            # Store turn-level cost data
            await self._store_turn_cost(turn_cost_data)
            
            # Update conversation-level cumulative costs
            cumulative_cost = await self._update_conversation_cumulative_cost(
                conversation_id, cost_breakdown["total_cost_usd"]
            )
            turn_cost_data["cumulative_conversation_cost"] = cumulative_cost
            
            # Check for budget breach at turn level
            budget_status = await self._check_turn_budget_breach(
                conversation_id, cumulative_cost, turn_cost_data
            )
            
            # Log detailed turn cost information
            logger.info(
                "💰 Turn cost tracked",
                conversation_id=conversation_id,
                turn_id=turn_id,
                agent=agent_name,
                turn_cost_usd=cost_breakdown["total_cost_usd"],
                cumulative_cost_usd=cumulative_cost,
                tokens_used=cost_breakdown["total_tokens"],
                model=cost_breakdown["model"],
                budget_status=budget_status["status"]
            )
            
            # Return comprehensive turn analytics
            return {
                "turn_data": turn_cost_data,
                "budget_status": budget_status,
                "analytics": await self._generate_turn_analytics(conversation_id, turn_cost_data),
                "recommendations": await self._generate_cost_recommendations(turn_cost_data, budget_status)
            }
            
        except Exception as e:
            logger.error(
                "Failed to track turn cost",
                error=str(e),
                conversation_id=conversation_id,
                turn_id=turn_id,
                agent_name=agent_name
            )
            return {
                "error": str(e),
                "turn_data": None,
                "budget_status": {"status": "error", "message": str(e)}
            }
    
    async def _get_turn_sequence(self, conversation_id: str) -> int:
        """Get the sequence number for this turn in the conversation."""
        try:
            conversation_data = await self.state_manager.get_conversation(conversation_id)
            if conversation_data and "messages" in conversation_data:
                return len(conversation_data["messages"]) + 1
            return 1
        except Exception:
            return 1
    
    async def _calculate_turn_efficiency(
        self, cost_breakdown: Dict[str, Any], context: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate efficiency metrics for this turn."""
        try:
            total_tokens = cost_breakdown["total_tokens"]
            total_cost = cost_breakdown["total_cost_usd"]
            
            # Calculate cost per token
            cost_per_token = total_cost / max(1, total_tokens)
            
            # Calculate output/input token ratio (higher is generally better)
            input_tokens = cost_breakdown["input_tokens"]
            output_tokens = cost_breakdown["output_tokens"]
            output_ratio = output_tokens / max(1, input_tokens)
            
            # Estimate content efficiency (characters per dollar)
            estimated_chars = output_tokens * 4  # Rough estimate: 4 chars per token
            chars_per_dollar = estimated_chars / max(0.001, total_cost)
            
            # Calculate model efficiency score (0.0-1.0)
            model = cost_breakdown["model"]
            model_efficiency = self._get_model_efficiency_score(model)
            
            return {
                "cost_per_token": round(cost_per_token, 6),
                "output_input_ratio": round(output_ratio, 3),
                "chars_per_dollar": round(chars_per_dollar, 2),
                "model_efficiency_score": model_efficiency,
                "total_efficiency_score": round(
                    (model_efficiency + min(1.0, output_ratio / 2.0) + 
                     min(1.0, chars_per_dollar / 1000)) / 3, 3
                )
            }
            
        except Exception as e:
            logger.warning("Failed to calculate turn efficiency", error=str(e))
            return {
                "cost_per_token": 0.0,
                "output_input_ratio": 0.0,
                "chars_per_dollar": 0.0,
                "model_efficiency_score": 0.5,
                "total_efficiency_score": 0.5
            }
    
    def _get_model_efficiency_score(self, model: str) -> float:
        """Get efficiency score for model (cost-effectiveness)."""
        # Higher scores for more cost-effective models
        efficiency_scores = {
            "gpt-4o-mini": 0.95,
            "gpt-3.5-turbo": 0.90,
            "claude-3-haiku-20240307": 0.85,
            "gpt-4o": 0.70,
            "claude-3-5-sonnet-20241022": 0.65,
            "gpt-4-turbo": 0.60,
            "claude-3-opus-20240229": 0.40,
        }
        return efficiency_scores.get(model, 0.5)
    
    async def _store_turn_cost(self, turn_cost_data: Dict[str, Any]) -> None:
        """Store detailed turn cost data."""
        try:
            # Create Redis key for turn cost storage
            turn_key = f"turn_cost:{turn_cost_data['conversation_id']}:{turn_cost_data['turn_id']}"
            
            # Store turn data with expiration (30 days)
            await self.state_manager.redis_client.setex(
                turn_key,
                30 * 24 * 3600,  # 30 days
                json.dumps(turn_cost_data, default=str)
            )
            
            # Also add to conversation turn list for querying
            turn_list_key = f"turn_list:{turn_cost_data['conversation_id']}"
            await self.state_manager.redis_client.lpush(turn_list_key, turn_cost_data['turn_id'])
            await self.state_manager.redis_client.expire(turn_list_key, 30 * 24 * 3600)
            
        except Exception as e:
            logger.error("Failed to store turn cost data", error=str(e))
    
    async def _update_conversation_cumulative_cost(
        self, conversation_id: str, turn_cost_usd: float
    ) -> float:
        """Update and return cumulative conversation cost."""
        try:
            cumulative_key = f"conversation_cost:{conversation_id}"
            
            # Get current cumulative cost
            current_cumulative = await self.state_manager.redis_client.get(cumulative_key)
            current_cumulative = float(current_cumulative or 0.0)
            
            # Add this turn's cost
            new_cumulative = current_cumulative + turn_cost_usd
            
            # Store updated cumulative cost
            await self.state_manager.redis_client.setex(
                cumulative_key,
                24 * 3600,  # 24 hours
                str(new_cumulative)
            )
            
            return new_cumulative
            
        except Exception as e:
            logger.error("Failed to update cumulative cost", error=str(e))
            return turn_cost_usd
    
    async def _check_turn_budget_breach(
        self, conversation_id: str, cumulative_cost: float, turn_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check for budget breaches at the turn level."""
        try:
            # Check daily budget
            daily_summary = await self.get_daily_summary()
            daily_cost = daily_summary["total_cost_usd"]
            
            # Check conversation-level budget (example: $5 per conversation)
            conversation_limit = 5.0
            conversation_breach = cumulative_cost > conversation_limit
            
            # Check daily budget
            daily_breach = daily_cost > self.cost_limit_usd
            
            # Check for unusual cost spikes (turn cost > 10% of daily limit)
            turn_cost = turn_data["cost_breakdown"]["total_cost_usd"]
            spike_threshold = self.cost_limit_usd * 0.1
            cost_spike = turn_cost > spike_threshold
            
            status = "healthy"
            warnings = []
            
            if daily_breach:
                status = "daily_budget_exceeded"
                warnings.append(f"Daily budget of ${self.cost_limit_usd} exceeded")
            elif conversation_breach:
                status = "conversation_budget_exceeded"
                warnings.append(f"Conversation budget of ${conversation_limit} exceeded")
            elif cost_spike:
                status = "cost_spike_detected"
                warnings.append(f"Turn cost spike: ${turn_cost} > ${spike_threshold}")
            elif daily_cost > self.cost_limit_usd * 0.8:
                status = "daily_budget_warning"
                warnings.append(f"Approaching daily budget limit: {daily_cost/self.cost_limit_usd*100:.1f}%")
            
            return {
                "status": status,
                "daily_cost_usd": daily_cost,
                "daily_limit_usd": self.cost_limit_usd,
                "conversation_cost_usd": cumulative_cost,
                "conversation_limit_usd": conversation_limit,
                "turn_cost_usd": turn_cost,
                "warnings": warnings,
                "recommendations": self._generate_budget_recommendations(status, warnings)
            }
            
        except Exception as e:
            logger.error("Failed to check turn budget breach", error=str(e))
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _generate_budget_recommendations(self, status: str, warnings: List[str]) -> List[str]:
        """Generate budget management recommendations."""
        recommendations = []
        
        if status == "daily_budget_exceeded":
            recommendations.extend([
                "Consider pausing non-critical conversations until tomorrow",
                "Review model selection - consider using more cost-effective models",
                "Implement conversation length limits"
            ])
        elif status == "conversation_budget_exceeded":
            recommendations.extend([
                "Consider ending this conversation gracefully",
                "Summarize key points to avoid repetitive exchanges",
                "Use more efficient models for follow-up responses"
            ])
        elif status == "cost_spike_detected":
            recommendations.extend([
                "Review the complexity of the request",
                "Consider breaking complex requests into smaller parts",
                "Monitor for prompt injection or unusual request patterns"
            ])
        elif status == "daily_budget_warning":
            recommendations.extend([
                "Monitor remaining conversations carefully",
                "Consider using gpt-4o-mini for less critical tasks",
                "Implement response length limits"
            ])
        
        return recommendations
    
    async def _generate_turn_analytics(
        self, conversation_id: str, turn_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive turn-level analytics."""
        try:
            # Get conversation turn history for comparison
            turn_history = await self._get_conversation_turn_history(conversation_id, limit=10)
            
            # Calculate moving averages
            if len(turn_history) > 1:
                recent_costs = [t["cost_breakdown"]["total_cost_usd"] for t in turn_history[-5:]]
                avg_turn_cost = sum(recent_costs) / len(recent_costs)
                
                recent_tokens = [t["cost_breakdown"]["total_tokens"] for t in turn_history[-5:]]
                avg_turn_tokens = sum(recent_tokens) / len(recent_tokens)
            else:
                avg_turn_cost = turn_data["cost_breakdown"]["total_cost_usd"]
                avg_turn_tokens = turn_data["cost_breakdown"]["total_tokens"]
            
            current_cost = turn_data["cost_breakdown"]["total_cost_usd"]
            current_tokens = turn_data["cost_breakdown"]["total_tokens"]
            
            return {
                "turn_sequence": turn_data["turn_sequence"],
                "current_turn_cost_usd": current_cost,
                "average_turn_cost_usd": round(avg_turn_cost, 4),
                "cost_deviation": round(((current_cost - avg_turn_cost) / max(0.001, avg_turn_cost)) * 100, 1),
                "current_turn_tokens": current_tokens,
                "average_turn_tokens": int(avg_turn_tokens),
                "token_deviation": round(((current_tokens - avg_turn_tokens) / max(1, avg_turn_tokens)) * 100, 1),
                "efficiency_trend": await self._calculate_efficiency_trend(turn_history, turn_data),
                "model_usage": turn_data["cost_breakdown"]["model"],
                "agent_performance": {
                    "agent_name": turn_data["agent_name"],
                    "efficiency_score": turn_data["efficiency_metrics"]["total_efficiency_score"]
                }
            }
            
        except Exception as e:
            logger.error("Failed to generate turn analytics", error=str(e))
            return {
                "turn_sequence": turn_data.get("turn_sequence", 0),
                "error": str(e)
            }
    
    async def _get_conversation_turn_history(
        self, conversation_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent turn history for a conversation."""
        try:
            turn_list_key = f"turn_list:{conversation_id}"
            turn_ids = await self.state_manager.redis_client.lrange(turn_list_key, 0, limit - 1)
            
            turn_history = []
            for turn_id in turn_ids:
                turn_key = f"turn_cost:{conversation_id}:{turn_id.decode()}"
                turn_data = await self.state_manager.redis_client.get(turn_key)
                if turn_data:
                    turn_history.append(json.loads(turn_data))
            
            # Sort by turn sequence
            turn_history.sort(key=lambda x: x.get("turn_sequence", 0))
            return turn_history
            
        except Exception as e:
            logger.error("Failed to get conversation turn history", error=str(e))
            return []
    
    async def _calculate_efficiency_trend(
        self, turn_history: List[Dict[str, Any]], current_turn: Dict[str, Any]
    ) -> str:
        """Calculate efficiency trend over recent turns."""
        if len(turn_history) < 3:
            return "insufficient_data"
        
        try:
            # Get efficiency scores for recent turns
            recent_scores = [
                t["efficiency_metrics"]["total_efficiency_score"] 
                for t in turn_history[-3:] 
                if "efficiency_metrics" in t
            ]
            
            current_score = current_turn["efficiency_metrics"]["total_efficiency_score"]
            
            if len(recent_scores) >= 2:
                avg_recent = sum(recent_scores) / len(recent_scores)
                if current_score > avg_recent * 1.1:
                    return "improving"
                elif current_score < avg_recent * 0.9:
                    return "declining"
                else:
                    return "stable"
            
            return "stable"
            
        except Exception:
            return "unknown"
    
    async def _generate_cost_recommendations(
        self, turn_data: Dict[str, Any], budget_status: Dict[str, Any]
    ) -> List[str]:
        """Generate cost optimization recommendations for this turn."""
        recommendations = []
        
        try:
            efficiency_score = turn_data["efficiency_metrics"]["total_efficiency_score"]
            cost = turn_data["cost_breakdown"]["total_cost_usd"]
            model = turn_data["cost_breakdown"]["model"]
            
            # Model recommendations
            if "gpt-4" in model and efficiency_score < 0.6:
                recommendations.append("Consider using gpt-4o-mini for similar tasks to reduce costs")
            elif "claude-3-opus" in model:
                recommendations.append("Consider claude-3-haiku for less complex reasoning tasks")
            
            # Cost threshold recommendations
            if cost > 0.1:  # $0.10 per turn
                recommendations.append("High per-turn cost detected - review prompt complexity")
            
            # Efficiency recommendations
            if efficiency_score < 0.4:
                recommendations.extend([
                    "Low efficiency detected - review prompt engineering",
                    "Consider breaking complex requests into simpler parts"
                ])
            
            # Token optimization
            output_input_ratio = turn_data["efficiency_metrics"]["output_input_ratio"]
            if output_input_ratio < 0.3:
                recommendations.append("Low output/input ratio - consider more specific prompts")
            
            # Budget-based recommendations
            if budget_status["status"] != "healthy":
                recommendations.extend(budget_status.get("recommendations", []))
            
        except Exception as e:
            logger.warning("Failed to generate cost recommendations", error=str(e))
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    async def get_conversation_cost_analytics(self, conversation_id: str) -> Dict[str, Any]:
        """Get comprehensive cost analytics for a conversation."""
        try:
            turn_history = await self._get_conversation_turn_history(conversation_id, limit=50)
            
            if not turn_history:
                return {"error": "No turn history found for conversation"}
            
            # Calculate aggregate metrics
            total_cost = sum(t["cost_breakdown"]["total_cost_usd"] for t in turn_history)
            total_tokens = sum(t["cost_breakdown"]["total_tokens"] for t in turn_history)
            avg_cost_per_turn = total_cost / len(turn_history)
            avg_tokens_per_turn = total_tokens / len(turn_history)
            
            # Model usage breakdown
            model_usage = {}
            for turn in turn_history:
                model = turn["cost_breakdown"]["model"]
                if model not in model_usage:
                    model_usage[model] = {"turns": 0, "cost": 0.0, "tokens": 0}
                model_usage[model]["turns"] += 1
                model_usage[model]["cost"] += turn["cost_breakdown"]["total_cost_usd"]
                model_usage[model]["tokens"] += turn["cost_breakdown"]["total_tokens"]
            
            # Agent performance breakdown
            agent_performance = {}
            for turn in turn_history:
                agent = turn["agent_name"]
                if agent not in agent_performance:
                    agent_performance[agent] = {"turns": 0, "cost": 0.0, "avg_efficiency": 0.0}
                agent_performance[agent]["turns"] += 1
                agent_performance[agent]["cost"] += turn["cost_breakdown"]["total_cost_usd"]
                if "efficiency_metrics" in turn:
                    agent_performance[agent]["avg_efficiency"] += turn["efficiency_metrics"]["total_efficiency_score"]
            
            # Calculate average efficiency per agent
            for agent_data in agent_performance.values():
                agent_data["avg_efficiency"] = agent_data["avg_efficiency"] / agent_data["turns"]
            
            return {
                "conversation_id": conversation_id,
                "summary": {
                    "total_turns": len(turn_history),
                    "total_cost_usd": round(total_cost, 4),
                    "total_tokens": total_tokens,
                    "avg_cost_per_turn": round(avg_cost_per_turn, 4),
                    "avg_tokens_per_turn": int(avg_tokens_per_turn),
                    "conversation_efficiency_score": round(
                        sum(t.get("efficiency_metrics", {}).get("total_efficiency_score", 0.5) for t in turn_history) / len(turn_history), 3
                    )
                },
                "model_usage": model_usage,
                "agent_performance": agent_performance,
                "cost_trend": self._calculate_cost_trend(turn_history),
                "recommendations": self._generate_conversation_recommendations(turn_history, total_cost)
            }
            
        except Exception as e:
            logger.error("Failed to get conversation cost analytics", error=str(e))
            return {"error": str(e)}
    
    def _calculate_cost_trend(self, turn_history: List[Dict[str, Any]]) -> str:
        """Calculate overall cost trend for the conversation."""
        if len(turn_history) < 5:
            return "insufficient_data"
        
        try:
            costs = [t["cost_breakdown"]["total_cost_usd"] for t in turn_history]
            first_half = costs[:len(costs)//2]
            second_half = costs[len(costs)//2:]
            
            avg_first_half = sum(first_half) / len(first_half)
            avg_second_half = sum(second_half) / len(second_half)
            
            if avg_second_half > avg_first_half * 1.2:
                return "increasing"
            elif avg_second_half < avg_first_half * 0.8:
                return "decreasing"
            else:
                return "stable"
                
        except Exception:
            return "unknown"
    
    def _generate_conversation_recommendations(
        self, turn_history: List[Dict[str, Any]], total_cost: float
    ) -> List[str]:
        """Generate recommendations for conversation-level cost optimization."""
        recommendations = []
        
        try:
            avg_efficiency = sum(
                t.get("efficiency_metrics", {}).get("total_efficiency_score", 0.5) 
                for t in turn_history
            ) / len(turn_history)
            
            if total_cost > 2.0:  # $2 per conversation
                recommendations.append("High conversation cost - consider conversation length limits")
            
            if avg_efficiency < 0.5:
                recommendations.extend([
                    "Low average efficiency - review prompt engineering strategies",
                    "Consider using more cost-effective models for routine tasks"
                ])
            
            if len(turn_history) > 20:
                recommendations.append("Long conversation detected - consider periodic summaries to reduce context")
            
            # Model optimization
            expensive_models = ["gpt-4-turbo", "claude-3-opus-20240229"]
            expensive_usage = sum(1 for t in turn_history if t["cost_breakdown"]["model"] in expensive_models)
            if expensive_usage > len(turn_history) * 0.5:
                recommendations.append("High usage of expensive models - evaluate if necessary for all turns")
            
        except Exception as e:
            logger.warning("Failed to generate conversation recommendations", error=str(e))
        
        return recommendations