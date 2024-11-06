from src.schema.responses.response_analysis_models import AnalysisResponseModel, ErrorResponseModel

successful_analysis_response_example = {
    "description": "Successful Response",
    "content": {
        "application/json": {
            "example": {
                "source_id": 1,
                "source_name": "CNN",
                "news_history": [
                    {"date": "2021-01-01", "news_count": 10},
                    {"date": "2021-01-02", "news_count": 10}
                ],
                "news_perception": [
                    {
                        "date": "2021-01-01",
                        "positive_sentiment_score": 0.5,
                        "negative_sentiment_score": 0.5
                    },
                    {
                        "date": "2021-01-02",
                        "positive_sentiment_score": 0.2,
                        "negative_sentiment_score": 0.8
                    }
                ],
                "news_count": 20,
                "sources_count": 5,
                "historic_interval": 3,
                "historic_interval_unit": "months",
                "general_perception": {
                    "positive_sentiment_score": 0.4,
                    "negative_sentiment_score": 0.6
                }
            }
        }
    }
}

# Ejemplo de respuesta 400 - Bad Request
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

# Ejemplo de respuesta 404 - Not Found
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

# Ejemplo de respuesta 500 - Internal Server Error
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

# Diccionario de respuestas de análisis
analysis_responses = {
    200: successful_analysis_response_example,
    400: bad_request_example,
    404: not_found_example,
    500: internal_server_error_example,
}
