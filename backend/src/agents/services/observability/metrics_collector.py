"""
Metrics Collector - Real-time metrics aggregation and monitoring
Collects and aggregates metrics from AutoGen workflows for monitoring and alerting.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics

import structlog
from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest, REGISTRY

logger = structlog.get_logger()


@dataclass
class MetricSnapshot:
    """Point-in-time metric snapshot"""
    timestamp: datetime
    metric_name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatedMetric:
    """Aggregated metric with statistics"""
    metric_name: str
    period: str  # "1m", "5m", "1h", "1d"
    count: int
    sum: float
    mean: float
    median: float
    min: float
    max: float
    p50: float
    p95: float
    p99: float
    stddev: float
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Advanced metrics collection and aggregation system"""
    
    def __init__(self, window_size_minutes: int = 60):
        self.window_size = window_size_minutes
        
        # Time series data storage
        self.metrics_buffer: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        
        # Prometheus metrics
        self._init_prometheus_metrics()
        
        # Aggregation intervals
        self.aggregation_intervals = {
            "1m": timedelta(minutes=1),
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "1h": timedelta(hours=1),
            "1d": timedelta(days=1)
        }
        
        # Alert thresholds
        self.alert_thresholds: Dict[str, Dict[str, float]] = {}
        self._init_default_thresholds()
        
        # Active alerts
        self.active_alerts: Set[str] = set()
        
        # Background tasks
        self.aggregation_task = None
        self.cleanup_task = None
        
        logger.info("📊 Metrics collector initialized")
    
    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics"""
        
        # Conversation metrics
        self.conversation_total = Counter(
            'convergio_conversations_total',
            'Total number of conversations',
            ['status', 'user_type']
        )
        
        self.conversation_duration = Histogram(
            'convergio_conversation_duration_seconds',
            'Conversation duration in seconds',
            ['workflow_type'],
            buckets=[0.5, 1, 2, 5, 10, 30, 60, 120, 300]
        )
        
        # Agent metrics
        self.agent_invocations = Counter(
            'convergio_agent_invocations_total',
            'Total agent invocations',
            ['agent_name', 'status']
        )
        
        self.agent_response_time = Histogram(
            'convergio_agent_response_time_seconds',
            'Agent response time',
            ['agent_name'],
            buckets=[0.1, 0.5, 1, 2, 5, 10]
        )
        
        # Cost metrics
        self.cost_per_turn = Histogram(
            'convergio_cost_per_turn_usd',
            'Cost per conversation turn',
            ['model', 'agent'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1]
        )
        
        self.daily_cost = Gauge(
            'convergio_daily_cost_usd',
            'Daily cost in USD'
        )
        
        self.budget_utilization = Gauge(
            'convergio_budget_utilization_percent',
            'Budget utilization percentage'
        )
        
        # Performance metrics
        self.active_conversations = Gauge(
            'convergio_active_conversations',
            'Number of active conversations'
        )
        
        self.queue_size = Gauge(
            'convergio_queue_size',
            'Message queue size',
            ['queue_name']
        )
        
        self.error_rate = Gauge(
            'convergio_error_rate_per_minute',
            'Errors per minute',
            ['error_type']
        )
        
        # Selection metrics
        self.selection_accuracy = Histogram(
            'convergio_selection_accuracy',
            'Agent selection accuracy',
            ['selection_method'],
            buckets=[0.1, 0.3, 0.5, 0.7, 0.9, 0.95, 0.99, 1.0]
        )
        
        # Memory metrics
        self.memory_operations = Counter(
            'convergio_memory_operations_total',
            'Memory operations',
            ['operation', 'memory_type']
        )
        
        self.memory_size_bytes = Gauge(
            'convergio_memory_size_bytes',
            'Memory size in bytes',
            ['memory_type']
        )
    
    def _init_default_thresholds(self):
        """Initialize default alert thresholds"""
        self.alert_thresholds = {
            "conversation_duration_p95": {"warning": 60, "critical": 120},
            "agent_response_time_p95": {"warning": 5, "critical": 10},
            "cost_per_turn_p95": {"warning": 0.1, "critical": 0.5},
            "error_rate": {"warning": 5, "critical": 10},
            "budget_utilization": {"warning": 80, "critical": 95},
            "active_conversations": {"warning": 100, "critical": 200},
            "queue_size": {"warning": 1000, "critical": 5000}
        }
    
    async def start(self):
        """Start background tasks"""
        self.aggregation_task = asyncio.create_task(self._aggregation_loop())
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Metrics collector background tasks started")
    
    async def stop(self):
        """Stop background tasks"""
        if self.aggregation_task:
            self.aggregation_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()
        logger.info("Metrics collector stopped")
    
    def record_conversation_metrics(
        self,
        conversation_id: str,
        duration_seconds: float,
        status: str,
        user_type: str = "standard",
        workflow_type: str = "general"
    ):
        """Record conversation metrics"""
        # Prometheus metrics
        self.conversation_total.labels(status=status, user_type=user_type).inc()
        self.conversation_duration.labels(workflow_type=workflow_type).observe(duration_seconds)
        
        # Time series storage
        self._store_metric(
            "conversation_duration",
            duration_seconds,
            {"status": status, "workflow_type": workflow_type}
        )
        
        # Check thresholds
        self._check_threshold("conversation_duration", duration_seconds)
    
    def record_agent_metrics(
        self,
        agent_name: str,
        response_time_seconds: float,
        status: str = "success"
    ):
        """Record agent performance metrics"""
        # Prometheus metrics
        self.agent_invocations.labels(agent_name=agent_name, status=status).inc()
        self.agent_response_time.labels(agent_name=agent_name).observe(response_time_seconds)
        
        # Time series storage
        self._store_metric(
            "agent_response_time",
            response_time_seconds,
            {"agent": agent_name, "status": status}
        )
        
        # Check thresholds
        self._check_threshold("agent_response_time", response_time_seconds)
    
    def record_cost_metrics(
        self,
        cost_usd: float,
        tokens: int,
        model: str,
        agent: str
    ):
        """Record cost metrics"""
        # Prometheus metrics
        self.cost_per_turn.labels(model=model, agent=agent).observe(cost_usd)
        
        # Time series storage
        self._store_metric(
            "cost_per_turn",
            cost_usd,
            {"model": model, "agent": agent, "tokens": tokens}
        )
        
        # Check thresholds
        self._check_threshold("cost_per_turn", cost_usd)
    
    def update_budget_metrics(
        self,
        daily_cost_usd: float,
        daily_limit_usd: float
    ):
        """Update budget metrics"""
        utilization = (daily_cost_usd / daily_limit_usd * 100) if daily_limit_usd > 0 else 0
        
        # Prometheus gauges
        self.daily_cost.set(daily_cost_usd)
        self.budget_utilization.set(utilization)
        
        # Check thresholds
        self._check_threshold("budget_utilization", utilization)
    
    def update_performance_metrics(
        self,
        active_conversations: int,
        queue_sizes: Dict[str, int],
        error_counts: Dict[str, int]
    ):
        """Update performance metrics"""
        # Active conversations
        self.active_conversations.set(active_conversations)
        self._check_threshold("active_conversations", active_conversations)
        
        # Queue sizes
        for queue_name, size in queue_sizes.items():
            self.queue_size.labels(queue_name=queue_name).set(size)
            self._check_threshold("queue_size", size)
        
        # Error rates (per minute)
        for error_type, count in error_counts.items():
            self.error_rate.labels(error_type=error_type).set(count)
            self._check_threshold("error_rate", count)
    
    def record_selection_metrics(
        self,
        accuracy_score: float,
        selection_method: str
    ):
        """Record agent selection metrics"""
        self.selection_accuracy.labels(selection_method=selection_method).observe(accuracy_score)
        
        self._store_metric(
            "selection_accuracy",
            accuracy_score,
            {"method": selection_method}
        )
    
    def record_memory_metrics(
        self,
        operation: str,
        memory_type: str,
        size_bytes: int
    ):
        """Record memory operation metrics"""
        self.memory_operations.labels(operation=operation, memory_type=memory_type).inc()
        
        if operation == "store":
            current = self.memory_size_bytes.labels(memory_type=memory_type)._value.get()
            self.memory_size_bytes.labels(memory_type=memory_type).set(current + size_bytes)
        
        self._store_metric(
            "memory_operation",
            size_bytes,
            {"operation": operation, "type": memory_type}
        )
    
    def _store_metric(
        self,
        metric_name: str,
        value: float,
        labels: Dict[str, str]
    ):
        """Store metric in time series buffer"""
        snapshot = MetricSnapshot(
            timestamp=datetime.utcnow(),
            metric_name=metric_name,
            value=value,
            labels=labels
        )
        
        # Create composite key for grouping
        key = f"{metric_name}:{json.dumps(labels, sort_keys=True)}"
        self.metrics_buffer[key].append(snapshot)
    
    def _check_threshold(self, metric_name: str, value: float):
        """Check if metric exceeds thresholds"""
        if metric_name not in self.alert_thresholds:
            return
        
        thresholds = self.alert_thresholds[metric_name]
        alert_key = f"{metric_name}:{value}"
        
        if value >= thresholds.get("critical", float('inf')):
            self._trigger_alert(metric_name, "critical", value)
        elif value >= thresholds.get("warning", float('inf')):
            self._trigger_alert(metric_name, "warning", value)
        else:
            self._clear_alert(alert_key)
    
    def _trigger_alert(self, metric_name: str, severity: str, value: float):
        """Trigger an alert"""
        alert_key = f"{metric_name}:{severity}"
        
        if alert_key not in self.active_alerts:
            self.active_alerts.add(alert_key)
            logger.warning(
                f"🚨 Alert triggered: {metric_name}",
                severity=severity,
                value=value,
                threshold=self.alert_thresholds[metric_name][severity]
            )
    
    def _clear_alert(self, alert_key: str):
        """Clear an alert"""
        if alert_key in self.active_alerts:
            self.active_alerts.remove(alert_key)
            logger.info(f"✅ Alert cleared: {alert_key}")
    
    async def get_aggregated_metrics(
        self,
        metric_name: str,
        period: str = "5m",
        labels: Optional[Dict[str, str]] = None
    ) -> List[AggregatedMetric]:
        """Get aggregated metrics for a period"""
        results = []
        interval = self.aggregation_intervals.get(period, timedelta(minutes=5))
        cutoff_time = datetime.utcnow() - interval
        
        # Filter metrics by name and time
        for key, snapshots in self.metrics_buffer.items():
            if not key.startswith(f"{metric_name}:"):
                continue
            
            # Filter by time window
            recent_snapshots = [s for s in snapshots if s.timestamp >= cutoff_time]
            
            if not recent_snapshots:
                continue
            
            # Filter by labels if provided
            if labels:
                sample_labels = recent_snapshots[0].labels
                if not all(sample_labels.get(k) == v for k, v in labels.items()):
                    continue
            
            # Calculate aggregates
            values = [s.value for s in recent_snapshots]
            
            aggregated = AggregatedMetric(
                metric_name=metric_name,
                period=period,
                count=len(values),
                sum=sum(values),
                mean=statistics.mean(values),
                median=statistics.median(values),
                min=min(values),
                max=max(values),
                p50=self._percentile(values, 50),
                p95=self._percentile(values, 95),
                p99=self._percentile(values, 99),
                stddev=statistics.stdev(values) if len(values) > 1 else 0,
                labels=recent_snapshots[0].labels
            )
            
            results.append(aggregated)
        
        return results
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile"""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        
        if index >= len(sorted_values):
            return sorted_values[-1]
        
        return sorted_values[index]
    
    async def _aggregation_loop(self):
        """Background task for metric aggregation"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                # Aggregate metrics for different periods
                for period in self.aggregation_intervals.keys():
                    for metric_name in set(k.split(":")[0] for k in self.metrics_buffer.keys()):
                        await self.get_aggregated_metrics(metric_name, period)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Aggregation loop error", error=str(e))
    
    async def _cleanup_loop(self):
        """Background task for cleaning old metrics"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                cutoff_time = datetime.utcnow() - timedelta(minutes=self.window_size)
                
                # Clean old metrics
                for key in list(self.metrics_buffer.keys()):
                    snapshots = self.metrics_buffer[key]
                    
                    # Remove old snapshots
                    while snapshots and snapshots[0].timestamp < cutoff_time:
                        snapshots.popleft()
                    
                    # Remove empty buffers
                    if not snapshots:
                        del self.metrics_buffer[key]
                
                logger.info(f"Cleaned old metrics, remaining buffers: {len(self.metrics_buffer)}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Cleanup loop error", error=str(e))
    
    def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        return generate_latest(REGISTRY).decode('utf-8')
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of metrics system"""
        return {
            "status": "healthy" if not self.active_alerts else "degraded",
            "active_alerts": list(self.active_alerts),
            "buffer_size": sum(len(v) for v in self.metrics_buffer.values()),
            "metric_types": len(set(k.split(":")[0] for k in self.metrics_buffer.keys())),
            "oldest_metric": min(
                (s.timestamp for snapshots in self.metrics_buffer.values() for s in snapshots),
                default=None
            )
        }
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get metrics for dashboard display"""
        return {
            "conversations": {
                "total": self.conversation_total._value.sum(),
                "active": self.active_conversations._value.get()
            },
            "agents": {
                "total_invocations": self.agent_invocations._value.sum()
            },
            "cost": {
                "daily_usd": self.daily_cost._value.get(),
                "budget_utilization": self.budget_utilization._value.get()
            },
            "performance": {
                "error_rate": sum(self.error_rate._value.values()),
                "queue_sizes": {
                    label: value
                    for label, value in self.queue_size._value.items()
                }
            },
            "alerts": list(self.active_alerts)
        }


# Global metrics collector
_metrics_collector: Optional[MetricsCollector] = None


def initialize_metrics_collector(window_size_minutes: int = 60) -> MetricsCollector:
    """Initialize global metrics collector"""
    global _metrics_collector
    _metrics_collector = MetricsCollector(window_size_minutes)
    return _metrics_collector


def get_metrics_collector() -> Optional[MetricsCollector]:
    """Get global metrics collector"""
    return _metrics_collector


__all__ = [
    "MetricsCollector",
    "MetricSnapshot",
    "AggregatedMetric",
    "initialize_metrics_collector",
    "get_metrics_collector"
]