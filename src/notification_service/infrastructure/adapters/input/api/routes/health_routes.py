"""Health check routes."""
from datetime import UTC, datetime
from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "notification-service",
        "timestamp": datetime.now(UTC).isoformat(),
    }
