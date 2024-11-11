# src/routes/api/v1/auth.py
import uuid
from fastapi import APIRouter, Request, Response
from src.services.auth_service import authenticate_user, handle_auth_callback

router = APIRouter()

@router.get("/login")
async def login(request: Request, response: Response):
    # Verificar si la cookie 'session_id' existe
    session_id = request.cookies.get("session_id")
    if not session_id:
        # Generar un nuevo 'session_id' y establecerlo en la cookie
        session_id = str(uuid.uuid4())
        response.set_cookie(key="session_id", value=session_id)
    
    # Llamar a la función de autenticación
    return await authenticate_user(request)

@router.get("/auth/callback")
async def auth_callback(request: Request):
    user_data = await handle_auth_callback(request)
    return {"message": "Autenticación exitosa", "user": user_data}
