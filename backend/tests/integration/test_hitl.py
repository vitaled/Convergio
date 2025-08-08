#!/usr/bin/env python3
import os, sys, pytest

_BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _BACKEND_PATH not in sys.path:
    sys.path.insert(0, _BACKEND_PATH)


@pytest.mark.skip(reason="HITL end-to-end pending API integration")
def test_hitl_end2end_placeholder():
    assert True


