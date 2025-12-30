try:
    from prometheus_client import Histogram, generate_latest, CONTENT_TYPE_LATEST
    METRICS_ENABLED = True
except Exception:
    METRICS_ENABLED = False

if METRICS_ENABLED:
    request_latency_histogram = Histogram('http_request_latency_seconds', 'HTTP request latency in seconds', ['method', 'endpoint', 'status_code'])

    def observe_request(method, endpoint, status_code, seconds):
        request_latency_histogram.labels(method=method, endpoint=endpoint, status_code=str(status_code)).observe(seconds)

    def metrics_response():
        return generate_latest()
else:
    def observe_request(method, endpoint, status_code, seconds):
        pass

    def metrics_response():
        raise RuntimeError('Prometheus client not installed')
