from fastapi import APIRouter, Depends, Query, HTTPException, status, Body
from sqlalchemy.orm import Session
from src.config.db_config import get_db
from src.services.subscription_service import SubscriptionService
from src.schema.requests.request_subscription_models import CreateSubscriptionRequest
from src.utils.logger import setup_logger
import logging

logger = setup_logger(__name__, level=logging.INFO)
router = APIRouter()
subscription_service = SubscriptionService()

@router.post("/subscriptions")
async def create_subscription(
    request: CreateSubscriptionRequest,
    token: str = Query(..., description="User authentication token"),
    db: Session = Depends(get_db)
):
    """Create a new subscription"""
    try:
        user = await subscription_service.get_user_from_token(token, db)
        result = await subscription_service.create_subscription(
            db=db,
            user_id=user.id,
            product_id=request.product_id,
            provider=request.platform,
            receipt_data=request.receipt_data
        )
        return {
            "message": "Subscription created successfully",
            "subscription_id": result.subscription_id,
            "tier": result.tier.value,
            "end_date": result.end_date.isoformat() if result.end_date else None
        }
    except HTTPException as http_exc:
        logger.error(f"HTTP Exception: {http_exc.detail}")
        raise
    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the subscription"
        )

@router.get("/subscriptions/verify")
async def verify_subscription(
    token: str = Query(..., description="User authentication token"),
    db: Session = Depends(get_db)
):
    """Verify subscription status"""
    try:
        return await subscription_service.verify_subscription(token, db)
    except HTTPException as http_exc:
        logger.error(f"HTTP Exception: {http_exc.detail}")
        raise
    except Exception as e:
        logger.error(f"Error verifying subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while verifying the subscription"
        )

@router.post("/subscriptions/cancel")
async def cancel_subscription(
    token: str = Query(..., description="User authentication token"),
    db: Session = Depends(get_db)
):
    """Cancel subscription"""
    try:
        return await subscription_service.cancel_subscription(token, db)
    except HTTPException as http_exc:
        logger.error(f"HTTP Exception: {http_exc.detail}")
        raise
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while cancelling the subscription"
        )

@router.post("/subscriptions/verify-receipt")
async def verify_receipt(
    token: str = Query(..., description="User authentication token"),
    receipt_data: dict = Body(..., description="Receipt data from store"),
    db: Session = Depends(get_db)
):
    """Verify receipt from App Store or Google Play and create/update subscription"""
    try:
        user = await subscription_service.get_user_from_token(token, db)
        
        # Extract required fields from receipt_data
        platform = receipt_data.get('platform', '').lower()
        product_id = receipt_data.get('productId')
        purchase_token = receipt_data.get('purchaseToken')
        
        if platform == 'android':
            platform = 'google_play'
        
        # Create or update subscription
        result = await subscription_service.create_subscription(
            db=db,
            user_id=user.id,
            product_id=product_id,
            provider=platform,
            receipt_data=receipt_data
        )
        
        return {
            "verified": True,
            "subscription_id": result.subscription_id,
            "tier": result.tier.value,
            "end_date": result.end_date.isoformat() if result.end_date else None
        }
    except HTTPException as http_exc:
        logger.error(f"HTTP Exception: {http_exc.detail}")
        raise
    except Exception as e:
        logger.error(f"Error verifying receipt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while verifying the receipt"
        ) 