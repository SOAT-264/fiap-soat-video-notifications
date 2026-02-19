from datetime import datetime
from uuid import uuid4

from notification_service.domain.entities import Notification, NotificationStatus, NotificationType


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
    )


def test_mark_sent_updates_status_and_sent_at() -> None:
    notification = build_notification()

    notification.mark_sent()

    assert notification.status == NotificationStatus.SENT
    assert isinstance(notification.sent_at, datetime)


def test_mark_failed_updates_status_and_error_message() -> None:
    notification = build_notification()

    notification.mark_failed("boom")

    assert notification.status == NotificationStatus.FAILED
    assert notification.error_message == "boom"


def test_notification_equality_and_hash_by_id() -> None:
    notification_id = uuid4()
    created_at = datetime.utcnow()
    first = Notification(
        id=notification_id,
        user_id=uuid4(),
        job_id=None,
        type=NotificationType.EMAIL,
        status=NotificationStatus.PENDING,
        recipient="one@example.com",
        subject="A",
        body="A body",
        created_at=created_at,
    )
    second = Notification(
        id=notification_id,
        user_id=uuid4(),
        job_id=None,
        type=NotificationType.EMAIL,
        status=NotificationStatus.FAILED,
        recipient="two@example.com",
        subject="B",
        body="B body",
        created_at=created_at,
    )

    assert first == second
    assert hash(first) == hash(second)
    assert first != object()
