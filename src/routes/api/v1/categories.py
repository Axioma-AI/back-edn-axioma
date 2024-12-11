import logging
from fastapi import APIRouter, Query, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
from src.schema.responses.response_categories_models import AddCategoriesResponseModel, CategoriesResponseModel, DeleteCategoriesResponseModel
from src.schema.examples.response_categories_examples import categories_responses_post, categories_responses_get, categories_responses_delete
from src.services.categories_service import CategoriesService
from src.utils.logger import setup_logger
from src.config.db_config import get_db

logger = setup_logger(__name__, level=logging.INFO)

router = APIRouter()
categories_service = CategoriesService()

@router.post(
    "/categories",
    description="Add keywords for the user based on the provided token",
    response_model=AddCategoriesResponseModel,
    responses=categories_responses_post,
)
async def add_categories(
    token: str = Query(..., description="User authentication token"),
    keywords: List[str] = Query(..., description="Keywords to monitor"),
    db: Session = Depends(get_db),
):
    """
    Endpoint to add keywords (categories) for the user.
    """
    try:
        logger.info(f"Adding categories for token: {token}, keywords: {keywords}")
        
        # Llamamos al servicio para procesar las categorías
        result = await categories_service.process_categories(token, keywords, db)
        
        logger.info(f"Categories added successfully for token: {token}")
        
        # Retornamos el mensaje, las categorías agregadas y las categorías ignoradas
        return {
            "message": result["message"],
            "categories": result["categories"],
            "skipped_categories": result.get("skipped_categories", [])
        }
    except HTTPException as http_exc:
        logger.error(f"HTTP Exception: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error while adding categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while adding categories. Please try again later.",
        )

@router.get(
    "/categories",
    description="Retrieve all keywords for the authenticated user",
    response_model=CategoriesResponseModel,
    responses=categories_responses_get,
)
async def get_categories(
    token: str = Query(..., description="User authentication token"),
    db: Session = Depends(get_db),
):
    """
    Endpoint to retrieve the user's keywords (categories).
    """
    try:
        logger.info(f"Fetching categories for token: {token}")
        user_interests = await categories_service.get_user_interests(token, db)
        logger.info(f"Categories fetched successfully for token: {token}")
        return user_interests
    except HTTPException as http_exc:
        logger.error(f"HTTP Exception: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error while fetching categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching categories. Please try again later.",
        )

@router.delete(
    "/categories",
    description="Delete one or more categories for the authenticated user",
    response_model=DeleteCategoriesResponseModel,
    responses=categories_responses_delete,
)
async def delete_categories(
    token: str = Query(..., description="User authentication token"),
    category_ids: List[int] = Query(..., description="List of category IDs to delete"),
    db: Session = Depends(get_db),
):
    """
    Endpoint to delete one or more categories for the user.
    """
    try:
        logger.info(f"Deleting categories {category_ids} for token: {token}")
        deleted_categories = await categories_service.delete_categories(token, category_ids, db)
        logger.info(f"Categories deleted successfully for token: {token}")
        return {
            "message": "Categories deleted successfully",
            "deleted_categories": deleted_categories,
        }
    except HTTPException as http_exc:
        logger.error(f"HTTP Exception: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error while deleting categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting categories. Please try again later.",
        )