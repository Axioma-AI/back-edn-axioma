from pydantic import BaseModel
from typing import List


class AddFavoriteResponseModel(BaseModel):
    message: str
    news_id: int

    class Config:
        schema_extra = {
            "example": {
                "message": "Favorite added successfully",
                "news_id": 123,
            }
        }


class FavoritesResponseModel(BaseModel):
    user_id: int
    news_ids: List[int]

    class Config:
        schema_extra = {
            "example": {
                "user_id": 42,
                "news_ids": [101, 202, 303],
            }
        }


class DeleteFavoriteResponseModel(BaseModel):
    message: str
    news_id: int

    class Config:
        schema_extra = {
            "example": {
                "message": "Favorite deleted successfully",
                "news_id": 123,
            }
        }
