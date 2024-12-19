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
    articles: List[ArticleResponseModel]

    class Config:
        schema_extra = {
            "example": {
                "user_id": 42,
                "articles": [
                    {
                        "id": 6845,
                        "source": {"id": "La Razon", "name": "La Razon"},
                        "author": "Yuri Flores",
                        "title": "Convenio entre Banco Unión...",
                        "description": "En julio del año pasado...",
                        "url": "https://www.la-razon.com/economia/2024/01/02/convenio...",
                        "urlToImage": "https://example.com/image.jpg",
                        "publishedAt": "2024-01-02T15:21:00",
                        "content": "Las negociaciones...",
                        "sentiment_category": "POSITIVO",
                        "sentiment_score": 0.35917,
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
