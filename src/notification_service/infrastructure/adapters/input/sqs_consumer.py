"""SQS Consumer for notification events from SNS.

Listens for job completed/failed events and sends email notifications.
"""
import asyncio
import json
import os
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

import httpx

import aioboto3

from notification_service.infrastructure.adapters.output.email.ses_sender import SESEmailSender
from notification_service.infrastructure.adapters.output.persistence import (
    get_session_context,
    SQLAlchemyNotificationRepository,
)
from notification_service.domain.entities import (
    Notification,
    NotificationStatus,
    NotificationType,
)
from notification_service.infrastructure.config import get_settings

settings = get_settings()


# Lambda handler for AWS
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler triggered by SQS (subscribed to SNS).
    
    Sends email notifications for job completion/failure events.
    """
    processed = []
    failed = []
    
    sender = SESEmailSender()
    
    for record in event.get("Records", []):
        try:
            body = json.loads(record["body"])
            
            # Handle SNS-wrapped messages
            if "Message" in body:
                body = json.loads(body["Message"])
            
            asyncio.get_event_loop().run_until_complete(
                _handle_event(sender, body)
            )
            
            processed.append(record.get("messageId"))
            
        except Exception as e:
            failed.append({
                "message_id": record.get("messageId"),
                "error": str(e),
            })
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "processed": processed,
            "failed": failed,
        }),
    }


def _normalize_event_type(event_type: Optional[str]) -> str:
    if not event_type:
        return ""
    return event_type.replace(".", "_").lower()


async def _handle_event(sender: SESEmailSender, body: Dict[str, Any]) -> None:
    """Process a single notification event."""
    event_type = _normalize_event_type(body.get("event_type"))
    user_id = body.get("user_id")
    job_id = body.get("job_id")
    user_email = body.get("user_email")

    if not user_id:
        print(f"No user_id in event: {body}")
        return

    subject = None
    body_text = None
    status = NotificationStatus.PENDING
    error_message = None

    if event_type == "job_completed":
        subject = "Video processing completed"
        body_text = "Your video processing has completed."
    elif event_type == "job_failed":
        subject = "Video processing failed"
        body_text = "Your video processing failed."
        error_message = body.get("error_message")
    else:
        subject = "Job update"
        body_text = "Your job status has been updated."

    if not user_email:
        user_email = await _fetch_user_email(str(user_id))

    recipient = user_email or str(user_id)

    async with get_session_context() as session:
        repository = SQLAlchemyNotificationRepository(session)
        notification = Notification(
            id=uuid4(),
            user_id=UUID(str(user_id)),
            job_id=UUID(str(job_id)) if job_id else None,
            type=NotificationType.EMAIL,
            status=status,
            recipient=recipient,
            subject=subject,
            body=body_text,
            error_message=error_message,
        )
        await repository.save(notification)

        if user_email:
            if event_type == "job_completed":
                sent = await sender.send_job_completed(
                    to=user_email,
                    video_name=body.get("video_name", "video.mp4"),
                    frame_count=body.get("frame_count", 0),
                    download_url=body.get("download_url", ""),
                )
                if sent:
                    notification.mark_sent()
                else:
                    notification.mark_failed("Email send failed")
            elif event_type == "job_failed":
                sent = await sender.send_job_failed(
                    to=user_email,
                    video_name=body.get("video_name", "video.mp4"),
                    error_message=body.get("error_message", "Unknown error"),
                )
                if sent:
                    notification.mark_sent()
                else:
                    notification.mark_failed("Email send failed")
            else:
                # No email template for job updates; record as sent without delivery.
                notification.mark_sent()

            await repository.update(notification)
        else:
            notification.mark_failed("User email not found")
            await repository.update(notification)


async def _fetch_user_email(user_id: str) -> Optional[str]:
    """Fetch user email from auth service by user ID."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/auth/users/{user_id}"
            )
            if response.status_code == 200:
                return response.json().get("email")
            return None
    except httpx.RequestError:
        return None


# Local SQS poller for development
class SQSNotificationConsumer:
    """Polls SQS notification queue for job events."""
    
    def __init__(
        self,
        queue_url: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        region: str = "us-east-1",
    ):
        self._queue_url = (
            queue_url
            or os.getenv("SQS_NOTIFICATION_QUEUE_URL")
            or os.getenv("SQS_QUEUE_URL")
        )
        self._endpoint_url = endpoint_url or os.getenv("AWS_ENDPOINT_URL")
        self._region = region
        self._session = aioboto3.Session()
        self._sender = SESEmailSender()
        self._running = False
    
    async def start(self) -> None:
        """Start polling for notification events."""
        self._running = True
        print(f"📧 Starting notification consumer for queue: {self._queue_url}")
        
        while self._running:
            await self._poll_and_process()
    
    async def stop(self) -> None:
        """Stop polling."""
        self._running = False
    
    async def _poll_and_process(self) -> None:
        """Poll queue and process messages."""
        async with self._session.client(
            "sqs",
            endpoint_url=self._endpoint_url,
            region_name=self._region,
        ) as sqs:
            try:
                response = await sqs.receive_message(
                    QueueUrl=self._queue_url,
                    MaxNumberOfMessages=10,
                    WaitTimeSeconds=20,
                )
                
                for message in response.get("Messages", []):
                    await self._process_message(sqs, message)
                    
            except Exception as e:
                print(f"❌ Error polling SQS: {e}")
                await asyncio.sleep(5)
    
    async def _process_message(self, sqs: Any, message: Dict[str, Any]) -> None:
        """Process a single notification message."""
        receipt_handle = message["ReceiptHandle"]
        
        try:
            body = json.loads(message["Body"])
            
            # Handle SNS-wrapped messages
            if "Message" in body:
                body = json.loads(body["Message"])
            
            await _handle_event(self._sender, body)
            
            # Delete message on success
            await sqs.delete_message(
                QueueUrl=self._queue_url,
                ReceiptHandle=receipt_handle,
            )
            
            print(f"✅ Notification sent for event: {body.get('event_type')}")
            
        except Exception as e:
            print(f"❌ Failed to process notification: {e}")


async def main():
    consumer = SQSNotificationConsumer()
    try:
        await consumer.start()
    except KeyboardInterrupt:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(main())
