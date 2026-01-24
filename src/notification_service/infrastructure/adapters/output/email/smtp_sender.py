"""SMTP Email Sender implementation."""
import aiosmtplib
from email.message import EmailMessage

from notification_service.application.ports.output import IEmailSender
from notification_service.infrastructure.config import get_settings

settings = get_settings()


class SMTPEmailSender(IEmailSender):
    """SMTP implementation of email sender."""

    async def send_email(self, to: str, subject: str, body: str) -> None:
        """Send an email via SMTP."""
        # Skip sending if SMTP not configured
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            print(f"[SKIP] Email would be sent to {to}: {subject}")
            return

        message = EmailMessage()
        message["From"] = settings.SMTP_FROM
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=settings.SMTP_USE_TLS,
        )
