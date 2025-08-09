#!/usr/bin/env python3
"""
Lightweight tracing utilities for agents. Provides a no-op start_span
context manager compatible with usage across the codebase.
"""
from contextlib import contextmanager
from typing import Dict, Any, Optional

@contextmanager
def start_span(name: str, attributes: Optional[Dict[str, Any]] = None):
    """No-op tracing span for local/test environments."""
    try:
        yield
    finally:
        pass


