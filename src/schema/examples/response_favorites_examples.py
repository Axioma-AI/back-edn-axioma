# Example for a successful POST response
successful_post_favorite_response_example = {
    "description": "Successfully added a news article to the user's favorites.",
    "content": {
        "application/json": {
            "example": {
                "message": "Favorite added successfully",
                "news_id": 123,
            }
        }
    },
}

# Example for a successful GET response
successful_get_favorites_response_example = {
    "description": "Successfully retrieved the user's favorite news articles.",
    "content": {
        "application/json": {
            "example": {
                "user_id": 42,
                "articles": [
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
                        "summary": "Resumen del artículo...",
                        "justification": "Justificación del contenido...",
                        "news_type_category": "Económico",
                        "news_type_justification": "Justificación económica...",
                        "purpose_objective": "Informar al público...",
                        "purpose_audience": "Empresas y público general",
                        "context_temporality": "Actualidad",
                        "context_location": "Bolivia",
                        "content_facts_vs_opinions": "Hechos",
                        "content_precision": "Alta",
                        "content_impartiality": "Neutral",
                        "structure_clarity": "Clara",
                        "structure_key_data": "Completa",
                        "tone_neutrality": "Neutral",
                        "tone_ethics": "Ético",
                        "is_favorite": True,
                        "translations": [
                            {
                                "id": 1,
                                "title_tra": "Agreement between Banco Unión and ICBC of China...",
                                "detail_tra": "In July of last year...",
                                "content_tra": "Negotiations to finalize the agreement...",
                                "summary_tra": "Summary in English...",
                                "justification_tra": "Justification in English...",
                                "news_type_category_tra": "Economic",
                                "news_type_justification_tra": "Economic justification...",
                                "purpose_objective_tra": "Inform the public...",
                                "purpose_audience_tra": "Companies and general public",
                                "context_temporality_tra": "Current",
                                "context_location_tra": "Bolivia",
                                "content_facts_vs_opinions_tra": "Facts",
                                "content_precision_tra": "High",
                                "content_impartiality_tra": "Neutral",
                                "structure_clarity_tra": "Clear",
                                "structure_key_data_tra": "Complete",
                                "tone_neutrality_tra": "Neutral",
                                "tone_ethics_tra": "Ethical",
                                "language": "en"
                            }
                        ],
                        "characters": [
                            {
                                "id": 1,
                                "character_name": "Carlos Mesa",
                                "character_description": "Former president of Bolivia...",
                                "translations": [
                                    {
                                        "id": 1,
                                        "character_description_tra": "Ex-presidente de Bolivia...",
                                        "language": "es"
                                    },
                                    {
                                        "id": 2,
                                        "character_description_tra": "Former president of Bolivia...",
                                        "language": "en"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    },
}

# Example for a successful DELETE response
successful_delete_favorite_response_example = {
    "description": "Successfully removed a news article from the user's favorites.",
    "content": {
        "application/json": {
            "example": {
                "message": "Favorite deleted successfully",
                "news_id": 123,
            }
        }
    },
}

# Example for a 404 Not Found response
not_found_favorite_response_example = {
    "description": "The specified resource was not found.",
    "content": {
        "application/json": {
            "example": {"detail": "User or news not found."},
        }
    },
}

# Example for a 400 Bad Request response
bad_request_favorite_response_example = {
    "description": "Bad request due to invalid parameters.",
    "content": {
        "application/json": {
            "example": {"detail": "Invalid request parameters."},
        }
    },
}

# Example for a 500 Internal Server Error response
internal_server_error_favorite_response_example = {
    "description": "An unexpected server error occurred.",
    "content": {
        "application/json": {
            "example": {"detail": "An unexpected error occurred. Please try again later."},
        }
    },
}

# Response configurations
favorites_responses_post = {
    200: successful_post_favorite_response_example,
    400: bad_request_favorite_response_example,
    404: not_found_favorite_response_example,
    500: internal_server_error_favorite_response_example,
}

favorites_responses_get = {
    200: successful_get_favorites_response_example,
    400: bad_request_favorite_response_example,
    404: not_found_favorite_response_example,
    500: internal_server_error_favorite_response_example,
}

favorites_responses_delete = {
    200: successful_delete_favorite_response_example,
    400: bad_request_favorite_response_example,
    404: not_found_favorite_response_example,
    500: internal_server_error_favorite_response_example,
}
