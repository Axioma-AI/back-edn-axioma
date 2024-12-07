import logging
from fastapi import APIRouter, HTTPException, Query, Depends, status
from sqlalchemy.orm import Session
from src.config.db_config import get_db
from src.schema.responses.response_favorites_models import AddFavoriteResponseModel, DeleteFavoriteResponseModel, FavoritesResponseModel
from src.schema.examples.response_favorites_examples import favorites_responses_post, favorites_responses_get, favorites_responses_delete
from src.services.favorites_service import FavoritesService
from src.utils.logger import setup_logger

logger = setup_logger(__name__, level=logging.INFO)

router = APIRouter()
favorites_service = FavoritesService()

logger = setup_logger(__name__, level=logging.INFO)
router = APIRouter()
favorites_service = FavoritesService()

@router.post(
    "/favorites",
    description="Add a news article to the user's favorites",
    response_model=AddFavoriteResponseModel,
    responses=favorites_responses_post,
)
async def add_favorite(
    token: str = Query(..., description="User authentication token"),
    news_id: int = Query(..., description="ID of the news to add to favorites"),
    db: Session = Depends(get_db),
):
    try:
        logger.info(f"Adding news_id {news_id} to favorites for token: {token}")
        result = await favorites_service.add_favorite(token, news_id, db)
        logger.info(f"News {news_id} successfully added to favorites")
        return {
            "message": "Favorite added successfully",
            "news_id": news_id,
        }
    except HTTPException as http_exc:
        logger.error(f"HTTP Exception: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while adding the favorite.",
        )

@router.get(
    "/favorites",
    description="Get the user's favorite news articles",
    response_model=FavoritesResponseModel,
    responses=favorites_responses_get,
)
async def get_favorites(
    token: str = Query(..., description="User authentication token"),
    db: Session = Depends(get_db),
):
    try:
        logger.info(f"Fetching favorites for token: {token}")
        result = await favorites_service.get_favorites(token, db)
        logger.info(f"Successfully fetched favorites for token: {token}")
        return result
    except HTTPException as http_exc:
        logger.error(f"HTTP Exception: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving favorites.",
        )

@router.delete(
    "/favorites",
    description="Remove a news article from the user's favorites",
    response_model=DeleteFavoriteResponseModel,
    responses=favorites_responses_delete,
)
async def delete_favorite(
    token: str = Query(..., description="User authentication token"),
    news_id: int = Query(..., description="ID of the news to remove from favorites"),
    db: Session = Depends(get_db),
):
    try:
        logger.info(f"Removing news_id {news_id} from favorites for token: {token}")
        result = await favorites_service.delete_favorite(token, news_id, db)
        logger.info(f"News {news_id} successfully removed from favorites")
        return {
            "message": "Favorite deleted successfully",
            "news_id": news_id,
        }
    except HTTPException as http_exc:
        logger.error(f"HTTP Exception: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting the favorite.",
        )