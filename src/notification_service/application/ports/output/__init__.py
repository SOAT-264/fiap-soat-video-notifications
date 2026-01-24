"""Output ports."""
from notification_service.application.ports.output.notification_repository import INotificationRepository
from notification_service.application.ports.output.email_sender import IEmailSender

__all__ = ["INotificationRepository", "IEmailSender"]
