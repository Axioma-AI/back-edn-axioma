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
        Procesa las categorías: elimina las existentes, maneja duplicados dentro de la solicitud y agrega las nuevas.
        """
        try:
            # Valida y sincroniza al usuario con la base de datos
            user = decode_and_sync_user(token, db)

            # Eliminar todas las categorías existentes del usuario
            db.query(InterestsModel).filter_by(user_id=user.id).delete()
            db.commit()  # Confirma la eliminación

            # Convertir todas las palabras clave a minúsculas
            keywords = [keyword.lower() for keyword in keywords]

            # Filtrar duplicados en las palabras clave enviadas
            unique_keywords = list(set(keywords))  # Usar set para eliminar duplicados en el mismo request

            # Obtener palabras clave existentes (después de eliminar las categorías previas)
            existing_keywords = {interest.keyword for interest in db.query(InterestsModel).filter_by(user_id=user.id).all()}

            # Filtrar palabras clave ya existentes
            new_keywords = [keyword for keyword in unique_keywords if keyword not in existing_keywords]
            skipped_keywords = [keyword for keyword in unique_keywords if keyword in existing_keywords]

            # Agregar las nuevas categorías
            interests = []
            for keyword in new_keywords:
                interest = InterestsModel(user_id=user.id, keyword=keyword)
                db.add(interest)
                interests.append(interest)

            # Commit de los intereses
            db.commit()

            # Construir la lista de categorías agregadas
            added_categories = [{"id": interest.id, "keyword": interest.keyword} for interest in interests]

            logger.info(f"Intereses procesados para el usuario: {user.email}")
            return {
                "message": "Categories added successfully",
                "categories": added_categories,
                "skipped_categories": skipped_keywords  # Duplicados ignorados
            }

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
