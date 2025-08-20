"""
GRAPHFLOW ORCHESTRATOR - Compatibility Wrapper
Uses the UnifiedOrchestrator for all functionality
"""

# Import compatibility adapter
from .unified_orchestrator_adapter import GraphFlowOrchestrator as _GraphFlowOrchestrator
from .unified_orchestrator_adapter import get_graphflow_orchestrator

# Re-export for backward compatibility
GraphFlowOrchestrator = _GraphFlowOrchestrator