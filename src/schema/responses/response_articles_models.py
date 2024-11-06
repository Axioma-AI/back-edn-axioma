from pydantic import BaseModel
from typing import List, Optional

class SourceModel(BaseModel):
    id: str
    name: str

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

    class Config:
        orm_mode = True
        schema_extra = {
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
                "distance": 0.5089
            }
        }

class ErrorResponseModel(BaseModel):
    detail: str

    class Config:
        schema_extra = {
            "example": {
                "detail": "Invalid request. Query parameter is missing."
            }
        }
