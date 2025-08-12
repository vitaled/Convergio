"""
Circuit Breaker and Health Monitoring for Orchestrators
Provides resilience patterns for orchestrator failures
"""

import asyncio
import time
from enum import Enum
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import structlog
from dataclasses import dataclass, field

logger = structlog.get_logger()


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    success_threshold: int = 3
    half_open_max_calls: int = 3


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker"""
    total_calls: int = 0
    failed_calls: int = 0
    successful_calls: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_changes: list = field(default_factory=list)


class CircuitBreaker:
    """Circuit breaker implementation for orchestrators"""
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self.half_open_calls = 0
        self.state_changed_at = datetime.now()
        
    def _change_state(self, new_state: CircuitState):
        """Change circuit breaker state"""
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            self.state_changed_at = datetime.now()
            self.stats.state_changes.append({
                "from": old_state.value,
                "to": new_state.value,
                "at": self.state_changed_at.isoformat()
            })
            logger.info(
                f"Circuit breaker {self.name} state changed",
                old_state=old_state.value,
                new_state=new_state.value
            )
            
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset from OPEN to HALF_OPEN"""
        if self.state != CircuitState.OPEN:
            return False
            
        time_since_change = (datetime.now() - self.state_changed_at).total_seconds()
        return time_since_change >= self.config.recovery_timeout
        
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker"""
        
        # Check if we should transition from OPEN to HALF_OPEN
        if self._should_attempt_reset():
            self._change_state(CircuitState.HALF_OPEN)
            self.half_open_calls = 0
            
        # Reject calls if circuit is OPEN
        if self.state == CircuitState.OPEN:
            raise Exception(f"Circuit breaker {self.name} is OPEN - rejecting call")
            
        # Limit calls in HALF_OPEN state
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.config.half_open_max_calls:
                raise Exception(f"Circuit breaker {self.name} HALF_OPEN limit reached")
            self.half_open_calls += 1
            
        # Execute the function
        try:
            self.stats.total_calls += 1
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
            
    def _on_success(self):
        """Handle successful call"""
        self.stats.successful_calls += 1
        self.stats.consecutive_successes += 1
        self.stats.consecutive_failures = 0
        self.stats.last_success_time = datetime.now()
        
        # Transition from HALF_OPEN to CLOSED after enough successes
        if self.state == CircuitState.HALF_OPEN:
            if self.stats.consecutive_successes >= self.config.success_threshold:
                self._change_state(CircuitState.CLOSED)
                
    def _on_failure(self):
        """Handle failed call"""
        self.stats.failed_calls += 1
        self.stats.consecutive_failures += 1
        self.stats.consecutive_successes = 0
        self.stats.last_failure_time = datetime.now()
        
        # Transition from CLOSED to OPEN after too many failures
        if self.state == CircuitState.CLOSED:
            if self.stats.consecutive_failures >= self.config.failure_threshold:
                self._change_state(CircuitState.OPEN)
                
        # Transition from HALF_OPEN back to OPEN on any failure
        elif self.state == CircuitState.HALF_OPEN:
            self._change_state(CircuitState.OPEN)
            
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        return {
            "name": self.name,
            "state": self.state.value,
            "stats": {
                "total_calls": self.stats.total_calls,
                "failed_calls": self.stats.failed_calls,
                "successful_calls": self.stats.successful_calls,
                "consecutive_failures": self.stats.consecutive_failures,
                "consecutive_successes": self.stats.consecutive_successes,
                "failure_rate": (
                    self.stats.failed_calls / self.stats.total_calls 
                    if self.stats.total_calls > 0 else 0
                ),
                "last_failure": (
                    self.stats.last_failure_time.isoformat() 
                    if self.stats.last_failure_time else None
                ),
                "last_success": (
                    self.stats.last_success_time.isoformat() 
                    if self.stats.last_success_time else None
                ),
            },
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
            },
            "state_changed_at": self.state_changed_at.isoformat(),
            "recent_state_changes": self.stats.state_changes[-5:]  # Last 5 changes
        }


class HealthMonitor:
    """Health monitoring for orchestrators"""
    
    def __init__(self, check_interval: int = 30):
        """
        Initialize health monitor
        
        Args:
            check_interval: Seconds between health checks
        """
        self.check_interval = check_interval
        self.orchestrator_health: Dict[str, Dict[str, Any]] = {}
        self._running = False
        self._task = None
        
    async def start(self, orchestrators: Dict[str, Any]):
        """Start health monitoring"""
        if self._running:
            logger.warning("Health monitor already running")
            return
            
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop(orchestrators))
        logger.info("Health monitor started", check_interval=self.check_interval)
        
    async def stop(self):
        """Stop health monitoring"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitor stopped")
        
    async def _monitor_loop(self, orchestrators: Dict[str, Any]):
        """Main monitoring loop"""
        while self._running:
            try:
                # Check health of each orchestrator
                for name, orchestrator in orchestrators.items():
                    health_status = await self._check_orchestrator_health(
                        name, orchestrator
                    )
                    self.orchestrator_health[name] = health_status
                    
                # Log summary
                healthy_count = sum(
                    1 for h in self.orchestrator_health.values() 
                    if h.get("healthy", False)
                )
                logger.info(
                    "Health check completed",
                    healthy=healthy_count,
                    total=len(orchestrators)
                )
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(self.check_interval)
                
    async def _check_orchestrator_health(
        self, 
        name: str, 
        orchestrator: Any
    ) -> Dict[str, Any]:
        """Check health of a single orchestrator"""
        try:
            start_time = time.time()
            
            # Call orchestrator's health method if it exists
            if hasattr(orchestrator, 'health'):
                is_healthy = await orchestrator.health()
            elif hasattr(orchestrator, 'is_healthy'):
                is_healthy = orchestrator.is_healthy()
            else:
                # Fallback: assume healthy if no health method
                is_healthy = True
                
            response_time = time.time() - start_time
            
            return {
                "name": name,
                "healthy": is_healthy,
                "response_time_ms": response_time * 1000,
                "checked_at": datetime.now().isoformat(),
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Health check failed for {name}: {e}")
            return {
                "name": name,
                "healthy": False,
                "response_time_ms": None,
                "checked_at": datetime.now().isoformat(),
                "error": str(e)
            }
            
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status of all orchestrators"""
        return {
            "orchestrators": self.orchestrator_health,
            "summary": {
                "total": len(self.orchestrator_health),
                "healthy": sum(
                    1 for h in self.orchestrator_health.values() 
                    if h.get("healthy", False)
                ),
                "unhealthy": sum(
                    1 for h in self.orchestrator_health.values() 
                    if not h.get("healthy", True)
                ),
            },
            "last_check": max(
                (h.get("checked_at") for h in self.orchestrator_health.values()),
                default=None
            )
        }
        
    def is_orchestrator_healthy(self, name: str) -> bool:
        """Check if specific orchestrator is healthy"""
        return self.orchestrator_health.get(name, {}).get("healthy", False)


class ResilientOrchestrator:
    """Wrapper that adds resilience to any orchestrator"""
    
    def __init__(
        self, 
        orchestrator: Any,
        name: str,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None
    ):
        self.orchestrator = orchestrator
        self.name = name
        self.circuit_breaker = CircuitBreaker(name, circuit_breaker_config)
        
    async def orchestrate(self, *args, **kwargs):
        """Orchestrate with circuit breaker protection"""
        return await self.circuit_breaker.call(
            self.orchestrator.orchestrate,
            *args,
            **kwargs
        )
        
    async def health(self) -> bool:
        """Check orchestrator health"""
        try:
            if hasattr(self.orchestrator, 'health'):
                return await self.orchestrator.health()
            elif hasattr(self.orchestrator, 'is_healthy'):
                return self.orchestrator.is_healthy()
            return True
        except:
            return False
            
    def get_circuit_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        return self.circuit_breaker.get_status()


# Prometheus metrics support (optional)
try:
    from prometheus_client import Counter, Histogram, Gauge
    
    # Metrics
    orchestrator_health_gauge = Gauge(
        'orchestrator_health_status',
        'Health status of orchestrators (1=healthy, 0=unhealthy)',
        ['orchestrator_name']
    )
    
    circuit_breaker_state_gauge = Gauge(
        'circuit_breaker_state',
        'Circuit breaker state (0=closed, 1=open, 2=half_open)',
        ['orchestrator_name']
    )
    
    orchestrator_failures_counter = Counter(
        'orchestrator_failures_total',
        'Total number of orchestrator failures',
        ['orchestrator_name']
    )
    
    orchestrator_latency_histogram = Histogram(
        'orchestrator_response_time_seconds',
        'Response time of orchestrators',
        ['orchestrator_name']
    )
    
    METRICS_ENABLED = True
    
except ImportError:
    METRICS_ENABLED = False
    logger.info("Prometheus metrics not available - install prometheus_client to enable")


def update_metrics(orchestrator_name: str, health_status: Dict[str, Any]):
    """Update Prometheus metrics if available"""
    if not METRICS_ENABLED:
        return
        
    try:
        # Update health gauge
        orchestrator_health_gauge.labels(
            orchestrator_name=orchestrator_name
        ).set(1 if health_status.get("healthy", False) else 0)
        
        # Update response time if available
        if health_status.get("response_time_ms"):
            orchestrator_latency_histogram.labels(
                orchestrator_name=orchestrator_name
            ).observe(health_status["response_time_ms"] / 1000)
            
    except Exception as e:
        logger.error(f"Failed to update metrics: {e}")