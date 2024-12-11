from pydantic import BaseModel
from typing import List
from src.schema.responses.response_articles_models import ArticleResponseModel


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
    articles: List[ArticleResponseModel]  # Cambiado de news_ids a una lista de artículos completos

    class Config:
        schema_extra = {
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
                        "distance": None
                    }
                ]
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
