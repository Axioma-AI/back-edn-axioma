import csv
import io
import logging
from fastapi import APIRouter, Query, HTTPException, Response, status
from typing import List, Optional
from src.services.article_service import ArticleService
from src.schema.responses.response_articles_models import ArticleResponseModel, NewsSourceResponseModel
from src.schema.examples.response_articles_examples import articles_responses, article_by_id_responses, news_sources_responses
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
    sort: str = Query("publish_datetime", description="Field to sort results by (default is by date)"),
    token: Optional[str] = Query(None, description="User authentication token to check favorites")
):
    try:
        query = query.lower()
        if not query:
            logger.debug(f"Empty query, fetching the most recent articles with limit={limit} sorted by {sort}.")
            articles = await article_service.get_articles(limit, sort, token)
        else:
            logger.debug(f"Fetching articles with query='{query}', limit={limit}, sort='{sort}'")
            articles = await article_service.search_by_text_db(query, limit, sort, token)

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

@router.get("/articles/by-email",
            description="Retrieve a list of articles based on user interests associated with the provided email",
            response_model=List[ArticleResponseModel],
            responses=articles_responses)
async def get_articles_by_email(
    email: str = Query(..., description="Email to retrieve articles based on user interests"),
    limit: int = Query(50, description="Maximum number of articles to return"),
    sort: str = Query("publish_datetime", description="Field to sort results by (default is by date)")
):
    try:
        logger.debug(f"Fetching articles for user email='{email}', limit={limit}, sort='{sort}'.")
        articles = await article_service.get_articles_by_email(email, limit, sort)
        logger.info(f"Returning {len(articles)} articles for email={email}.")
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


@router.get("/articles/excel", description="Retrieve all articles and return them in Excel (.xlsx) format")
async def get_articles_excel(
    query: str = "",  # Optional parameter to filter articles by query
):

    try:
        query = query.lower()
        # Fetch all articles matching the query, or all if query is empty
        articles = await article_service.search_by_text_db(query, limit=10000) if query else await article_service.get_all_articles()

        # Create an in-memory Excel workbook
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Articles"

        # Add header row
        headers = [
            "id", "source", "author", "title", "description", "url", "urlToImage", "publishedAt", "content",
            "sentiment_category", "sentiment_score", "summary", "justification", "news_type_category", "news_type_justification",
            "purpose_objective", "purpose_audience", "context_temporality", "context_location", "content_facts_vs_opinions",
            "content_precision", "content_impartiality", "structure_clarity", "structure_key_data", "tone_neutrality", "tone_ethics"
        ]
        sheet.append(headers)

        # Add article rows
        for article in articles:
            sheet.append([
                article.id,
                article.source.name,
                article.author or "",
                article.title,
                article.description or "",
                article.url,
                article.urlToImage or "",
                article.publishedAt or "",
                article.content or "",
                article.sentiment_category,
                article.sentiment_score,
                article.summary or "",
                article.justification or "",
                article.news_type_category or "",
                article.news_type_justification or "",
                article.purpose_objective or "",
                article.purpose_audience or "",
                article.context_temporality or "",
                article.context_location or "",
                article.content_facts_vs_opinions or "",
                article.content_precision or "",
                article.content_impartiality or "",
                article.structure_clarity or "",
                article.structure_key_data or "",
                article.tone_neutrality or "",
                article.tone_ethics or ""
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

@router.get(
    "/sources",
    description="Retrieve a list of unique news sources",
    response_model=NewsSourceResponseModel,
    responses=news_sources_responses,
)
async def get_news_sources():
    try:
        sources = await article_service.get_all_news_sources()
        if not sources:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The requested resource does not exist.",
            )
        logger.info(f"Retrieved {len(sources)} unique news sources.")
        return {"sources": sources}
    except HTTPException as http_exc:
        logger.error(f"HTTP Exception: {http_exc.detail}")
        raise http_exc
    except ValueError:
        logger.error("Invalid request. Query parameter is invalid or missing.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request. Query parameter is invalid or missing.",
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        )

@router.get("/articles/by-source",
            description="Retrieve a list of articles filtered by news source",
            response_model=List[ArticleResponseModel],
            responses=articles_responses)
async def get_articles_by_source(
    source: str = Query(..., description="News source to filter articles"),
    limit: int = Query(50, description="Maximum number of articles to return"),
    sort: str = Query("publish_datetime", description="Field to sort results by (default is by date)"),
    token: Optional[str] = Query(None, description="User authentication token to check favorites")
):
    # Lógica del endpoint
    try:
        source = source.lower()

        logger.debug(f"Fetching articles with source='{source}', limit={limit}, sort='{sort}'.")
        articles = await article_service.search_by_source(source, limit, sort, token)
        
        logger.info(f"Returning {len(articles)} articles for source='{source}'.")
        return articles
    except HTTPException as http_exc:
        logger.error(f"HTTP Exception: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        )

@router.get("/articles/{id}",
            description="Retrieve a single article by its ID",
            response_model=ArticleResponseModel,
            responses=article_by_id_responses)
async def get_article_by_id(id: int, token: Optional[str] = None):
    try:
        logger.debug(f"Fetching article with ID: {id} and token: {token}")
        article = await article_service.get_article_by_id(id, token)
        if not article:
            logger.warning(f"Article with ID {id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The article with the specified ID was not found."
            )
        return article
    except HTTPException as http_exc:
        logger.error(f"HTTP Exception: {http_exc.detail}")
        raise http_exc
    except ValueError:
        logger.error(f"Invalid article ID: {id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request. The article ID must be a valid integer greater than 0."
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )
    
