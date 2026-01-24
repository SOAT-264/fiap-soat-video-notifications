"""Notification Repository Interface."""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from notification_service.domain.entities import Notification


class INotificationRepository(ABC):
    """Interface for notification repository."""

    @abstractmethod
    async def save(self, notification: Notification) -> Notification:
        """Save a notification."""
        pass

    @abstractmethod
    async def find_by_id(self, notification_id: UUID) -> Optional[Notification]:
        """Find notification by ID."""
        pass

    @abstractmethod
    async def find_by_user_id(
        self, user_id: UUID, skip: int = 0, limit: int = 10
    ) -> List[Notification]:
        """Find notifications by user ID."""
        pass

    @abstractmethod
    async def update(self, notification: Notification) -> Notification:
        """Update a notification."""
        pass
