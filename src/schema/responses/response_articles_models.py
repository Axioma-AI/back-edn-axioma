from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class SourceModel(BaseModel):
    id: str
    name: str

class TranslationModel(BaseModel):
    id: int
    title_tra: str
    detail_tra: str
    content_tra: str
    language: str

class ArticleResponseModel(BaseModel):
    id: int
    source: SourceModel
    author: Optional[str] = None
    title: str
    description: Optional[str] = None
    url: str
    urlToImage: Optional[str] = None
    publishedAt: str
    content: Optional[str] = None
    sentiment_category: str
    sentiment_score: float
    distance: Optional[float] = None
    is_favorite: Optional[bool] = None
    category: Optional[str] = None
    translations: List[TranslationModel] = []

    model_config = ConfigDict(from_attributes=True, json_schema_extra={
        "example": {
            "id": 6845,
            "source": {"id": "La Razon", "name": "La Razon"},
            "author": "Yuri Flores",
            "title": "Convenio entre Banco Unión e ICBC de China está en fase final para operaciones en yuanes",
            "description": "En julio del año pasado, el Gobierno informaba sobre las gestiones que realizaba para que un banco chino se instale en el país.",
            "url": "https://www.la-razon.com/economia/2024/01/02/convenio-entre-banco-union-e-icbc-de-china-esta-en-fase-final-para-operaciones-en-yuanes/",
            "urlToImage": "https://www.la-razon.com/wp-content/uploads/2024/01/02/19/WhatsApp-Image-2024-01-02-at-14.06.44.jpeg",
            "publishedAt": "2024-01-02T15:21:00",
            "content": "Las negociaciones para establecer un convenio entre el estatal Banco Unión...",
            "sentiment_category": "POSITIVO",
            "sentiment_score": 0.35917,
            "distance": 0.5089,
            "is_favorite": True,
            "category": "economia",
            "translations": [
                {
                    "id": 1,
                    "title_tra": "Agreement between Banco Unión and ICBC of China is in its final phase for yuan operations",
                    "detail_tra": "In July of last year, the government reported on the steps...",
                    "content_tra": "Negotiations to establish an agreement between the state Banco Unión...",
                    "language": "en"
                },
                {
                    "id": 2,
                    "title_tra": "Convenio entre Banco Unión e ICBC de China está en fase final para operaciones en yuanes",
                    "detail_tra": "En julio del año pasado, el Gobierno informaba sobre las gestiones...",
                    "content_tra": "Las negociaciones para establecer un convenio entre el estatal Banco Unión...",
                    "language": "es"
                }
            ]
        }
    })

class ErrorResponseModel(BaseModel):
    detail: str

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "detail": "Invalid request. Query parameter is missing."
        }
    })

class NewsSourceResponseModel(BaseModel):
    sources: List[str]

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "sources": ["CNN", "BBC", "Reuters", "Al Jazeera"]
        }
    })
