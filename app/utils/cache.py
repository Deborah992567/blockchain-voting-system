import json
import requests
from redis import Redis
from app.config import settings
from app.utils.logger import logger as base_logger
from datetime import datetime, timedelta
import threading

# Metrics: try to use prometheus_client if available, otherwise use simple counters
try:
    if settings.METRICS_ENABLED:
        from prometheus_client import Counter
        cache_hits_total = Counter("cache_hits_total", "Cache hits")
        cache_misses_total = Counter("cache_misses_total", "Cache misses")
        cache_fallback_uses_total = Counter("cache_fallback_uses_total", "Cache fallback uses")
    else:
        raise Exception("Metrics disabled")
except Exception:
    # fallback simple counters
    cache_hits_total = 0
    cache_misses_total = 0
    cache_fallback_uses_total = 0
    _metrics_lock = threading.Lock()

logger = base_logger.bind(context="cache")


def _make_client() -> Redis:
    try:
        client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        # quick connectivity check
        client.ping()
        logger.info("Connected to Redis", url=settings.REDIS_URL)
        return client
    except Exception:
        logger.exception("Failed to connect to Redis; falling back to in-memory cache")
        return None


_client = None
_use_fallback = False
_fallback_store: dict = {}
_fallback_lock = None

def _init_fallback():
    global _fallback_lock, _fallback_store, _use_fallback, _fallback_alert_sent
    if _fallback_lock is None:
        _fallback_lock = threading.Lock()
        _fallback_store = {}
        _use_fallback = True
        _fallback_alert_sent = False
        logger.warning("Initialized in-memory fallback cache")
        # send one-time alert if configured
        if settings.SLACK_WEBHOOK_URL:
            try:
                _send_slack_alert("Redis unavailable: using in-memory fallback cache")
                _fallback_alert_sent = True
            except Exception:
                logger.exception("Failed to send fallback alert")


def _send_slack_alert(message: str):
    """Send a one-off Slack webhook alert if configured."""
    if not settings.SLACK_WEBHOOK_URL:
        logger.debug("No Slack webhook configured; skipping alert")
        return
    payload = {"text": message}
    try:
        resp = requests.post(settings.SLACK_WEBHOOK_URL, json=payload, timeout=5)
        if resp.status_code >= 400:
            logger.error("Slack webhook returned non-200", status_code=resp.status_code, body=resp.text)
        else:
            logger.info("Sent Slack fallback alert")
    except Exception:
        logger.exception("Failed to post Slack webhook")


def client() -> Redis:
    global _client
    if _client is None:
        _client = _make_client()
        if _client is None:
            # initialize fallback store
            _init_fallback()
    return _client


def _inc_hit():
    global cache_hits_total
    try:
        if isinstance(cache_hits_total, int):
            with _metrics_lock:
                globals()["cache_hits_total"] += 1
        else:
            cache_hits_total.inc()
    except Exception:
        pass


def _inc_miss():
    global cache_misses_total
    try:
        if isinstance(cache_misses_total, int):
            with _metrics_lock:
                globals()["cache_misses_total"] += 1
        else:
            cache_misses_total.inc()
    except Exception:
        pass


def _inc_fallback():
    global cache_fallback_uses_total
    try:
        if isinstance(cache_fallback_uses_total, int):
            with _metrics_lock:
                globals()["cache_fallback_uses_total"] += 1
        else:
            cache_fallback_uses_total.inc()
    except Exception:
        pass


def get_metrics():
    """Return dict of current metric values (for tests/inspection)."""
    try:
        if isinstance(cache_hits_total, int):
            with _metrics_lock:
                return {
                    "cache_hits_total": cache_hits_total,
                    "cache_misses_total": cache_misses_total,
                    "cache_fallback_uses_total": cache_fallback_uses_total,
                }
        else:
            return {
                "cache_hits_total": cache_hits_total._value.get(),
                "cache_misses_total": cache_misses_total._value.get(),
                "cache_fallback_uses_total": cache_fallback_uses_total._value.get(),
            }
    except Exception:
        return {}


def get(key: str):
    try:
        c = client()
        if c is None:
            # fallback to in-memory
            if not _use_fallback:
                return None
            _inc_fallback()
            with _fallback_lock:
                entry = _fallback_store.get(key)
                if not entry:
                    _inc_miss()
                    return None
                value, expires_at = entry
                if expires_at is not None and expires_at < int(datetime.utcnow().timestamp()):
                    del _fallback_store[key]
                    _inc_miss()
                    return None
                    _inc_hit()
                    return value

        val = c.get(key)
        if val is None:
            _inc_miss()
            return None
        try:
            _inc_hit()
            return json.loads(val)
        except Exception:
            _inc_hit()
            return val
    except Exception:
        logger.exception("Redis GET failed", key=key)
        return None


def set(key: str, value, ex: int | None = None):
    try:
        c = client()
        v = json.dumps(value) if not isinstance(value, str) else value
        if c is None:
            if not _use_fallback:
                return
            # store with expiry timestamp
            expires_at = None
            if ex is not None:
                expires_at = int((datetime.utcnow() + timedelta(seconds=ex)).timestamp())
            with _fallback_lock:
                _fallback_store[key] = (value, expires_at)
            _inc_fallback()
            logger.debug("Fallback cache SET", key=key, ex=ex)
            return

        c.set(key, v, ex=ex)
        logger.debug("Redis SET", key=key, ex=ex)
    except Exception:
        logger.exception("Redis SET failed", key=key)


def delete(key: str):
    try:
        c = client()
        if c is None:
            if not _use_fallback:
                return
            with _fallback_lock:
                _fallback_store.pop(key, None)
            _inc_fallback()
            logger.debug("Fallback cache DEL", key=key)
            return
        c.delete(key)
        logger.debug("Redis DEL", key=key)
    except Exception:
        logger.exception("Redis DEL failed", key=key)
