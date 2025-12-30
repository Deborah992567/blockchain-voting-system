import time
from fastapi import Request
from app.utils.logger import logger as base_logger

logger = base_logger.bind(context="deps.timing")

async def timing_dependency(request: Request):
    """A dependency that measures handler processing time (before/after the path operation).

    Use as a global dependency to record per-endpoint server processing time.
    """
    start = time.monotonic()
    try:
        yield
    finally:
        elapsed_ms = (time.monotonic() - start) * 1000
        endpoint = request.scope.get('endpoint')
        ep_name = getattr(endpoint, '__name__', str(endpoint)) if endpoint else '<unknown>'
        logger.info("handler_time", method=request.method, path=str(request.url.path), endpoint=ep_name, handler_time_ms=round(elapsed_ms, 2))
