from fastapi import APIRouter, Depends, Query, HTTPException, Request, status, Body
from sqlalchemy.orm import Session
from src.config.db_config import get_db
from src.services.subscription_service import SubscriptionService
from src.schema.requests.request_subscription_models import CreateSubscriptionRequest
from src.utils.logger import setup_logger
import logging
import json

logger = setup_logger(__name__, level=logging.INFO)
router = APIRouter()
subscription_service = SubscriptionService()

@router.post("/subscriptions")
async def create_subscription(
    request: CreateSubscriptionRequest,
    token: str = Query(..., description="User authentication token")
):
    """Create a new subscription"""
    try:
        user = await subscription_service.get_user_from_token(token)

        # Ya no pasamos db manualmente; create_subscription debe usar async for db in get_db()
        result = await subscription_service.create_subscription(
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
    token: str = Query(..., description="User authentication token")
):
    """Verify subscription status"""
    try:
        logger.info(f"Verifying subscription for token: {token[:10]}...")
        result = await subscription_service.verify_subscription(token)
        logger.info(f"Subscription verification result: {result}")
        return result
    except HTTPException as http_exc:
        logger.error(f"HTTP Exception in verify_subscription: {http_exc.detail}")
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error verifying subscription: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while verifying the subscription"
        )

@router.post("/subscriptions/verify")
async def verify_subscription_post(
    request: Request
):
    """Verify subscription status using POST method"""
    try:
        body = await request.json()
        token = body.get("token")

        if not token:
            logger.error("Missing required token in request body")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required token"
            )

        logger.info(f"Verifying subscription for token: {token[:10]}...")
        result = await subscription_service.verify_subscription(token)
        logger.info(f"Subscription verification result: {result}")
        return result

    except json.JSONDecodeError:
        logger.error("Invalid JSON body in request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body"
        )
    except HTTPException as http_exc:
        logger.error(f"HTTP Exception in verify_subscription_post: {http_exc.detail}")
        raise
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Error verifying subscription (POST): {str(e)}\nTraceback: {error_traceback}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while verifying the subscription"
        )

@router.post("/subscriptions/cancel")
async def cancel_subscription(
    token: str = Query(..., description="User authentication token")
):
    """Cancel subscription"""
    try:
        return await subscription_service.cancel_subscription(token)
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
    receipt_data: dict = Body(..., description="Receipt data from store")
):
    """Verify receipt from App Store or Google Play and create/update subscription"""
    try:
        # Obtener usuario autenticado desde el token
        user = await subscription_service.get_user_from_token(token)

        # Extraer campos del recibo
        platform = receipt_data.get('platform', '').lower()
        product_id = receipt_data.get('productId')
        purchase_token = receipt_data.get('purchaseToken')

        if platform == 'android':
            platform = 'google_play'

        # Crear o actualizar la suscripción de forma asíncrona
        result = await subscription_service.create_subscription(
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
