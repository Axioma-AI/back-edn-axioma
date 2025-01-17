from http.client import HTTPException
import logging
from sqlalchemy.orm import Session, joinedload
from src.models.news_tag_model import NewsCharactersModel, NewsModel
from src.models.favorites_model import FavoritesModel
from src.utils.auth_utils import decode_and_sync_user
from src.utils.logger import setup_logger
from src.schema.responses.response_favorites_models import FavoritesResponseModel
from src.schema.responses.response_articles_models import ArticleResponseModel, SourceModel, TranslationModel, NewsCharacterModel, NewsCharacterTranslationModel

logger = setup_logger(__name__, level=logging.INFO)

class FavoritesService:
    async def add_favorite(self, token: str, news_id: int, db: Session):
        """
        Agrega una noticia a la lista de favoritos del usuario.
        """
        try:
            # Valida y sincroniza al usuario con la base de datos
            user = decode_and_sync_user(token, db)

            # Verifica si la noticia existe
            news = db.query(NewsModel).filter_by(id=news_id).first()
            if not news:
                raise HTTPException(status_code=404, detail="News not found")

            # Verifica si ya está en favoritos
            existing_favorite = db.query(FavoritesModel).filter_by(user_id=user.id, news_id=news_id).first()
            if existing_favorite:
                raise HTTPException(status_code=400, detail="News already in favorites")

            # Agrega el favorito
            favorite = FavoritesModel(user_id=user.id, news_id=news_id)
            db.add(favorite)

            # Commit de los cambios
            db.commit()

            logger.info(f"Favorite added successfully for user: {user.email}, news_id: {news_id}")
            return {"message": "Favorite added successfully"}

        except Exception as e:
            # Si ocurre un error, realiza un rollback
            logger.error(f"Error while adding favorite: {e}")
            db.rollback()
            raise e

    async def get_favorites(self, token: str, db: Session):
        try:
            logger.debug("Decoding user token and fetching user info.")
            user = decode_and_sync_user(token, db)

            logger.debug("Querying favorite articles for user.")
            favorites = db.query(FavoritesModel).filter_by(user_id=user.id).all()
            favorite_ids = [favorite.news_id for favorite in favorites]

            logger.debug("Fetching full articles for favorite IDs.")
            articles = (
                db.query(NewsModel)
                .options(
                    joinedload(NewsModel.translations),
                    joinedload(NewsModel.characters).joinedload(NewsCharactersModel.translations)
                )
                .filter(NewsModel.id.in_(favorite_ids))
                .all()
            )

            formatted_articles = [
                ArticleResponseModel(
                    id=article.id,
                    source=SourceModel(id=article.news_source, name=article.news_source),
                    author=article.author,
                    title=article.title,
                    description=article.detail,
                    url=article.source_link,
                    urlToImage=article.image_url,
                    publishedAt=article.publish_datetime.isoformat() if article.publish_datetime else None,
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
                    is_favorite=True,
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

            logger.info(f"Favorites retrieved successfully for user: {user.email}")
            return FavoritesResponseModel(user_id=user.id, articles=formatted_articles)

        except Exception as e:
            logger.error(f"Error while retrieving favorites: {e}")
            raise e
    
    async def delete_favorite(self, token: str, news_id: int, db: Session):
        """
        Elimina una noticia de la lista de favoritos del usuario.
        """
        try:
            # Valida y sincroniza al usuario con la base de datos
            user = decode_and_sync_user(token, db)

            # Verifica si el favorito existe
            favorite = db.query(FavoritesModel).filter_by(user_id=user.id, news_id=news_id).first()
            if not favorite:
                raise HTTPException(status_code=404, detail="Favorite not found")

            # Elimina el favorito
            db.delete(favorite)

            # Commit de los cambios
            db.commit()

            logger.info(f"Favorite deleted successfully for user: {user.email}, news_id: {news_id}")
            return {"message": "Favorite deleted successfully"}

        except Exception as e:
            # Si ocurre un error, realiza un rollback
            logger.error(f"Error while deleting favorite: {e}")
            db.rollback()
            raise e
