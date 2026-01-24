"""SQS Consumer for notification events from SNS.

Listens for job completed/failed events and sends email notifications.
"""
import asyncio
import json
import os
from typing import Any, Dict, Optional

import aioboto3

from notification_service.infrastructure.adapters.output.email.ses_sender import SESEmailSender


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


async def _handle_event(sender: SESEmailSender, body: Dict[str, Any]) -> None:
    """Process a single notification event."""
    event_type = body.get("event_type")
    user_email = body.get("user_email")
    
    if not user_email:
        print(f"No user_email in event: {body}")
        return
    
    if event_type == "job_completed":
        await sender.send_job_completed(
            to=user_email,
            video_name=body.get("video_name", "video.mp4"),
            frame_count=body.get("frame_count", 0),
            download_url=body.get("download_url", ""),
        )
    elif event_type == "job_failed":
        await sender.send_job_failed(
            to=user_email,
            video_name=body.get("video_name", "video.mp4"),
            error_message=body.get("error_message", "Unknown error"),
        )


# Local SQS poller for development
class SQSNotificationConsumer:
    """Polls SQS notification queue for job events."""
    
    def __init__(
        self,
        queue_url: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        region: str = "us-east-1",
    ):
        self._queue_url = queue_url or os.getenv("SQS_NOTIFICATION_QUEUE_URL")
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
