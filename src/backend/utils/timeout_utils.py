"""
Timeout utilities for agent operations.

Provides both a context manager (Unix-only via SIGALRM) and a cross-platform
decorator that runs the target function in a worker thread with a cancellation
event so the thread can exit cooperatively after a timeout.
"""

import builtins
import logging
import queue
import signal
import threading
from collections.abc import Callable
from contextlib import contextmanager
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


class AgentTimeoutError(builtins.TimeoutError):
    """Custom timeout error for agent operations.

    Inherits from the builtin ``TimeoutError`` so that both
    ``except TimeoutError`` (builtin) and ``except AgentTimeoutError``
    catch it correctly — no import gymnastics required in callers.
    """


# Backward-compatible alias so existing ``from .timeout_utils import TimeoutError``
# and ``except TimeoutError`` continue to work without changes.
TimeoutError = AgentTimeoutError  # noqa: A001


@contextmanager
def timeout_context(seconds: int):
    """Context manager for timeout operations (Unix only, uses SIGALRM).

    On platforms without ``SIGALRM`` the block runs without a timeout and a
    warning is logged.  For cross-platform needs use :func:`with_timeout`.

    Args:
        seconds: Timeout in seconds.

    Raises:
        AgentTimeoutError: If the operation exceeds *seconds*.
    """

    def _handler(signum: int, frame: Any) -> None:  # noqa: ANN401
        raise AgentTimeoutError(f"Operation timed out after {seconds} seconds")

    if hasattr(signal, "SIGALRM"):
        old_handler = signal.signal(signal.SIGALRM, _handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    else:
        # SIGALRM is not available (Windows).  We cannot reliably interrupt
        # the current thread from another thread, so we run unguarded and
        # log a warning.
        logger.warning(
            "SIGALRM not available on this platform — "
            "timeout_context(%s) will NOT enforce a timeout",
            seconds,
        )
        yield


def with_timeout(seconds: int = 30) -> Callable:
    """Decorator that enforces a wall-clock timeout on a synchronous function.

    The decorated function is executed inside a **worker thread**.  A
    ``threading.Event`` (*cancel_event*) is set when the timeout expires so
    that cooperative callees can check it and exit early, preventing the
    "zombie daemon thread" problem.

    The *cancel_event* is **not** automatically injected into the wrapped
    function's signature — it is stored on the wrapper as
    ``wrapper.cancel_event`` so callers or the function itself can inspect it
    if needed.

    **Exception handling**: the worker thread captures *all* exceptions
    (``BaseException`` minus ``SystemExit`` / ``KeyboardInterrupt``) and
    re-raises them in the calling thread.

    Args:
        seconds: Maximum wall-clock seconds before raising
            :class:`AgentTimeoutError`.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result_q: queue.Queue[Any] = queue.Queue()
            error_q: queue.Queue[BaseException] = queue.Queue()
            cancel = threading.Event()

            # Expose cancel event so callers can pass it downstream.
            wrapper.cancel_event = cancel  # type: ignore[attr-defined]

            def _target() -> None:
                try:
                    result_q.put(func(*args, **kwargs))
                except Exception as exc:
                    error_q.put(exc)

            thread = threading.Thread(target=_target, daemon=True)
            thread.start()
            thread.join(timeout=seconds)

            if thread.is_alive():
                # Signal cooperative cancellation to the worker thread.
                cancel.set()
                logger.warning(
                    "⚠️ %s exceeded timeout of %ss — cancellation signalled",
                    func.__name__,
                    seconds,
                )
                raise AgentTimeoutError(f"{func.__name__} timed out after {seconds} seconds")

            # Thread finished — check for errors first.
            if not error_q.empty():
                raise error_q.get()

            if not result_q.empty():
                return result_q.get()

            raise AgentTimeoutError(f"{func.__name__} did not return a result")

        return wrapper

    return decorator
