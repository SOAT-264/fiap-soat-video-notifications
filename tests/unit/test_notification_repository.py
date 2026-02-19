from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from notification_service.domain.entities import Notification, NotificationStatus, NotificationType
from notification_service.infrastructure.adapters.output.persistence.models import NotificationModel
from notification_service.infrastructure.adapters.output.persistence.notification_repository import (
    SQLAlchemyNotificationRepository,
)


def build_notification() -> Notification:
    return Notification(
        id=uuid4(),
        user_id=uuid4(),
        job_id=uuid4(),
        type=NotificationType.EMAIL,
        status=NotificationStatus.PENDING,
        recipient="user@example.com",
        subject="subject",
        body="body",
        created_at=datetime.utcnow(),
    )


@pytest.mark.asyncio
async def test_save_adds_model_and_flushes() -> None:
    session = MagicMock()
    session.flush = AsyncMock()
    repository = SQLAlchemyNotificationRepository(session)
    notification = build_notification()

    result = await repository.save(notification)

    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    assert result is notification


@pytest.mark.asyncio
async def test_find_by_id_returns_none_when_not_found() -> None:
    session = MagicMock()
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=execute_result)
    repository = SQLAlchemyNotificationRepository(session)

    result = await repository.find_by_id(uuid4())

    assert result is None


@pytest.mark.asyncio
async def test_find_by_id_returns_entity_when_found() -> None:
    session = MagicMock()
    model = NotificationModel(
        id=uuid4(),
        user_id=uuid4(),
        job_id=None,
        type=NotificationType.EMAIL,
        status=NotificationStatus.SENT,
        recipient="user@example.com",
        subject="subject",
        body="body",
        error_message=None,
        sent_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = model
    session.execute = AsyncMock(return_value=execute_result)
    repository = SQLAlchemyNotificationRepository(session)

    result = await repository.find_by_id(model.id)

    assert result is not None
    assert result.id == model.id
    assert result.status == NotificationStatus.SENT


@pytest.mark.asyncio
async def test_find_by_user_id_maps_models_to_entities() -> None:
    session = MagicMock()
    model = NotificationModel(
        id=uuid4(),
        user_id=uuid4(),
        job_id=None,
        type=NotificationType.EMAIL,
        status=NotificationStatus.PENDING,
        recipient="user@example.com",
        subject="subject",
        body="body",
        error_message=None,
        sent_at=None,
        created_at=datetime.utcnow(),
    )
    scalars_result = MagicMock()
    scalars_result.all.return_value = [model]
    execute_result = MagicMock()
    execute_result.scalars.return_value = scalars_result
    session.execute = AsyncMock(return_value=execute_result)
    repository = SQLAlchemyNotificationRepository(session)

    result = await repository.find_by_user_id(model.user_id, 0, 10)

    assert len(result) == 1
    assert result[0].id == model.id


@pytest.mark.asyncio
async def test_update_flushes_when_model_exists() -> None:
    session = MagicMock()
    session.flush = AsyncMock()
    notification = build_notification()
    notification.mark_failed("failed")

    model = NotificationModel(
        id=notification.id,
        user_id=notification.user_id,
        job_id=notification.job_id,
        type=notification.type,
        status=NotificationStatus.PENDING,
        recipient=notification.recipient,
        subject=notification.subject,
        body=notification.body,
        error_message=None,
        sent_at=None,
        created_at=notification.created_at,
    )

    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = model
    session.execute = AsyncMock(return_value=execute_result)
    repository = SQLAlchemyNotificationRepository(session)

    result = await repository.update(notification)

    session.flush.assert_awaited_once()
    assert result is notification
    assert model.status == NotificationStatus.FAILED
    assert model.error_message == "failed"
