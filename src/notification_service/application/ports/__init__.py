"""Application ports."""
from notification_service.application.ports.output import INotificationRepository, IEmailSender

__all__ = ["INotificationRepository", "IEmailSender"]
