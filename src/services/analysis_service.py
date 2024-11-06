import logging
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from src.models.news_tag_model import NewsModel
from src.config.db_config import get_db
from src.utils.logger import setup_logger
from typing import Dict, Any

logger = setup_logger(__name__, level=logging.INFO)

class AnalysisService:
    def __init__(self):
        pass

    def get_analysis(self, source: str, interval: int, unit: str) -> Dict[str, Any]:
        db = next(get_db())
        end_date = datetime.now()

        # Configure the date range based on the unit
        if unit == 'months':
            start_date = end_date - timedelta(days=30 * interval)
        elif unit == 'days':
            start_date = end_date - timedelta(days=interval)
        elif unit == 'weeks':
            start_date = end_date - timedelta(weeks=interval)
        elif unit == 'years':
            start_date = end_date - timedelta(days=365 * interval)
        else:
            raise ValueError("Invalid time unit")

        logger.info(f"Fetching analysis for source: {source}, interval: {interval} {unit} from {start_date} to {end_date}")

        # Query for news and sentiment analysis
        news_data = db.query(
            NewsModel.publish_datetime,
            func.count(NewsModel.id).label('news_count'),
            func.avg(NewsModel.sentiment_score).label('avg_sentiment')
        ).filter(
            NewsModel.news_source == source,
            NewsModel.publish_datetime.between(start_date, end_date)
        ).group_by(
            extract('day', NewsModel.publish_datetime)
        ).all()

        logger.debug(f"Number of records fetched: {len(news_data)}")

        # Construct `news_history` and `news_perception`
        news_history = [
            {
                "date": str(news.publish_datetime.date()),
                "news_count": news.news_count
            }
            for news in news_data
        ]

        news_perception = [
            {
                "date": str(news.publish_datetime.date()),
                "positive_sentiment_score": max(0, news.avg_sentiment),
                "negative_sentiment_score": abs(min(0, news.avg_sentiment))
            }
            for news in news_data
        ]

        # Additional calculations
        news_count = sum(news.news_count for news in news_data)
        sources_count = db.query(NewsModel.news_source).distinct().count()

        total_positive = sum(n.avg_sentiment for n in news_data if n.avg_sentiment > 0)
        total_negative = sum(abs(n.avg_sentiment) for n in news_data if n.avg_sentiment < 0)
        general_perception = {
            "positive_sentiment_score": total_positive / len(news_data) if len(news_data) > 0 else 0,
            "negative_sentiment_score": total_negative / len(news_data) if len(news_data) > 0 else 0
        }

        db.close()

        formatted_analysis = {
            "source": {"id": source, "name": source},
            "news_history": news_history,
            "news_perception": news_perception,
            "news_count": news_count,
            "sources_count": sources_count,
            "historic_interval": interval,
            "historic_interval_unit": unit,
            "general_perception": general_perception
        }

        logger.info(f"Analysis data formatted: {formatted_analysis}")
        return formatted_analysis
