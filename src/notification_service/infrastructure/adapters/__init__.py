"""Infrastructure adapters."""
from notification_service.infrastructure.adapters.input import app
from notification_service.infrastructure.adapters.output import (
    get_session,
    get_session_context,
    SQLAlchemyNotificationRepository,
    SMTPEmailSender,
)

__all__ = [
    "app",
    "get_session",
    "get_session_context",
    "SQLAlchemyNotificationRepository",
    "SMTPEmailSender",
]
