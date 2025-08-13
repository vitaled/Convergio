"""Compatibility shim for legacy tests expecting WebSearchService."""

from __future__ import annotations
from typing import Any, Dict


class WebSearchService:
    def __init__(self) -> None:
        pass

    async def search(self, query: str) -> Dict[str, Any]:
        return {"query": query, "results": []}
