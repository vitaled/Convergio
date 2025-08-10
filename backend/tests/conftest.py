import os
import re
import time
import pytest

from .utils.transcript import TranscriptLogger


def _sanitize(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", name)


@pytest.fixture
def transcript_logger(request):
    """
    Provides a TranscriptLogger that writes to repo-root logs/ folder with
    filename: <test_name>-<YYYYMMDD_HHMMSS>.log
    """
    test_name = request.node.name or "test"
    ts = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    filename = f"{_sanitize(test_name)}-{ts}.log"
    # logs/ is at repo root; tests run from backend/ so go up one and then into logs
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    logs_dir = os.path.join(repo_root, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    path = os.path.join(logs_dir, filename)

    logger = TranscriptLogger(path, test_name)
    yield logger
    logger.close("completed")
