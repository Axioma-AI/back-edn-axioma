from src.schema.responses.response_categories_models import CategoriesResponseModel, ErrorResponseModel

# Ejemplo para respuesta 200 - Respuesta exitosa al obtener categorías (GET /categories)
successful_get_response_example = {
    "description": "Successful Response - Categories retrieved successfully",
    "content": {
        "application/json": {
            "example": {
                "user_id": 42,
                "email": "example@example.com",
                "categories": [
                    {"id": 1, "keyword": "tecnología"},
                    {"id": 2, "keyword": "innovación"},
                    {"id": 3, "keyword": "blockchain"}
                ]
            }
        }
    },
}

# Ejemplo para respuesta 200 - Respuesta exitosa al agregar categorías (POST /categories)
successful_post_response_example = {
    "description": "Successful Response - Categories added successfully",
    "content": {
        "application/json": {
            "example": {
                "message": "Categories added successfully",
                "categories": [
                    {"id": 4, "keyword": "data science"},
                    {"id": 5, "keyword": "machine learning"}
                ]
            }
        }
    },
}

# Ejemplo para respuesta 400 - Solicitud incorrecta (común para GET y POST)
bad_request_example = {
    "model": ErrorResponseModel,
    "description": "Bad Request - Invalid Parameters",
    "content": {
        "application/json": {
            "example": {"detail": "Invalid request. Required parameters are missing or incorrect."}
        }
    },
}

# Ejemplo para respuesta 404 - Usuario no encontrado (GET /categories)
not_found_get_example = {
    "model": ErrorResponseModel,
    "description": "Not Found - User not found",
    "content": {
        "application/json": {
            "example": {"detail": "No user found with the provided token."}
        }
    },
}

# Ejemplo para respuesta 404 - Categorías no encontradas (GET /categories)
not_found_categories_example = {
    "model": ErrorResponseModel,
    "description": "Not Found - Categories not found",
    "content": {
        "application/json": {
            "example": {"detail": "No categories found for the user."}
        }
    },
}

# Ejemplo para respuesta 500 - Error interno del servidor (común para GET y POST)
internal_server_error_example = {
    "model": ErrorResponseModel,
    "description": "Internal Server Error - Unexpected error",
    "content": {
        "application/json": {
            "example": {"detail": "An unexpected error occurred. Please try again later."}
        }
    },
}

# Ejemplo para respuesta 200 - Respuesta exitosa al eliminar categorías (DELETE /categories)
successful_delete_response_example = {
    "description": "Successful Response - Categories deleted successfully",
    "content": {
        "application/json": {
            "example": {
                "message": "Categories deleted successfully",
                "deleted_categories": [
                    {"id": 1, "keyword": "tecnología"},
                    {"id": 3, "keyword": "blockchain"}
                ]
            }
        }
    },
}

# Ejemplo para respuesta 404 - Categorías no encontradas (DELETE /categories)
not_found_delete_categories_example = {
    "model": ErrorResponseModel,
    "description": "Not Found - Some or all categories not found",
    "content": {
        "application/json": {
            "example": {"detail": "Some categories were not found for the user."}
        }
    },
}

# Configuración de respuestas para el endpoint de eliminación de categorías
categories_responses_delete = {
    200: successful_delete_response_example,
    404: not_found_delete_categories_example,
    400: bad_request_example,
    500: internal_server_error_example,
}

# Configuración de respuestas para el endpoint de categorías
categories_responses_get = {
    200: successful_get_response_example,
    400: bad_request_example,
    404: not_found_get_example,
    500: internal_server_error_example,
}

categories_responses_post = {
    200: successful_post_response_example,
    400: bad_request_example,
    500: internal_server_error_example,
}
