import logging
from typing import Optional
from fastapi import HTTPException
from contextlib import asynccontextmanager
from src.models.categories_model import InterestsModel
from src.models.favorites_model import FavoritesModel
from src.schema.responses.response_articles_models import ArticleResponseModel, NewsCharacterModel, NewsCharacterTranslationModel, SourceModel, TranslationModel
from src.models.news_tag_model import NewsModel, NewsCharactersModel, NewsTransCharactersModel
from sqlalchemy.orm import joinedload, selectinload, aliased
from sqlalchemy import text, select
from src.config.db_config import get_db
from src.models.user_model import UserModel
from src.utils.auth_utils import decode_and_sync_user
from src.utils.logger import setup_logger

# Configure the logger
logger = setup_logger(__name__, level=logging.DEBUG)

class ArticleService:

    async def get_articles(self, limit: int, sort: str = "publish_datetime", token: Optional[str] = None):
        async for db in get_db():
            try:
                logger.debug(f"Fetching articles with limit={limit} sorted by {sort} in descending order.")

                stmt = (
                    select(NewsModel)
                    .options(
                        selectinload(NewsModel.translations),
                        selectinload(NewsModel.characters).selectinload(NewsCharactersModel.translations)
                    )
                    .order_by(getattr(NewsModel, sort).desc())
                    .limit(limit)
                )
                result = await db.execute(stmt)
                articles = result.scalars().all()

                logger.info(f"Obtained {len(articles)} articles sorted by {sort} in descending order.")

                favorite_ids = set()
                if token:
                    logger.debug(f"Token provided. Decoding and checking favorites for the user.")
                    user = decode_and_sync_user(token, db)
                    fav_stmt = select(FavoritesModel.news_id).where(FavoritesModel.user_id == user.id)
                    fav_result = await db.execute(fav_stmt)
                    favorite_ids = {row[0] for row in fav_result.all()}

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

    async def search_by_text_db(self, query: str, limit: int, sort: str = "publish_datetime", token: Optional[str] = None):
        logger.debug(f"Performing SQL search for query='{query}' with limit={limit}.")

        # Validación contra SQL injection en columna sort
        valid_sort_columns = {"publish_datetime", "title", "author", "sentiment_score"}
        if sort not in valid_sort_columns:
            logger.warning(f"Invalid sort column: {sort}. Defaulting to 'publish_datetime'.")
            sort = "publish_datetime"

        async for db in get_db():
            try:
                logger.debug(f"Fetching articles using FULLTEXT MATCH with query='{query}'.")

                quoted_query = f'"{query}"'

                sql = text(f"""
                    SELECT *, MATCH(title, content) AGAINST(:query IN BOOLEAN MODE) AS distance
                    FROM news
                    WHERE MATCH(title, content) AGAINST(:query IN BOOLEAN MODE)
                    ORDER BY {sort} DESC
                    LIMIT :limit
                """)

                result = await db.execute(sql, {"query": quoted_query, "limit": limit})
                rows = result.fetchall()

                # Mapear manualmente los resultados
                articles = []
                for row in rows:
                    news_data = dict(row._mapping)
                    distance = news_data.pop("distance")
                    article = NewsModel(**news_data)
                    articles.append((article, distance))

                favorite_ids = set()
                if token:
                    logger.debug("Token provided. Decoding and checking favorites for the user.")
                    user = decode_and_sync_user(token, db)
                    favs = await db.execute(
                        text("SELECT news_id FROM favorites WHERE user_id = :uid"),
                        {"uid": user.id}
                    )
                    favorite_ids = {row[0] for row in favs.fetchall()}

                formatted_results = [
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
                        sentiment_category=article.sentiment_category,
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
                        distance=distance,
                        is_favorite=article.id in favorite_ids,
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
                    for article, distance in articles
                ]

                logger.info(f"Returning {len(formatted_results)} articles from SQL search.")
                return formatted_results

            except Exception as e:
                import traceback
                logger.error(f"Error while performing SQL search: {e}\n{traceback.format_exc()}")
                raise

    async def get_all_articles(self):
        async for db in get_db():
            try:
                logger.debug("Fetching all articles sorted by publish_datetime in descending order.")

                stmt = (
                    select(NewsModel)
                    .options(
                        selectinload(NewsModel.translations),
                        selectinload(NewsModel.characters).selectinload(NewsCharactersModel.translations)
                    )
                    .order_by(NewsModel.publish_datetime.desc())
                )
                result = await db.execute(stmt)
                articles = result.scalars().all()
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
    
    async def get_article_by_id(self, article_id: int, token: Optional[str] = None):
        async for db in get_db():
            try:
                logger.debug(f"Querying database for article with ID: {article_id}")

                stmt = (
                    select(NewsModel)
                    .options(
                        selectinload(NewsModel.translations),
                        selectinload(NewsModel.characters).selectinload(NewsCharactersModel.translations)
                    )
                    .where(NewsModel.id == article_id)
                )
                result = await db.execute(stmt)
                article = result.scalars().first()

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

                if token:
                    user = decode_and_sync_user(token, db)
                    stmt_fav = select(FavoritesModel).where(
                        FavoritesModel.user_id == user.id,
                        FavoritesModel.news_id == article_id
                    )
                    fav_result = await db.execute(stmt_fav)
                    formatted_article.is_favorite = fav_result.scalars().first() is not None
                else:
                    formatted_article.is_favorite = None

                return formatted_article

            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                logger.error(f"Error while fetching article by ID: {e}\n{error_details}")
                raise

    async def get_all_news_sources(self):
        async for db in get_db():
            try:
                logger.debug("Fetching all unique news sources.")

                stmt = select(NewsModel.news_source).distinct()
                result = await db.execute(stmt)
                sources = result.scalars().all()

                unique_sources = [source for source in sources if source is not None]
                logger.info(f"Found {len(unique_sources)} unique news sources.")
                return unique_sources

            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                logger.error(f"Error while fetching unique news sources: {e}\n{error_details}")
                raise

    async def search_by_source(self, source: str, limit: int, sort: str = "publish_datetime", token: Optional[str] = None):
        async for db in get_db():
            try:
                logger.debug(f"Querying database for articles with news_source='{source}', limit={limit}, sort={sort}.")

                stmt = (
                    select(NewsModel)
                    .options(
                        selectinload(NewsModel.translations),
                        selectinload(NewsModel.characters).selectinload(NewsCharactersModel.translations)
                    )
                    .where(NewsModel.news_source.ilike(f"%{source}%"))
                    .order_by(getattr(NewsModel, sort).desc())
                    .limit(limit)
                )
                result = await db.execute(stmt)
                articles = result.scalars().all()

                logger.info(f"Obtained {len(articles)} articles for source='{source}'.")

                favorite_ids = set()
                if token:
                    logger.debug("Token provided. Decoding and checking favorites for the user.")
                    user = decode_and_sync_user(token, db)
                    fav_stmt = select(FavoritesModel.news_id).where(FavoritesModel.user_id == user.id)
                    fav_result = await db.execute(fav_stmt)
                    favorite_ids = {row[0] for row in fav_result.fetchall()}

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

    # Método para obtener artículos basados en el correo del usuario
    async def get_articles_by_email(self, email: str, limit: int, sort: str):
        async for db in get_db():
            try:
                logger.debug(f"Fetching articles for email: {email} with limit={limit} sorted by {sort}.")

                # Verificar si el usuario existe
                user_stmt = select(UserModel).where(UserModel.email == email)
                user_result = await db.execute(user_stmt)
                user = user_result.scalars().first()
                if not user:
                    raise HTTPException(status_code=404, detail="User not found.")

                # Buscar los intereses del usuario
                interests_stmt = select(InterestsModel).where(InterestsModel.user_id == user.id)
                interests_result = await db.execute(interests_stmt)
                interests = interests_result.scalars().all()
                if not interests:
                    raise HTTPException(status_code=404, detail="No interests found for the provided email.")

                articles = []

                for interest in interests:
                    # Vector DB Search (aún síncrona porque self.collection es local)
                    query_results = self.collection.query(query_texts=[interest.keyword], n_results=limit)
                    article_urls = query_results["ids"][0]

                    # Buscar artículos por URL
                    stmt = (
                        select(NewsModel)
                        .options(
                            selectinload(NewsModel.translations),
                            selectinload(NewsModel.characters).selectinload(NewsCharactersModel.translations)
                        )
                        .where(NewsModel.source_link.in_(article_urls))
                        .order_by(getattr(NewsModel, sort).desc())
                        .limit(limit)
                    )
                    result = await db.execute(stmt)
                    keyword_articles = result.scalars().all()

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
