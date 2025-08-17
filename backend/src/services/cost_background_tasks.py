"""
⚡ Cost System Background Tasks
Orchestrates all cost-related background services and monitoring
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

import structlog

from services.budget_monitor_service import budget_monitor
from services.circuit_breaker_service import circuit_breaker
from services.pricing_updater_service import pricing_updater

logger = structlog.get_logger()


class CostBackgroundTaskManager:
    """Manager for all cost-related background tasks"""
    
    def __init__(self):
        """Initialize background task manager"""
        self.running = False
        self.tasks = []
        
    async def start_all_services(self):
        """Start all cost-related background services"""
        
        if self.running:
            logger.warning("⚠️ Cost background services already running")
            return
        
        self.running = True
        logger.info("🚀 Starting cost system background services")
        
        try:
            # Start all background tasks concurrently
            self.tasks = await asyncio.gather(
                self._start_budget_monitoring(),
                self._start_circuit_breaker(),
                self._start_pricing_updates(),
                self._start_system_health_check(),
                return_exceptions=True
            )
            
            logger.info("✅ All cost background services started successfully")
            
        except Exception as e:
            logger.error("❌ Failed to start cost background services", error=str(e))
            await self.stop_all_services()
            raise
    
    async def stop_all_services(self):
        """Stop all background services"""
        
        if not self.running:
            return
        
        self.running = False
        logger.info("🛑 Stopping cost system background services")
        
        # Cancel all running tasks
        for task in self.tasks:
            if isinstance(task, asyncio.Task) and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self.tasks.clear()
        logger.info("✅ All cost background services stopped")
    
    async def _start_budget_monitoring(self):
        """Start budget monitoring loop"""
        
        logger.info("💰 Starting budget monitoring service")
        
        while self.running:
            try:
                # Run comprehensive budget check every 5 minutes
                budget_status = await budget_monitor.check_all_limits()
                
                # Log status summary
                alerts_count = len(budget_status.get("alerts_generated", []))
                circuit_active = budget_status.get("circuit_breaker", {}).get("should_trigger", False)
                
                if alerts_count > 0 or circuit_active:
                    logger.warning("🚨 Budget monitoring alerts generated",
                                 alerts_count=alerts_count,
                                 circuit_breaker_active=circuit_active)
                else:
                    logger.debug("✅ Budget monitoring check completed - all healthy")
                
                # Wait 5 minutes before next check
                await asyncio.sleep(300)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("❌ Budget monitoring error", error=str(e))
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def _start_circuit_breaker(self):
        """Start circuit breaker monitoring"""
        
        logger.info("🚦 Starting circuit breaker monitoring service")
        
        try:
            await circuit_breaker.start_monitoring()
        except asyncio.CancelledError:
            logger.info("🚦 Circuit breaker monitoring stopped")
        except Exception as e:
            logger.error("❌ Circuit breaker monitoring error", error=str(e))
    
    async def _start_pricing_updates(self):
        """Start automatic pricing updates"""
        
        logger.info("💲 Starting automatic pricing update service")
        
        while self.running:
            try:
                # Update pricing once per day at 6 AM (or on startup)
                now = datetime.utcnow()
                
                # Check if it's 6 AM UTC or if this is the first run
                if now.hour == 6 and now.minute < 10:
                    logger.info("🔄 Running daily pricing update")
                    result = await pricing_updater.update_all_pricing()
                    
                    providers_updated = len(result.get("providers_updated", []))
                    errors = len(result.get("errors", []))
                    
                    if errors > 0:
                        logger.warning("⚠️ Pricing update completed with errors",
                                     providers_updated=providers_updated,
                                     errors=errors)
                    else:
                        logger.info("✅ Pricing update completed successfully",
                                   providers_updated=providers_updated)
                
                # Wait 1 hour before next check
                await asyncio.sleep(3600)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("❌ Pricing update error", error=str(e))
                await asyncio.sleep(3600)  # Wait 1 hour before retry
    
    async def _start_system_health_check(self):
        """Start system health monitoring"""
        
        logger.info("🏥 Starting system health monitoring")
        
        while self.running:
            try:
                # Get comprehensive system status
                health_status = await self._get_system_health()
                
                # Log health summary
                overall_status = health_status["overall_status"]
                critical_issues = health_status["critical_issues"]
                
                if critical_issues > 0:
                    logger.error("🚨 System health issues detected",
                               overall_status=overall_status,
                               critical_issues=critical_issues)
                elif overall_status != "healthy":
                    logger.warning("⚠️ System health degraded",
                                 overall_status=overall_status)
                else:
                    logger.debug("✅ System health check completed - all systems operational")
                
                # Wait 2 minutes before next check
                await asyncio.sleep(120)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("❌ System health check error", error=str(e))
                await asyncio.sleep(120)  # Wait 2 minutes before retry
    
    async def _get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        
        try:
            # Get status from all services
            budget_summary = await budget_monitor.get_budget_status_summary()
            circuit_status = await circuit_breaker.get_circuit_status()
            
            # Determine overall health
            overall_status = "healthy"
            critical_issues = 0
            
            # Check budget status
            if budget_summary["overall_status"] == "critical":
                overall_status = "critical"
                critical_issues += 1
            elif budget_summary["overall_status"] in ["warning", "moderate"] and overall_status == "healthy":
                overall_status = budget_summary["overall_status"]
            
            # Check circuit breaker
            if circuit_status["circuit_state"] == "OPEN":
                overall_status = "critical"
                critical_issues += 1
            elif circuit_status["circuit_state"] == "HALF_OPEN" and overall_status == "healthy":
                overall_status = "degraded"
            
            # Check for suspended services
            suspended_count = len(circuit_status["suspended_providers"]) + len(circuit_status["suspended_agents"])
            if suspended_count > 0:
                if overall_status == "healthy":
                    overall_status = "degraded"
                if suspended_count > 2:
                    critical_issues += 1
            
            return {
                "overall_status": overall_status,
                "critical_issues": critical_issues,
                "timestamp": datetime.utcnow().isoformat(),
                "components": {
                    "budget_monitor": budget_summary["overall_status"],
                    "circuit_breaker": circuit_status["health_status"],
                    "suspended_services": suspended_count
                },
                "metrics": {
                    "daily_utilization": budget_summary["daily_utilization"],
                    "monthly_utilization": budget_summary["monthly_utilization"],
                    "circuit_breaker_active": budget_summary["circuit_breaker_active"],
                    "total_alerts": budget_summary["total_alerts"]
                }
            }
            
        except Exception as e:
            logger.error("❌ Failed to get system health", error=str(e))
            return {
                "overall_status": "unknown",
                "critical_issues": 1,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get status of all background services"""
        
        try:
            system_health = await self._get_system_health()
            budget_summary = await budget_monitor.get_budget_status_summary()
            circuit_status = await circuit_breaker.get_circuit_status()
            
            return {
                "services_running": self.running,
                "active_tasks": len([t for t in self.tasks if isinstance(t, asyncio.Task) and not t.done()]),
                "system_health": system_health,
                "budget_summary": budget_summary,
                "circuit_breaker": circuit_status,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("❌ Failed to get background services status", error=str(e))
            return {
                "services_running": self.running,
                "active_tasks": 0,
                "error": str(e),
                "last_updated": datetime.utcnow().isoformat()
            }
    
    async def trigger_manual_check(self) -> Dict[str, Any]:
        """Trigger a manual check of all systems"""
        
        logger.info("🔄 Manual system check triggered")
        
        try:
            # Run all checks concurrently
            budget_status, pricing_comparison, system_health = await asyncio.gather(
                budget_monitor.check_all_limits(),
                pricing_updater.get_pricing_comparison(),
                self._get_system_health(),
                return_exceptions=True
            )
            
            return {
                "check_completed": datetime.utcnow().isoformat(),
                "budget_status": budget_status if not isinstance(budget_status, Exception) else {"error": str(budget_status)},
                "pricing_data": pricing_comparison if not isinstance(pricing_comparison, Exception) else {"error": str(pricing_comparison)},
                "system_health": system_health if not isinstance(system_health, Exception) else {"error": str(system_health)}
            }
            
        except Exception as e:
            logger.error("❌ Manual check failed", error=str(e))
            return {
                "check_completed": datetime.utcnow().isoformat(),
                "error": str(e)
            }


# Global background task manager instance
cost_task_manager = CostBackgroundTaskManager()


# Helper function to start services on app startup
async def start_cost_services():
    """Start cost services - called from app startup"""
    
    try:
        await cost_task_manager.start_all_services()
        logger.info("🚀 Cost services started successfully")
        
    except Exception as e:
        logger.error("❌ Failed to start cost services", error=str(e))
        # Don't fail the app startup, just log the error


# Helper function to stop services on app shutdown
async def stop_cost_services():
    """Stop cost services - called from app shutdown"""
    
    try:
        await cost_task_manager.stop_all_services()
        logger.info("🛑 Cost services stopped successfully")
        
    except Exception as e:
        logger.error("❌ Failed to stop cost services", error=str(e))