import logging
import json
import base64
import threading
from google.cloud import pubsub_v1
from sqlalchemy.orm import Session
from google.oauth2 import service_account
from src.config.config import get_settings
from src.services.subscription_service import SubscriptionService
from src.utils.logger import setup_logger
from src.config.db_config import get_db_session

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
            # Create credentials from Firebase service account
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
            
            # Create credentials object
            credentials = service_account.Credentials.from_service_account_info(
                firebase_credentials,
                scopes=['https://www.googleapis.com/auth/pubsub']
            )
            
            # Create Pub/Sub client with explicit credentials
            subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
            subscription_path = subscriber.subscription_path(
                self.project_id, self.subscription_id
            )
            
            logger.info(f"Pub/Sub: Listening for messages on {subscription_path}")
            
            def callback(message):
                try:
                    # Only log message ID to reduce noise
                    logger.info(f"Pub/Sub: Received message ID: {message.message_id}")
                    
                    data = json.loads(message.data.decode("utf-8"))

                    logger.info(f"Pub/Sub: Message data: {data}")
                    
                    # Process the notification with a database session
                    with get_db_session() as db:
                        self.process_notification(data, db)
                    
                    # Acknowledge the message
                    message.ack()
                    logger.info(f"Pub/Sub: Message {message.message_id} processed successfully")
                except Exception as e:
                    logger.error(f"Pub/Sub: Error processing message: {e}")
                    # Don't acknowledge to allow retry
            
            streaming_pull_future = subscriber.subscribe(
                subscription_path, callback=callback
            )
            
            logger.info("Pub/Sub: Listener started successfully")
            
            # Keep the thread running until shutdown is requested
            while not self._shutdown_event.is_set():
                try:
                    # This will block for 1 second
                    self._shutdown_event.wait(timeout=1)
                except Exception as e:
                    logger.error(f"Pub/Sub: Error in listener loop: {e}")
            
            # Shutdown was requested, cancel the subscription
            logger.info("Pub/Sub: Shutting down listener...")
            streaming_pull_future.cancel()
            logger.info("Pub/Sub: Listener shutdown complete")
            
        except Exception as e:
            logger.error(f"Pub/Sub: Error in listener: {e}")
    
    def shutdown(self):
        """Signal the listener to shut down"""
        logger.info("Pub/Sub: Signaling listener to shut down")
        self._shutdown_event.set()
    
    def process_notification(self, data, db: Session):
        """Process a notification from Pub/Sub"""
        try:
            # For Google Play notifications, the structure might be nested
            notification_data = data
            
            # If the data is from a Pub/Sub push subscription, it might be wrapped
            if "message" in data and "data" in data["message"]:
                encoded_data = data["message"]["data"]
                if isinstance(encoded_data, str):
                    decoded_data = base64.b64decode(encoded_data).decode("utf-8")
                    notification_data = json.loads(decoded_data)
            
            # Process the notification with a database session
            self.subscription_service.process_subscription_notification_sync(notification_data, db)
            
        except Exception as e:
            logger.error(f"Pub/Sub: Error processing notification: {e}")
            raise 