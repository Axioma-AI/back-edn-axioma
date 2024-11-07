import logging
from fastapi import APIRouter, Query, HTTPException, status
from typing import Union
from src.services.analysis_service import AnalysisService
from src.schema.responses.response_analysis_models import AnalysisResponseModel
from src.schema.examples.response_analysis_examples import analysis_responses
from src.utils.logger import setup_logger

logger = setup_logger(__name__, level=logging.INFO)

router = APIRouter()
analysis_service = AnalysisService()

@router.get("/analysis", 
            response_model=AnalysisResponseModel,  # Usamos AnalysisResponseModel actualizado
            responses=analysis_responses
            )
async def get_analysis(
    query: str = Query(..., description="Keyword for the news source"),
    interval: int = Query(..., description="Historical interval for analysis"),
    unit: str = Query(..., description="Interval unit (days, weeks, months, years)")
):
    try:
        logger.debug(f"Performing analysis with source_query='{query}', interval={interval}, unit='{unit}'")
        analysis_data = analysis_service.search_by_text_analysis(query=query, interval=interval, unit=unit)
        logger.info("Analysis data successfully retrieved.")
        return analysis_data

    except HTTPException as http_exc:
        logger.error(f"HTTP Exception: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )
