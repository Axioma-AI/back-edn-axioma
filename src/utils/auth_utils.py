from fastapi import HTTPException
from sqlalchemy.orm import Session
from firebase_admin import auth
from src.config.firebase_config import initialize_firebase
from src.models.user_model import UserModel, FirebaseTokenModel
import logging

logger = logging.getLogger(__name__)

# Inicializar Firebase una sola vez
firebase_app = initialize_firebase()

def decode_and_sync_user(token: str, db: Session):
    """
    Decodifica el token de Firebase, sincroniza el usuario con la base de datos y registra el token.
    Retorna el usuario sincronizado.
    """
    try:
        # Decodifica el token de Firebase
        decoded_token = auth.verify_id_token(token)
        logger.debug(f"Token decodificado correctamente: {decoded_token}")
    except Exception as e:
        logger.error(f"Error al decodificar el token: {e}")
        raise HTTPException(status_code=401, detail="Token inválido")

    # Verifica si el usuario está en Firebase
    try:
        firebase_user = auth.get_user(decoded_token["uid"])
        logger.info(f"Usuario encontrado en Firebase: {firebase_user.email}")
    except Exception as e:
        logger.error(f"El usuario no existe en Firebase: {e}")
        raise HTTPException(status_code=404, detail="Usuario no registrado en Firebase")

    # Verifica si el usuario ya está en la base de datos
    user = db.query(UserModel).filter_by(email=decoded_token["email"]).first()
    if not user:
        logger.info(f"Usuario no encontrado en la base de datos, registrando: {decoded_token['email']}")
        user = UserModel(
            email=decoded_token["email"],
            name=decoded_token.get("name"),
            phone=decoded_token.get("phone_number"),
            email_verified=decoded_token.get("email_verified"),
            country_code=decoded_token.get("country"),
        )
        db.add(user)
        db.commit()

    # Registra el token de Firebase en la base de datos
    firebase_token = FirebaseTokenModel(
        user_id=user.id,
        iss=decoded_token["iss"],
        aud=decoded_token["aud"],
        auth_time=decoded_token["auth_time"],
        iat=decoded_token["iat"],
        exp=decoded_token["exp"],
    )
    db.add(firebase_token)
    db.commit()

    return user
