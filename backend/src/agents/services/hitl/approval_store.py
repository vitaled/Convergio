"""
HITL Approval Store
Minimal in-memory approval tracking with optional Redis backing (future).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Any


@dataclass
class Approval:
    approval_id: str
    conversation_id: str
    user_id: str
    status: str  # pending | approved | denied
    payload: Dict[str, Any]
    created_at: str
    updated_at: str


class ApprovalStore:
    def __init__(self):
        self._store: Dict[str, Approval] = {}

    # Backward/alt-compatible API used by tests and orchestrator
    def request_approval(self, request_id: str, user_id: str, action: str, metadata: Dict[str, Any]) -> Approval:  # type: ignore[override]
        payload = {"action": action, **(metadata or {})}
        return self.create(approval_id=request_id, conversation_id=request_id, user_id=user_id, payload=payload)

    def create(self, approval_id: str, conversation_id: str, user_id: str, payload: Dict[str, Any]) -> Approval:
        now = datetime.utcnow().isoformat()
        approval = Approval(
            approval_id=approval_id,
            conversation_id=conversation_id,
            user_id=user_id,
            status="pending",
            payload=payload,
            created_at=now,
            updated_at=now,
        )
        self._store[approval_id] = approval
        return approval

    def get(self, approval_id: str) -> Optional[Approval]:
        return self._store.get(approval_id)

    def approve(self, approval_id: str) -> Optional[Approval]:
        ap = self._store.get(approval_id)
        if not ap:
            return None
        ap.status = "approved"
        ap.updated_at = datetime.utcnow().isoformat()
        return ap

    def deny(self, approval_id: str) -> Optional[Approval]:
        ap = self._store.get(approval_id)
        if not ap:
            return None
        ap.status = "denied"
        ap.updated_at = datetime.utcnow().isoformat()
        return ap

    def clear(self) -> None:
        self._store.clear()


