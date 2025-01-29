import logging
from typing import Optional
from fastapi import HTTPException
# from src.config.chromadb_config import get_chroma_db_client
from src.models.categories_model import InterestsModel
from src.models.favorites_model import FavoritesModel
from src.schema.responses.response_articles_models import ArticleResponseModel, NewsCharacterModel, NewsCharacterTranslationModel, SourceModel, TranslationModel
from src.models.news_tag_model import NewsModel, NewsCharactersModel, NewsTransCharactersModel
from sqlalchemy.orm import joinedload
from sqlalchemy import text
from src.config.db_config import get_db
from src.models.user_model import UserModel
from src.utils.auth_utils import decode_and_sync_user
from src.utils.logger import setup_logger

# Configure the logger
logger = setup_logger(__name__, level=logging.DEBUG)

class ArticleService:
    # def __init__(self):
        # self.collection = get_chroma_db_client()
        # logger.debug("Chroma DB client initialized.")

    async def get_articles(self, limit: int, sort: str = "publish_datetime", token: Optional[str] = None):
        db = next(get_db())
        try:
            logger.debug(f"Fetching articles with limit={limit} sorted by {sort} in descending order.")

            # Consulta con relaciones correctamente especificadas
            articles = (
                db.query(NewsModel)
                .options(
                    joinedload(NewsModel.translations),
                    joinedload(NewsModel.characters).joinedload(NewsCharactersModel.translations)
                )
                .order_by(getattr(NewsModel, sort).desc())
                .limit(limit)
                .all()
            )

            logger.info(f"Obtained the limit of articles sorted by {sort} in descending order.")

            favorite_ids = set()
            if token:
                logger.debug(f"Token provided. Decoding and checking favorites for the user.")
                user = decode_and_sync_user(token, db)
                favorite_ids = {fav.news_id for fav in db.query(FavoritesModel).filter_by(user_id=user.id).all()}

            formatted_articles = [
                ArticleResponseModel(
                    id=article.id,
                    source=SourceModel(id=article.news_source, name=article.news_source),
                    author=article.author,
                    title=article.title,
                    description=article.detail,
                    url=article.source_link,
                    urlToImage=article.image_url,
                    publishedAt=article.publish_datetime.isoformat() if article.publish_datetime else "",
                    content=article.content,
                    sentiment_category=article.sentiment_category.name,
                    sentiment_score=float(article.sentiment_score),
                    summary=article.summary,
                    justification=article.justification,
                    news_type_category=article.news_type_category,
                    news_type_justification=article.news_type_justification,
                    purpose_objective=article.purpose_objective,
                    purpose_audience=article.purpose_audience,
                    context_temporality=article.context_temporality,
                    context_location=article.context_location,
                    content_facts_vs_opinions=article.content_facts_vs_opinions,
                    content_precision=article.content_precision,
                    content_impartiality=article.content_impartiality,
                    structure_clarity=article.structure_clarity,
                    structure_key_data=article.structure_key_data,
                    tone_neutrality=article.tone_neutrality,
                    tone_ethics=article.tone_ethics,
                    is_favorite=article.id in favorite_ids if token else None,
                    translations=[
                        TranslationModel(
                            id=translation.id,
                            title_tra=translation.title_tra,
                            detail_tra=translation.detail_tra,
                            content_tra=translation.content_tra,
                            summary_tra=translation.summary_tra,
                            justification_tra=translation.justification_tra,
                            news_type_category_tra=translation.news_type_category_tra,
                            news_type_justification_tra=translation.news_type_justification_tra,
                            purpose_objective_tra=translation.purpose_objective_tra,
                            purpose_audience_tra=translation.purpose_audience_tra,
                            context_temporality_tra=translation.context_temporality_tra,
                            context_location_tra=translation.context_location_tra,
                            content_facts_vs_opinions_tra=translation.content_facts_vs_opinions_tra,
                            content_precision_tra=translation.content_precision_tra,
                            content_impartiality_tra=translation.content_impartiality_tra,
                            structure_clarity_tra=translation.structure_clarity_tra,
                            structure_key_data_tra=translation.structure_key_data_tra,
                            tone_neutrality_tra=translation.tone_neutrality_tra,
                            tone_ethics_tra=translation.tone_ethics_tra,
                            language=translation.language
                        )
                        for translation in article.translations
                    ],
                    characters=[
                        NewsCharacterModel(
                            id=character.id,
                            character_name=character.character_name,
                            character_description=character.character_description,
                            translations=[
                                NewsCharacterTranslationModel(
                                    id=translation.id,
                                    character_description_tra=translation.character_description_tra,
                                    language=translation.language
                                )
                                for translation in character.translations
                            ]
                        )
                        for character in article.characters
                    ]
                )
                for article in articles
            ]

            logger.info(f"Returning {len(formatted_articles)} articles formatted using ArticleResponseModel.")
            return formatted_articles

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error while fetching articles: {e}\n{error_details}")
            raise
        finally:
            db.close()
            logger.debug("Database session closed after fetching articles.")

    # async def search_by_text_vdb(self, query: str, limit: int, sort: str = "publish_datetime", token: Optional[str] = None):
    #     logger.debug(f"Performing vector search for query='{query}' with limit={limit}.")
    #     query_results = self.collection.query(query_texts=[query], n_results=limit)
    #     article_urls = query_results["ids"][0]
    #     distances = query_results["distances"][0]

    #     db = next(get_db())
    #     try:
    #         logger.debug(f"Fetching articles from DB for {len(article_urls)} URLs.")
    #         articles = (
    #             db.query(NewsModel)
    #             .filter(NewsModel.source_link.in_(article_urls))
    #             .order_by(getattr(NewsModel, sort).desc())
    #             .all()
    #         )
    #         article_dict = {article.source_link: article for article in articles}

    #         if token:
    #             logger.debug(f"Token provided. Decoding and checking favorites for the user.")
    #             user = decode_and_sync_user(token, db)
    #             favorite_ids = {fav.news_id for fav in db.query(FavoritesModel).filter_by(user_id=user.id).all()}
    #             logger.info(f"Retrieved {len(favorite_ids)} favorite IDs for user ID: {user.id}.")
    #         else:
    #             favorite_ids = set()
    #             logger.debug(f"No token provided. Skipping favorite check.")

    #         formatted_results = [
    #             {
    #                 **self.format_article(article_dict[article_url]),
    #                 "distance": distance,
    #                 "is_favorite": article_dict[article_url].id in favorite_ids if article_url in article_dict else None,
    #             }
    #             for article_url, distance in zip(article_urls, distances)
    #             if article_url in article_dict
    #         ]
    #         logger.info(f"Returning {len(formatted_results)} articles with distance and favorite information.")
    #         return formatted_results

    #     except Exception as e:
    #         logger.error(f"Error while performing vector search: {e}")
    #         raise
    #     finally:
    #         db.close()
    #         logger.debug("Database session closed after vector search.")

    async def search_by_text_db(self, query: str, limit: int, sort: str = "publish_datetime", token: Optional[str] = None):
        logger.debug(f"Performing SQL search for query='{query}' with limit={limit}.")
        db = next(get_db())
        try:
            logger.debug(f"Fetching articles from DB using MATCH and AGAINST for query='{query}'.")

            # Ajustar el formato de la consulta
            query = f'"{query}"'
            # Usar columnas calculadas con alias explícito
            articles = db.query(
                NewsModel,
                text("MATCH(title, content) AGAINST(:query IN BOOLEAN MODE) AS distance")
            ).filter(
                text("MATCH(title, content) AGAINST(:query IN BOOLEAN MODE)")
            ).params(query=query).order_by(getattr(NewsModel, sort).desc()).limit(limit).all()

            # Gestión de favoritos
            favorite_ids = set()
            if token:
                logger.debug("Token provided. Decoding and checking favorites for the user.")
                user = decode_and_sync_user(token, db)
                favorite_ids = {fav.news_id for fav in db.query(FavoritesModel).filter_by(user_id=user.id).all()}

            # Formateo de resultados
            formatted_results = [
                ArticleResponseModel(
                    id=article[0].id,
                    source=SourceModel(id=article[0].news_source, name=article[0].news_source),
                    author=article[0].author,
                    title=article[0].title,
                    description=article[0].detail,
                    url=article[0].source_link,
                    urlToImage=article[0].image_url,
                    publishedAt=article[0].publish_datetime.isoformat() if article[0].publish_datetime else "",
                    content=article[0].content,
                    sentiment_category=article[0].sentiment_category.name,
                    sentiment_score=float(article[0].sentiment_score),
                    summary=article[0].summary,
                    justification=article[0].justification,
                    news_type_category=article[0].news_type_category,
                    news_type_justification=article[0].news_type_justification,
                    purpose_objective=article[0].purpose_objective,
                    purpose_audience=article[0].purpose_audience,
                    context_temporality=article[0].context_temporality,
                    context_location=article[0].context_location,
                    content_facts_vs_opinions=article[0].content_facts_vs_opinions,
                    content_precision=article[0].content_precision,
                    content_impartiality=article[0].content_impartiality,
                    structure_clarity=article[0].structure_clarity,
                    structure_key_data=article[0].structure_key_data,
                    tone_neutrality=article[0].tone_neutrality,
                    tone_ethics=article[0].tone_ethics,
                    distance=article[1],  # Columna calculada 'distance'
                    is_favorite=article[0].id in favorite_ids,
                    translations=[
                        TranslationModel(
                            id=translation.id,
                            title_tra=translation.title_tra,
                            detail_tra=translation.detail_tra,
                            content_tra=translation.content_tra,
                            summary_tra=translation.summary_tra,
                            justification_tra=translation.justification_tra,
                            news_type_category_tra=translation.news_type_category_tra,
                            news_type_justification_tra=translation.news_type_justification_tra,
                            purpose_objective_tra=translation.purpose_objective_tra,
                            purpose_audience_tra=translation.purpose_audience_tra,
                            context_temporality_tra=translation.context_temporality_tra,
                            context_location_tra=translation.context_location_tra,
                            content_facts_vs_opinions_tra=translation.content_facts_vs_opinions_tra,
                            content_precision_tra=translation.content_precision_tra,
                            content_impartiality_tra=translation.content_impartiality_tra,
                            structure_clarity_tra=translation.structure_clarity_tra,
                            structure_key_data_tra=translation.structure_key_data_tra,
                            tone_neutrality_tra=translation.tone_neutrality_tra,
                            tone_ethics_tra=translation.tone_ethics_tra,
                            language=translation.language
                        )
                        for translation in article[0].translations
                    ],
                    characters=[
                        NewsCharacterModel(
                            id=character.id,
                            character_name=character.character_name,
                            character_description=character.character_description,
                            translations=[
                                NewsCharacterTranslationModel(
                                    id=translation.id,
                                    character_description_tra=translation.character_description_tra,
                                    language=translation.language
                                )
                                for translation in character.translations
                            ]
                        )
                        for character in article[0].characters
                    ]
                )
                for article in articles
            ]

            logger.info(f"Returning {len(formatted_results)} articles from SQL search with distance.")
            return formatted_results

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error while performing SQL search: {e}\n{error_details}")
            raise
        finally:
            db.close()
            logger.debug("Database session closed after SQL search.")

    # def format_article(self, article):
    #     logger.debug(f"Formatting article with id={article.id}.")
    #     formatted_article = {
    #         "id": article.id,
    #         "source": {"id": article.news_source, "name": article.news_source},
    #         "author": article.author,
    #         "title": article.title,
    #         "description": article.detail,
    #         "url": article.source_link,
    #         "urlToImage": article.image_url,
    #         "publishedAt": article.publish_datetime.isoformat() if article.publish_datetime else "",
    #         "content": article.content,
    #         "sentiment_category": article.sentiment_category.name,
    #         "sentiment_score": float(article.sentiment_score),
    #         "translations": [
    #             {
    #                 "id": translation.id,
    #                 "title_tra": translation.title_tra,
    #                 "detail_tra": translation.detail_tra,
    #                 "content_tra": translation.content_tra,
    #                 "language": translation.language
    #             }
    #             for translation in article.translations
    #         ],
    #     }
    #     logger.debug(f"Formatted article with translations and with id={article.id}.")
    #     return formatted_article

    async def get_all_articles(self):
        db = next(get_db())
        try:
            logger.debug("Fetching all articles sorted by publish_datetime in descending order.")

            # Query with joined relationships
            articles = (
                db.query(NewsModel)
                .options(
                    joinedload(NewsModel.translations),
                    joinedload(NewsModel.characters).joinedload(NewsCharactersModel.translations)
                )
                .order_by(NewsModel.publish_datetime.desc())
                .all()
            )
            logger.info(f"Fetched {len(articles)} articles.")

            formatted_articles = [
                ArticleResponseModel(
                    id=article.id,
                    source=SourceModel(id=article.news_source, name=article.news_source),
                    author=article.author,
                    title=article.title,
                    description=article.detail,
                    url=article.source_link,
                    urlToImage=article.image_url,
                    publishedAt=article.publish_datetime.isoformat() if article.publish_datetime else "",
                    content=article.content,
                    sentiment_category=article.sentiment_category.name,
                    sentiment_score=float(article.sentiment_score),
                    summary=article.summary,
                    justification=article.justification,
                    news_type_category=article.news_type_category,
                    news_type_justification=article.news_type_justification,
                    purpose_objective=article.purpose_objective,
                    purpose_audience=article.purpose_audience,
                    context_temporality=article.context_temporality,
                    context_location=article.context_location,
                    content_facts_vs_opinions=article.content_facts_vs_opinions,
                    content_precision=article.content_precision,
                    content_impartiality=article.content_impartiality,
                    structure_clarity=article.structure_clarity,
                    structure_key_data=article.structure_key_data,
                    tone_neutrality=article.tone_neutrality,
                    tone_ethics=article.tone_ethics,
                    is_favorite=None,
                    translations=[
                        TranslationModel(
                            id=translation.id,
                            title_tra=translation.title_tra,
                            detail_tra=translation.detail_tra,
                            content_tra=translation.content_tra,
                            summary_tra=translation.summary_tra,
                            justification_tra=translation.justification_tra,
                            news_type_category_tra=translation.news_type_category_tra,
                            news_type_justification_tra=translation.news_type_justification_tra,
                            purpose_objective_tra=translation.purpose_objective_tra,
                            purpose_audience_tra=translation.purpose_audience_tra,
                            context_temporality_tra=translation.context_temporality_tra,
                            context_location_tra=translation.context_location_tra,
                            content_facts_vs_opinions_tra=translation.content_facts_vs_opinions_tra,
                            content_precision_tra=translation.content_precision_tra,
                            content_impartiality_tra=translation.content_impartiality_tra,
                            structure_clarity_tra=translation.structure_clarity_tra,
                            structure_key_data_tra=translation.structure_key_data_tra,
                            tone_neutrality_tra=translation.tone_neutrality_tra,
                            tone_ethics_tra=translation.tone_ethics_tra,
                            language=translation.language
                        )
                        for translation in article.translations
                    ],
                    characters=[
                        NewsCharacterModel(
                            id=character.id,
                            character_name=character.character_name,
                            character_description=character.character_description,
                            translations=[
                                NewsCharacterTranslationModel(
                                    id=translation.id,
                                    character_description_tra=translation.character_description_tra,
                                    language=translation.language
                                )
                                for translation in character.translations
                            ]
                        )
                        for character in article.characters
                    ]
                )
                for article in articles
            ]

            return formatted_articles

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error while fetching all articles: {e}\n{error_details}")
            raise
        finally:
            db.close()
            logger.debug("Database session closed after fetching all articles.")

    
    async def get_article_by_id(self, article_id: int, token: Optional[str] = None):
        db = next(get_db())
        try:
            logger.debug(f"Querying database for article with ID: {article_id}")

            # Query with joined relationships
            article = (
                db.query(NewsModel)
                .options(
                    joinedload(NewsModel.translations),
                    joinedload(NewsModel.characters).joinedload(NewsCharactersModel.translations)
                )
                .filter(NewsModel.id == article_id)
                .first()
            )

            if not article:
                logger.warning(f"No article found with ID: {article_id}")
                return None

            formatted_article = ArticleResponseModel(
                id=article.id,
                source=SourceModel(id=article.news_source, name=article.news_source),
                author=article.author,
                title=article.title,
                description=article.detail,
                url=article.source_link,
                urlToImage=article.image_url,
                publishedAt=article.publish_datetime.isoformat() if article.publish_datetime else "",
                content=article.content,
                sentiment_category=article.sentiment_category.name,
                sentiment_score=float(article.sentiment_score),
                summary=article.summary,
                justification=article.justification,
                news_type_category=article.news_type_category,
                news_type_justification=article.news_type_justification,
                purpose_objective=article.purpose_objective,
                purpose_audience=article.purpose_audience,
                context_temporality=article.context_temporality,
                context_location=article.context_location,
                content_facts_vs_opinions=article.content_facts_vs_opinions,
                content_precision=article.content_precision,
                content_impartiality=article.content_impartiality,
                structure_clarity=article.structure_clarity,
                structure_key_data=article.structure_key_data,
                tone_neutrality=article.tone_neutrality,
                tone_ethics=article.tone_ethics,
                translations=[
                    TranslationModel(
                        id=translation.id,
                        title_tra=translation.title_tra,
                        detail_tra=translation.detail_tra,
                        content_tra=translation.content_tra,
                        summary_tra=translation.summary_tra,
                        justification_tra=translation.justification_tra,
                        news_type_category_tra=translation.news_type_category_tra,
                        news_type_justification_tra=translation.news_type_justification_tra,
                        purpose_objective_tra=translation.purpose_objective_tra,
                        purpose_audience_tra=translation.purpose_audience_tra,
                        context_temporality_tra=translation.context_temporality_tra,
                        context_location_tra=translation.context_location_tra,
                        content_facts_vs_opinions_tra=translation.content_facts_vs_opinions_tra,
                        content_precision_tra=translation.content_precision_tra,
                        content_impartiality_tra=translation.content_impartiality_tra,
                        structure_clarity_tra=translation.structure_clarity_tra,
                        structure_key_data_tra=translation.structure_key_data_tra,
                        tone_neutrality_tra=translation.tone_neutrality_tra,
                        tone_ethics_tra=translation.tone_ethics_tra,
                        language=translation.language
                    )
                    for translation in article.translations
                ],
                characters=[
                    NewsCharacterModel(
                        id=character.id,
                        character_name=character.character_name,
                        character_description=character.character_description,
                        translations=[
                            NewsCharacterTranslationModel(
                                id=translation.id,
                                character_description_tra=translation.character_description_tra,
                                language=translation.language
                            )
                            for translation in character.translations
                        ]
                    )
                    for character in article.characters
                ]
            )

            if token:
                user = decode_and_sync_user(token, db)
                is_favorite = (
                    db.query(FavoritesModel)
                    .filter_by(user_id=user.id, news_id=article_id)
                    .first()
                    is not None
                )
                formatted_article.is_favorite = is_favorite
            else:
                formatted_article.is_favorite = None

            return formatted_article

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error while fetching article by ID: {e}\n{error_details}")
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

            # Query with joined relationships
            articles = (
                db.query(NewsModel)
                .options(
                    joinedload(NewsModel.translations),
                    joinedload(NewsModel.characters).joinedload(NewsCharactersModel.translations)
                )
                .filter(NewsModel.news_source.ilike(f"%{source}%"))
                .order_by(getattr(NewsModel, sort).desc())
                .limit(limit)
                .all()
            )

            logger.info(f"Obtained the limit of articles for source='{source}'.")

            # Gestión de favoritos si se proporciona un token
            favorite_ids = set()
            if token:
                logger.debug("Token provided. Decoding and checking favorites for the user.")
                user = decode_and_sync_user(token, db)
                favorite_ids = {fav.news_id for fav in db.query(FavoritesModel).filter_by(user_id=user.id).all()}

            formatted_articles = [
                ArticleResponseModel(
                    id=article.id,
                    source=SourceModel(id=article.news_source, name=article.news_source),
                    author=article.author,
                    title=article.title,
                    description=article.detail,
                    url=article.source_link,
                    urlToImage=article.image_url,
                    publishedAt=article.publish_datetime.isoformat() if article.publish_datetime else "",
                    content=article.content,
                    sentiment_category=article.sentiment_category.name,
                    sentiment_score=float(article.sentiment_score),
                    summary=article.summary,
                    justification=article.justification,
                    news_type_category=article.news_type_category,
                    news_type_justification=article.news_type_justification,
                    purpose_objective=article.purpose_objective,
                    purpose_audience=article.purpose_audience,
                    context_temporality=article.context_temporality,
                    context_location=article.context_location,
                    content_facts_vs_opinions=article.content_facts_vs_opinions,
                    content_precision=article.content_precision,
                    content_impartiality=article.content_impartiality,
                    structure_clarity=article.structure_clarity,
                    structure_key_data=article.structure_key_data,
                    tone_neutrality=article.tone_neutrality,
                    tone_ethics=article.tone_ethics,
                    is_favorite=article.id in favorite_ids if token else None,
                    translations=[
                        TranslationModel(
                            id=translation.id,
                            title_tra=translation.title_tra,
                            detail_tra=translation.detail_tra,
                            content_tra=translation.content_tra,
                            summary_tra=translation.summary_tra,
                            justification_tra=translation.justification_tra,
                            news_type_category_tra=translation.news_type_category_tra,
                            news_type_justification_tra=translation.news_type_justification_tra,
                            purpose_objective_tra=translation.purpose_objective_tra,
                            purpose_audience_tra=translation.purpose_audience_tra,
                            context_temporality_tra=translation.context_temporality_tra,
                            context_location_tra=translation.context_location_tra,
                            content_facts_vs_opinions_tra=translation.content_facts_vs_opinions_tra,
                            content_precision_tra=translation.content_precision_tra,
                            content_impartiality_tra=translation.content_impartiality_tra,
                            structure_clarity_tra=translation.structure_clarity_tra,
                            structure_key_data_tra=translation.structure_key_data_tra,
                            tone_neutrality_tra=translation.tone_neutrality_tra,
                            tone_ethics_tra=translation.tone_ethics_tra,
                            language=translation.language
                        )
                        for translation in article.translations
                    ],
                    characters=[
                        NewsCharacterModel(
                            id=character.id,
                            character_name=character.character_name,
                            character_description=character.character_description,
                            translations=[
                                NewsCharacterTranslationModel(
                                    id=translation.id,
                                    character_description_tra=translation.character_description_tra,
                                    language=translation.language
                                )
                                for translation in character.translations
                            ]
                        )
                        for character in article.characters
                    ]
                )
                for article in articles
            ]

            logger.info(f"Returning {len(formatted_articles)} articles formatted using ArticleResponseModel.")
            return formatted_articles

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error while fetching articles by source: {e}\n{error_details}")
            raise
        finally:
            db.close()
            logger.debug("Database session closed after querying articles by source.")

    # Método para obtener artículos basados en el correo del usuario
    async def get_articles_by_email(self, email: str, limit: int, sort: str):
        db = next(get_db())
        try:
            logger.debug(f"Fetching articles for email: {email} with limit={limit} sorted by {sort}.")

            # Verificar si el usuario existe
            user = db.query(UserModel).filter(UserModel.email == email).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found.")

            # Buscar los intereses del usuario
            interests = db.query(InterestsModel).filter(InterestsModel.user_id == user.id).all()
            if not interests:
                raise HTTPException(status_code=404, detail="No interests found for the provided email.")

            articles = []

            # Buscar artículos relacionados con los intereses del usuario
            for interest in interests:
                query_results = self.collection.query(query_texts=[interest.keyword], n_results=limit)
                article_urls = query_results["ids"][0]
                keyword_articles = (
                    db.query(NewsModel)
                    .options(
                        joinedload(NewsModel.translations),
                        joinedload(NewsModel.characters).joinedload(NewsCharactersModel.translations)
                    )
                    .filter(NewsModel.source_link.in_(article_urls))
                    .order_by(getattr(NewsModel, sort).desc())
                    .limit(limit)
                    .all()
                )

                for article in keyword_articles:
                    articles.append(
                        ArticleResponseModel(
                            id=article.id,
                            source=SourceModel(id=article.news_source, name=article.news_source),
                            author=article.author,
                            title=article.title,
                            description=article.detail,
                            url=article.source_link,
                            urlToImage=article.image_url,
                            publishedAt=article.publish_datetime.isoformat() if article.publish_datetime else "",
                            content=article.content,
                            sentiment_category=article.sentiment_category.name,
                            sentiment_score=float(article.sentiment_score),
                            summary=article.summary,
                            justification=article.justification,
                            news_type_category=article.news_type_category,
                            news_type_justification=article.news_type_justification,
                            purpose_objective=article.purpose_objective,
                            purpose_audience=article.purpose_audience,
                            context_temporality=article.context_temporality,
                            context_location=article.context_location,
                            content_facts_vs_opinions=article.content_facts_vs_opinions,
                            content_precision=article.content_precision,
                            content_impartiality=article.content_impartiality,
                            structure_clarity=article.structure_clarity,
                            structure_key_data=article.structure_key_data,
                            tone_neutrality=article.tone_neutrality,
                            tone_ethics=article.tone_ethics,
                            is_favorite=None,  # No se está gestionando favoritos aquí
                            translations=[
                                TranslationModel(
                                    id=translation.id,
                                    title_tra=translation.title_tra,
                                    detail_tra=translation.detail_tra,
                                    content_tra=translation.content_tra,
                                    summary_tra=translation.summary_tra,
                                    justification_tra=translation.justification_tra,
                                    news_type_category_tra=translation.news_type_category_tra,
                                    news_type_justification_tra=translation.news_type_justification_tra,
                                    purpose_objective_tra=translation.purpose_objective_tra,
                                    purpose_audience_tra=translation.purpose_audience_tra,
                                    context_temporality_tra=translation.context_temporality_tra,
                                    context_location_tra=translation.context_location_tra,
                                    content_facts_vs_opinions_tra=translation.content_facts_vs_opinions_tra,
                                    content_precision_tra=translation.content_precision_tra,
                                    content_impartiality_tra=translation.content_impartiality_tra,
                                    structure_clarity_tra=translation.structure_clarity_tra,
                                    structure_key_data_tra=translation.structure_key_data_tra,
                                    tone_neutrality_tra=translation.tone_neutrality_tra,
                                    tone_ethics_tra=translation.tone_ethics_tra,
                                    language=translation.language
                                )
                                for translation in article.translations
                            ],
                            characters=[
                                NewsCharacterModel(
                                    id=character.id,
                                    character_name=character.character_name,
                                    character_description=character.character_description,
                                    translations=[
                                        NewsCharacterTranslationModel(
                                            id=translation.id,
                                            character_description_tra=translation.character_description_tra,
                                            language=translation.language
                                        )
                                        for translation in character.translations
                                    ]
                                )
                                for character in article.characters
                            ],
                            category=interest.keyword
                        )
                    )

            logger.info(f"Returning {len(articles)} articles for the provided email.")
            return articles

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error while fetching articles by email: {e}\n{error_details}")
            raise
        finally:
            db.close()
            logger.debug("Database session closed after querying articles by email.")
