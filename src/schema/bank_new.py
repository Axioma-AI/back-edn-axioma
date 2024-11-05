import pandas as pd
from datetime import datetime

from src.schema.sentiment_category import SentimentCategory
from src.utils.convert import convert_nan_to_none

class BankNew:
    def __init__(
        self,
        source_link: str,
        ticker: str | None = None,
        extraction_date: datetime | None = None,
        news_source: str | None = None,
        title: str | None = None,
        detail: str | None = None,
        image_url: str | None = None,
        author: str | None = None,
        publish_datetime: datetime | None = None,
        location: str | None = None,
        content: str | None = None,
        related_themes: list[str] | None = None,
        fact_number: str | None = None,
        sentiment_category: SentimentCategory = SentimentCategory.DESCONOCIDO,
        sentiment_score: float = 0.0,
    ):
        self.ticker = ticker
        self.extraction_date = extraction_date
        self.news_source = news_source
        self.title = title
        self.detail = detail
        self.image_url = image_url
        self.author = author
        self.publish_datetime = publish_datetime
        self.location = location
        self.content = content
        self.related_themes = related_themes
        self.source_link = source_link
        self.fact_number = fact_number
        self.sentiment_category = sentiment_category
        self.sentiment_score = sentiment_score

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f'BankNew({self.ticker}, {self.extraction_date}, {self.news_source}, {self.title}, {self.detail}, {self.image_url}, {self.author}, {self.publish_datetime}, {self.location}, {self.content}, {self.related_themes}, {self.source_link}, {self.fact_number}), {self.sentiment_category}, {self.sentiment_score}'

    def __dict__(self):        
        return {
            'ticker': convert_nan_to_none(self.ticker),
            'extraction_date': convert_nan_to_none(self.extraction_date),
            'news_source': convert_nan_to_none(self.news_source),
            'title': convert_nan_to_none(self.title),
            'detail': convert_nan_to_none(self.detail),
            'image_url': convert_nan_to_none(self.image_url),
            'author': convert_nan_to_none(self.author),
            'publish_datetime': convert_nan_to_none(self.publish_datetime),
            'location': convert_nan_to_none(self.location),
            'content': convert_nan_to_none(self.content),
            'related_themes': convert_nan_to_none(self.related_themes),
            'source_link': convert_nan_to_none(self.source_link),
            'fact_number': convert_nan_to_none(self.fact_number),
            'sentiment_category': convert_nan_to_none(self.sentiment_category),
            'sentiment_score': convert_nan_to_none(self.sentiment_score),
        }