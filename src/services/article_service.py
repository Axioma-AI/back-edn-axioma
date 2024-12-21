import logging
from typing import Optional
from src.config.chromadb_config import get_chroma_db_client
from src.models.favorites_model import FavoritesModel
from src.models.news_tag_model import NewsModel
from sqlalchemy.orm import Session, joinedload
from src.config.db_config import get_db
from src.utils.auth_utils import decode_and_sync_user
from src.utils.logger import setup_logger

# Configure the logger
logger = setup_logger(__name__, level=logging.DEBUG)

class ArticleService:
    def __init__(self):
        self.collection = get_chroma_db_client()
        logger.debug("Chroma DB client initialized.")

    async def get_articles(self, limit: int, sort: str = "publish_datetime", token: Optional[str] = None):
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
            logger.info(f"Obtained the limit of articles sorted by {sort} in descending order.")
            if token:
                logger.debug(f"Token provided. Decoding and checking favorites for the user.")
                user = decode_and_sync_user(token, db)
                favorite_ids = {fav.news_id for fav in db.query(FavoritesModel).filter_by(user_id=user.id).all()}
                formatted_articles = [
                    {**self.format_article(article), "is_favorite": article.id in favorite_ids}
                    for article in articles
                ]
                logger.info(f"Processed favorites for user ID: {user.id}.")
            else:
                logger.debug(f"No token provided. Returning articles without favorite information.")
                formatted_articles = [
                    {**self.format_article(article), "is_favorite": None}
                    for article in articles
                ]
            return formatted_articles

        except Exception as e:
            logger.error(f"Error while fetching articles: {e}")
            raise
        finally:
            db.close()
            logger.debug("Database session closed after fetching articles.")

    async def search_by_text(self, query: str, limit: int, sort: str = "publish_datetime", token: Optional[str] = None):
        logger.debug(f"Performing vector search for query='{query}' with limit={limit}.")
        query_results = self.collection.query(query_texts=[query], n_results=limit)
        article_urls = query_results["ids"][0]
        distances = query_results["distances"][0]

        db = next(get_db())
        try:
            logger.debug(f"Fetching articles from DB for {len(article_urls)} URLs.")
            articles = (
                db.query(NewsModel)
                .filter(NewsModel.source_link.in_(article_urls))
                .order_by(getattr(NewsModel, sort).desc())
                .all()
            )
            article_dict = {article.source_link: article for article in articles}

            if token:
                logger.debug(f"Token provided. Decoding and checking favorites for the user.")
                user = decode_and_sync_user(token, db)
                favorite_ids = {fav.news_id for fav in db.query(FavoritesModel).filter_by(user_id=user.id).all()}
                logger.info(f"Retrieved {len(favorite_ids)} favorite IDs for user ID: {user.id}.")
            else:
                favorite_ids = set()
                logger.debug(f"No token provided. Skipping favorite check.")

            formatted_results = [
                {
                    **self.format_article(article_dict[article_url]),
                    "distance": distance,
                    "is_favorite": article_dict[article_url].id in favorite_ids if article_url in article_dict else None,
                }
                for article_url, distance in zip(article_urls, distances)
                if article_url in article_dict
            ]
            logger.info(f"Returning {len(formatted_results)} articles with distance and favorite information.")
            return formatted_results

        except Exception as e:
            logger.error(f"Error while performing vector search: {e}")
            raise
        finally:
            db.close()
            logger.debug("Database session closed after vector search.")

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
    
    async def get_article_by_id(self, article_id: int, token: Optional[str] = None):
        db = next(get_db())
        try:
            logger.debug(f"Querying database for article with ID: {article_id}")
            article = (
                db.query(NewsModel)
                .options(joinedload(NewsModel.translations))
                .filter(NewsModel.id == article_id)
                .first()
            )
            if not article:
                logger.warning(f"No article found with ID: {article_id}")
                return None
            
            formatted_article = self.format_article(article)

            # Determinar si está en favoritos si se proporciona el token
            if token:
                user = decode_and_sync_user(token, db)
                is_favorite = (
                    db.query(FavoritesModel)
                    .filter_by(user_id=user.id, news_id=article_id)
                    .first()
                    is not None
                )
                formatted_article["is_favorite"] = is_favorite
            else:
                formatted_article["is_favorite"] = None

            return formatted_article

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

    async def search_by_source(self, source: str, limit: int, sort: str = "publish_datetime", token: Optional[str] = None):
        db = next(get_db())
        try:
            logger.debug(f"Querying database for articles with news_source='{source}', limit={limit}, sort={sort}.")
            articles = (
                db.query(NewsModel)
                .options(joinedload(NewsModel.translations))  # Load translations
                .filter(NewsModel.news_source.ilike(f"%{source}%"))
                .order_by(getattr(NewsModel, sort).desc())
                .limit(limit)
                .all()
            )
            logger.info(f"Obtained the limit of articles for source='{source}'.")

            if token:
                logger.debug(f"Token provided. Decoding and checking favorites for the user.")
                user = decode_and_sync_user(token, db)
                favorite_ids = {fav.news_id for fav in db.query(FavoritesModel).filter_by(user_id=user.id).all()}
                formatted_articles = [
                    {**self.format_article(article), "is_favorite": article.id in favorite_ids}
                    for article in articles
                ]
                logger.info(f"Processed favorites for user ID: {user.id}.")
            else:
                logger.debug(f"No token provided. Returning articles without favorite information.")
                formatted_articles = [
                    {**self.format_article(article), "is_favorite": None}
                    for article in articles
                ]
            return formatted_articles

        except Exception as e:
            logger.error(f"Error while fetching articles by source: {e}")
            raise
        finally:
            db.close()
            logger.debug("Database session closed after querying articles by source.")