import logging
import threading
from src.utils.logger import setup_logger
from src.services.pubsub_service import PubSubService

logger = setup_logger(__name__, level=logging.INFO)

class BackgroundService:
    """Service to manage background tasks"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BackgroundService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not BackgroundService._initialized:
            self.pubsub_service = PubSubService()
            self.pubsub_thread = None
            BackgroundService._initialized = True
    
    def start_pubsub_listener(self):
        """Start the Pub/Sub listener in a background thread"""
        if self.pubsub_thread is None or not self.pubsub_thread.is_alive():
            logger.info("Starting Pub/Sub listener in background thread")
            self.pubsub_thread = threading.Thread(
                target=self.pubsub_service.start_subscription_listener,
                daemon=True  # This ensures the thread will exit when the main program exits
            )
            self.pubsub_thread.start()
        else:
            logger.info("Pub/Sub listener already running")
    
    def stop_pubsub_listener(self):
        """Stop the Pub/Sub listener thread"""
        if self.pubsub_thread and self.pubsub_thread.is_alive():
            logger.info("Stopping Pub/Sub listener")
            self.pubsub_service.shutdown()  # Signal the service to shut down
            self.pubsub_thread.join(timeout=5)  # Wait up to 5 seconds for the thread to exit
            if self.pubsub_thread.is_alive():
                logger.warning("Pub/Sub listener thread did not exit cleanly") 