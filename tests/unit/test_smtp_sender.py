from unittest.mock import AsyncMock

import pytest

from notification_service.infrastructure.adapters.output.email import smtp_sender
from notification_service.infrastructure.adapters.output.email.smtp_sender import SMTPEmailSender


@pytest.mark.asyncio
async def test_send_email_skips_when_smtp_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(smtp_sender.settings, "SMTP_USER", "")
    monkeypatch.setattr(smtp_sender.settings, "SMTP_PASSWORD", "")
    send_mock = AsyncMock()
    monkeypatch.setattr(smtp_sender.aiosmtplib, "send", send_mock)

    sender = SMTPEmailSender()
    await sender.send_email("user@example.com", "subject", "body")

    send_mock.assert_not_called()


@pytest.mark.asyncio
async def test_send_email_uses_aiosmtplib_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(smtp_sender.settings, "SMTP_USER", "smtp-user")
    monkeypatch.setattr(smtp_sender.settings, "SMTP_PASSWORD", "smtp-pass")
    monkeypatch.setattr(smtp_sender.settings, "SMTP_FROM", "no-reply@example.com")
    monkeypatch.setattr(smtp_sender.settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(smtp_sender.settings, "SMTP_PORT", 2525)
    monkeypatch.setattr(smtp_sender.settings, "SMTP_USE_TLS", True)

    send_mock = AsyncMock()
    monkeypatch.setattr(smtp_sender.aiosmtplib, "send", send_mock)

    sender = SMTPEmailSender()
    await sender.send_email("user@example.com", "subject", "body")

    send_mock.assert_awaited_once()
    kwargs = send_mock.await_args.kwargs
    assert kwargs["hostname"] == "smtp.example.com"
    assert kwargs["port"] == 2525
    assert kwargs["username"] == "smtp-user"
    assert kwargs["password"] == "smtp-pass"
    assert kwargs["start_tls"] is True
