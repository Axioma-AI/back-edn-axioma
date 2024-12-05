from http.client import HTTPException
import logging
from sqlalchemy.orm import Session
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
        """
        Obtiene las noticias favoritas del usuario.
        """
        try:
            # Valida y sincroniza al usuario con la base de datos
            user = decode_and_sync_user(token, db)

            # Obtiene las noticias favoritas del usuario
            favorites = db.query(FavoritesModel).filter_by(user_id=user.id).all()

            logger.info(f"Favorites retrieved successfully for user: {user.email}")
            return {
                "user_id": user.id,
                "news_ids": [favorite.news_id for favorite in favorites],
            }

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