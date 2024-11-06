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
            description="Obtener una lista de artículos que coincidan con la búsqueda de una palabra clave en el contenido de los artículos",
            response_model=List[ArticleResponseModel],
            responses=articles_responses)
async def get_articles(
    query: str = Query(..., description="Palabra clave para buscar en los artículos"),
    limit: int = Query(50, description="Número máximo de artículos a devolver"),
    sort: str = Query("publish_datetime", description="Campo para ordenar los resultados")
):
    try:
        logger.debug(f"Obteniendo artículos con query='{query}', limit={limit}, sort='{sort}'")
        articles = await article_service.search_by_text(query, limit, sort)
        
        # Retorna la lista de artículos directamente
        logger.info(f"Devolviendo {len(articles)} artículos.")
        return articles

    except HTTPException as http_exc:
        logger.error(f"HTTP Exception: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )
