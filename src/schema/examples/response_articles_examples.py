from src.schema.responses.response_articles_models import ArticleResponseModel, ErrorResponseModel

# Ejemplo para respuesta 200 - Respuesta exitosa
successful_response_example = {
    "description": "Successful Response",
    "content": {
        "application/json": {
            "example": [
                {
                    "id": 6845,
                    "source": {"id": "La Razon", "name": "La Razon"},
                    "author": "Yuri Flores",
                    "title": "Convenio entre Banco Unión e ICBC de China está en fase final para operaciones en yuanes",
                    "description": "En julio del año pasado...",
                    "url": "https://www.la-razon.com/economia/2024/01/02/convenio-entre-banco-union-e-icbc-de-china-esta-en-fase-final-para-operaciones-en-yuanes/",
                    "urlToImage": "https://www.la-razon.com/wp-content/uploads/2024/01/02/19/WhatsApp-Image-2024-01-02-at-14.06.44.jpeg",
                    "publishedAt": "2024-01-02T15:21:00",
                    "content": "Las negociaciones...",
                    "sentiment_category": "POSITIVO",
                    "sentiment_score": 0.35917,
                    "distance": 0.5089
                },
                {
                    "id": 6846,
                    "source": {"id": "El Deber", "name": "El Deber"},
                    "author": "Carlos Gustavo",
                    "title": "El Gobierno anuncia que el BCB emitirá bonos soberanos en yuanes",
                    "description": "El ministro de Economía, Marcelo Montenegro, informó que el Banco Central de Bolivia emitirá bonos soberanos en yuanes...",
                    "url": "https://eldeber.com.bo/economia/El-Gobierno-anuncia-que-el-BCB-emitira-bonos-soberanos-en-yuanes-20240102-0063.html",
                    "urlToImage": "https://eldeber.com.bo/export/sites/eldeber/img/2024/01/02/20240102-0063.jpg_1359985865.jpg",
                    "publishedAt": "2024-01-02T15:21:00",
                    "content": "El ministro de Economía, Marcelo Montenegro, informó...",
                    "sentiment_category": "NEUTRAL",
                    "sentiment_score": 0.0,
                    "distance": 0.0
                }
            ]
        }
    },
}

# Ejemplo para respuesta 400 - Solicitud incorrecta
bad_request_example = {
    "model": ErrorResponseModel,
    "description": "Bad Request - Invalid Query Parameter",
    "content": {
        "application/json": {
            "example": {"detail": "Invalid request. Query parameter is missing."}
        }
    },
}

# Ejemplo para respuesta 404 - No encontrado
not_found_example = {
    "model": ErrorResponseModel,
    "description": "Not Found - The requested item does not exist",
    "content": {
        "application/json": {
            "example": {"detail": "The article with the specified ID was not found."}
        }
    },
}

# Ejemplo para respuesta 500 - Error interno del servidor
internal_server_error_example = {
    "model": ErrorResponseModel,
    "description": "Internal Server Error - Unexpected error",
    "content": {
        "application/json": {
            "example": {"detail": "An unexpected error occurred. Please try again later."}
        }
    },
}

# Configuración de respuestas para el endpoint
articles_responses = {
    200: successful_response_example,
    400: bad_request_example,
    404: not_found_example,
    500: internal_server_error_example,
}
