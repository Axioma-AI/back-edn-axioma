import csv
import io
import logging
from fastapi import APIRouter, Query, HTTPException, Response, status
from typing import List
from src.services.article_service import ArticleService
from src.schema.responses.response_articles_models import ArticleResponseModel
from src.schema.examples.response_articles_examples import articles_responses
from src.utils.logger import setup_logger
from openpyxl import Workbook

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
        query = query.lower()

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

def clean_illegal_characters(text):
    if text is None:
        return ""
    # Remove illegal characters by filtering out non-ASCII or known illegal characters
    return ''.join(c for c in text if ord(c) < 128 and c not in ['\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', '\x08', '\x0B', '\x0C', '\x0E', '\x0F', '\x10', '\x11', '\x12', '\x13', '\x14', '\x15', '\x16', '\x17', '\x18', '\x19', '\x1A', '\x1B', '\x1C', '\x1D', '\x1E', '\x1F'])


@router.get("/excel", description="Retrieve all articles and return them in Excel (.xlsx) format")
async def get_articles_excel(
    query: str = "",  # Optional parameter to filter articles by query
):
    try:
        query = query.lower()
        # Fetch all articles matching the query, or all if query is empty
        articles = await article_service.search_by_text(query, limit=10000) if query else await article_service.get_all_articles()

        # Check if articles were returned
        if articles is None:
            logger.error("No articles were fetched. The returned data is None.")
            raise HTTPException(status_code=500, detail="No articles were found for the specified query.")

        # Create an in-memory Excel workbook
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Articles"

        # Add header row
        headers = ["id", "source", "author", "title", "description", "url", "urlToImage", "publishedAt", "content", "sentiment_category", "sentiment_score"]
        sheet.append(headers)

        # Add article rows
        for article in articles:
            # Sanitize content to remove illegal characters
            sheet.append([
                article["id"],
                article["source"]["name"],
                article.get("author", ""),
                article["title"],
                clean_illegal_characters(article.get("description", "")),
                article["url"],
                article.get("urlToImage", ""),
                article.get("publishedAt", ""),
                clean_illegal_characters(article.get("content", "")),
                article["sentiment_category"],
                article["sentiment_score"]
            ])

        # Save workbook to an in-memory buffer
        buffer = io.BytesIO()
        workbook.save(buffer)
        buffer.seek(0)

        # Return as an Excel file response
        return Response(
            content=buffer.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=articles.xlsx"}
        )

    except HTTPException as http_exc:
        logger.error(f"HTTP Exception: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please try again later."
        )
