from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from notification_service.application.use_cases.send_notification import (
    SendNotificationInput,
    SendNotificationUseCase,
)
from notification_service.domain.entities import NotificationStatus
from notification_service.domain.exceptions import EmailSendError


@pytest.mark.asyncio
async def test_execute_sends_email_and_updates_as_sent() -> None:
    repository = AsyncMock()
    email_sender = AsyncMock()
    use_case = SendNotificationUseCase(repository, email_sender)
    input_data = SendNotificationInput(
        user_id=uuid4(),
        recipient="user@example.com",
        subject="Hello",
        body="Body",
        job_id=uuid4(),
    )

    output = await use_case.execute(input_data)

    repository.save.assert_awaited_once()
    repository.update.assert_awaited_once()
    email_sender.send_email.assert_awaited_once_with(
        to="user@example.com",
        subject="Hello",
        body="Body",
    )
    assert output.status == NotificationStatus.SENT
    assert output.error_message is None


@pytest.mark.asyncio
async def test_execute_marks_failed_and_raises_when_email_sender_fails() -> None:
    repository = AsyncMock()
    email_sender = AsyncMock()
    email_sender.send_email.side_effect = RuntimeError("smtp down")
    use_case = SendNotificationUseCase(repository, email_sender)
    input_data = SendNotificationInput(
        user_id=uuid4(),
        recipient="user@example.com",
        subject="Hello",
        body="Body",
    )

    with pytest.raises(EmailSendError) as exc_info:
        await use_case.execute(input_data)

    repository.save.assert_awaited_once()
    repository.update.assert_awaited_once()
    assert "smtp down" in str(exc_info.value)
