import logging
from firebase_admin import credentials, initialize_app, get_app
from src.config.config import get_settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__, level=logging.DEBUG)

# Cargar configuraciones desde el archivo de entorno
_SETTINGS = get_settings()

firebase_app = None

def initialize_firebase():
    global firebase_app
    if firebase_app:
        logger.info("Firebase ya está inicializado.")
        return firebase_app

    # Verificar las variables de entorno necesarias para Firebase
    if not all([
        _SETTINGS.firebase_project_id,
        _SETTINGS.firebase_private_key,
        _SETTINGS.firebase_client_email
    ]):
        logger.error('No se han definido las variables de entorno necesarias para Firebase')
        raise RuntimeError("Variables de entorno de Firebase faltantes.")

    logger.info('Variables de entorno de Firebase configuradas correctamente')

    try:
        firebase_credentials = {
            "type": _SETTINGS.firebase_type,
            "project_id": _SETTINGS.firebase_project_id,
            "private_key_id": _SETTINGS.firebase_private_key_id,
            "private_key": _SETTINGS.firebase_private_key.replace("||", "\n"),
            "client_email": _SETTINGS.firebase_client_email,
            "client_id": _SETTINGS.firebase_client_id,
            "auth_uri": _SETTINGS.firebase_auth_uri,
            "token_uri": _SETTINGS.firebase_token_uri,
            "auth_provider_x509_cert_url": _SETTINGS.firebase_auth_provider_x509_cert_url,
            "client_x509_cert_url": _SETTINGS.firebase_client_x509_cert_url,
        }

        cred = credentials.Certificate(firebase_credentials)
        firebase_app = initialize_app(cred, {"databaseURL": _SETTINGS.firebase_database_url})
        logger.info("Firebase inicializado correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar Firebase: {e}")
        raise RuntimeError("Error inicializando Firebase.")

    return firebase_app

if __name__ == "__main__":
    try:
        if firebase_app:
            logger.info("Firebase configurado y listo para usarse")
        else:
            logger.error("Firebase no se pudo inicializar")
    except Exception as e:
        logger.error(f"Error al probar la configuración de Firebase: {e}")
