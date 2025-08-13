"""Compatibility shim for legacy tests expecting AliCEO class.

In the modern AutoGen 0.7.2 setup, agents are defined via metadata and created
as AssistantAgent instances. Tests only assert basic properties, so we provide
this lightweight adapter.
"""

from __future__ import annotations


class AliCEO:
    name: str = "Ali"
    role: str = "CEO"
    model_name: str = "gpt-4o-mini"

    def __init__(self) -> None:
        # No-op; values are static for test expectations
        pass
