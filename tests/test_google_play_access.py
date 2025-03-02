import sys
import os
import logging
import json
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.config.config import get_settings
from src.utils.logger import setup_logger

# Optional: For Google Play verification
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    print("Google API libraries not available. Please install with: pip install google-auth google-api-python-client")

logger = setup_logger(__name__, level=logging.INFO)
_SETTINGS = get_settings()

def test_google_play_access():
    """Test if Firebase service account has access to Google Play API"""
    if not GOOGLE_API_AVAILABLE:
        logger.error("Google API libraries not available")
        print("ERROR: Google API libraries not available. Please install with: pip install google-auth google-api-python-client")
        return False
    
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
        
        # Log the credentials being used (without the private key)
        safe_credentials = firebase_credentials.copy()
        safe_credentials["private_key"] = "REDACTED"
        logger.info(f"Using Firebase credentials: {json.dumps(safe_credentials, indent=2)}")
        
        # Create credentials object
        creds = service_account.Credentials.from_service_account_info(
            firebase_credentials,
            scopes=['https://www.googleapis.com/auth/androidpublisher']
        )
        
        # Build the Android Publisher API client
        service = build('androidpublisher', 'v3', credentials=creds)
        
        # Try to access a simple endpoint (list subscriptions)
        package_name = _SETTINGS.google_play_package_name
        logger.info(f"Attempting to access Google Play API for package: {package_name}")
        
        # First, try to get app details (a simpler operation)
        app_details = service.edits().insert(packageName=package_name).execute()
        logger.info(f"Successfully created edit for app: {app_details}")
        
        # Try to list in-app products
        inapp_products = service.inappproducts().list(packageName=package_name).execute()
        logger.info(f"Successfully retrieved in-app products: {inapp_products}")
        
        # Try to list subscriptions if available
        try:
            subscriptions = service.monetization().subscriptions().list(
                packageName=package_name
            ).execute()
            logger.info(f"Successfully retrieved subscriptions: {subscriptions}")
        except Exception as e:
            logger.warning(f"Could not retrieve subscriptions (this might be normal if you don't have any): {e}")
        
        print("SUCCESS: Firebase service account has access to Google Play API!")
        return True
    except Exception as e:
        logger.error(f"Error testing Google Play API access: {e}")
        print(f"ERROR: Failed to access Google Play API: {e}")
        
        # Provide troubleshooting guidance
        print("\nTROUBLESHOOTING TIPS:")
        print("1. Ensure your Firebase service account is added to Google Play Console with appropriate permissions")
        print("2. Verify the Google Play Developer API is enabled in Google Cloud Console")
        print("3. Check that your package name is correct in the .env file")
        print("4. Make sure your Firebase project and Google Play Console project are linked")
        return False

if __name__ == "__main__":
    print("\n=== TESTING GOOGLE PLAY API ACCESS ===\n")
    test_google_play_access() 