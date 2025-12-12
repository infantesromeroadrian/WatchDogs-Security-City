"""
Timeout utilities for agent operations.
"""
import logging
import signal
from contextlib import contextmanager
from typing import Any, Callable
from functools import wraps

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Custom timeout error for agent operations."""
    pass


@contextmanager
def timeout_context(seconds: int):
    """
    Context manager for timeout operations.
    
    Args:
        seconds: Timeout in seconds
        
    Raises:
        TimeoutError: If operation exceeds timeout
    """
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    # Set signal handler (Unix only)
    if hasattr(signal, 'SIGALRM'):
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    else:
        # Windows: use threading.Timer as fallback
        import threading
        
        def timeout_callback():
            raise TimeoutError(f"Operation timed out after {seconds} seconds")
        
        timer = threading.Timer(seconds, timeout_callback)
        timer.start()
        try:
            yield
        finally:
            timer.cancel()


def with_timeout(seconds: int = 30):
    """
    Decorator to add timeout to functions.
    
    Note: For Windows compatibility, this uses threading.Timer.
    For production, consider using asyncio with proper timeout handling.
    
    Args:
        seconds: Timeout in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            import threading
            import queue
            
            result_queue = queue.Queue()
            exception_queue = queue.Queue()
            
            def target():
                try:
                    result = func(*args, **kwargs)
                    result_queue.put(result)
                except Exception as e:
                    exception_queue.put(e)
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout=seconds)
            
            if thread.is_alive():
                logger.warning(f"⚠️ {func.__name__} exceeded timeout of {seconds}s")
                raise TimeoutError(f"{func.__name__} timed out after {seconds} seconds")
            
            if not exception_queue.empty():
                raise exception_queue.get()
            
            if not result_queue.empty():
                return result_queue.get()
            
            raise TimeoutError(f"{func.__name__} did not return a result")
        
        return wrapper
    return decorator

