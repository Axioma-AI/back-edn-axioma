import logging
from src.config.chromadb_config import get_chroma_db_client
from src.models.news_tag_model import NewsModel
from sqlalchemy.orm import Session, joinedload
from src.config.db_config import get_db
from src.utils.logger import setup_logger

# Configure the logger
logger = setup_logger(__name__, level=logging.DEBUG)

class ArticleService:
    def __init__(self):
        self.collection = get_chroma_db_client()
        logger.debug("Chroma DB client initialized.")

    async def get_articles(self, limit: int, sort: str = "publish_datetime"):
        db = next(get_db())
        try:
            logger.debug(f"Fetching articles with limit={limit} sorted by {sort} in descending order.")
            articles = (
                db.query(NewsModel)
                .options(joinedload(NewsModel.translations))  # Load translations
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

    async def search_by_text(self, query: str, limit: int, sort: str = "publish_datetime"):
        query_results = self.collection.query(query_texts=[query], n_results=limit)
        article_urls = query_results["ids"][0]
        distances = query_results["distances"][0]

        db = next(get_db())
        try:
            articles = (
                db.query(NewsModel)
                .filter(NewsModel.source_link.in_(article_urls))
                .order_by(getattr(NewsModel, sort).desc())
                .all()
            )
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
            "publishedAt": article.publish_datetime.isoformat() if article.publish_datetime else "",
            "content": article.content,
            "sentiment_category": article.sentiment_category.name,
            "sentiment_score": float(article.sentiment_score),
            "translations": [
                {
                    "id": translation.id,
                    "title_tra": translation.title_tra,
                    "detail_tra": translation.detail_tra,
                    "content_tra": translation.content_tra,
                    "language": translation.language
                }
                for translation in article.translations
            ],
        }
        logger.debug(f"Formatted article with translations: {formatted_article}")
        return formatted_article

    async def get_all_articles(self):
        db = next(get_db())
        try:
            logger.debug("Fetching all articles sorted by publish_datetime in descending order.")
            articles = db.query(NewsModel).order_by(NewsModel.publish_datetime.desc()).all()
            logger.info(f"Fetched {len(articles)} articles.")
            return [self.format_article(article) for article in articles]
        except Exception as e:
            logger.error(f"Error while fetching all articles: {e}")
            raise
        finally:
            db.close()
            logger.debug("Database session closed after fetching all articles.")
    
    async def get_article_by_id(self, article_id: int):
        db = next(get_db())
        try:
            logger.debug(f"Querying database for article with ID: {article_id}")
            # Añadir joinedload para cargar la relación de traducciones
            article = (
                db.query(NewsModel)
                .options(joinedload(NewsModel.translations))  # Cargar la relación 'translations'
                .filter(NewsModel.id == article_id)
                .first()
            )
            if article:
                logger.info(f"Article with ID {article_id} found.")
                return self.format_article(article)
            else:
                logger.warning(f"No article found with ID: {article_id}")
                return None
        except Exception as e:
            logger.error(f"Error while fetching article by ID: {e}")
            raise
        finally:
            db.close()
            logger.debug("Database session closed after querying article by ID.")

    async def get_all_news_sources(self):
        db = next(get_db())
        try:
            logger.debug("Fetching all unique news sources.")
            sources = db.query(NewsModel.news_source).distinct().all()
            unique_sources = [source[0] for source in sources if source[0] is not None]
            logger.info(f"Found {len(unique_sources)} unique news sources.")
            return unique_sources
        except Exception as e:
            logger.error(f"Error while fetching unique news sources: {e}")
            raise
        finally:
            db.close()
            logger.debug("Database session closed after fetching unique news sources.")

    async def search_by_source(self, source: str, limit: int, sort: str = "publish_datetime"):
        db = next(get_db())
        try:
            logger.debug(f"Querying database for articles with news_source='{source}'.")
            articles = (
                db.query(NewsModel)
                .options(joinedload(NewsModel.translations))  # Cargar las traducciones
                .filter(NewsModel.news_source.ilike(f"%{source}%"))
                .order_by(getattr(NewsModel, sort).desc())
                .limit(limit)
                .all()
            )
            logger.info(f"Fetched {len(articles)} articles for source='{source}'.")
            return [self.format_article(article) for article in articles]
        except Exception as e:
            logger.error(f"Error while fetching articles by source: {e}")
            raise
        finally:
            db.close()
            logger.debug("Database session closed after querying articles by source.")
