from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from backend.dataBase.config import get_settings
from backend.rate_limit import limiter
from backend.services.ip_service import is_ip_blocked
from backend.handlers.prediction_handler import start_monitor, stop_monitor
from backend.routers import dashboard
from backend.routers import settings as settings_router
from backend.routers import security_ops
from backend.routers import pages
from backend.routers import agent

_cfg = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_monitor()
    yield
    stop_monitor()


app = FastAPI(
    title="Sentinel IDS",
    description="Intelligent Intrusion Detection System",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_origins = [o.strip() for o in _cfg.ALLOWED_ORIGINS.split(",") if o.strip()]
_hosts = [h.strip() for h in _cfg.ALLOWED_HOSTS.split(",") if h.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins if _origins != ["*"] else ["*"],
    allow_credentials=_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(dashboard.router)
app.include_router(settings_router.router)
app.include_router(security_ops.router)
app.include_router(pages.router)
app.include_router(agent.router)


@app.middleware("http")
async def check_blocked_ips(request: Request, call_next):
    path = request.url.path
    if (
        path.startswith("/static")
        or path.startswith("/docs")
        or path.startswith("/redoc")
        or path.startswith("/openapi")
        or path.startswith("/api/ws")
        or path.startswith("/ws")
    ):
        return await call_next(request)

    client_ip = request.client.host if request.client else None
    if client_ip and await is_ip_blocked(client_ip):
        return JSONResponse(
            status_code=403,
            content={"detail": "Access denied."},
        )

    return await call_next(request)
