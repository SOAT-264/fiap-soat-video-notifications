"""API Routes."""
from notification_service.infrastructure.adapters.input.api.routes.health_routes import (
    router as health_router,
)
from notification_service.infrastructure.adapters.input.api.routes.notification_routes import (
    router as notification_router,
)

__all__ = ["health_router", "notification_router"]
