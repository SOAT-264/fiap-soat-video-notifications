"""Notification routes."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import ConfigDict, BaseModel

from notification_service.infrastructure.adapters.output.persistence import (
    get_session,
    SQLAlchemyNotificationRepository,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    job_id: Optional[UUID] = None
    type: str
    status: str
    recipient: str
    subject: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


def get_notification_repository(
    session: AsyncSession = Depends(get_session),
) -> SQLAlchemyNotificationRepository:
    return SQLAlchemyNotificationRepository(session)


@router.get("", response_model=List[NotificationResponse])
async def list_notifications(
    user_id: UUID = Query(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    repository: SQLAlchemyNotificationRepository = Depends(get_notification_repository),
) -> List[NotificationResponse]:
    """List notifications for a user."""
    notifications = await repository.find_by_user_id(user_id, skip, limit)
    return [
        NotificationResponse(
            id=n.id,
            user_id=n.user_id,
            job_id=n.job_id,
            type=n.type.value,
            status=n.status.value,
            recipient=n.recipient,
            subject=n.subject,
            sent_at=n.sent_at,
            created_at=n.created_at,
        )
        for n in notifications
    ]
