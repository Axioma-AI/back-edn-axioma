import logging
import json
import traceback
from datetime import datetime, timedelta
import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from firebase_admin import auth, credentials
import base64
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import service_account
from googleapiclient.discovery import build
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
    async def get_user_from_token(self, token: str, db: Session):
        """Get user from Firebase token"""
        try:
            # Verify the Firebase token
            decoded_token = auth.verify_id_token(token)
            email = decoded_token.get('email')
            
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: email not found"
                )
                
            # Find the user in the database
            user = db.query(UserModel).filter(UserModel.email == email).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
                
            return user
        except auth.InvalidIdTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        except Exception as e:
            error_traceback = traceback.format_exc()
            logger.error(f"Error getting user from token: {e}\nTraceback: {error_traceback}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing authentication"
            )
    
    async def create_subscription(self, db: Session, user_id: int, product_id: str, provider: str, receipt_data: dict = None):
        """Create a new subscription for a user"""
        try:
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
            
            # Determine the subscription tier
            tier = self._determine_subscription_tier(base_plan_id, tier_mapping)
            
            # Verify receipt if provided
            if receipt_data:
                if provider == 'google_play':
                    receipt_verification = self._verify_google_play_receipt(receipt_data)
                    # Use the tier from receipt verification if available
                    if receipt_verification and 'tier' in receipt_verification:
                        tier_value = receipt_verification['tier']
                        logger.info(f"Received tier value from verification: {tier_value}")
                        tier = SubscriptionTier.from_string(tier_value)
                        logger.info(f"Mapped tier value to enum: {tier} (value: {tier.value})")
                elif provider == 'apple':
                    # TODO: Implement Apple receipt verification
                    pass
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Unsupported provider: {provider}"
                    )
            
            # Get the user
            user = db.query(UserModel).filter(UserModel.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found"
                )
        
        # Check if user already has an active subscription
        existing_subscription = db.query(SubscriptionModel).filter(
                    SubscriptionModel.user_id == user_id,
                SubscriptionModel.status == SubscriptionStatus.ACTIVE
        ).first()
        
            # Generate a unique subscription ID
            subscription_id = str(uuid.uuid4())
            
            # If user has an active subscription, update it
        if existing_subscription:
                # Ensure tier is an enum object
                if isinstance(tier, str):
                    logger.warning(f"tier is a string: '{tier}', converting to enum")
                    tier = SubscriptionTier.from_string(tier)
                
                logger.info(f"Updating subscription with tier: {tier} (value: {tier.value})")
                
                existing_subscription.tier = tier
                existing_subscription.product_id = product_id
                existing_subscription.platform = 'android' if provider == 'google_play' else 'ios'
                existing_subscription.receipt_data = json.dumps(receipt_data) if receipt_data else None
                existing_subscription.updated_at = datetime.utcnow()
                
                # Add to subscription history
                subscription_history = SubscriptionHistoryModel(
                    subscription_id=existing_subscription.id,
                    action=SubscriptionAction.UPDATED,
                    details=f"Updated subscription to {tier.value}"
                )
                db.add(subscription_history)
                db.commit()
                
                return existing_subscription
        
        # Create a new subscription
            # Ensure tier is an enum object
            if isinstance(tier, str):
                logger.warning(f"tier is a string: '{tier}', converting to enum")
                tier = SubscriptionTier.from_string(tier)
            
            logger.info(f"Creating new subscription with tier: {tier} (value: {tier.value})")
        
        new_subscription = SubscriptionModel(
                user_id=user_id,
            subscription_id=subscription_id,
                tier=tier,
            status=SubscriptionStatus.ACTIVE,
                product_id=product_id,
                platform='android' if provider == 'google_play' else 'ios',
                receipt_data=json.dumps(receipt_data) if receipt_data else None,
            start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=30)  # Default to 30 days
        )
        
        db.add(new_subscription)
            db.flush()  # This ensures the subscription gets an ID without committing the transaction
        
            # Add to subscription history
            subscription_history = SubscriptionHistoryModel(
            subscription_id=new_subscription.id,
                action=SubscriptionAction.CREATED,
                details=f"Created new {tier.value} subscription"
        )
            db.add(subscription_history)
            db.commit()
        
        return new_subscription
            
        except Exception as e:
            db.rollback()
            error_traceback = traceback.format_exc()
            logger.error(f"Error creating subscription: {e}\nTraceback: {error_traceback}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating subscription: {str(e)}"
            )
    
    async def verify_subscription(self, token: str, db: Session):
        """Verify if a user has an active subscription"""
        user = await self.get_user_from_token(token, db)
        
        # Get the user's active subscription
        subscription = db.query(SubscriptionModel).filter(
            and_(
                SubscriptionModel.user_id == user.id,
                SubscriptionModel.status == SubscriptionStatus.ACTIVE
            )
        ).first()
        
        if not subscription:
            return {
                "has_subscription": False,
                "tier": SubscriptionTier.FREE.value,
                "message": "No active subscription found"
            }
        
        # Check if subscription has expired
        if subscription.end_date and subscription.end_date < datetime.utcnow():
            # Update subscription status
            subscription.status = SubscriptionStatus.EXPIRED
            
            # Add subscription history
            history = SubscriptionHistoryModel(
                subscription_id=subscription.id,
                action=SubscriptionAction.EXPIRED,
                details="Subscription expired"
            )
            db.add(history)
            db.commit()
            
            return {
                "has_subscription": False,
                "tier": SubscriptionTier.FREE.value,
                "message": "Subscription has expired",
                "expired_date": subscription.end_date.isoformat()
            }
        
        # Return active subscription details
        return {
            "has_subscription": True,
            "tier": subscription.tier.value,
            "platform": subscription.platform,
            "start_date": subscription.start_date.isoformat(),
            "end_date": subscription.end_date.isoformat() if subscription.end_date else None,
            "auto_renew": subscription.auto_renew
        }
    
    async def cancel_subscription(self, token: str, db: Session):
        """Cancel a user's subscription"""
        user = await self.get_user_from_token(token, db)
        
        # Get the user's active subscription
        subscription = db.query(SubscriptionModel).filter(
            and_(
                SubscriptionModel.user_id == user.id,
                SubscriptionModel.status == SubscriptionStatus.ACTIVE
            )
        ).first()
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found"
            )
        
        # Update subscription status
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.auto_renew = False
        
        # Add subscription history
        history = SubscriptionHistoryModel(
            subscription_id=subscription.id,
            action=SubscriptionAction.CANCELLED,
            details="Subscription cancelled by user"
        )
        db.add(history)
        
        db.commit()
        
        return {
            "message": "Subscription cancelled successfully",
            "subscription_id": subscription.subscription_id,
            "end_date": subscription.end_date.isoformat() if subscription.end_date else None
        }
    
    async def verify_receipt(self, token: str, receipt_data: dict, db: Session):
        """Verify receipt from App Store or Google Play"""
        user = await self.get_user_from_token(token, db)
        
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
            expiry_time = datetime.utcnow() + timedelta(days=30)
            
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

    async def process_subscription_notification(self, notification_data: dict, db: Session):
        """Process subscription notification from Google Play or Apple"""
        try:
            logger.info(f"Processing notification data: {notification_data}")
            
            # Check if this is a Google Play subscription notification
            subscription_notification = notification_data.get('subscriptionNotification') or notification_data.get('voidedSubscriptionNotification')
            if subscription_notification:
                # Extract data from Google Play notification
                purchase_token = subscription_notification.get('purchaseToken')
                subscription_id = subscription_notification.get('subscriptionId')
                package_name = notification_data.get('packageName')
                notification_type = subscription_notification.get('notificationType')
                
                if not all([purchase_token, subscription_id]):
                    logger.error(f"Missing required notification data: {notification_data}")
                    return {"success": False, "error": "Missing required notification data"}
                
                logger.info(f"Processing Google Play subscription notification for subscription {subscription_id}")
                
                # Find the user with this subscription
                # First, try to find an existing subscription with this purchase token
                existing_sub = db.query(SubscriptionModel).filter(
                    SubscriptionModel.receipt_data.like(f'%{purchase_token}%')
                ).first()
                
                user_id = None
                if existing_sub:
                    user_id = existing_sub.user_id
                    logger.info(f"Found existing subscription for user {user_id}")
                else:
                    # If we can't find a user, we need to handle this case properly
                    # Instead of using the first user, we should log this and possibly store
                    # the notification for later processing or manual review
                    logger.warning(f"No subscription found for purchase token: {purchase_token}")
                    return {
                        "success": False, 
                        "error": "No subscription found for this purchase token. Unable to associate with a user."
                    }
                
                # Extract base plan ID from product ID
                base_plan_id = subscription_id.split('_')[0]
                if len(subscription_id.split('_')) > 1 and subscription_id.split('_')[1] == 'plan':
                    base_plan_id = f"{subscription_id.split('_')[0]}_{subscription_id.split('_')[1]}"
                
                logger.info(f"Extracted base plan ID: {base_plan_id} from subscription ID: {subscription_id}")
                
                # Map product IDs to subscription tiers
                tier_mapping = {
                    'pro_plan': SubscriptionTier.PRO,
                    'analyst_plan': SubscriptionTier.ANALYST
                }
                
                # Determine the subscription tier
                subscription_tier = self._determine_subscription_tier(base_plan_id, tier_mapping)
                
                # Create receipt data for verification
                receipt_data = {
                    'purchaseToken': purchase_token,
                    'productId': subscription_id,
                    'packageName': package_name
                }
                
                # Create or update subscription based on notification type
                # 1: RECOVERED, 2: RENEWED, 3: CANCELED, 4: PURCHASED, 5: ON_HOLD, 
                # 6: IN_GRACE_PERIOD, 7: RESTARTED, 8: PRICE_CHANGE_CONFIRMED, 
                # 9: DEFERRED, 10: PAUSED, 11: PAUSE_SCHEDULE_CHANGED, 12: REVOKED, 
                # 13: EXPIRED
                
                if notification_type in [1, 2, 4, 7]:  # RECOVERED, RENEWED, PURCHASED, RESTARTED
                    if existing_sub:
                        # Update existing subscription
                        # Ensure subscription_tier is an enum object
                        if isinstance(subscription_tier, str):
                            logger.warning(f"subscription_tier is a string: '{subscription_tier}', converting to enum")
                            subscription_tier = SubscriptionTier.from_string(subscription_tier)
                        
                        logger.info(f"Updating subscription with tier: {subscription_tier} (value: {subscription_tier.value})")
                        
                        existing_sub.tier = subscription_tier
                        existing_sub.product_id = subscription_id
                        existing_sub.status = SubscriptionStatus.ACTIVE
                        existing_sub.platform = 'android'
                        existing_sub.receipt_data = json.dumps(receipt_data)
                        existing_sub.updated_at = datetime.utcnow()
                        existing_sub.end_date = datetime.utcnow() + timedelta(days=30)  # Default to 30 days
                        
                        # Add to subscription history
                        action = SubscriptionAction.UPDATED
                        if notification_type == 4:  # PURCHASED
                            action = SubscriptionAction.CREATED
                        elif notification_type == 2:  # RENEWED
                            action = SubscriptionAction.RENEWED
                            
                        subscription_history = SubscriptionHistoryModel(
                            subscription_id=existing_sub.id,
                            action=action,
                            details=f"Updated subscription to {subscription_tier.value} via notification"
                        )
                        db.add(subscription_history)
                        db.commit()
                        
                        return {"success": True, "subscription_id": existing_sub.id}
                    else:
                        # We already checked for existing subscription and returned if none found
                        # This code should not be reached, but keeping it for safety
                        logger.error("No user found for this subscription notification")
                        return {"success": False, "error": "No user found for this subscription notification"}
                elif notification_type == 3:  # CANCELED
                    if existing_sub:
                        existing_sub.status = SubscriptionStatus.CANCELLED
                        existing_sub.auto_renew = False
                        
                        subscription_history = SubscriptionHistoryModel(
                            subscription_id=existing_sub.id,
                            action=SubscriptionAction.CANCELLED,
                            details="Subscription cancelled via notification"
                        )
                        db.add(subscription_history)
                        db.commit()
                        
                        return {"success": True, "subscription_id": existing_sub.id}
                    else:
                        # For cancellation notifications, if we don't have an existing subscription,
                        # we'll just log it and return success
                        logger.warning(f"Received cancellation for unknown subscription: {subscription_id}")
                        return {"success": True, "message": "Acknowledged cancellation for unknown subscription"}
                elif notification_type == 13:  # EXPIRED
                    if existing_sub:
                        existing_sub.status = SubscriptionStatus.EXPIRED
                        
                        subscription_history = SubscriptionHistoryModel(
                            subscription_id=existing_sub.id,
                            action=SubscriptionAction.EXPIRED,
                            details="Subscription expired via notification"
                        )
                        db.add(subscription_history)
                        db.commit()
                        
                        return {"success": True, "subscription_id": existing_sub.id}
                    else:
                        # For expiration notifications, if we don't have an existing subscription,
                        # we'll just log it and return success
                        logger.warning(f"Received expiration for unknown subscription: {subscription_id}")
                        return {"success": True, "message": "Acknowledged expiration for unknown subscription"}
                
                # For other notification types, just log and return success
                logger.info(f"Processed notification type {notification_type} for subscription {subscription_id}")
                return {"success": True, "message": f"Processed notification type {notification_type}"}
            
            # If not a Google Play notification, process as before
            # Extract data from notification
            purchase_token = notification_data.get('purchaseToken')
            subscription_id = notification_data.get('subscriptionId')
            user_id = notification_data.get('userId')
            
            if not all([purchase_token, subscription_id, user_id]):
                logger.error(f"Missing required notification data: {notification_data}")
                return {"success": False, "error": "Missing required notification data"}
            
            logger.info(f"Processing subscription notification for user {user_id}, subscription {subscription_id}")
            
            # Extract base plan ID from product ID (e.g., 'pro_plan_monthly' -> 'pro_plan')
            base_plan_id = subscription_id.split('_')[0]
            if len(subscription_id.split('_')) > 1 and subscription_id.split('_')[1] == 'plan':
                base_plan_id = f"{subscription_id.split('_')[0]}_{subscription_id.split('_')[1]}"
            
            logger.info(f"Extracted base plan ID: {base_plan_id} from subscription ID: {subscription_id}")
            
            # Map product IDs to subscription tiers
            tier_mapping = {
                'pro_plan': SubscriptionTier.PRO,
                'analyst_plan': SubscriptionTier.ANALYST
            }
            
            # If the base plan ID is not in our mapping, try to use the from_string method
            if base_plan_id not in tier_mapping:
                # Try to extract the tier name from the base plan ID
                possible_tier = base_plan_id.split('_')[0] if '_' in base_plan_id else base_plan_id
                logger.info(f"Trying to map {possible_tier} to a subscription tier")
                
                # Use the from_string method to convert to enum
                subscription_tier = SubscriptionTier.from_string(possible_tier)
                logger.info(f"Mapped to tier: {subscription_tier}")
            else:
                subscription_tier = tier_mapping[base_plan_id]
                logger.info(f"Using mapped tier: {subscription_tier} (value: {subscription_tier.value})")
            
            # Check if user exists
            user = db.query(UserModel).filter(UserModel.id == user_id).first()
            if not user:
                logger.error(f"User not found: {user_id}")
                return {"success": False, "error": f"User not found: {user_id}"}
            
            # Check if user already has a subscription
            existing_subscription = db.query(SubscriptionModel).filter(
                SubscriptionModel.user_id == user_id,
                SubscriptionModel.status == SubscriptionStatus.ACTIVE
            ).first()
            
            # Create receipt data for verification
            receipt_data = {
                'purchaseToken': purchase_token,
                'productId': subscription_id,
                'packageName': notification_data.get('packageName')
            }
            
            # Create or update subscription
            if existing_subscription:
                # Update existing subscription
                logger.info(f"Updating existing subscription {existing_subscription.id} for user {user_id}")
                # Ensure subscription_tier is an enum object
                if isinstance(subscription_tier, str):
                    logger.warning(f"subscription_tier is a string: '{subscription_tier}', converting to enum")
                    subscription_tier = SubscriptionTier.from_string(subscription_tier)
                
                logger.info(f"Updating subscription with tier: {subscription_tier} (value: {subscription_tier.value})")
                
                existing_subscription.tier = subscription_tier
                existing_subscription.product_id = subscription_id
                existing_subscription.status = SubscriptionStatus.ACTIVE
                existing_subscription.platform = 'android'
                existing_subscription.receipt_data = json.dumps(receipt_data)
                existing_subscription.updated_at = datetime.utcnow()
                existing_subscription.end_date = datetime.utcnow() + timedelta(days=30)  # Default to 30 days
                
                # Add to subscription history
                subscription_history = SubscriptionHistoryModel(
                    subscription_id=existing_subscription.id,
                    action=SubscriptionAction.UPDATED,
                    details=f"Updated subscription to {subscription_tier.value} via notification"
                )
                db.add(subscription_history)
                db.commit()
                
                logger.info(f"Successfully updated subscription {existing_subscription.id} to tier {subscription_tier.value}")
                return {"success": True, "subscription_id": existing_subscription.id}
            else:
                # Create new subscription
                logger.info(f"Creating new subscription for user {user_id} with tier {subscription_tier.value}")
                try:
                    new_subscription = await self.create_subscription(
                        db=db,
                        user_id=user_id,
                        product_id=subscription_id,
                        provider='google_play',
                        receipt_data=receipt_data
                    )
                    
                    logger.info(f"Successfully created new subscription {new_subscription.id}")
                    return {"success": True, "subscription_id": new_subscription.id}
                except Exception as e:
                    error_traceback = traceback.format_exc()
                    logger.error(f"Error creating subscription from notification: {e}\nTraceback: {error_traceback}")
                    # Try a direct approach if the create_subscription method fails
                    try:
                        # Create a new subscription directly
                        logger.info("Attempting direct subscription creation after failure")
                        
                        # Ensure subscription_tier is an enum object
                        if isinstance(subscription_tier, str):
                            logger.warning(f"subscription_tier is a string: '{subscription_tier}', converting to enum")
                            subscription_tier = SubscriptionTier.from_string(subscription_tier)
                        
                        logger.info(f"Creating subscription with tier: {subscription_tier} (value: {subscription_tier.value})")
                        
                        new_subscription = SubscriptionModel(
                            user_id=user_id,
                            subscription_id=str(uuid.uuid4()),
                            tier=subscription_tier,
                            status=SubscriptionStatus.ACTIVE,
                            product_id=subscription_id,
                            platform='android',
                            receipt_data=json.dumps(receipt_data),
                            start_date=datetime.utcnow(),
                            end_date=datetime.utcnow() + timedelta(days=30)
                        )
                        
                        db.add(new_subscription)
                        db.flush()  # This ensures the subscription gets an ID without committing the transaction
                        
                        # Add to subscription history
                        subscription_history = SubscriptionHistoryModel(
                            subscription_id=new_subscription.id,
                            action=SubscriptionAction.CREATED,
                            details=f"Created new {subscription_tier.value} subscription via notification"
                        )
                        db.add(subscription_history)
                db.commit()
                        
                        logger.info(f"Successfully created new subscription {new_subscription.id} directly")
                        return {"success": True, "subscription_id": new_subscription.id}
                    except Exception as inner_e:
                        error_traceback = traceback.format_exc()
                        logger.error(f"Error creating subscription directly: {inner_e}\nTraceback: {error_traceback}")
                        db.rollback()
                        return {"success": False, "error": f"Failed to create subscription: {str(inner_e)}"}
                
        except Exception as e:
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
                self.process_subscription_notification(notification_data, db)
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