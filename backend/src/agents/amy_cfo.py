"""Compatibility shim for legacy tests expecting AmyCFO class."""

from __future__ import annotations


class AmyCFO:
    name: str = "Amy"
    role: str = "CFO"
    model_name: str = "gpt-4o-mini"

    def __init__(self) -> None:
        pass
