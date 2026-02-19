from unittest.mock import AsyncMock

import pytest

from notification_service.infrastructure.adapters.output.email.ses_sender import SESEmailSender


class FakeClientContext:
    def __init__(self, ses_client):
        self.ses_client = ses_client

    async def __aenter__(self):
        return self.ses_client

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeSession:
    def __init__(self, ses_client):
        self.ses_client = ses_client

    def client(self, *args, **kwargs):
        return FakeClientContext(self.ses_client)


@pytest.mark.asyncio
async def test_send_returns_true_on_success() -> None:
    ses_client = AsyncMock()
    sender = SESEmailSender(from_email="from@example.com")
    sender._session = FakeSession(ses_client)

    result = await sender.send("to@example.com", "subject", "body")

    assert result is True
    ses_client.send_email.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_returns_false_on_exception() -> None:
    ses_client = AsyncMock()
    ses_client.send_email.side_effect = RuntimeError("ses unavailable")
    sender = SESEmailSender(from_email="from@example.com")
    sender._session = FakeSession(ses_client)

    result = await sender.send("to@example.com", "subject", "body")

    assert result is False


@pytest.mark.asyncio
async def test_send_email_delegates_to_send(monkeypatch: pytest.MonkeyPatch) -> None:
    sender = SESEmailSender(from_email="from@example.com")
    send_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(sender, "send", send_mock)

    await sender.send_email("to@example.com", "subject", "body")

    send_mock.assert_awaited_once_with(to="to@example.com", subject="subject", body="body")


@pytest.mark.asyncio
async def test_send_job_completed_and_failed_delegate_to_send(monkeypatch: pytest.MonkeyPatch) -> None:
    sender = SESEmailSender(from_email="from@example.com")
    send_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(sender, "send", send_mock)

    completed = await sender.send_job_completed(
        to="to@example.com",
        video_name="video.mp4",
        frame_count=24,
        download_url="https://download",
    )
    failed = await sender.send_job_failed(
        to="to@example.com",
        video_name="video.mp4",
        error_message="boom",
    )

    assert completed is True
    assert failed is True
    assert send_mock.await_count == 2
    first_args = send_mock.await_args_list[0].args
    second_args = send_mock.await_args_list[1].args
    assert "Video Processing Complete" in first_args[1]
    assert "Video Processing Failed" in second_args[1]
