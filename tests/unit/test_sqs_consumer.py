import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from notification_service.infrastructure.adapters.input import sqs_consumer


class DummySessionContext:
    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeRepository:
    def __init__(self):
        self.saved = []
        self.updated = []

    async def save(self, notification):
        self.saved.append(notification)

    async def update(self, notification):
        self.updated.append(notification)


class SQSClientContext:
    def __init__(self, client):
        self.client = client

    async def __aenter__(self):
        return self.client

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeSession:
    def __init__(self, client):
        self._client = client

    def client(self, *args, **kwargs):
        return SQSClientContext(self._client)


@pytest.mark.asyncio
async def test_normalize_event_type() -> None:
    assert sqs_consumer._normalize_event_type("job.completed") == "job_completed"
    assert sqs_consumer._normalize_event_type("JOB_FAILED") == "job_failed"
    assert sqs_consumer._normalize_event_type(None) == ""


@pytest.mark.asyncio
async def test_fetch_user_email_success(monkeypatch: pytest.MonkeyPatch) -> None:
    response = SimpleNamespace(status_code=200, json=lambda: {"email": "user@example.com"})

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url):
            return response

    monkeypatch.setattr(sqs_consumer.httpx, "AsyncClient", lambda timeout: FakeClient())

    email = await sqs_consumer._fetch_user_email("123")

    assert email == "user@example.com"


@pytest.mark.asyncio
async def test_fetch_user_email_returns_none_on_request_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url):
            raise sqs_consumer.httpx.RequestError("network")

    monkeypatch.setattr(sqs_consumer.httpx, "AsyncClient", lambda timeout: FakeClient())

    email = await sqs_consumer._fetch_user_email("123")

    assert email is None


@pytest.mark.asyncio
async def test_handle_event_job_completed_saves_and_marks_sent(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_repository = FakeRepository()
    fake_sender = SimpleNamespace(send_job_completed=AsyncMock(return_value=True))

    monkeypatch.setattr(sqs_consumer, "get_session_context", lambda: DummySessionContext(object()))
    monkeypatch.setattr(sqs_consumer, "SQLAlchemyNotificationRepository", lambda session: fake_repository)
    monkeypatch.setattr(sqs_consumer, "_fetch_user_email", AsyncMock(return_value="user@example.com"))

    payload = {
        "event_type": "job.completed",
        "user_id": str(uuid4()),
        "job_id": str(uuid4()),
        "video_name": "video.mp4",
        "frame_count": 20,
        "download_url": "https://download",
    }

    await sqs_consumer._handle_event(fake_sender, payload)

    assert len(fake_repository.saved) == 1
    assert len(fake_repository.updated) == 1
    assert fake_repository.updated[0].status.value == "SENT"


@pytest.mark.asyncio
async def test_handle_event_without_user_id_returns_early(monkeypatch: pytest.MonkeyPatch) -> None:
    called = {"opened": False}

    def fake_context():
        called["opened"] = True
        return DummySessionContext(object())

    monkeypatch.setattr(sqs_consumer, "get_session_context", fake_context)

    await sqs_consumer._handle_event(SimpleNamespace(), {"event_type": "job.failed"})

    assert called["opened"] is False


@pytest.mark.asyncio
async def test_handle_event_marks_failed_when_email_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_repository = FakeRepository()

    monkeypatch.setattr(sqs_consumer, "get_session_context", lambda: DummySessionContext(object()))
    monkeypatch.setattr(sqs_consumer, "SQLAlchemyNotificationRepository", lambda session: fake_repository)
    monkeypatch.setattr(sqs_consumer, "_fetch_user_email", AsyncMock(return_value=None))

    payload = {
        "event_type": "job.failed",
        "user_id": str(uuid4()),
        "job_id": str(uuid4()),
        "error_message": "boom",
    }

    await sqs_consumer._handle_event(SimpleNamespace(), payload)

    assert len(fake_repository.saved) == 1
    assert len(fake_repository.updated) == 1
    assert fake_repository.updated[0].status.value == "FAILED"
    assert fake_repository.updated[0].error_message == "User email not found"


@pytest.mark.asyncio
async def test_process_message_deletes_message_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    consumer = sqs_consumer.SQSNotificationConsumer(queue_url="queue-url")
    consumer._sender = object()
    consumer._queue_url = "queue-url"
    handle_mock = AsyncMock()
    monkeypatch.setattr(sqs_consumer, "_handle_event", handle_mock)

    sqs = SimpleNamespace(delete_message=AsyncMock())
    message = {
        "ReceiptHandle": "receipt",
        "Body": json.dumps({"event_type": "job.completed", "user_id": str(uuid4())}),
    }

    await consumer._process_message(sqs, message)

    handle_mock.assert_awaited_once()
    sqs.delete_message.assert_awaited_once_with(QueueUrl="queue-url", ReceiptHandle="receipt")


@pytest.mark.asyncio
async def test_process_message_does_not_delete_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    consumer = sqs_consumer.SQSNotificationConsumer(queue_url="queue-url")
    consumer._sender = object()
    consumer._queue_url = "queue-url"
    monkeypatch.setattr(sqs_consumer, "_handle_event", AsyncMock(side_effect=RuntimeError("fail")))

    sqs = SimpleNamespace(delete_message=AsyncMock())
    message = {
        "ReceiptHandle": "receipt",
        "Body": json.dumps({"event_type": "job.completed", "user_id": str(uuid4())}),
    }

    await consumer._process_message(sqs, message)

    sqs.delete_message.assert_not_called()


@pytest.mark.asyncio
async def test_poll_and_process_sleeps_on_poll_error(monkeypatch: pytest.MonkeyPatch) -> None:
    consumer = sqs_consumer.SQSNotificationConsumer(queue_url="queue-url")
    consumer._queue_url = "queue-url"

    fake_client = SimpleNamespace(receive_message=AsyncMock(side_effect=RuntimeError("sqs down")))
    consumer._session = FakeSession(fake_client)

    sleep_mock = AsyncMock()
    monkeypatch.setattr(sqs_consumer.asyncio, "sleep", sleep_mock)

    await consumer._poll_and_process()

    sleep_mock.assert_awaited_once_with(5)


def test_lambda_handler_tracks_processed_and_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sqs_consumer, "SESEmailSender", lambda: object())

    async def fake_handle_event(sender, body):
        if body.get("raise"):
            raise RuntimeError("bad event")

    class FakeLoop:
        def run_until_complete(self, coro):
            import asyncio

            return asyncio.run(coro)

    monkeypatch.setattr(sqs_consumer, "_handle_event", fake_handle_event)
    monkeypatch.setattr(sqs_consumer.asyncio, "get_event_loop", lambda: FakeLoop())

    event = {
        "Records": [
            {"messageId": "1", "body": json.dumps({"ok": True})},
            {"messageId": "2", "body": json.dumps({"raise": True})},
        ]
    }

    response = sqs_consumer.lambda_handler(event, None)
    parsed = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert parsed["processed"] == ["1"]
    assert parsed["failed"][0]["message_id"] == "2"
