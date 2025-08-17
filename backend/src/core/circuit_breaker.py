"""
Minimal circuit breaker stub for test compatibility.
Provides a no-op decorator and simple CircuitBreaker class interface.
"""
from typing import Callable, TypeVar, Any

F = TypeVar("F", bound=Callable[..., Any])


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

    def call(self, func: F) -> F:
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper  # type: ignore


def circuit_breaker(failure_threshold: int = 5, recovery_timeout: float = 30.0):
    """No-op decorator for compatibility in tests."""
    cb = CircuitBreaker(failure_threshold, recovery_timeout)

    def decorator(func: F) -> F:
        return cb.call(func)

    return decorator
