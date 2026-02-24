"""Notification Entity."""
from datetime import UTC, datetime
from enum import Enum
from typing import Optional
from uuid import UUID


class NotificationType(str, Enum):
    """Type of notification."""
    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"


class NotificationStatus(str, Enum):
    """Status of notification."""
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class Notification:
    """Notification Entity."""

    def __init__(
        self,
        id: UUID,
        user_id: UUID,
        job_id: Optional[UUID],
        type: NotificationType,
        status: NotificationStatus,
        recipient: str,
        subject: Optional[str],
        body: Optional[str],
        error_message: Optional[str] = None,
        sent_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.user_id = user_id
        self.job_id = job_id
        self.type = type
        self.status = status
        self.recipient = recipient
        self.subject = subject
        self.body = body
        self.error_message = error_message
        self.sent_at = sent_at
        self.created_at = created_at or datetime.now(UTC)

    def mark_sent(self) -> None:
        """Mark notification as sent."""
        self.status = NotificationStatus.SENT
        self.sent_at = datetime.now(UTC)

    def mark_failed(self, error_message: str) -> None:
        """Mark notification as failed."""
        self.status = NotificationStatus.FAILED
        self.error_message = error_message

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Notification):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
