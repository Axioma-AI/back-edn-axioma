import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from src.config.config import get_settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__, level=logging.DEBUG)

_SETTINGS = get_settings()

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{_SETTINGS.db_user}:{_SETTINGS.db_password}@{_SETTINGS.db_host}:{_SETTINGS.db_port}/{_SETTINGS.db_name}"

# Obteniendo el motor de la base de datos
if not _SETTINGS.db_user or not _SETTINGS.db_password or not _SETTINGS.db_host or not _SETTINGS.db_port or not _SETTINGS.db_name:
    logger.error('No se han definido las variables de entorno de la base de datos')
else:
    logger.info('Variables de entorno de la base de datos configuradas')

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    try:
        logger.info("Iniciando conexión a la base de datos")
        with engine.connect() as connection:
            logger.info("Conexión a la base de datos establecida correctamente.")
    except Exception as e:
        logger.error(f"Error al conectar con la base de datos: {e}")