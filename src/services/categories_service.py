import logging
from sqlalchemy import select, delete
from src.config.db_config import get_db
from src.models.categories_model import InterestsModel
from src.schema.responses.response_categories_models import CategoriesResponseModel
from src.utils.auth_utils import decode_and_sync_user
from src.utils.logger import setup_logger

logger = setup_logger(__name__, level=logging.INFO)

class CategoriesService:
    async def process_categories(self, token: str, keywords: list):
        async for db in get_db():
            try:
                # Validar y sincronizar usuario
                user = decode_and_sync_user(token, db)

                # Eliminar intereses existentes
                delete_stmt = delete(InterestsModel).where(InterestsModel.user_id == user.id)
                await db.execute(delete_stmt)
                await db.commit()

                keywords = [keyword.lower() for keyword in keywords]
                unique_keywords = list(set(keywords))

                # Obtener intereses restantes (aunque se borraron, por seguridad)
                stmt = select(InterestsModel.keyword).where(InterestsModel.user_id == user.id)
                result = await db.execute(stmt)
                existing_keywords = {row[0] for row in result.fetchall()}

                new_keywords = [k for k in unique_keywords if k not in existing_keywords]
                skipped_keywords = [k for k in unique_keywords if k in existing_keywords]

                # Agregar nuevos intereses
                interests = []
                for keyword in new_keywords:
                    interest = InterestsModel(user_id=user.id, keyword=keyword)
                    db.add(interest)
                    interests.append(interest)

                await db.commit()

                added_categories = [{"id": interest.id, "keyword": interest.keyword} for interest in interests]

                logger.info(f"Processed interests for user: {user.email}")
                return {
                    "message": "Categories added successfully",
                    "categories": added_categories,
                    "skipped_categories": skipped_keywords
                }

            except Exception as e:
                await db.rollback()
                logger.error(f"Error processing categories: {e}")
                raise

    async def get_user_interests(self, token: str) -> CategoriesResponseModel:
        async for db in get_db():
            try:
                user = decode_and_sync_user(token, db)

                stmt = select(InterestsModel).where(InterestsModel.user_id == user.id)
                result = await db.execute(stmt)
                interests = result.scalars().all()

                categories = [{"id": interest.id, "keyword": interest.keyword} for interest in interests]

                return CategoriesResponseModel(
                    user_id=user.id,
                    email=user.email,
                    categories=categories
                )

            except Exception as e:
                logger.error(f"Error al obtener intereses: {e}")
                raise

    async def delete_categories(self, token: str, category_ids: list):
        async for db in get_db():
            try:
                user = decode_and_sync_user(token, db)
                deleted_categories = []

                for category_id in category_ids:
                    stmt = select(InterestsModel).where(
                        InterestsModel.id == category_id,
                        InterestsModel.user_id == user.id
                    )
                    result = await db.execute(stmt)
                    category = result.scalars().first()

                    if category:
                        deleted_categories.append({"id": category.id, "keyword": category.keyword})
                        await db.delete(category)
                    else:
                        logger.warning(f"Categoría con ID {category_id} no encontrada para {user.email}")

                await db.commit()

                return deleted_categories

            except Exception as e:
                await db.rollback()
                logger.error(f"Error al eliminar categorías: {e}")
                raise