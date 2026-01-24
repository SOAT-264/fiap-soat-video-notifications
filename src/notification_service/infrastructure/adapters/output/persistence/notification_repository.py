"""SQLAlchemy Notification Repository."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from notification_service.domain.entities import (
    Notification,
    NotificationType,
    NotificationStatus,
)
from notification_service.application.ports.output import INotificationRepository
from notification_service.infrastructure.adapters.output.persistence.models import NotificationModel


class SQLAlchemyNotificationRepository(INotificationRepository):
    """SQLAlchemy implementation of notification repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, notification: Notification) -> Notification:
        """Save a notification."""
        model = NotificationModel(
            id=notification.id,
            user_id=notification.user_id,
            job_id=notification.job_id,
            type=notification.type,
            status=notification.status,
            recipient=notification.recipient,
            subject=notification.subject,
            body=notification.body,
            error_message=notification.error_message,
            sent_at=notification.sent_at,
            created_at=notification.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return notification

    async def find_by_id(self, notification_id: UUID) -> Optional[Notification]:
        """Find notification by ID."""
        result = await self._session.execute(
            select(NotificationModel).where(NotificationModel.id == notification_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_user_id(
        self, user_id: UUID, skip: int = 0, limit: int = 10
    ) -> List[Notification]:
        """Find notifications by user ID."""
        result = await self._session.execute(
            select(NotificationModel)
            .where(NotificationModel.user_id == user_id)
            .order_by(NotificationModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def update(self, notification: Notification) -> Notification:
        """Update a notification."""
        result = await self._session.execute(
            select(NotificationModel).where(NotificationModel.id == notification.id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.status = notification.status
            model.error_message = notification.error_message
            model.sent_at = notification.sent_at
            await self._session.flush()
        return notification

    def _to_entity(self, model: NotificationModel) -> Notification:
        """Convert model to entity."""
        return Notification(
            id=model.id,
            user_id=model.user_id,
            job_id=model.job_id,
            type=model.type,
            status=model.status,
            recipient=model.recipient,
            subject=model.subject,
            body=model.body,
            error_message=model.error_message,
            sent_at=model.sent_at,
            created_at=model.created_at,
        )
