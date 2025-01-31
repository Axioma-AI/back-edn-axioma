from collections import defaultdict
from datetime import datetime, timedelta
import logging
from sqlalchemy import text
from src.models.news_tag_model import NewsModel
from src.schema.responses.response_analysis_models import AnalysisResponseModel, NewsHistoryModel, NewsPerceptionModel, GeneralPerceptionModel
from src.utils.logger import setup_logger
# from src.config.chromadb_config import get_chroma_db_client
from src.config.db_config import get_db
from sqlalchemy.orm import Session

logger = setup_logger(__name__, level=logging.DEBUG)

class AnalysisService:
    # def __init__(self):
        # self.collection = get_chroma_db_client()
        # logger.debug("Chroma DB client initialized.")

    def search_by_text_analysis(self, query: str, interval: int, unit: str) -> AnalysisResponseModel:
        # Calcular el rango de fechas
        logger.info(f"Calculating date range for interval: {interval} {unit}")
        end_date = datetime.now()
        if unit == "days":
            start_date = end_date - timedelta(days=interval)
        elif unit == "weeks":
            start_date = end_date - timedelta(weeks=interval)
        elif unit == "months":
            start_date = end_date - timedelta(days=30 * interval)
        elif unit == "years":
            start_date = end_date - timedelta(days=365 * interval)
        logger.debug(f"Date range calculated: start_date={start_date}, end_date={end_date}")

        # Realizar la búsqueda en la base de datos
        logger.info(f"Performing text search in database for query: '{query}'")
        db = next(get_db())
        try:
            query = f'"{query}"'
            articles = db.query(
                NewsModel,
                text("MATCH(title, content) AGAINST(:query IN BOOLEAN MODE) AS distance")
            ).filter(
                text("MATCH(title, content) AGAINST(:query IN BOOLEAN MODE)"),
                NewsModel.publish_datetime >= start_date,
                NewsModel.publish_datetime <= end_date
            ).params(query=query).order_by(getattr(NewsModel, "publish_datetime").desc()).limit(100).all()
            logger.debug(f"Text search completed. Found {len(articles)} articles.")
        finally:
            db.close()
            logger.debug("Database session closed after fetching articles for analysis.")

        # Recopilar puntajes para promedios
        average_scores = defaultdict(list)
        sources_history = defaultdict(int)

        for article, distance in articles:
            date = article.publish_datetime.date()
            sources_history[date] += 1
            average_scores[date].append(float(article.sentiment_score))

        # Construir `news_history`
        news_history_list = [
            NewsHistoryModel(date=str(date), news_count=count)
            for date, count in sorted(sources_history.items())
        ]

        # Construir `news_perception`
        news_perception_list = [
            NewsPerceptionModel(
                date=str(date),
                positive_sentiment_score=(1 + (sum(scores) / len(scores)) if scores else 0.5) / 2,
                negative_sentiment_score=(1 - (sum(scores) / len(scores)) if scores else 0.5) / 2
            )
            for date, scores in average_scores.items()
        ]
        scores = [score for scores in average_scores.values() for score in scores]

        # Calcular `general_perception`
        general_perception = GeneralPerceptionModel(
            positive_sentiment_score=(1 + (sum(scores) / len(scores)) if scores else 0.5) / 2,
            negative_sentiment_score=(1 - (sum(scores) / len(scores)) if scores else 0.5) / 2
        )

        # Construir la respuesta final
        response = AnalysisResponseModel(
            source_query=query,
            news_history=news_history_list,
            news_perception=news_perception_list,
            news_count=sum(sources_history.values()),
            sources_count=len(set(article.news_source for article, _ in articles)),
            historic_interval=interval,
            historic_interval_unit=unit,
            general_perception=general_perception
        )

        logger.info("Analysis response successfully built.")
        return response
