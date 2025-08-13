import os
import re
import sys
import time
import pytest

# Ensure tests/utils is importable even when tests isn't a package
_THIS_DIR = os.path.dirname(__file__)
_UTILS_DIR = os.path.join(_THIS_DIR, "utils")
if _UTILS_DIR not in sys.path:
    sys.path.insert(0, _UTILS_DIR)
from transcript import TranscriptLogger


def _sanitize(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", name)


def _make_logger(request) -> TranscriptLogger:
    test_name = request.node.name or "test"
    ts = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    filename = f"{_sanitize(test_name)}-{ts}.log"
    # logs/ is at repo root; tests run from backend/ so go up one and then into logs
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    logs_dir = os.path.join(repo_root, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    path = os.path.join(logs_dir, filename)
    return TranscriptLogger(path, test_name)


@pytest.fixture(autouse=True)
def _auto_transcript_logger(request):
    """Create a transcript for every test automatically."""
    logger = _make_logger(request)
    # Attach so other fixtures/tests can reuse
    setattr(request.node, "_transcript_logger", logger)
    yield
    logger.close("completed")


@pytest.fixture
def transcript_logger(request) -> TranscriptLogger:
    """Return the per-test TranscriptLogger created by the autouse fixture."""
    existing = getattr(request.node, "_transcript_logger", None)
    if existing is not None:
        return existing
    # Fallback (should not happen): create one
    return _make_logger(request)
