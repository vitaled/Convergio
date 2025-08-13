"""
Lightweight transcript logger used by tests to record per-test activity.

The tests' conftest expects a `TranscriptLogger` class with a constructor
accepting (path, test_name) and a `close(status: str)` method. We also provide
simple `log(msg)` and `section(title)` helpers for potential future use.
"""

from __future__ import annotations

import datetime as _dt
import io
import os
from typing import Optional


class TranscriptLogger:
    def __init__(self, path: str, test_name: str) -> None:
        # Ensure parent directory exists (conftest already does this, but be safe)
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # Open the file in append mode to avoid clobbering if recreated
        self._fp: io.TextIOWrapper = open(path, "a", encoding="utf-8")
        self._closed: bool = False
        self._path: str = path
        self._test_name: str = test_name

        ts = _dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        self._write_line(f"=== Transcript start: {test_name} @ {ts} ===")

    def _write_line(self, line: str) -> None:
        if self._closed:
            return
        self._fp.write(line.rstrip("\n") + "\n")
        self._fp.flush()

    def log(self, message: str) -> None:
        now = _dt.datetime.utcnow().strftime("%H:%M:%S")
        self._write_line(f"[{now}] {message}")

    def section(self, title: str) -> None:
        self._write_line("")
        self._write_line(f"--- {title} ---")

    def close(self, status: Optional[str] = None) -> None:
        if self._closed:
            return
        ts = _dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        suffix = f" status={status}" if status else ""
        self._write_line(f"=== Transcript end: {self._test_name} @ {ts}{suffix} ===")
        try:
            self._fp.close()
        finally:
            self._closed = True
