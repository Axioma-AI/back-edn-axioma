import logging
from fastapi import APIRouter, Query, HTTPException, status
from typing import List
from src.services.article_service import ArticleService
from src.schema.responses.response_articles_models import ArticleResponseModel
from src.schema.examples.response_articles_examples import articles_responses
from src.utils.logger import setup_logger

logger = setup_logger(__name__, level=logging.INFO)

router = APIRouter()
article_service = ArticleService()

@router.get("/articles", 
            description="Retrieve a list of articles that match a keyword search within the article content",
            response_model=List[ArticleResponseModel],
            responses=articles_responses)
async def get_articles(
    query: str = Query("", description="Keyword to search within articles (leave empty to retrieve the most recent articles)"),
    limit: int = Query(50, description="Maximum number of articles to return"),
    sort: str = Query("publish_datetime", description="Field to sort results by (default is by date)")
):
    try:
        # Check if `query` is empty
        if not query:
            logger.debug(f"Empty query, fetching the most recent articles with limit={limit} sorted by {sort}.")
            articles = await article_service.get_articles(limit, sort)
        else:
            logger.debug(f"Fetching articles with query='{query}', limit={limit}, sort='{sort}'")
            articles = await article_service.search_by_text(query, limit, sort)
        
        # Return the list of articles directly
        logger.info(f"Returning {len(articles)} articles.")
        return articles

    except HTTPException as http_exc:
        logger.error(f"HTTP Exception: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )
