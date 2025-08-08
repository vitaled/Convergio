#!/usr/bin/env python3
import os, sys

_BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _BACKEND_PATH not in sys.path:
    sys.path.insert(0, _BACKEND_PATH)


def test_approval_store_happy_path():
    from src.agents.services.hitl.approval_store import ApprovalStore
    store = ApprovalStore()
    ap = store.create("ap-1", "conv-1", "u1", {"action": "publish"})
    assert ap.status == "pending"
    assert store.get("ap-1").approval_id == "ap-1"
    ap2 = store.approve("ap-1")
    assert ap2 and ap2.status == "approved"
    ap3 = store.deny("ap-1")
    assert ap3 and ap3.status == "denied"


