from src.schema.responses.response_analysis_models import AnalysisResponseModel, ErrorResponseModel

# Ejemplo de respuesta 200 - Respuesta Exitosa
successful_analysis_response_example = {
    "description": "Successful Response",
    "content": {
        "application/json": {
            "example": {
                "source_query": "ganaderia",
                "news_history": [
                    {"date": "2024-02-15", "news_count": 15},
                    {"date": "2024-04-02", "news_count": 20}
                ],
                "news_perception": [
                    {
                        "date": "2024-02-15",
                        "positive_sentiment_score": 0.5,
                        "negative_sentiment_score": 0.3
                    },
                    {
                        "date": "2024-04-02",
                        "positive_sentiment_score": 0.7,
                        "negative_sentiment_score": 0.2
                    },
                    {
                        "date": "2024-05-20",
                        "positive_sentiment_score": 0.4,
                        "negative_sentiment_score": 0.6
                    },
                    {
                        "date": "2024-06-15",
                        "positive_sentiment_score": 0.3,
                        "negative_sentiment_score": 0.7
                    }
                ],
                "news_count": 35,
                "sources_count": 3,
                "historic_interval": 9,
                "historic_interval_unit": "months",
                "general_perception": {
                    "positive_sentiment_score": 0.5,
                    "negative_sentiment_score": 0.45
                }
            }
        }
    }
}

# Ejemplo de respuesta 400 - Solicitud Incorrecta
bad_request_example = {
    "description": "Bad Request - Parámetros de solicitud no válidos",
    "content": {
        "application/json": {
            "example": {
                "detail": "Parámetros no válidos proporcionados. Por favor, verifica la solicitud."
            }
        }
    }
}

# Ejemplo de respuesta 404 - No Encontrado
not_found_example = {
    "description": "Not Found - Fuente de noticias no encontrada",
    "content": {
        "application/json": {
            "example": {
                "detail": "No se encontró ninguna noticia para la fuente especificada."
            }
        }
    }
}

# Ejemplo de respuesta 500 - Error Interno del Servidor
internal_server_error_example = {
    "description": "Internal Server Error - Error en el servidor",
    "content": {
        "application/json": {
            "example": {
                "detail": "Ocurrió un error inesperado en el servidor. Intenta nuevamente más tarde."
            }
        }
    }
}

# Diccionario de ejemplos de respuestas para el endpoint de análisis
analysis_responses = {
    200: successful_analysis_response_example,
    400: bad_request_example,
    404: not_found_example,
    500: internal_server_error_example,
}
