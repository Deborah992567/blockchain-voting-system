import time
from starlette.requests import Request
from starlette.responses import Response
from app.utils.logger import logger as base_logger
from app.metrics import observe_request

logger = base_logger.bind(context="middleware.request_timing")

async def request_timing_middleware(request: Request, call_next):
    """Middleware to log request latency and server processing time per endpoint.

    Adds headers: X-Process-Time-ms
    Logs: method, path, status_code, process_time_ms, endpoint
    """
    start = time.monotonic()
    try:
        response: Response = await call_next(request)
        status = response.status_code
    except Exception as exc:
        status = 500
        # compute elapsed before re-raising
        elapsed_ms = (time.monotonic() - start) * 1000
        endpoint = _get_endpoint_name(request)
        logger.exception("Request failed", method=request.method, path=str(request.url.path), endpoint=endpoint, status_code=status, process_time_ms=round(elapsed_ms, 2))
        raise

    elapsed_ms = (time.monotonic() - start) * 1000
    endpoint = _get_endpoint_name(request)

    # attach timing header for clients and internal debugging
    try:
        response.headers['X-Process-Time-ms'] = f"{round(elapsed_ms,2)}"
    except Exception:
        # headers may not be writable in some response types
        pass

    logger.info("http_request", method=request.method, path=str(request.url.path), endpoint=endpoint, status_code=status, process_time_ms=round(elapsed_ms, 2))
    try:
        observe_request(request.method, endpoint, status, elapsed_ms / 1000.0)
    except Exception:
        pass
    return response


def _get_endpoint_name(request: Request) -> str:
    try:
        ep = request.scope.get('endpoint')
        if ep is None:
            return "<unknown>"
        if hasattr(ep, '__name__'):
            return ep.__name__
        return str(ep)
    except Exception:
        return "<unknown>"
