import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config.config import get_settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__, level=logging.DEBUG)

_SETTINGS = get_settings()

DATABASE_URL = f"mysql+mysqlconnector://{_SETTINGS.db_user}:{_SETTINGS.db_password}@{_SETTINGS.db_host}:{_SETTINGS.db_port}/{_SETTINGS.db_name}"

# Obteniendo el motor de la base de datos
if not _SETTINGS.db_user or not _SETTINGS.db_password or not _SETTINGS.db_host or not _SETTINGS.db_port or not _SETTINGS.db_name:
    logger.error('No se han definido las variables de entorno de la base de datos')
else:
    logger.info('Variables de entorno de la base de datos configuradas')

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    try:
        logger.info("Iniciando conexión a la base de datos")
        with engine.connect() as connection:
            logger.info("Conexión a la base de datos establecida correctamente.")
    except Exception as e:
        logger.error(f"Error al conectar con la base de datos: {e}")