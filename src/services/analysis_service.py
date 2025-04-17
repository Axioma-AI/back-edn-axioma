from collections import defaultdict
from datetime import datetime, timedelta
import logging
from sqlalchemy import text, select
from src.models.news_tag_model import NewsModel
from src.schema.responses.response_analysis_models import AnalysisResponseModel, NewsHistoryModel, NewsPerceptionModel, GeneralPerceptionModel
from src.utils.logger import setup_logger
from src.config.db_config import get_db
from sqlalchemy.orm import Session

logger = setup_logger(__name__, level=logging.DEBUG)

class AnalysisService:

    async def search_by_text_analysis(self, query: str, interval: int, unit: str) -> AnalysisResponseModel:
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
        else:
            raise ValueError("Invalid time unit")

        logger.debug(f"Date range calculated: start_date={start_date}, end_date={end_date}")
        query_str = f'"{query}"'

        async for db in get_db():
            try:
                logger.info(f"Performing async text search in database for query: '{query}'")
                sql = text("""
                    SELECT *, MATCH(title, content) AGAINST(:query IN BOOLEAN MODE) AS distance
                    FROM news
                    WHERE MATCH(title, content) AGAINST(:query IN BOOLEAN MODE)
                    AND publish_datetime BETWEEN :start_date AND :end_date
                    ORDER BY publish_datetime DESC
                    LIMIT 100
                """)
                result = await db.execute(sql, {
                    "query": query_str,
                    "start_date": start_date,
                    "end_date": end_date
                })

                rows = result.fetchall()
                logger.debug(f"Text search completed. Found {len(rows)} articles.")

                average_scores = defaultdict(list)
                sources_history = defaultdict(int)

                articles = []
                for row in rows:
                    news_data = dict(row._mapping)
                    distance = news_data.pop("distance")
                    article = NewsModel(**news_data)
                    articles.append((article, distance))

                    date = article.publish_datetime.date()
                    sources_history[date] += 1
                    average_scores[date].append(float(article.sentiment_score))

                news_history_list = [
                    NewsHistoryModel(date=str(date), news_count=count)
                    for date, count in sorted(sources_history.items())
                ]

                news_perception_list = [
                    NewsPerceptionModel(
                        date=str(date),
                        positive_sentiment_score=(1 + (sum(scores) / len(scores)) if scores else 0.5) / 2,
                        negative_sentiment_score=(1 - (sum(scores) / len(scores)) if scores else 0.5) / 2
                    )
                    for date, scores in average_scores.items()
                ]

                all_scores = [score for scores in average_scores.values() for score in scores]
                general_perception = GeneralPerceptionModel(
                    positive_sentiment_score=(1 + (sum(all_scores) / len(all_scores)) if all_scores else 0.5) / 2,
                    negative_sentiment_score=(1 - (sum(all_scores) / len(all_scores)) if all_scores else 0.5) / 2
                )

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

            except Exception as e:
                logger.error(f"Error in async analysis: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                raise
