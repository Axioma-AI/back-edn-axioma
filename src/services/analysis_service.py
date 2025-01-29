from collections import defaultdict
from datetime import datetime, timedelta
import logging
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

        # Realizar la búsqueda de texto en Chroma DB
        logger.info(f"Performing text search in Chroma DB for query: '{query}'")
        query_results = self.collection.query(query_texts=[query], n_results=100)
        article_urls = query_results["ids"][0]
        distances = query_results["distances"][0]
        logger.debug(f"Text search completed. Found {len(article_urls)} articles.")

        # Consultar los artículos de la base de datos basados en las URLs
        db = next(get_db())
        try:
            logger.info("Fetching articles from database based on URLs and date range.")
            news_records = db.query(NewsModel).filter(
                NewsModel.source_link.in_(article_urls),
                NewsModel.publish_datetime >= start_date,
                NewsModel.publish_datetime <= end_date
            ).all()
            logger.debug(f"Fetched {len(news_records)} articles from database.")
        finally:
            db.close()
            logger.debug("Database session closed after fetching articles for analysis.")

        # Recopilar todos los puntajes para calcular el promedio general
        average_scores = defaultdict(list)
        logger.debug(f"General average sentiment score calculated: {average_scores}")

        # Agrupar las noticias por fecha para `news_history`
        sources_history = defaultdict(int)

        for news in news_records:
            date = news.publish_datetime.date()
            sources_history[date] += 1  # Contar el número de noticias por fecha

            # Clasificar en positivo o negativo basado en el promedio general
            average_scores[date].append(float(news.sentiment_score))

        # Construir `news_history` como lista de noticias por fecha sin segmentación
        news_history_list = [
            NewsHistoryModel(date=str(date), news_count=count)
            for date, count in sorted(sources_history.items())
        ]

        # Construir `news_perception` para todas las fechas combinadas con las nuevas reglas
        news_perception_list = [
            NewsPerceptionModel(
                date=str(date),
                positive_sentiment_score=(1 + (sum(average_scores[date]) / len(average_scores[date])) if average_scores[date] else 0.5) / 2,
                negative_sentiment_score=(1 - (sum(average_scores[date]) / len(average_scores[date])) if average_scores[date] else 0.5) / 2
            )
            for date in sorted(set(average_scores.keys()))
        ]
        scores = [score for scores in average_scores.values() for score in scores]

        # Calcular `general_perception` como promedio de todos los puntajes clasificados, asegurando que la suma sea 1
        general_perception = GeneralPerceptionModel(
            positive_sentiment_score=(1 + (sum(scores) / len(scores)) if scores else 0.5) / 2,
            negative_sentiment_score=(1 - (sum(scores) / len(scores)) if scores else 0.5) / 2
        )

        # Construir la respuesta final como instancia de `AnalysisResponseModel`
        response = AnalysisResponseModel(
            source_query=query,
            news_history=news_history_list,
            news_perception=news_perception_list,
            news_count=sum(sources_history.values()),
            sources_count=len(set(article.news_source for article in news_records)),
            historic_interval=interval,
            historic_interval_unit=unit,
            general_perception=general_perception
        )

        logger.info("Analysis response successfully built.")
        return response
