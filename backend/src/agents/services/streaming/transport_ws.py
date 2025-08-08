"""
WebSocket Transport Helpers
Utility functions to send structured streaming events to clients.
"""

import json
from datetime import datetime
from typing import Any, Dict

from fastapi import WebSocket


async def send_event(ws: WebSocket, event_type: str, payload: Dict[str, Any]) -> None:
    await ws.send_text(
        json.dumps({
            "type": event_type,
            **payload,
            "timestamp": datetime.utcnow().isoformat(),
        })
    )


