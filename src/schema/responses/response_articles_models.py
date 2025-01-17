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
    summary_tra: Optional[str] = None
    justification_tra: Optional[str] = None
    news_type_category_tra: Optional[str] = None
    news_type_justification_tra: Optional[str] = None
    purpose_objective_tra: Optional[str] = None
    purpose_audience_tra: Optional[str] = None
    context_temporality_tra: Optional[str] = None
    context_location_tra: Optional[str] = None
    content_facts_vs_opinions_tra: Optional[str] = None
    content_precision_tra: Optional[str] = None
    content_impartiality_tra: Optional[str] = None
    structure_clarity_tra: Optional[str] = None
    structure_key_data_tra: Optional[str] = None
    tone_neutrality_tra: Optional[str] = None
    tone_ethics_tra: Optional[str] = None
    language: str

class NewsCharacterTranslationModel(BaseModel):
    id: int
    character_description_tra: str
    language: str

class NewsCharacterModel(BaseModel):
    id: int
    character_name: str
    character_description: str
    translations: List[NewsCharacterTranslationModel] = []

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
    summary: Optional[str] = None
    justification: Optional[str] = None
    news_type_category: Optional[str] = None
    news_type_justification: Optional[str] = None
    purpose_objective: Optional[str] = None
    purpose_audience: Optional[str] = None
    context_temporality: Optional[str] = None
    context_location: Optional[str] = None
    content_facts_vs_opinions: Optional[str] = None
    content_precision: Optional[str] = None
    content_impartiality: Optional[str] = None
    structure_clarity: Optional[str] = None
    structure_key_data: Optional[str] = None
    tone_neutrality: Optional[str] = None
    tone_ethics: Optional[str] = None
    distance: Optional[float] = None
    is_favorite: Optional[bool] = None
    category: Optional[str] = None
    translations: List[TranslationModel] = []
    characters: List[NewsCharacterModel] = []

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
            "summary": "Negociaciones avanzadas entre bancos.",
            "justification": "Acuerdo estratégico entre instituciones.",
            "news_type_category": "Economía",
            "news_type_justification": "Promoción del yuan en el mercado.",
            "purpose_objective": "Fortalecer relaciones comerciales.",
            "purpose_audience": "Empresas e instituciones financieras.",
            "context_temporality": "Actual",
            "context_location": "Bolivia y China",
            "content_facts_vs_opinions": "Predominio de hechos.",
            "content_precision": "Alta",
            "content_impartiality": "Neutral",
            "structure_clarity": "Ordenada",
            "structure_key_data": "Datos clave presentes.",
            "tone_neutrality": "Neutral",
            "tone_ethics": "Ético",
            "distance": 0.5089,
            "is_favorite": True,
            "category": "economía",
            "translations": [
                {
                    "id": 1,
                    "title_tra": "Agreement between Banco Unión and ICBC of China is in its final phase for yuan operations",
                    "detail_tra": "In July of last year, the government reported on the steps...",
                    "content_tra": "Negotiations to establish an agreement between the state Banco Unión...",
                    "summary_tra": "Advanced negotiations between banks.",
                    "justification_tra": "Strategic agreement between institutions.",
                    "news_type_category_tra": "Economy",
                    "news_type_justification_tra": "Promotion of the yuan in the market.",
                    "purpose_objective_tra": "Strengthen trade relations.",
                    "purpose_audience_tra": "Companies and financial institutions.",
                    "context_temporality_tra": "Current",
                    "context_location_tra": "Bolivia and China",
                    "content_facts_vs_opinions_tra": "Fact-dominant.",
                    "content_precision_tra": "High",
                    "content_impartiality_tra": "Neutral",
                    "structure_clarity_tra": "Organized",
                    "structure_key_data_tra": "Key data included.",
                    "tone_neutrality_tra": "Neutral",
                    "tone_ethics_tra": "Ethical",
                    "language": "en"
                }
            ],
            "characters": [
                {
                    "id": 1,
                    "character_name": "John Doe",
                    "character_description": "A key figure in the article...",
                    "translations": [
                        {
                            "id": 1,
                            "character_description_tra": "Un personaje clave en el artículo...",
                            "language": "es"
                        }
                    ]
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
