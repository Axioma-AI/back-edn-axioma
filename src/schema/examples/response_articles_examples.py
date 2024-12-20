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
                    "distance": 0.5089,
                    "translations": [
                        {
                            "id": 1,
                            "title_tra": "Agreement between Banco Unión...",
                            "detail_tra": "In July of last year...",
                            "content_tra": "Negotiations are ongoing...",
                            "language": "en"
                        },
                        {
                            "id": 2,
                            "title_tra": "Convenio entre Banco Unión...",
                            "detail_tra": "En julio del año pasado...",
                            "content_tra": "Las negociaciones están en curso...",
                            "language": "es"
                        }
                    ]
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

# Ejemplo para respuesta 200 - Respuesta exitosa
# Ejemplo para respuesta 200 - Respuesta exitosa
successful_response_example_by_id = {
    "description": "Successful Response - Article found by ID",
    "content": {
        "application/json": {
            "example": {
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
                "is_favorite": True,  # Nuevo campo incluido
                "translations": [
                    {
                        "id": 1,
                        "title_tra": "Agreement between Banco Unión...",
                        "detail_tra": "In July of last year...",
                        "content_tra": "Negotiations are ongoing...",
                        "language": "en"
                    },
                    {
                        "id": 2,
                        "title_tra": "Convenio entre Banco Unión...",
                        "detail_tra": "En julio del año pasado...",
                        "content_tra": "Las negociaciones están en curso...",
                        "language": "es"
                    }
                ]
            }
        }
    },
}

# Ejemplo para respuesta 400 - Solicitud incorrecta
bad_request_example_by_id = {
    "model": ErrorResponseModel,
    "description": "Bad Request - Invalid Request",
    "content": {
        "application/json": {
            "example": {"detail": "Invalid request. The article ID must be a valid integer greater than 0."}
        }
    },
}

# Ejemplo para respuesta 404 - No encontrado
not_found_example_by_id = {
    "model": ErrorResponseModel,
    "description": "Not Found - The requested article does not exist",
    "content": {
        "application/json": {
            "example": {"detail": "The article with the specified ID was not found."}
        }
    },
}

# Ejemplo para respuesta 500 - Error interno del servidor
internal_server_error_example_by_id = {
    "model": ErrorResponseModel,
    "description": "Internal Server Error - Unexpected error",
    "content": {
        "application/json": {
            "example": {"detail": "An unexpected error occurred. Please try again later."}
        }
    },
}

# Ejemplo para respuesta 200 - Respuesta exitosa
news_sources_successful_response_example = {
    "description": "Successful Response - List of unique news sources",
    "content": {
        "application/json": {
            "example": {
                "sources": ["CNN", "BBC", "Reuters", "Al Jazeera"]
            }
        }
    },
}

# Ejemplo para respuesta 400 - Solicitud Incorrecta
news_sources_bad_request_example = {
    "model": ErrorResponseModel,
    "description": "Bad Request - Invalid Query Parameter",
    "content": {
        "application/json": {
            "example": {
                "detail": "Invalid request. Query parameter is invalid or missing."
            }
        }
    },
}

# Ejemplo para respuesta 404 - No Encontrado
news_sources_not_found_example = {
    "model": ErrorResponseModel,
    "description": "Not Found - The requested resource does not exist",
    "content": {
        "application/json": {
            "example": {
                "detail": "The requested resource does not exist."
            }
        }
    },
}

# Ejemplo para respuesta 500 - Error Interno del Servidor
news_sources_internal_server_error_example = {
    "model": ErrorResponseModel,
    "description": "Internal Server Error - Unexpected error",
    "content": {
        "application/json": {
            "example": {"detail": "An unexpected error occurred. Please try again later."}
        }
    },
}

# Configuración de respuestas para el endpoint /sources
news_sources_responses = {
    200: news_sources_successful_response_example,
    400: news_sources_bad_request_example,
    404: news_sources_not_found_example,
    500: news_sources_internal_server_error_example,
}

# Configuración de respuestas para el endpoint
article_by_id_responses = {
    200: successful_response_example_by_id,
    400: bad_request_example_by_id,
    404: not_found_example_by_id,
    500: internal_server_error_example_by_id,
}

# Configuración de respuestas para el endpoint
articles_responses = {
    200: successful_response_example,
    400: bad_request_example,
    404: not_found_example,
    500: internal_server_error_example,
}
