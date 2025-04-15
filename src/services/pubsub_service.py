import logging
import json
import base64
import threading
import asyncio
from google.cloud import pubsub_v1
from google.oauth2 import service_account
from src.config.config import get_settings
from src.services.subscription_service import SubscriptionService
from src.utils.logger import setup_logger
from src.config.db_config import get_db

logger = setup_logger(__name__, level=logging.INFO)
_SETTINGS = get_settings()

class PubSubService:
    def __init__(self):
        self.project_id = _SETTINGS.firebase_project_id
        self.subscription_id = _SETTINGS.pubsub_subscription_name
        self.subscription_service = SubscriptionService()
        self._shutdown_event = threading.Event()

    def start_subscription_listener(self):
        """Start listening for Pub/Sub messages"""
        try:
            firebase_credentials = {
                "type": _SETTINGS.firebase_type,
                "project_id": _SETTINGS.firebase_project_id,
                "private_key_id": _SETTINGS.firebase_private_key_id,
                "private_key": _SETTINGS.firebase_private_key.replace("||", "\n"),
                "client_email": _SETTINGS.firebase_client_email,
                "client_id": _SETTINGS.firebase_client_id,
                "auth_uri": _SETTINGS.firebase_auth_uri,
                "token_uri": _SETTINGS.firebase_token_uri,
                "auth_provider_x509_cert_url": _SETTINGS.firebase_auth_provider_x509_cert_url,
                "client_x509_cert_url": _SETTINGS.firebase_client_x509_cert_url,
            }

            credentials = service_account.Credentials.from_service_account_info(
                firebase_credentials,
                scopes=['https://www.googleapis.com/auth/pubsub']
            )

            subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
            subscription_path = subscriber.subscription_path(
                self.project_id, self.subscription_id
            )

            logger.info(f"Pub/Sub: Listening for messages on {subscription_path}")

            def callback(message):
                logger.info(f"Pub/Sub: Received message ID: {message.message_id}")
                asyncio.run(self._handle_message(message))

            streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
            logger.info("Pub/Sub: Listener started successfully")

            while not self._shutdown_event.is_set():
                self._shutdown_event.wait(timeout=1)

            logger.info("Pub/Sub: Shutting down listener...")
            streaming_pull_future.cancel()
            logger.info("Pub/Sub: Listener shutdown complete")

        except Exception as e:
            logger.error(f"Pub/Sub: Error in listener: {e}")

    def shutdown(self):
        """Signal the listener to shut down"""
        logger.info("Pub/Sub: Signaling listener to shut down")
        self._shutdown_event.set()

    async def _handle_message(self, message):
        try:
            data = json.loads(message.data.decode("utf-8"))
            logger.info(f"Pub/Sub: Message data: {data}")
            await self.process_notification(data)
            message.ack()
            logger.info(f"Pub/Sub: Message {message.message_id} processed successfully")
        except Exception as e:
            logger.error(f"Pub/Sub: Error processing message: {e}")
            # Do not ack to trigger retry

    async def process_notification(self, data):
        """Process a notification from Pub/Sub"""
        try:
            notification_data = data
            if "message" in data and "data" in data["message"]:
                encoded_data = data["message"]["data"]
                if isinstance(encoded_data, str):
                    decoded_data = base64.b64decode(encoded_data).decode("utf-8")
                    notification_data = json.loads(decoded_data)

            # Usamos sesión async
            async for db in get_db():
                await self.subscription_service.process_subscription_notification(notification_data, db)

        except Exception as e:
            logger.error(f"Pub/Sub: Error processing notification: {e}")
            raise
