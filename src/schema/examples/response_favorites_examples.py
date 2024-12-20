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
                        "distance": None,
                        "is_favorite": True,
                        "translations": [
                            {
                                "id": 1,
                                "title_tra": "Agreement between Banco Unión and ICBC of China...",
                                "detail_tra": "In July of last year...",
                                "content_tra": "Negotiations to finalize the agreement...",
                                "language": "en"
                            },
                            {
                                "id": 2,
                                "title_tra": "Convenio entre Banco Unión e ICBC de China...",
                                "detail_tra": "En julio del año pasado...",
                                "content_tra": "Las negociaciones para establecer un acuerdo...",
                                "language": "es"
                            }
                        ]
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
                        "distance": None,
                        "is_favorite": True,
                        "translations": [
                            {
                                "id": 3,
                                "title_tra": "Government announces BCB to issue sovereign bonds in yuan",
                                "detail_tra": "The Minister of Economy, Marcelo Montenegro...",
                                "content_tra": "The Central Bank of Bolivia plans to issue yuan bonds...",
                                "language": "en"
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
