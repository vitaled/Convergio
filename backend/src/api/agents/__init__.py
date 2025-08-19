"""
AI Agents API Module
Modularized from monolithic agents.py file
"""

from .router import router
from agents.utils.config import get_settings

# Make settings available for testing monkeypatch
settings = get_settings()

__all__ = ['router', 'settings']