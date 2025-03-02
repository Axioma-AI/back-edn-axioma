import logging
import json
import httpx
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from src.config.config import get_settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__, level=logging.INFO)
_SETTINGS = get_settings()

class ReceiptVerifier:
    # Apple sandbox and production URLs
    APPLE_SANDBOX_URL = "https://sandbox.itunes.apple.com/verifyReceipt"
    APPLE_PROD_URL = "https://buy.itunes.apple.com/verifyReceipt"
    
    # Google Play API settings
    GOOGLE_PLAY_API_VERSION = "v3"
    GOOGLE_PLAY_SCOPE = "https://www.googleapis.com/auth/androidpublisher"

    @staticmethod
    async def verify_apple_receipt(receipt_data: str, sandbox: bool = False) -> dict:
        """Verify Apple App Store receipt"""
        try:
            url = ReceiptVerifier.APPLE_SANDBOX_URL if sandbox else ReceiptVerifier.APPLE_PROD_URL
            
            # Prepare the request payload
            payload = {
                "receipt-data": receipt_data,
                "password": _SETTINGS.apple_shared_secret  # Your App Store Connect shared secret
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                data = response.json()

                # Handle sandbox vs production environment
                if not sandbox and data.get("status") == 21007:  # Sandbox receipt sent to production
                    logger.info("Receipt is from sandbox, retrying with sandbox environment")
                    return await ReceiptVerifier.verify_apple_receipt(receipt_data, sandbox=True)

                return data

        except Exception as e:
            logger.error(f"Error verifying Apple receipt: {e}")
            raise

    @staticmethod
    async def verify_google_receipt(purchase_token: str, product_id: str, package_name: str) -> dict:
        """Verify Google Play receipt"""
        try:
            # Load Google Play credentials
            credentials = service_account.Credentials.from_service_account_info(
                json.loads(_SETTINGS.google_play_credentials),
                scopes=[ReceiptVerifier.GOOGLE_PLAY_SCOPE]
            )

            if credentials.expired:
                credentials.refresh(Request())

            # Construct the Google Play API URL
            url = (
                f"https://androidpublisher.googleapis.com/androidpublisher/"
                f"{ReceiptVerifier.GOOGLE_PLAY_API_VERSION}/applications/"
                f"{package_name}/purchases/subscriptions/{product_id}/"
                f"tokens/{purchase_token}"
            )

            headers = {
                "Authorization": f"Bearer {credentials.token}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                return response.json()

        except Exception as e:
            logger.error(f"Error verifying Google Play receipt: {e}")
            raise 