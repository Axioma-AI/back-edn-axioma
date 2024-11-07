from fastapi.middleware.cors import CORSMiddleware

allowed_origins = [
    'http://localhost:8000',
    'http://192.168.232.220:8000',
    'http://localhost:80',
    'http://192.168.232.230:80',
    'http://localhost',
    'http://192.168.232.230',
    'http://localhost/',
    'http://192.168.232.230/',
    'http://localhost:5173',
    '*'
]

def add_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,  # Permitir estos orígenes
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Métodos permitidos
        allow_headers=["Authorization", "Content-Type"],  # Headers permitidos
    )
