import os
import json
from copy import deepcopy
from datetime import datetime
from typing import Any, Optional, Mapping


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


class TranscriptLogger:
    """
    Lightweight, human-readable transcript writer for tests.

    Produces append-only UTF-8 logs with clear sections and timestamps so
    humans can follow interactions between agents, DB/vector, and OpenAI.
    """

    def __init__(self, path: str, test_name: str):
        self.path = path
        self.test_name = test_name
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._write_line(f"# Test transcript | {self.test_name}")
        self._write_line(f"# Started: {_now()}")
        self._write_line("")

    # Public API
    def section(self, title: str, payload: Optional[Any] = None) -> None:
        self._write_line(f"## {title} | {_now()}")
        if payload is not None:
            try:
                self._write_line(json.dumps(payload, ensure_ascii=False, indent=2))
            except Exception:
                self._write_line(str(payload))
        self._write_line("")

    def http(self,
             name: str,
             method: str,
             url: str,
             request_json: Optional[Any],
             status: int,
             response_json: Optional[Any],
             duration_s: Optional[float] = None) -> None:
        self._write_line(f"### HTTP {name} | {_now()}")
        self._write_line(f"- Method: {method}")
        self._write_line(f"- URL: {url}")
        if duration_s is not None:
            self._write_line(f"- Duration: {duration_s:.2f}s")
        if request_json is not None:
            try:
                safe_request = self._redact(request_json)
                self._write_line("- Request:")
                self._write_line(self._indent(json.dumps(safe_request, ensure_ascii=False, indent=2)))
            except Exception:
                self._write_line("- Request: [unserializable]")
        self._write_line(f"- Status: {status}")
        if response_json is not None:
            try:
                safe_response = self._redact(response_json)
                self._write_line("- Response:")
                self._write_line(self._indent(json.dumps(safe_response, ensure_ascii=False, indent=2)))
            except Exception:
                self._write_line("- Response: [unserializable]")
        self._write_line("")

    def note(self, text: str) -> None:
        self._write_line(f"- {text}")

    def close(self, status: str = "completed") -> None:
        self._write_line("")
        self._write_line(f"# Finished: {_now()} | Status: {status}")

    # Internals
    def _write_line(self, s: str) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(s + "\n")

    @staticmethod
    def _indent(s: str, n: int = 2) -> str:
        pad = " " * n
        return "\n".join(pad + line for line in s.splitlines())

    def _redact(self, obj: Any) -> Any:
        """Recursively redact secrets from mappings/lists/strings."""
        secret_keys = {
            "openai_api_key", "openai", "api_key", "apikey", "authorization",
            "bearer", "token", "password", "secret", "access_token", "refresh_token"
        }

        def redact_str(val: str) -> str:
            if len(val) <= 8:
                return "***"
            # keep first 4 and last 2 chars
            return val[:4] + "***" + val[-2:]

        def walk(x: Any) -> Any:
            try:
                if isinstance(x, str):
                    lx = x.lower()
                    if "sk-" in lx or "api_key" in lx or "bearer " in lx:
                        return redact_str(x)
                    return x
                if isinstance(x, Mapping):
                    y = {}
                    for k, v in x.items():
                        if str(k).lower() in secret_keys:
                            if isinstance(v, str):
                                y[k] = redact_str(v)
                            else:
                                y[k] = "***"
                        else:
                            y[k] = walk(v)
                    return y
                elif isinstance(x, list):
                    return [walk(i) for i in x]
                else:
                    return x
            except Exception:
                return "***"

        try:
            return walk(deepcopy(obj))
        except Exception:
            return "***"
