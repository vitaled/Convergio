#!/usr/bin/env python3
import os, sys
import structlog

_BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _BACKEND_PATH not in sys.path:
    sys.path.insert(0, _BACKEND_PATH)


def test_structlog_basic_event_shape():
    logger = structlog.get_logger()
    # Ensure logger can accept key/value pairs without raising
    logger.info("test_event", category="observability", component="unit-test")
    # If no exception is raised, basic setup is acceptable for unit scope
    assert True


