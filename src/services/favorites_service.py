from http.client import HTTPException
import logging
from sqlalchemy.orm import Session, joinedload
from src.models.news_tag_model import NewsModel
from src.models.favorites_model import FavoritesModel
from src.utils.auth_utils import decode_and_sync_user
from src.utils.logger import setup_logger

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
            # Valida y sincroniza al usuario con la base de datos
            user = decode_and_sync_user(token, db)

            # Obtiene los IDs de las noticias favoritas
            favorites = db.query(FavoritesModel).filter_by(user_id=user.id).all()
            favorite_ids = [favorite.news_id for favorite in favorites]

            # Recupera las noticias completas asociadas a los IDs
            articles = (
                db.query(NewsModel)
                .options(joinedload(NewsModel.translations))  # Cargar traducciones
                .filter(NewsModel.id.in_(favorite_ids))
                .all()
            )

            # Formatea las noticias y añade el campo `is_favorite: True`
            formatted_articles = [
                {
                    "id": article.id,
                    "source": {"id": article.news_source, "name": article.news_source},
                    "author": article.author,
                    "title": article.title,
                    "description": article.detail,
                    "url": article.source_link,
                    "urlToImage": article.image_url,
                    "publishedAt": article.publish_datetime.isoformat() if article.publish_datetime else None,
                    "content": article.content,
                    "sentiment_category": article.sentiment_category.name,
                    "sentiment_score": float(article.sentiment_score),
                    "is_favorite": True,  # Campo fijo porque están en favoritos
                    "translations": [
                        {
                            "id": translation.id,
                            "title_tra": translation.title_tra,
                            "detail_tra": translation.detail_tra,
                            "content_tra": translation.content_tra,
                            "language": translation.language,
                        }
                        for translation in article.translations
                    ],
                }
                for article in articles
            ]

            logger.info(f"Favorites retrieved successfully for user: {user.email}")
            return {"user_id": user.id, "articles": formatted_articles}

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
