import logging
import json
import traceback
from datetime import datetime, timedelta, timezone
import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.config.db_config import get_db
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_
from firebase_admin import auth
import asyncio

from src.models.user_model import UserModel
from src.models.subscription_model import (
    SubscriptionModel, 
    SubscriptionHistoryModel, 
    SubscriptionStatus, 
    SubscriptionTier,
    SubscriptionAction
)
from src.config.config import get_settings
from src.utils.logger import setup_logger

# Optional: For Google Play verification
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

logger = setup_logger(__name__, level=logging.INFO)
_SETTINGS = get_settings()

class SubscriptionService:
    async def get_user_from_token(self, token: str):
        """
        Valida el token de Firebase y obtiene al usuario desde la base de datos usando SQLAlchemy async.
        """
        try:
            logger.info(f"Verifying Firebase token: {token[:10]}...")

            # Verificar token con Firebase
            decoded_token = auth.verify_id_token(token)
            logger.info(f"Token verified successfully. Decoded token contains: {list(decoded_token.keys())}")

            email = decoded_token.get('email')
            if not email:
                logger.error("Email not found in decoded token")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: email not found"
                )

            async for db in get_db():
                stmt = select(UserModel).where(UserModel.email == email)
                result = await db.execute(stmt)
                user = result.scalars().first()

                if not user:
                    logger.error(f"User not found for email: {email}")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found"
                    )

                logger.info(f"User found: id={user.id}, email={user.email}")
                return user

        except auth.InvalidIdTokenError as e:
            logger.error(f"Invalid Firebase token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or expired token: {str(e)}"
            )
        except Exception as e:
            error_traceback = traceback.format_exc()
            logger.error(f"Error getting user from token: {e}\nTraceback: {error_traceback}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing authentication: {str(e)}"
            )
    
    async def create_subscription(self, user_id: int, product_id: str, provider: str, receipt_data: dict = None):
        """Create a new subscription for a user or update an existing one"""
        async for db in get_db():
            try:
                # Extract base plan ID
                base_plan_id = self._extract_base_plan_id(product_id)
                logger.info(f"Extracted base plan ID: {base_plan_id} from product ID: {product_id}")

                # Determine the subscription tier
                tier_mapping = {
                    'pro_plan': SubscriptionTier.PRO,
                    'analyst_plan': SubscriptionTier.ANALYST,
                }
                tier = self._determine_subscription_tier(base_plan_id, tier_mapping)

                # If receipt is provided, verify it and possibly update tier
                if receipt_data:
                    tier = self._verify_receipt_and_get_tier(provider, receipt_data, tier)

                if isinstance(tier, str):
                    logger.warning(f"Tier is a string: '{tier}', converting to enum")
                    tier = SubscriptionTier.from_string(tier)

                logger.info(f"Processing subscription with tier: {tier} (value: {tier.value})")

                # Check for existing active subscription
                stmt = select(SubscriptionModel).where(
                    SubscriptionModel.user_id == user_id,
                    SubscriptionModel.status == SubscriptionStatus.ACTIVE
                )
                result = await db.execute(stmt)
                existing_subscription = result.scalars().first()

                current_time = datetime.now(timezone.utc)

                if existing_subscription:
                    logger.info(f"Updating existing subscription for user {user_id}")
                    subscription = await self._update_existing_subscription(
                        db, existing_subscription, tier, product_id, provider, receipt_data, current_time
                    )
                else:
                    logger.info(f"Creating new subscription for user {user_id}")
                    subscription = await self._create_new_subscription(
                        db, user_id, tier, product_id, provider, receipt_data, current_time
                    )

                return subscription

            except Exception as e:
                await db.rollback()
                error_traceback = traceback.format_exc()
                logger.error(f"Error creating subscription: {e}\nTraceback: {error_traceback}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error creating subscription: {str(e)}"
                )
            
    def _extract_base_plan_id(self, product_id):
        """Extract the base plan ID from a product ID"""
        parts = product_id.split('_')
        base_plan_id = parts[0]
        if len(parts) > 1 and parts[1] == 'plan':
            base_plan_id = f"{parts[0]}_{parts[1]}"
        return base_plan_id
            
    def _verify_receipt_and_get_tier(self, provider, receipt_data, default_tier):
        """Verify receipt data and extract tier information"""
        if provider == 'google_play':
            receipt_verification = self._verify_google_play_receipt(receipt_data)
            # Use the tier from receipt verification if available
            if receipt_verification and 'tier' in receipt_verification:
                tier_value = receipt_verification['tier']
                logger.info(f"Received tier value from verification: {tier_value}")
                return SubscriptionTier.from_string(tier_value)
        elif provider == 'apple':
            # TODO: Implement Apple receipt verification
            pass
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {provider}"
            )
        return default_tier
        
    async def _create_new_subscription(
        self,
        db: AsyncSession,
        user_id: int,
        tier,
        product_id: str,
        provider: str,
        receipt_data: dict,
        current_time
    ):
        """Create a new subscription record"""

        # Preparar campos base
        subscription = SubscriptionModel(
            user_id=user_id,
            tier=tier.value,
            product_id=product_id,
            provider=provider,
            platform='android' if provider == 'google_play' else 'ios',
            receipt_data=json.dumps(receipt_data) if receipt_data else None,
            status=SubscriptionStatus.ACTIVE,
            auto_renew=True,
            created_at=current_time,
            updated_at=current_time,
            end_date=self._extract_subscription_end_date(None, receipt_data, provider)
        )

        # Agregar suscripción y commit
        db.add(subscription)
        await db.flush()  # Para obtener el ID sin cerrar la transacción

        # Historial de creación
        subscription_history = SubscriptionHistoryModel(
            subscription_id=subscription.id,
            action=SubscriptionAction.CREATED,
            details=f"New subscription created for tier {tier.value}",
            created_at=current_time
        )
        db.add(subscription_history)

        await db.commit()
        logger.info(f"Successfully created new subscription for user {user_id}, subscription ID: {subscription.id}")
        return subscription
        
    async def _create_new_subscription(
        self,
        db: AsyncSession,
        user_id: int,
        tier,
        product_id: str,
        provider: str,
        receipt_data: dict,
        current_time
    ):
        """Create a new subscription record"""

        # Generate a unique subscription ID
        unique_id = str(uuid.uuid4())

        new_subscription = SubscriptionModel(
            user_id=user_id,
            subscription_id=unique_id,
            tier=tier.value,
            status=SubscriptionStatus.ACTIVE,
            platform='android' if provider == 'google_play' else 'ios',
            product_id=product_id,
            provider=provider,
            start_date=current_time,
            end_date=self._extract_subscription_end_date(None, receipt_data, provider),
            receipt_data=json.dumps(receipt_data) if receipt_data else None,
            created_at=current_time,
            updated_at=current_time
        )

        db.add(new_subscription)
        await db.flush()  # Ensure subscription gets an ID without committing

        # Add to subscription history
        subscription_history = SubscriptionHistoryModel(
            subscription_id=new_subscription.id,
            action=SubscriptionAction.CREATED,
            details=f"Created new {tier.value} subscription",
            created_at=current_time
        )
        db.add(subscription_history)
        await db.commit()

        logger.info(f"Successfully created subscription {new_subscription.id} with tier {tier.value}")
        return new_subscription
    
    async def verify_subscription(self, token: str):
        """Verify user subscription using async SQLAlchemy."""
        async for db in get_db():
            try:
                logger.info("Starting subscription verification process")
                user = await self.get_user_from_token(token)
                logger.info(f"User retrieved from token: user_id={user.id}, email={user.email}")

                current_time = datetime.now(timezone.utc)

                # Buscar suscripción activa
                stmt_active = (
                    select(SubscriptionModel)
                    .where(
                        SubscriptionModel.user_id == user.id,
                        SubscriptionModel.status == SubscriptionStatus.ACTIVE,
                        SubscriptionModel.end_date > current_time
                    )
                    .order_by(SubscriptionModel.created_at.desc())
                )
                result_active = await db.execute(stmt_active)
                subscription = result_active.scalars().first()

                if subscription:
                    logger.info(f"Found active subscription: id={subscription.id}")
                    return {
                        "has_subscription": True,
                        "subscription": {
                            "id": subscription.id,
                            "tier": subscription.tier.value,
                            "status": subscription.status.value,
                            "provider": subscription.provider,
                            "product_id": subscription.product_id,
                            "start_date": subscription.created_at.isoformat(),
                            "end_date": subscription.end_date.isoformat()
                        }
                    }

                # Buscar suscripción expirada
                logger.info("No active subscription found, checking for expired subscriptions")
                stmt_expired = (
                    select(SubscriptionModel)
                    .where(
                        SubscriptionModel.user_id == user.id,
                        SubscriptionModel.status == SubscriptionStatus.ACTIVE,
                        SubscriptionModel.end_date <= current_time
                    )
                    .order_by(SubscriptionModel.created_at.desc())
                )
                result_expired = await db.execute(stmt_expired)
                expired_subscription = result_expired.scalars().first()

                if expired_subscription:
                    logger.info(f"Found expired subscription: id={expired_subscription.id}, updating to EXPIRED")
                    expired_subscription.status = SubscriptionStatus.EXPIRED
                    db.add(expired_subscription)

                    history = SubscriptionHistoryModel(
                        subscription_id=expired_subscription.id,
                        action=SubscriptionAction.EXPIRED,
                        tier=expired_subscription.tier,
                        created_at=current_time
                    )
                    db.add(history)
                    await db.commit()
                    logger.info("Subscription status updated and history created")

                return {"has_subscription": False}

            except Exception as e:
                import traceback
                logger.error(f"Error in verify_subscription: {e}\n{traceback.format_exc()}")
                raise
    
    async def cancel_subscription(self, token: str):
        """Cancel a user's active subscription"""
        async for db in get_db():
            try:
                user = await self.get_user_from_token(token)

                # Buscar suscripción activa
                stmt = (
                    select(SubscriptionModel)
                    .where(
                        and_(
                            SubscriptionModel.user_id == user.id,
                            SubscriptionModel.status == SubscriptionStatus.ACTIVE
                        )
                    )
                )
                result = await db.execute(stmt)
                subscription = result.scalars().first()

                if not subscription:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No active subscription found"
                    )

                # Actualizar estado
                subscription.status = SubscriptionStatus.CANCELLED
                subscription.auto_renew = False

                history = SubscriptionHistoryModel(
                    subscription_id=subscription.id,
                    action=SubscriptionAction.CANCELLED,
                    details="Subscription cancelled by user"
                )
                db.add(history)
                await db.commit()

                return {
                    "message": "Subscription cancelled successfully",
                    "subscription_id": subscription.subscription_id,
                    "end_date": subscription.end_date.isoformat() if subscription.end_date else None
                }

            except Exception as e:
                await db.rollback()
                import traceback
                logger.error(f"Error cancelling subscription: {e}\n{traceback.format_exc()}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="An error occurred while cancelling the subscription"
                )
    async def verify_receipt(self, token: str, receipt_data: dict):
        """Verify receipt from App Store or Google Play"""
        user = await self.get_user_from_token(token)

        platform = receipt_data.get('platform', '').lower()

        if platform == 'android':
            return self._verify_google_play_receipt(receipt_data)
        elif platform == 'ios':
            # iOS verification is disabled for now
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="iOS subscription verification is not enabled yet"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid platform specified"
            )
    
    def _verify_google_play_receipt(self, receipt_data):
        """Verify Google Play receipt using Firebase credentials"""
        if not GOOGLE_API_AVAILABLE:
            logger.error("Google API dependencies not available")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google API verification not available"
            )
        
        try:
            # Get required data from receipt
            purchase_token = receipt_data.get('purchaseToken')
            product_id = receipt_data.get('productId')
            package_name = receipt_data.get('packageName', _SETTINGS.google_play_package_name)
            
            if not all([purchase_token, product_id]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing required receipt data"
                )
            
            # Extract base plan ID from product ID (e.g., 'pro_plan_monthly' -> 'pro_plan')
            base_plan_id = product_id.split('_')[0]
            if len(product_id.split('_')) > 1 and product_id.split('_')[1] == 'plan':
                base_plan_id = f"{product_id.split('_')[0]}_{product_id.split('_')[1]}"
            
            logger.info(f"Extracted base plan ID: {base_plan_id} from product ID: {product_id}")
            
            # Map product IDs to subscription tiers
            tier_mapping = {
                'pro_plan': SubscriptionTier.PRO,
                'analyst_plan': SubscriptionTier.ANALYST,
                # Add more product IDs as needed
            }
            
            # If the base plan ID is not in our mapping, try to use the from_string method
            if base_plan_id not in tier_mapping:
                # Try to extract the tier name from the base plan ID
                possible_tier = base_plan_id.split('_')[0] if '_' in base_plan_id else base_plan_id
                logger.info(f"Trying to map {possible_tier} to a subscription tier")
                
                # Use the from_string method to convert to enum
                try:
                    subscription_tier = SubscriptionTier.from_string(possible_tier)
                    logger.info(f"Successfully mapped to tier: {subscription_tier} (value: {subscription_tier.value})")
                except Exception as tier_error:
                    error_traceback = traceback.format_exc()
                    logger.error(f"Error mapping tier from string '{possible_tier}': {tier_error}\nTraceback: {error_traceback}")
                    # Default to FREE tier if mapping fails
                    subscription_tier = SubscriptionTier.FREE
                    logger.info(f"Defaulting to FREE tier after mapping failure")
            else:
                subscription_tier = tier_mapping[base_plan_id]
                logger.info(f"Using mapped tier: {subscription_tier} (value: {subscription_tier.value})")
            
            # For now, return a mock verification response
            # This avoids the private key issues until proper credentials are set up
            logger.info(f"Returning mock verification for product ID: {product_id}")
            
            # Set a default expiry time (30 days from now)
            expiry_time = datetime.now(timezone.utc) + timedelta(days=30)
            
            return {
                "verified": True,
                "subscription_id": product_id,
                "tier": subscription_tier.value,
                "end_date": expiry_time.isoformat()
            }
            
        except Exception as e:
            error_traceback = traceback.format_exc()
            logger.error(f"Error verifying Google Play receipt: {e}\nTraceback: {error_traceback}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error verifying Google Play receipt: {str(e)}"
            )

    async def process_subscription_notification(self, notification_data: dict, token: str = None):
        async for db in get_db():
            try:
                logger.info(f"Processing notification data: {notification_data}")

                # Check if this is a Google Play subscription notification
                subscription_notification = notification_data.get('subscriptionNotification') or notification_data.get('voidedPurchaseNotification')
                if subscription_notification:
                    # Extract data from notification
                    purchase_token = subscription_notification.get('purchaseToken')
                    subscription_id = subscription_notification.get('subscriptionId')
                    package_name = notification_data.get('packageName')
                    notification_type = subscription_notification.get('notificationType')

                    if not all([purchase_token, subscription_id]):
                        logger.error(f"Missing required notification data: {notification_data}")
                        return {"success": False, "error": "Missing required notification data"}

                    # Find the user with this subscription by searching the receipt_data
                    stmt = select(SubscriptionModel).where(
                        SubscriptionModel.receipt_data.like(f'%{purchase_token}%')
                    )
                    result = await db.execute(stmt)
                    existing_sub = result.scalars().first()

                    if not existing_sub:
                        logger.warning(f"No subscription found for purchase token: {purchase_token}")
                        return {
                            "success": False,
                            "error": "No subscription found for this purchase token. Unable to associate with a user."
                        }

                    # Extract base plan ID and determine subscription tier
                    user_id = existing_sub.user_id
                    base_plan_id = self._extract_base_plan_id(subscription_id)
                    tier_mapping = {'pro_plan': SubscriptionTier.PRO, 'analyst_plan': SubscriptionTier.ANALYST}
                    subscription_tier = self._determine_subscription_tier(base_plan_id, tier_mapping)

                    # Prepare receipt data object
                    receipt_data = {
                        'purchaseToken': purchase_token,
                        'productId': subscription_id,
                        'packageName': package_name
                    }

                    now = datetime.now(timezone.utc)

                    # Handle notification types
                    if notification_type in [1, 2, 4, 7]:  # RECOVERED, RENEWED, PURCHASED, RESTARTED
                        if isinstance(subscription_tier, str):
                            subscription_tier = SubscriptionTier.from_string(subscription_tier)

                        # Update existing subscription
                        existing_sub.tier = subscription_tier
                        existing_sub.product_id = subscription_id
                        existing_sub.status = SubscriptionStatus.ACTIVE
                        existing_sub.platform = 'android'
                        existing_sub.receipt_data = json.dumps(receipt_data)
                        existing_sub.updated_at = now
                        existing_sub.end_date = self._extract_subscription_end_date(notification_data, receipt_data, 'google_play')

                        # Determine action type
                        action = SubscriptionAction.UPDATED
                        if notification_type == 4:
                            action = SubscriptionAction.CREATED
                        elif notification_type == 2:
                            action = SubscriptionAction.RENEWED

                        # Add to subscription history
                        db.add(SubscriptionHistoryModel(
                            subscription_id=existing_sub.id,
                            action=action,
                            details=f"Updated subscription to {subscription_tier.value} via notification",
                            created_at=now
                        ))
                        await db.commit()
                        return {"success": True, "subscription_id": existing_sub.id}

                    elif notification_type == 3:  # CANCELED
                        existing_sub.status = SubscriptionStatus.CANCELLED
                        existing_sub.auto_renew = False

                        db.add(SubscriptionHistoryModel(
                            subscription_id=existing_sub.id,
                            action=SubscriptionAction.CANCELLED,
                            details="Subscription cancelled via notification",
                            created_at=now
                        ))
                        await db.commit()
                        return {"success": True, "subscription_id": existing_sub.id}

                    elif notification_type == 13:  # EXPIRED
                        existing_sub.status = SubscriptionStatus.EXPIRED

                        db.add(SubscriptionHistoryModel(
                            subscription_id=existing_sub.id,
                            action=SubscriptionAction.EXPIRED,
                            details="Subscription expired via notification",
                            created_at=now
                        ))
                        await db.commit()
                        return {"success": True, "subscription_id": existing_sub.id}

                    # Default handling for untracked types
                    logger.info(f"Processed notification type {notification_type} for subscription {subscription_id}")
                    return {"success": True, "message": f"Processed notification type {notification_type}"}

                # If no known notification format found
                logger.warning("No valid notification found in payload")
                return {"success": False, "error": "Invalid or unsupported notification format"}

            except Exception as e:
                await db.rollback()
                error_traceback = traceback.format_exc()
                logger.error(f"Error processing subscription notification: {e}\nTraceback: {error_traceback}")
                return {"success": False, "error": str(e)}

    async def _get_subscription_info(self, package_name, subscription_id, token):
        """Get subscription details from Google Play"""
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
            creds = service_account.Credentials.from_service_account_info(
                firebase_credentials,
                scopes=['https://www.googleapis.com/auth/androidpublisher']
            )
            
            # Build the Android Publisher API client
            service = build('androidpublisher', 'v3', credentials=creds)
            
            # Get subscription purchase details
            result = service.purchases().subscriptions().get(
                packageName=package_name,
                subscriptionId=subscription_id,
                token=token
            ).execute()
            
            return result
        except Exception as e:
            error_traceback = traceback.format_exc()
            logger.error(f"Error getting subscription info from Google Play: {e}\nTraceback: {error_traceback}")
            return None

    def process_subscription_notification_sync(self, notification_data, db):
        """Synchronous version of process_subscription_notification"""
        try:
            # Create an event loop for this thread if it doesn't exist
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run the async function in the event loop
            return loop.run_until_complete(
                self.process_subscription_notification(
                    notification_data, 
                    db, 
                    notification_data.get('token') or notification_data.get('idToken')
                )
            )
        except Exception as e:
            error_traceback = traceback.format_exc()
            logger.error(f"Error in sync subscription notification processing: {e}\nTraceback: {error_traceback}")
            raise 

    def _determine_subscription_tier(self, base_plan_id, tier_mapping=None):
        """Helper method to determine subscription tier from plan ID"""
        if tier_mapping is None:
            tier_mapping = {
                'pro_plan': SubscriptionTier.PRO,
                'analyst_plan': SubscriptionTier.ANALYST,
            }
            
        # If the base plan ID is not in our mapping, try to use the from_string method
        if base_plan_id not in tier_mapping:
            # Try to extract the tier name from the base plan ID
            possible_tier = base_plan_id.split('_')[0] if '_' in base_plan_id else base_plan_id
            logger.info(f"Trying to map {possible_tier} to a subscription tier")
            
            # Use the from_string method to convert to enum
            try:
                subscription_tier = SubscriptionTier.from_string(possible_tier)
                logger.info(f"Successfully mapped to tier: {subscription_tier} (value: {subscription_tier.value})")
            except Exception as tier_error:
                error_traceback = traceback.format_exc()
                logger.error(f"Error mapping tier from string '{possible_tier}': {tier_error}\nTraceback: {error_traceback}")
                # Default to FREE tier if mapping fails
                subscription_tier = SubscriptionTier.FREE
                logger.info(f"Defaulting to FREE tier after mapping failure")
        else:
            subscription_tier = tier_mapping[base_plan_id]
            logger.info(f"Using mapped tier: {subscription_tier} (value: {subscription_tier.value})")
            
        return subscription_tier 

    def _extract_subscription_end_date(self, notification_data, receipt_data=None, provider=None):
        """Extract subscription end date from notification or receipt data"""
        end_date = None
        # Try to get from notification data first
        logger.info(f"Extracting subscription end date from notification data: {notification_data}")
        logger.info(f"Extracting subscription end date from receipt data: {receipt_data}")
        if notification_data:
            # For Google Play
            if 'expiryTimeMillis' in notification_data:
                millis = int(notification_data['expiryTimeMillis'])
                end_date = datetime.fromtimestamp(millis / 1000.0, tz=timezone.utc)
                logger.info(f"Extracted end date from expiryTimeMillis: {end_date}")
                return end_date
                
            # For Google Play - alternative field
            if 'validUntilTimestampMsec' in notification_data:
                millis = int(notification_data['validUntilTimestampMsec'])
                end_date = datetime.fromtimestamp(millis / 1000.0, tz=timezone.utc)
                logger.info(f"Extracted end date from validUntilTimestampMsec: {end_date}")
                return end_date
                
            # For Google Play - another alternative
            if 'expireTime' in notification_data:
                # Could be in ISO format string
                try:
                    end_date = datetime.fromisoformat(notification_data['expireTime'].replace('Z', '+00:00'))
                    logger.info(f"Extracted end date from expireTime: {end_date}")
                    return end_date
                except (ValueError, TypeError):
                    logger.warning(f"Failed to parse expireTime: {notification_data['expireTime']}")
            
            # For Apple App Store
            if 'expires_date_ms' in notification_data:
                millis = int(notification_data['expires_date_ms'])
                end_date = datetime.fromtimestamp(millis / 1000.0, tz=timezone.utc)
                logger.info(f"Extracted end date from expires_date_ms: {end_date}")
                return end_date

        # Try to get from receipt data if available
        if receipt_data:
            # For Google Play
            if 'expiryTimeMillis' in receipt_data:
                millis = int(receipt_data['expiryTimeMillis'])
                end_date = datetime.fromtimestamp(millis / 1000.0, tz=timezone.utc)
                logger.info(f"Extracted end date from receipt expiryTimeMillis: {end_date}")
                return end_date
                
            # For Apple App Store
            if 'expires_date_ms' in receipt_data:
                millis = int(receipt_data['expires_date_ms'])
                end_date = datetime.fromtimestamp(millis / 1000.0, tz=timezone.utc)
                logger.info(f"Extracted end date from receipt expires_date_ms: {end_date}")
                return end_date
        
        # If we couldn't find an end date, use default period based on provider
        current_time = datetime.now(timezone.utc)
        if provider == 'google_play' or provider == 'android':
            # Default to 30 days for Google Play
            end_date = current_time + timedelta(days=30)
            logger.warning(f"Using default end date (30 days): {end_date}")
        else:
            # Default to 30 days for Apple/other providers
            end_date = current_time + timedelta(days=30)
            logger.warning(f"Using default end date (30 days): {end_date}")
            
        return end_date 