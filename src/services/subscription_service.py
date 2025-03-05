import logging
import json
import traceback
from datetime import datetime, timedelta, timezone
import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
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
    async def get_user_from_token(self, token: str, db: Session):
        """Get user from Firebase token"""
        try:
            logger.info(f"Verifying Firebase token: {token[:10]}...")
            
            # Verify the Firebase token
            decoded_token = auth.verify_id_token(token)
            logger.info(f"Token verified successfully. Decoded token contains: {list(decoded_token.keys())}")
            
            email = decoded_token.get('email')
            
            if not email:
                logger.error(f"Email not found in token. Token keys: {list(decoded_token.keys())}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: email not found"
                )
                
            # Find the user in the database
            logger.info(f"Looking up user by email: {email}")
            user = db.query(UserModel).filter(UserModel.email == email).first()
            
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
    
    async def create_subscription(self, db: Session, user_id: int, product_id: str, provider: str, receipt_data: dict = None):
        """Create a new subscription for a user or update an existing one"""
        try:
            # Extract base plan ID from product ID (e.g., 'pro_plan_monthly' -> 'pro_plan')
            base_plan_id = self._extract_base_plan_id(product_id)
            logger.info(f"Extracted base plan ID: {base_plan_id} from product ID: {product_id}")
            
            # Determine the subscription tier
            tier_mapping = {
                'pro_plan': SubscriptionTier.PRO,
                'analyst_plan': SubscriptionTier.ANALYST,
            }
            tier = self._determine_subscription_tier(base_plan_id, tier_mapping)
            
            # Verify receipt if provided and update tier if necessary
            if receipt_data:
                tier = self._verify_receipt_and_get_tier(provider, receipt_data, tier)
            
            # Ensure tier is an enum object
            if isinstance(tier, str):
                logger.warning(f"tier is a string: '{tier}', converting to enum")
                tier = SubscriptionTier.from_string(tier)
                
            logger.info(f"Processing subscription with tier: {tier} (value: {tier.value})")
            
            # Check if user has an active subscription
            existing_subscription = (
                db.query(SubscriptionModel)
                .filter(SubscriptionModel.user_id == user_id, SubscriptionModel.status == SubscriptionStatus.ACTIVE)
                .first()
            )
            
            current_time = datetime.now(timezone.utc)
            
            # Either update existing subscription or create a new one
            if existing_subscription:
                logger.info(f"Updating existing subscription for user {user_id}")
                subscription = self._update_existing_subscription(
                    db, existing_subscription, tier, product_id, provider, receipt_data, current_time
                )
            else:
                logger.info(f"Creating new subscription for user {user_id}")
                subscription = self._create_new_subscription(
                    db, user_id, tier, product_id, provider, receipt_data, current_time
                )
            
            return subscription
            
        except Exception as e:
            db.rollback()
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
        
    def _update_existing_subscription(self, db, subscription, tier, product_id, provider, receipt_data, current_time):
        """Update an existing subscription with new details"""
        # Update subscription details
        subscription.tier = tier.value
        subscription.product_id = product_id
        subscription.provider = provider
        subscription.platform = 'android' if provider == 'google_play' else 'ios'
        if receipt_data:
            subscription.receipt_data = json.dumps(receipt_data)
        subscription.updated_at = current_time
        subscription.end_date = self._extract_subscription_end_date(None, receipt_data, provider)
        
        # Add to subscription history
        subscription_history = SubscriptionHistoryModel(
            subscription_id=subscription.id,
            action=SubscriptionAction.UPDATED,
            details=f"Updated subscription to {tier.value}",
            created_at=current_time
        )
        db.add(subscription_history)
        db.commit()
        
        logger.info(f"Successfully updated subscription {subscription.id} to tier {tier.value}")
        return subscription
        
    def _create_new_subscription(self, db, user_id, tier, product_id, provider, receipt_data, current_time):
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
        db.flush()  # This ensures the subscription gets an ID without committing the transaction
        
        # Add to subscription history
        subscription_history = SubscriptionHistoryModel(
            subscription_id=new_subscription.id,
            action=SubscriptionAction.CREATED,
            details=f"Created new {tier.value} subscription",
            created_at=current_time
        )
        db.add(subscription_history)
        db.commit()
        
        logger.info(f"Successfully created subscription {new_subscription.id} with tier {tier.value}")
        return new_subscription
    
    async def verify_subscription(self, token: str, db: Session):
        """Verify user subscription"""
        try:
            logger.info("Starting subscription verification process")
            user = await self.get_user_from_token(token, db)
            logger.info(f"User retrieved from token: user_id={user.id}, email={user.email}")
            
            # Check if user has active subscription
            current_time = datetime.now(timezone.utc)
            logger.info(f"Checking active subscriptions at current time: {current_time}")
            
            subscription = (
                db.query(SubscriptionModel)
                .filter(
                    SubscriptionModel.user_id == user.id,
                    SubscriptionModel.status == SubscriptionStatus.ACTIVE,
                    SubscriptionModel.end_date > current_time
                )
                .order_by(SubscriptionModel.created_at.desc())
                .first()
            )
            
            if subscription:
                logger.info(f"Found active subscription: id={subscription.id}, tier={subscription.tier}, end_date={subscription.end_date}")
                # User has active subscription, return subscription details
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
            
            # Check if user has expired subscription
            logger.info("No active subscription found, checking for expired subscriptions")
            expired_subscription = (
                db.query(SubscriptionModel)
                .filter(
                    SubscriptionModel.user_id == user.id,
                    SubscriptionModel.status == SubscriptionStatus.ACTIVE,
                    SubscriptionModel.end_date <= current_time
                )
                .order_by(SubscriptionModel.created_at.desc())
                .first()
            )
            
            if expired_subscription:
                logger.info(f"Found expired subscription: id={expired_subscription.id}, updating status to EXPIRED")
                # Update status to EXPIRED
                expired_subscription.status = SubscriptionStatus.EXPIRED
                db.add(expired_subscription)
                
                # Create subscription history record
                history = SubscriptionHistoryModel(
                    subscription_id=expired_subscription.id,
                    action=SubscriptionAction.EXPIRED,
                    tier=expired_subscription.tier,
                    created_at=current_time
                )
                db.add(history)
                db.commit()
                logger.info("Subscription status updated to EXPIRED and history record created")
            
            logger.info("No active subscription found for user")
            return {
                "has_subscription": False
            }
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"Error in verify_subscription: {str(e)}\nTraceback: {error_traceback}")
            raise
    
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

    async def process_subscription_notification(self, notification_data: dict, db: Session, token: str = None):
        """Process a subscription notification from Google Play or App Store"""
        try:
            logger.info(f"Processing notification data: {notification_data}")
            
            # Check if this is a Google Play subscription notification
            subscription_notification = notification_data.get('subscriptionNotification') or notification_data.get('voidedPurchaseNotification')
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
                        existing_sub.updated_at = datetime.now(timezone.utc)
                        existing_sub.end_date = self._extract_subscription_end_date(notification_data, receipt_data, 'google_play')
                        
                        # Add to subscription history
                        action = SubscriptionAction.UPDATED
                        if notification_type == 4:  # PURCHASED
                            action = SubscriptionAction.CREATED
                        elif notification_type == 2:  # RENEWED
                            action = SubscriptionAction.RENEWED
                            
                        subscription_history = SubscriptionHistoryModel(
                            subscription_id=existing_sub.id,
                            action=action,
                            details=f"Updated subscription to {subscription_tier.value} via notification",
                            created_at=datetime.now(timezone.utc)
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
                            details="Subscription cancelled via notification",
                            created_at=datetime.now(timezone.utc)
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
                            details="Subscription expired via notification",
                            created_at=datetime.now(timezone.utc)
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
            
            # Check if this is a voided purchase notification (refund)
            if 'voidedPurchaseNotification' in notification_data:
                voided_data = notification_data['voidedPurchaseNotification']
                purchase_token = voided_data.get('purchaseToken')
                logger.info(f"Processing voided purchase notification with token: {purchase_token}")
                
                if not purchase_token:
                    logger.error(f"Missing purchase token in voided notification: {notification_data}")
                    return {"success": False, "error": "Missing purchase token in voided notification"}
                
                # Find subscription by purchase token (stored in receipt_data)
                subscriptions = db.query(SubscriptionModel).filter(
                    SubscriptionModel.status == SubscriptionStatus.ACTIVE
                ).all()
                
                found_subscription = None
                for sub in subscriptions:
                    if not sub.receipt_data:
                        continue
                    
                    try:
                        receipt = json.loads(sub.receipt_data)
                        if receipt.get('purchaseToken') == purchase_token:
                            found_subscription = sub
                            break
                    except (json.JSONDecodeError, TypeError):
                        continue
                
                if found_subscription:
                    logger.info(f"Found subscription {found_subscription.id} for voided purchase")
                    found_subscription.status = SubscriptionStatus.CANCELLED
                    
                    # Add subscription history
                    subscription_history = SubscriptionHistoryModel(
                        subscription_id=found_subscription.id,
                        action=SubscriptionAction.CANCELLED,
                        details="Subscription cancelled due to refund",
                        created_at=datetime.now(timezone.utc)
                    )
                    db.add(subscription_history)
                    db.commit()
                    
                    return {"success": True, "message": "Subscription cancelled due to refund"}
                else:
                    logger.warning(f"No active subscription found for voided purchase token: {purchase_token}")
                    return {"success": True, "message": "No active subscription found for voided purchase"}
            
            # Check if this is a subscription notification
            elif 'subscriptionNotification' in notification_data:
                sub_notification = notification_data['subscriptionNotification']
                purchase_token = sub_notification.get('purchaseToken')
                subscription_id = sub_notification.get('subscriptionId')
                notification_type = sub_notification.get('notificationType')
                
                logger.info(f"Processing subscription notification type {notification_type} for subscription {subscription_id}")
                
                if not purchase_token or not subscription_id:
                    logger.error(f"Missing purchase token or subscription ID in notification: {notification_data}")
                    return {"success": False, "error": "Missing purchase token or subscription ID in notification"}
                
                # Update user_id to None since it's not directly in the notification
                # We'll need to find the user by subscription
                user_id = None
                
                # Find subscription by purchase token (stored in receipt_data) or subscription_id
                subscriptions = db.query(SubscriptionModel).all()
                
                found_subscription = None
                for sub in subscriptions:
                    # Check by subscription_id first
                    if sub.subscription_id == subscription_id:
                        found_subscription = sub
                        break
                        
                    # Then try by receipt_data
                    if not sub.receipt_data:
                        continue
                    
                    try:
                        receipt = json.loads(sub.receipt_data)
                        if receipt.get('purchaseToken') == purchase_token:
                            found_subscription = sub
                            break
                    except (json.JSONDecodeError, TypeError):
                        continue
                
                if found_subscription:
                    # Found the subscription, use its user_id
                    user_id = found_subscription.user_id
                    
                    # Process different notification types
                    # 1: RECOVERED, 2: RENEWED, 3: CANCELED, 4: PURCHASED, 5: ON_HOLD, 
                    # 6: IN_GRACE_PERIOD, 7: RESTARTED, 8: PRICE_CHANGE_CONFIRMED, 
                    # 9: DEFERRED, 10: PAUSED, 11: PAUSE_SCHEDULE_CHANGED, 12: REVOKED, 
                    # 13: EXPIRED
                    if notification_type in [1, 2, 4, 7]:  # RECOVERED, RENEWED, PURCHASED, RESTARTED
                        # Update existing subscription
                        found_subscription.status = SubscriptionStatus.ACTIVE
                        
                        # Extract base plan ID
                        base_plan_id = self._extract_base_plan_id(subscription_id)
                        tier = self._determine_subscription_tier(base_plan_id)
                        
                        # Prepare receipt data
                        receipt_data = {
                            'purchaseToken': purchase_token,
                            'productId': subscription_id
                        }
                        
                        # Update end date
                        found_subscription.end_date = self._extract_subscription_end_date(
                            notification_data, receipt_data, found_subscription.provider
                        )
                        
                        action = SubscriptionAction.UPDATED
                        if notification_type == 4:  # PURCHASED
                            action = SubscriptionAction.CREATED
                        elif notification_type == 2:  # RENEWED
                            action = SubscriptionAction.RENEWED
                        
                        # Add subscription history
                        subscription_history = SubscriptionHistoryModel(
                            subscription_id=found_subscription.id,
                            action=action,
                            details=f"Subscription {action.value.lower()} via notification",
                            created_at=datetime.now(timezone.utc)
                        )
                        db.add(subscription_history)
                        db.commit()
                        
                        return {"success": True, "subscription_id": found_subscription.id}
                    
                    elif notification_type == 3:  # CANCELED
                        found_subscription.status = SubscriptionStatus.CANCELLED
                        
                        # Add subscription history
                        subscription_history = SubscriptionHistoryModel(
                            subscription_id=found_subscription.id,
                            action=SubscriptionAction.CANCELLED,
                            details="Subscription cancelled via notification",
                            created_at=datetime.now(timezone.utc)
                        )
                        db.add(subscription_history)
                        db.commit()
                        
                        return {"success": True, "subscription_id": found_subscription.id}
                    
                elif notification_type == 13:  # EXPIRED
                        found_subscription.status = SubscriptionStatus.EXPIRED
                        
                        # Add subscription history
                        subscription_history = SubscriptionHistoryModel(
                            subscription_id=found_subscription.id,
                            action=SubscriptionAction.EXPIRED,
                            details="Subscription expired via notification",
                            created_at=datetime.now(timezone.utc)
                        )
                        db.add(subscription_history)
                        db.commit()
                        
                        return {"success": True, "subscription_id": found_subscription.id}
                    
                # For other notification types, just log and return success
                logger.info(f"Processed notification type {notification_type} for subscription {subscription_id}")
                return {"success": True, "message": f"Processed notification type {notification_type}"}
            else:
                logger.warning(f"No subscription found for ID: {subscription_id} or token: {purchase_token}")
                
                # If this is a PURCHASED notification and we don't have the subscription yet,
                # we can't create it without a user ID
                if notification_type == 4:  # PURCHASED
                    logger.warning("Received PURCHASED notification for unknown subscription")
                
                return {"success": True, "message": "Acknowledged notification for unknown subscription"}
                
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