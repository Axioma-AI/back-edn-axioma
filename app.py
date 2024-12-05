import logging
from fastapi import FastAPI
from src.config.config import get_settings
from src.config.cors_config import add_cors
from src.routes.api.v1 import router as v1_router
from src.utils.logger import setup_logger

logger = setup_logger(__name__, level=logging.INFO)

_SETTINGS = get_settings()

app = FastAPI(
    title=_SETTINGS.service_name,
    version=_SETTINGS.k_revision,
    level=_SETTINGS.log_level,
)

add_cors(app)

# Incluir las rutas
# app.include_router(v1_router, prefix="/api/v1", tags=["API v1"])

app.include_router(v1_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    logger.info("Iniciando la aplicación...")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)