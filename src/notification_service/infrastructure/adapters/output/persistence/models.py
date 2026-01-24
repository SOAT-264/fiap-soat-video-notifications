"""SQLAlchemy models for notifications."""
from datetime import datetime
from uuid import UUID as PyUUID

from sqlalchemy import Column, String, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import UUID

from notification_service.infrastructure.adapters.output.persistence.database import Base
from notification_service.domain.entities import NotificationType, NotificationStatus


class NotificationModel(Base):
    """SQLAlchemy model for notifications table."""
    
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    type = Column(
        Enum(NotificationType, name="notification_type", create_type=False),
        nullable=False,
        default=NotificationType.EMAIL,
    )
    status = Column(
        Enum(NotificationStatus, name="notification_status", create_type=False),
        nullable=False,
        default=NotificationStatus.PENDING,
        index=True,
    )
    recipient = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=True)
    body = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
