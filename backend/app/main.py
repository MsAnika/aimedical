import logging
import sys
import json
from pathlib import Path
from typing import Any
from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.database import Base, engine, get_db

# ------------------------------------------------------------------
# 5️⃣  Structured JSON logging
# ------------------------------------------------------------------
class InterceptHandler(logging.Handler):
    """Intercept standard logging and emit JSON lines compatible with
    tools like Datadog, Sentry, Loki, etc."""
    def emit(self, record: logging.LogRecord) -> None:
        payload = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        extra = getattr(record, "extra", {})
        if extra:
            payload.update(extra)
        sys.stdout.write(json.dumps(payload) + "\n")

# Moved logger config to lifespan to avoid side-effects at import time
# root logger config will be set up in lifespan

# -----------------------------------------------------------------
# FastAPI app definition
# -----------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Set up logging on startup
    logging.root.handlers = []
    logging.root.addHandler(InterceptHandler())
    logging.root.setLevel(logging.INFO)
    # Create DB tables on startup for dev/demo
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title=get_settings().app_name,
    version="0.1.0",
    lifespan=lifespan,
)

media_path = Path(get_settings().media_dir)
media_path.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=media_path), name="media")

# Import route modules so that their `router` objects are available
from app.api.routes import auth, predictions, history, reports, admin  # noqa: E402

# -----------------------------------------------------------------
# CORS – 9️⃣  Restrict to known origins
# -----------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        # Add your production domain once you have one:
        # "https://your‑domain.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------
# API routes use the /api/... contract consumed by the frontend.
# -----------------------------------------------------------------
app.include_router(auth.router, tags=["auth"])
app.include_router(predictions.router, tags=["predictions"])
app.include_router(history.router, tags=["history"])
app.include_router(reports.router, tags=["reports"])
app.include_router(admin.router, tags=["admin"])

# -----------------------------------------------------------------
# 6️⃣  Prometheus‑style metrics (in‑process counters)
# -----------------------------------------------------------------
from app.metrics import add_metrics_app
add_metrics_app(app)

# -----------------------------------------------------------------
# /healthz endpoint that checks DB connectivity (no unnecessary commit)
# -----------------------------------------------------------------
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

@app.get("/api/healthz", include_in_schema=False)
def healthz(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
        db_state = "ok"
    except Exception:
        db_state = "unreachable"
    return {"status": db_state, "db": db_state}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": "AI Medical Diagnostic System"}

# -----------------------------------------------------------------
# 11️⃣  Basic rate‑limit middleware (in‑memory count per IP)
# -----------------------------------------------------------------
from collections import defaultdict
from time import monotonic

_ip_requests: defaultdict[str, list[float]] = defaultdict(list)

def check_rate_limit(ip: str, limit: int = 100, window: int = 60) -> bool:
    """Return True if the request is allowed, False if rate‑limited."""
    now = monotonic()
    timestamps = _ip_requests[ip]
    while timestamps and now - timestamps[0] > window:
        timestamps.pop(0)
    if len(timestamps) >= limit:
        return False
    timestamps.append(now)
    return True

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ip = request.client.host
        if not check_rate_limit(ip):
            return Response(
                content="Rate limit exceeded",
                status_code=429,
                headers={"Retry-After": "60"},
            )
        response = await call_next(request)
        return response

app.add_middleware(RateLimitMiddleware)