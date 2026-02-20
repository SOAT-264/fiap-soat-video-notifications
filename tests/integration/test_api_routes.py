from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi.testclient import TestClient

from notification_service.domain.entities import Notification, NotificationStatus, NotificationType
from notification_service.infrastructure.adapters.input.api import main as api_main
from notification_service.infrastructure.adapters.input.api.main import app
from notification_service.infrastructure.adapters.input.api.routes.notification_routes import (
    get_notification_repository,
)


class StubNotificationRepository:
    def __init__(self, notifications):
        self.notifications = notifications

    async def find_by_user_id(self, user_id, skip: int, limit: int):
        return self.notifications[skip : skip + limit]


def test_root_returns_service_status() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "notification-service"
    assert payload["status"] == "running"


def test_health_endpoint_returns_healthy() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["service"] == "notification-service"
    assert "timestamp" in payload


def test_lifespan_calls_close_redis_on_shutdown(monkeypatch) -> None:
    close_mock = AsyncMock()
    monkeypatch.setattr(api_main, "close_redis", close_mock)

    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200

    close_mock.assert_awaited_once()


def test_list_notifications_with_dependency_override() -> None:
    user_id = uuid4()
    notification = Notification(
        id=uuid4(),
        user_id=user_id,
        job_id=None,
        type=NotificationType.EMAIL,
        status=NotificationStatus.SENT,
        recipient="user@example.com",
        subject="Subject",
        body="Body",
        sent_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )

    stub = StubNotificationRepository([notification])
    app.dependency_overrides[get_notification_repository] = lambda: stub

    client = TestClient(app)
    response = client.get(f"/notifications?user_id={user_id}&skip=0&limit=20")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == str(notification.id)
    assert payload[0]["status"] == "SENT"
    assert payload[0]["type"] == "EMAIL"

    app.dependency_overrides.clear()
