from pydantic import BaseModel
from typing import List, Optional

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
    source: dict  # {"id": int, "name": str}
    news_history: List[NewsHistoryModel]
    news_perception: List[NewsPerceptionModel]
    news_count: int
    sources_count: int
    historic_interval: int
    historic_interval_unit: str
    general_perception: GeneralPerceptionModel

    class Config:
        schema_extra = {
            "example": {
                "source": {"id": 1, "name": "CNN"},
                "news_history": [
                    {"date": "2021-01-01", "news_count": 10},
                    {"date": "2021-01-02", "news_count": 10}
                ],
                "news_perception": [
                    {
                        "date": "2021-01-01",
                        "positive_sentiment_score": 0.5,
                        "negative_sentiment_score": 0.5
                    },
                    {
                        "date": "2021-01-02",
                        "positive_sentiment_score": 0.2,
                        "negative_sentiment_score": 0.8
                    }
                ],
                "news_count": 20,
                "sources_count": 5,
                "historic_interval": 3,
                "historic_interval_unit": "months",
                "general_perception": {
                    "positive_sentiment_score": 0.4,
                    "negative_sentiment_score": 0.6
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
