"""6️⃣  Simple in‑process Prometheus‑style metrics."""
from fastapi import FastAPI, Request, Response
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse
import time

# ------------------------------------------------------------------
# Counters we expose
# ------------------------------------------------------------------
REQUEST_COUNT = 0
PREDICTION_COUNT = {"pneumonia": 0, "skin": 0, "diabetes": 0, "heart": 0}
MODEL_DEMO_COUNT = 0   # how many predictions were served in demo mode


# -----------------------------------------------------------------
# Middleware that increments the counters on every request
# -----------------------------------------------------------------
class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        global REQUEST_COUNT
        REQUEST_COUNT += 1

        response = await call_next(request)

        # Track demo predictions by checking response headers
        # (set by prediction endpoints via a response header)
        if response.headers.get("x-demo") == "true":
            global MODEL_DEMO_COUNT
            MODEL_DEMO_COUNT += 1

        return response


# -----------------------------------------------------------------
# FastAPI app wiring
# -----------------------------------------------------------------
def add_metrics_app(app: FastAPI) -> None:
    """Add the middleware and a /metrics endpoint."""
    app.add_middleware(MetricsMiddleware)

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        payload = {
            "requests_total": REQUEST_COUNT,
            "predictions_by_disease": PREDICTION_COUNT,
            "demo_predictions": MODEL_DEMO_COUNT,
        }
        lines = [
            '# HELP requests_total Total number of HTTP requests',
            '# TYPE requests_total counter',
            f'requests_total {payload["requests_total"]}',
            '# HELP predictions_by_disease Predictions per disease',
            '# TYPE predictions_by_disease counter',
            f'predictions_by_disease{{disease="pneumonia"}} {payload["predictions_by_disease"]["pneumonia"]}',
            f'predictions_by_disease{{disease="skin"}}       {payload["predictions_by_disease"]["skin"]}',
            f'predictions_by_disease{{disease="diabetes"}} {payload["predictions_by_disease"]["diabetes"]}',
            f'predictions_by_disease{{disease="heart"}}       {payload["predictions_by_disease"]["heart"]}',
            '# HELP demo_predictions Number of demo‑mode predictions',
            '# TYPE demo_predictions counter',
            f'demo_predictions {payload["demo_predictions"]}',
        ]
        return PlainTextResponse("\n".join(lines), media_type="text/plain; version=0.0.4; charset=utf-8")