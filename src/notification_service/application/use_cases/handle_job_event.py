"""Handle Job Event Use Case."""
from typing import Optional
from uuid import UUID

from notification_service.application.use_cases.send_notification import (
    SendNotificationUseCase,
    SendNotificationInput,
)
from notification_service.application.ports.output import INotificationRepository, IEmailSender


class HandleJobEventUseCase:
    """Use case for handling job events and sending appropriate notifications."""

    def __init__(
        self,
        notification_repository: INotificationRepository,
        email_sender: IEmailSender,
    ):
        self._send_notification = SendNotificationUseCase(
            notification_repository=notification_repository,
            email_sender=email_sender,
        )

    async def handle_job_completed(
        self,
        user_id: UUID,
        job_id: UUID,
        recipient_email: str,
        video_filename: str,
        frame_count: int,
        download_url: Optional[str] = None,
    ) -> None:
        """Handle job completed event - send success notification."""
        subject = f"✅ Video Processing Complete: {video_filename}"
        body = f"""
Hello!

Your video "{video_filename}" has been processed successfully!

📊 Processing Results:
- Frames extracted: {frame_count}
- Status: COMPLETED

{f"📥 Download your frames: {download_url}" if download_url else ""}

Thank you for using our Video Processor!

Best regards,
Video Processor Team
        """.strip()

        await self._send_notification.execute(
            SendNotificationInput(
                user_id=user_id,
                job_id=job_id,
                recipient=recipient_email,
                subject=subject,
                body=body,
            )
        )

    async def handle_job_failed(
        self,
        user_id: UUID,
        job_id: UUID,
        recipient_email: str,
        video_filename: str,
        error_message: str,
    ) -> None:
        """Handle job failed event - send error notification."""
        subject = f"❌ Video Processing Failed: {video_filename}"
        body = f"""
Hello!

Unfortunately, we encountered an error processing your video "{video_filename}".

❌ Error Details:
{error_message}

Please try uploading your video again. If the problem persists, 
please contact our support team.

We apologize for the inconvenience.

Best regards,
Video Processor Team
        """.strip()

        await self._send_notification.execute(
            SendNotificationInput(
                user_id=user_id,
                job_id=job_id,
                recipient=recipient_email,
                subject=subject,
                body=body,
            )
        )
