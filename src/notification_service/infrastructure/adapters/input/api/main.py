"""FastAPI Main Application."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from notification_service.infrastructure.config import get_settings
from notification_service.infrastructure.adapters.input.api.routes import health_router, notification_router
from notification_service.infrastructure.adapters.output.cache import close_redis

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    yield
    await close_redis()


app = FastAPI(
    title="Notification Service",
    description="Email notification microservice",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(notification_router)
app.mount("/metrics", make_asgi_app())


@app.get("/")
async def root():
    return {
        "service": settings.SERVICE_NAME,
        "version": "0.1.0",
        "status": "running",
    }
