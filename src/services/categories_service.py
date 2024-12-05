import logging
from sqlalchemy.orm import Session
from src.models.categories_model import InterestsModel
from src.schema.responses.response_categories_models import CategoriesResponseModel
from src.utils.auth_utils import decode_and_sync_user
from src.utils.logger import setup_logger

logger = setup_logger(__name__, level=logging.INFO)

class CategoriesService:
    async def process_categories(self, token: str, keywords: list, db: Session):
        """
        Procesa las categorías: valida el token, sincroniza el usuario con la base de datos,
        y almacena los intereses del usuario. Retorna las categorías agregadas.
        """
        try:
            # Valida y sincroniza al usuario con la base de datos
            user = decode_and_sync_user(token, db)

            # Agrega los intereses del usuario
            interests = []
            for keyword in keywords:
                lower_keyword = keyword.lower()
                interest = InterestsModel(user_id=user.id, keyword=lower_keyword)
                db.add(interest)
                interests.append(interest)

            # Commit de los intereses
            db.commit()

            # Construye la lista de categorías agregadas después del commit
            added_categories = [{"id": interest.id, "keyword": interest.keyword} for interest in interests]

            logger.info(f"Intereses agregados exitosamente para el usuario: {user.email}")
            return added_categories

        except Exception as e:
            # Si ocurre un error, realiza un rollback
            logger.error(f"Error al procesar categorías: {e}")
            db.rollback()
            raise e

    async def get_user_interests(self, token: str, db: Session) -> CategoriesResponseModel:
        """
        Recupera los intereses del usuario autenticado basado en el token proporcionado.
        """
        try:
            # Valida y sincroniza al usuario con la base de datos
            user = decode_and_sync_user(token, db)

            # Recupera las categorías del usuario
            interests = db.query(InterestsModel).filter_by(user_id=user.id).all()

            # Construye la respuesta usando el modelo Pydantic
            categories = [{"id": interest.id, "keyword": interest.keyword} for interest in interests]
            response = CategoriesResponseModel(
                user_id=user.id,
                email=user.email,
                categories=categories
            )

            return response

        except Exception as e:
            logger.error(f"Error al obtener intereses: {e}")
            raise e

    async def delete_categories(self, token: str, category_ids: list, db: Session):
        """
        Elimina una o varias categorías asociadas a un usuario autenticado.
        """
        try:
            # Valida y sincroniza al usuario con la base de datos
            user = decode_and_sync_user(token, db)

            # Verifica y elimina las categorías especificadas
            deleted_categories = []
            for category_id in category_ids:
                category = db.query(InterestsModel).filter_by(id=category_id, user_id=user.id).first()
                if category:
                    deleted_categories.append({"id": category.id, "keyword": category.keyword})
                    db.delete(category)
                else:
                    logger.warning(f"Categoría con ID {category_id} no encontrada para el usuario {user.email}")

            # Commit de los cambios
            db.commit()

            # Retorna las categorías eliminadas
            return deleted_categories

        except Exception as e:
            # Si ocurre un error, realiza un rollback
            logger.error(f"Error al eliminar categorías: {e}")
            db.rollback()
            raise e
