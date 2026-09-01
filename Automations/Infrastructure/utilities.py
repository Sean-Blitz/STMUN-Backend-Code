import time
import random
import logging
import requests
from functools import wraps

logger = logging.getLogger(__name__)

def retry_on_http_error(max_retries=4, initial_backoff=1.0, backoff_factor=2.0):
    """
    Decorator that retries a function with exponential backoff and jitter 
    when transient HTTP or network errors occur.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_backoff
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    # Extract status code if available (handles requests & google-api-client errors)
                    status_code = getattr(getattr(exc, 'resp', None), 'status', None) or \
                                  getattr(getattr(exc, 'response', None), 'status_code', None)
                    
                    # 429 = Rate Limit, 5xx = Server Errors, or Connection Drops
                    is_retryable = status_code in (429, 500, 502, 503, 504) or isinstance(exc, (requests.ConnectionError, requests.Timeout))

                    if not is_retryable or attempt == max_retries:
                        logger.error(f"Failure in {func.__name__} (Attempt {attempt}/{max_retries}): {exc}")
                        raise exc

                    # Exponential backoff + random jitter
                    jittered_delay = delay + random.uniform(0, 0.5)
                    logger.warning(
                        f"[Attempt {attempt}/{max_retries}] {func.__name__} failed ({exc}). "
                        f"Retrying in {jittered_delay:.2f}s..."
                    )
                    time.sleep(jittered_delay)
                    delay *= backoff_factor

        return wrapper
    return decorator