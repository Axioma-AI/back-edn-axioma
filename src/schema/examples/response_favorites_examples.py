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
                "news_ids": [101, 202, 303],
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
