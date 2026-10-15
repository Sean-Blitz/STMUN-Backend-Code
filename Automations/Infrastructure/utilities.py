import errno
import logging
import random
import socket
import ssl
import time
from functools import wraps

import requests

try:  # The HTTP transport used by googleapiclient.
    import httplib2
except ImportError:  # pragma: no cover - optional transitive dependency
    httplib2 = None

try:  # Raised when an OAuth token refresh fails at the network layer.
    from google.auth.exceptions import TransportError as _GoogleAuthTransportError
except ImportError:  # pragma: no cover - optional transitive dependency
    _GoogleAuthTransportError = None

logger = logging.getLogger(__name__)

# 408 = Request Timeout, 429 = Rate Limit, 5xx = Server Errors
RETRYABLE_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})

# errno values that mean "the connection dropped or could not be reached".
# Matches the set googleapiclient itself retries on, plus unreachable hosts.
_RETRYABLE_ERRNO_NAMES = (
    "ECONNRESET",
    "ECONNABORTED",
    "EPIPE",
    "ETIMEDOUT",
    "ECONNREFUSED",
    "ENETRESET",
    "ENETDOWN",
    "ENETUNREACH",
    "EHOSTDOWN",
    "EHOSTUNREACH",
    "EAGAIN",
)
RETRYABLE_ERRNOS = frozenset(
    getattr(errno, name) for name in _RETRYABLE_ERRNO_NAMES if hasattr(errno, name)
)


def _extract_status_code(exc):
    """
    Best-effort HTTP status lookup across the exception shapes we can see.

    googleapiclient errors expose ``exc.resp.status``, requests errors expose
    ``exc.response.status_code``, and some libraries expose ``status_code``.
    """
    for attribute in ("resp", "response"):
        response = getattr(exc, attribute, None)
        if response is None:
            continue
        status = getattr(response, "status", None)
        if status is None:
            status = getattr(response, "status_code", None)
        if status is not None:
            return status
    return getattr(exc, "status_code", None)


def is_retryable(exc) -> bool:
    """
    True when an exception looks like a transient transport or server failure.

    Note that googleapiclient talks over httplib2, so the network failures it
    raises are stdlib exceptions (e.g. ``ConnectionResetError``, a subclass of
    the builtin ``ConnectionError``/``OSError``) -- *not* the ``requests``
    hierarchy. ``requests.ConnectionError`` and the builtin ``ConnectionError``
    are unrelated classes despite the shared name, so both must be checked.
    """
    if _extract_status_code(exc) in RETRYABLE_STATUS_CODES:
        return True

    if isinstance(exc, (requests.ConnectionError, requests.Timeout)):
        return True

    # stdlib network failures: ConnectionResetError, ConnectionAbortedError,
    # TimeoutError/socket.timeout, ssl.SSLError, ...
    if isinstance(exc, (ConnectionError, TimeoutError, socket.timeout, ssl.SSLError)):
        return True

    if httplib2 is not None and isinstance(exc, httplib2.HttpLib2Error):
        return True

    if _GoogleAuthTransportError is not None and isinstance(exc, _GoogleAuthTransportError):
        return True

    # Remaining OSErrors are only retryable for connection-level errnos, so
    # things like FileNotFoundError (ENOENT) still fail fast.
    if isinstance(exc, OSError) and exc.errno in RETRYABLE_ERRNOS:
        return True

    return False


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
                    retryable = is_retryable(exc)

                    if not retryable or attempt == max_retries:
                        reason = "not retryable" if not retryable else "retries exhausted"
                        logger.error(
                            f"Failure in {func.__name__} (Attempt {attempt}/{max_retries}, "
                            f"{reason}): {exc}"
                        )
                        raise

                    # Exponential backoff + random jitter
                    jittered_delay = delay + random.uniform(0, 0.5)
                    logger.warning(
                        f"[Attempt {attempt}/{max_retries}] {func.__name__} failed ({exc!r}). "
                        f"Retrying in {jittered_delay:.2f}s..."
                    )
                    time.sleep(jittered_delay)
                    delay *= backoff_factor

        return wrapper
    return decorator
