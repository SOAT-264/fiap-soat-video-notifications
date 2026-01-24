"""Output adapters."""
from notification_service.infrastructure.adapters.output.persistence import (
    get_session,
    get_session_context,
    Base,
    SQLAlchemyNotificationRepository,
)
from notification_service.infrastructure.adapters.output.cache import get_redis, close_redis
from notification_service.infrastructure.adapters.output.email import SMTPEmailSender

__all__ = [
    "get_session",
    "get_session_context",
    "Base",
    "SQLAlchemyNotificationRepository",
    "get_redis",
    "close_redis",
    "SMTPEmailSender",
]
