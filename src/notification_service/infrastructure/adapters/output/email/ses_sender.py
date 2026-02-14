"""SES-based email sender for notifications."""
import os
from typing import Optional

import aioboto3

from notification_service.application.ports.output.email_sender import IEmailSender


class SESEmailSender(IEmailSender):
    """Send emails using AWS SES."""
    
    def __init__(
        self,
        from_email: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        region: str = "us-east-1",
    ):
        self._from_email = from_email or os.getenv(
            "SES_FROM_EMAIL", "noreply@videoprocessor.local"
        )
        self._endpoint_url = endpoint_url or os.getenv("AWS_ENDPOINT_URL")
        self._region = region
        self._session = aioboto3.Session()
    
    async def send(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
    ) -> bool:
        """Send an email via SES."""
        try:
            async with self._session.client(
                "ses",
                endpoint_url=self._endpoint_url,
                region_name=self._region,
            ) as ses:
                message_body = {"Text": {"Data": body, "Charset": "UTF-8"}}
                
                if html_body:
                    message_body["Html"] = {"Data": html_body, "Charset": "UTF-8"}
                
                await ses.send_email(
                    Source=self._from_email,
                    Destination={"ToAddresses": [to]},
                    Message={
                        "Subject": {"Data": subject, "Charset": "UTF-8"},
                        "Body": message_body,
                    },
                )
                return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    async def send_email(self, to: str, subject: str, body: str) -> None:
        """Send a plain-text email via SES (interface compatibility)."""
        await self.send(to=to, subject=subject, body=body)
    
    async def send_job_completed(
        self,
        to: str,
        video_name: str,
        frame_count: int,
        download_url: str,
    ) -> bool:
        """Send job completion notification."""
        subject = f"✅ Video Processing Complete: {video_name}"
        
        body = f"""
Hello!

Your video "{video_name}" has been processed successfully!

📊 Processing Results:
- Frames extracted: {frame_count}
- Status: COMPLETED

📥 Download your frames:
{download_url}

Thank you for using Video Processor!

Best regards,
Video Processor Team
        """.strip()
        
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #22c55e;">✅ Video Processing Complete</h2>
    <p>Your video <strong>"{video_name}"</strong> has been processed successfully!</p>
    
    <div style="background: #f3f4f6; padding: 16px; border-radius: 8px; margin: 16px 0;">
        <h3 style="margin-top: 0;">📊 Processing Results</h3>
        <ul>
            <li>Frames extracted: <strong>{frame_count}</strong></li>
            <li>Status: <strong style="color: #22c55e;">COMPLETED</strong></li>
        </ul>
    </div>
    
    <a href="{download_url}" style="display: inline-block; background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 16px 0;">
        📥 Download Frames
    </a>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 32px;">
        Thank you for using Video Processor!<br>
        Best regards,<br>
        <strong>Video Processor Team</strong>
    </p>
</body>
</html>
        """.strip()
        
        return await self.send(to, subject, body, html_body)
    
    async def send_job_failed(
        self,
        to: str,
        video_name: str,
        error_message: str,
    ) -> bool:
        """Send job failure notification."""
        subject = f"❌ Video Processing Failed: {video_name}"
        
        body = f"""
Hello!

Unfortunately, we encountered an error processing your video "{video_name}".

❌ Error Details:
{error_message}

Please try uploading your video again. If the problem persists,
please contact our support team.

We apologize for the inconvenience.

Best regards,
Video Processor Team
        """.strip()
        
        return await self.send(to, subject, body)
