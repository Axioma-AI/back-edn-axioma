import logging
from src.config.chromadb_config import get_chroma_db_client
from src.models.news_tag_model import NewsModel
from sqlalchemy.orm import Session
from src.config.db_config import get_db
from src.utils.logger import setup_logger

# Configurar el logger
logger = setup_logger(__name__, level=logging.DEBUG)

class ArticleService:
    def __init__(self):
        self.collection = get_chroma_db_client()
        logger.debug("Chroma DB client initialized.")

    async def get_articles(self, limit: int, sort: str):
        db = next(get_db())
        try:
            logger.debug(f"Fetching articles with limit={limit} and sort={sort}.")
            articles = (
                db.query(NewsModel)
                .order_by(getattr(NewsModel, sort).desc())
                .limit(limit)
                .all()
            )
            logger.info(f"Fetched {len(articles)} articles sorted by {sort}.")
            return [self.format_article(article) for article in articles]
        except Exception as e:
            logger.error(f"Error while fetching articles: {e}")
            raise
        finally:
            db.close()
            logger.debug("Database session closed after fetching articles.")

    async def search_by_text(self, query: str, limit: int, sort: str):
        query_results = self.collection.query(query_texts=[query], n_results=limit)
        article_urls = query_results["ids"][0]
        distances = query_results["distances"][0]

        db = next(get_db())
        try:
            articles = db.query(NewsModel).filter(NewsModel.source_link.in_(article_urls)).order_by(getattr(NewsModel, sort).desc()).all()
            article_dict = {article.source_link: article for article in articles}
        finally:
            db.close()

        return [
            {
                **self.format_article(article_dict[article_url]),
                "distance": distance,
            }
            for article_url, distance in zip(article_urls, distances)
            if article_url in article_dict
        ]

    def format_article(self, article):
        logger.debug(f"Formatting article with id={article.id}.")
        formatted_article = {
            "id": article.id,
            "source": {"id": article.news_source, "name": article.news_source},
            "author": article.author,
            "title": article.title,
            "description": article.detail,
            "url": article.source_link,
            "urlToImage": article.image_url,
            "publishedAt": article.publish_datetime.isoformat(),
            "content": article.content,
            "sentiment_category": article.sentiment_category.name,
            "sentiment_score": float(article.sentiment_score),
        }
        logger.debug(f"Formatted article: {formatted_article}")
        return formatted_article
