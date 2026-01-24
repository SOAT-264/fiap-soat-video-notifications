"""Email Sender Interface."""
from abc import ABC, abstractmethod


class IEmailSender(ABC):
    """Interface for email sender."""

    @abstractmethod
    async def send_email(self, to: str, subject: str, body: str) -> None:
        """Send an email."""
        pass
