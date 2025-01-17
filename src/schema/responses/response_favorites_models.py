from pydantic import BaseModel, ConfigDict
from typing import List
from src.schema.responses.response_articles_models import ArticleResponseModel

class FavoriteCharacterTranslationModel(BaseModel):
    id: int
    character_description_tra: str
    language: str

class FavoriteCharacterModel(BaseModel):
    id: int
    character_name: str
    character_description: str
    translations: List[FavoriteCharacterTranslationModel]

class AddFavoriteResponseModel(BaseModel):
    message: str
    news_id: int

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "message": "Favorite added successfully",
            "news_id": 123
        }
    })

class FavoritesResponseModel(BaseModel):
    user_id: int
    articles: List[ArticleResponseModel]

    model_config = ConfigDict(json_schema_extra={
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
                            "title_tra": "Agreement between Banco Unión...",
                            "detail_tra": "In July of last year...",
                            "content_tra": "Negotiations are ongoing...",
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
    })

class DeleteFavoriteResponseModel(BaseModel):
    message: str
    news_id: int

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "message": "Favorite deleted successfully",
            "news_id": 123
        }
    })
