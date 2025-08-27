"""
🤖 Convergio - AI Agents API
Modularized version - imports from submodules
"""

# Import the router from the modularized agents package (api.agents.router)
from ..api.agents.router import router

# Re-export for backward compatibility
__all__ = ['router']