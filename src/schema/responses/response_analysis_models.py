from pydantic import BaseModel
from typing import List

class NewsHistoryModel(BaseModel):
    date: str
    news_count: int

class NewsPerceptionModel(BaseModel):
    date: str
    positive_sentiment_score: float
    negative_sentiment_score: float

class GeneralPerceptionModel(BaseModel):
    positive_sentiment_score: float
    negative_sentiment_score: float

class AnalysisResponseModel(BaseModel):
    source_query: str  # Término de búsqueda utilizado
    news_history: List[NewsHistoryModel]  # Historial de noticias por fecha sin segmentación por fuente
    news_perception: List[NewsPerceptionModel]  # Percepción de noticias general
    news_count: int  # Número total de noticias
    sources_count: int  # Número de fuentes únicas
    historic_interval: int  # Intervalo histórico
    historic_interval_unit: str  # Unidad del intervalo histórico (days, weeks, months, years)
    general_perception: GeneralPerceptionModel  # Percepción general

    class Config:
        schema_extra = {
            "example": {
                "source_query": "ganaderia",
                "news_history": [
                    {"date": "2024-02-15", "news_count": 15},
                    {"date": "2024-04-02", "news_count": 20}
                ],
                "news_perception": [
                    {
                        "date": "2024-02-15",
                        "positive_sentiment_score": 0.5,
                        "negative_sentiment_score": 0.3
                    },
                    {
                        "date": "2024-04-02",
                        "positive_sentiment_score": 0.7,
                        "negative_sentiment_score": 0.2
                    }
                ],
                "news_count": 35,
                "sources_count": 3,
                "historic_interval": 9,
                "historic_interval_unit": "months",
                "general_perception": {
                    "positive_sentiment_score": 0.6,
                    "negative_sentiment_score": 0.4
                }
            }
        }

class ErrorResponseModel(BaseModel):
    detail: str

    class Config:
        schema_extra = {
            "example": {
                "detail": "Invalid request. Query parameter is missing."
            }
        }
