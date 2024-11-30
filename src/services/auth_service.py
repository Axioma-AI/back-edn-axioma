# src/services/auth_service.py
import datetime
import logging
import uuid
from authlib.integrations.starlette_client import OAuth
from fastapi import Request, HTTPException, Response
from jwt import PyJWKClient
import jwt
from src.config.config import get_settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__, level=logging.INFO)

settings = get_settings()

# OAuth setup (including OpenID configuration and JWKs URI)
oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',  # URL de descubrimiento de OpenID
    client_kwargs={'scope': 'openid email profile'},
)

# Almacenamiento temporal de sesiones (usar Redis o base de datos en producción)
auth_sessions = {}

async def authenticate_user(request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    if not session_id:
        # Generate a new 'session_id' if not present
        session_id = str(uuid.uuid4())
        # Set cookie without expiration time (session-based cookie)
        response.set_cookie(key="session_id", value=session_id)

    # Redirect the user to Google for authentication
    redirect_uri = settings.redirect_uri
    auth_url = await oauth.google.authorize_redirect(request, redirect_uri)

    # Initialize an empty dictionary for this session
    auth_sessions[session_id] = {}
    return auth_url

async def handle_auth_callback(request: Request):
    # Obtener el session_id desde la cookie
    session_id = request.cookies.get("session_id")
    if not session_id:
        logger.error("No se ha encontrado el ID de sesión en la cookie.")
        raise HTTPException(status_code=403, detail="No se ha encontrado el ID de sesión.")
    
    # Completar el flujo OAuth y obtener los datos del usuario
    logger.info("Intentando completar el flujo OAuth para session_id: %s", session_id)
    token = await oauth.google.authorize_access_token(request)
    id_token = token.get("id_token")
    
    if not id_token:
        logger.error("El token de ID no fue recibido.")
        raise HTTPException(status_code=500, detail="El token de ID no fue recibido.")
    
    # Decodificar manualmente el id_token
    try:
        GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
        jwks_client = PyJWKClient(GOOGLE_CERTS_URL)
        signing_key = jwks_client.get_signing_key_from_jwt(id_token)
        user_data = jwt.decode(id_token, signing_key.key, algorithms=["RS256"], audience=settings.google_client_id)
    except jwt.PyJWTError as e:
        logger.error("Error al verificar el token de ID: %s", e)
        raise HTTPException(status_code=403, detail="Error al verificar el token de ID") from e

    # Guardar los datos del usuario en el almacenamiento temporal
    auth_sessions[session_id] = {
        "email": user_data.get("email"),
        "name": user_data.get("name"),
    }
    logger.info("Usuario autenticado correctamente: %s", auth_sessions[session_id])
    return auth_sessions[session_id]
