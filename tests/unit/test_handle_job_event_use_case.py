from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from notification_service.application.use_cases.handle_job_event import HandleJobEventUseCase


@pytest.mark.asyncio
async def test_handle_job_completed_builds_success_notification_payload() -> None:
    use_case = HandleJobEventUseCase(notification_repository=AsyncMock(), email_sender=AsyncMock())
    mocked_execute = AsyncMock()
    use_case._send_notification.execute = mocked_execute

    user_id = uuid4()
    job_id = uuid4()
    await use_case.handle_job_completed(
        user_id=user_id,
        job_id=job_id,
        recipient_email="user@example.com",
        video_filename="video.mp4",
        frame_count=120,
        download_url="https://example.com/download",
    )

    mocked_execute.assert_awaited_once()
    sent_input = mocked_execute.await_args.args[0]
    assert sent_input.user_id == user_id
    assert sent_input.job_id == job_id
    assert sent_input.recipient == "user@example.com"
    assert "Video Processing Complete" in sent_input.subject
    assert "Frames extracted: 120" in sent_input.body
    assert "https://example.com/download" in sent_input.body


@pytest.mark.asyncio
async def test_handle_job_failed_builds_failure_notification_payload() -> None:
    use_case = HandleJobEventUseCase(notification_repository=AsyncMock(), email_sender=AsyncMock())
    mocked_execute = AsyncMock()
    use_case._send_notification.execute = mocked_execute

    user_id = uuid4()
    job_id = uuid4()
    await use_case.handle_job_failed(
        user_id=user_id,
        job_id=job_id,
        recipient_email="user@example.com",
        video_filename="video.mp4",
        error_message="encoder crashed",
    )

    mocked_execute.assert_awaited_once()
    sent_input = mocked_execute.await_args.args[0]
    assert sent_input.user_id == user_id
    assert sent_input.job_id == job_id
    assert sent_input.recipient == "user@example.com"
    assert "Video Processing Failed" in sent_input.subject
    assert "encoder crashed" in sent_input.body
