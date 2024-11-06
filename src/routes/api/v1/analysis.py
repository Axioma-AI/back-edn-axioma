import logging
from fastapi import APIRouter, Query, HTTPException, status
from src.services.analysis_service import AnalysisService
from src.schema.responses.response_analysis_models import AnalysisResponseModel
from src.schema.examples.response_analysis_examples import analysis_responses
from src.utils.logger import setup_logger

logger = setup_logger(__name__, level=logging.INFO)
router = APIRouter()
analysis_service = AnalysisService()

@router.get(
    "/analysis",
    description="Obtener un análisis de noticias basado en la fuente y el intervalo",
    response_model=AnalysisResponseModel,
    responses=analysis_responses
)
async def get_analysis(
    source: str = Query(..., description="Fuente de las noticias a analizar"),
    interval: int = Query(1, description="Intervalo de tiempo para el análisis"),
    unit: str = Query("days", description="Unidad de tiempo ('days', 'weeks', 'months', 'years')")
):
    try:
        logger.info(f"Starting analysis for source: {source}, interval: {interval} {unit}")
        analysis_data = analysis_service.get_analysis(source, interval, unit)
        return analysis_data
    except ValueError as e:
        logger.error(f"Value error in analysis: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in analysis: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error procesando los datos")