"""Send Notification Use Case."""
from dataclasses import dataclass
from uuid import UUID, uuid4
from typing import Optional

from notification_service.domain.entities import (
    Notification,
    NotificationType,
    NotificationStatus,
)
from notification_service.application.ports.output import INotificationRepository, IEmailSender
from notification_service.domain.exceptions import EmailSendError


@dataclass
class SendNotificationInput:
    user_id: UUID
    recipient: str
    subject: str
    body: str
    job_id: Optional[UUID] = None


@dataclass
class SendNotificationOutput:
    id: UUID
    status: NotificationStatus
    error_message: Optional[str] = None


class SendNotificationUseCase:
    """Use case for sending notifications."""

    def __init__(
        self,
        notification_repository: INotificationRepository,
        email_sender: IEmailSender,
    ):
        self._repository = notification_repository
        self._email_sender = email_sender

    async def execute(self, input_data: SendNotificationInput) -> SendNotificationOutput:
        """Send a notification email."""
        notification = Notification(
            id=uuid4(),
            user_id=input_data.user_id,
            job_id=input_data.job_id,
            type=NotificationType.EMAIL,
            status=NotificationStatus.PENDING,
            recipient=input_data.recipient,
            subject=input_data.subject,
            body=input_data.body,
        )

        await self._repository.save(notification)

        try:
            await self._email_sender.send_email(
                to=input_data.recipient,
                subject=input_data.subject,
                body=input_data.body,
            )
            notification.mark_sent()
        except Exception as e:
            notification.mark_failed(str(e))
            await self._repository.update(notification)
            raise EmailSendError(f"Failed to send email: {e}")

        await self._repository.update(notification)

        return SendNotificationOutput(
            id=notification.id,
            status=notification.status,
            error_message=notification.error_message,
        )
