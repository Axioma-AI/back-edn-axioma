from __future__ import annotations  # Enable forward references

import pandas as pd
from sqlalchemy import Column, Integer, Numeric, String, ForeignKey, DateTime, Text, DECIMAL, Enum
from sqlalchemy.orm import relationship
from src.models.base_model import Base
from src.schema.sentiment_category import SentimentCategory
from src.schema.bank_new import BankNew

class NewsTagAssociation(Base):
    __tablename__ = 'news_tag'
    news_id = Column(Integer, ForeignKey('news.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tag.id'), primary_key=True)
    distance = Column(DECIMAL, nullable=False)
    
    news = relationship('NewsModel', back_populates='tag_associations', overlaps="tags")
    tag = relationship('TagsModel', back_populates='news_associations', overlaps="news")

class TagsModel(Base):
    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    news_associations = relationship('NewsTagAssociation', back_populates='tag', overlaps="news,tags")
    news = relationship('NewsModel', secondary='news_tag', back_populates='tags', overlaps="tag_associations", viewonly=True)

class NewsTranslationModel(Base):
    __tablename__ = 'news_translation'

    id = Column(Integer, primary_key=True, autoincrement=True)
    news_id = Column(Integer, ForeignKey('news.id'), nullable=False)
    title_tra = Column(Text, nullable=False)
    detail_tra = Column(Text, nullable=False)
    content_tra = Column(Text, nullable=False)
    summary_tra = Column(Text, nullable=True)
    justification_tra = Column(Text, nullable=True)
    news_type_category_tra = Column(String(50), nullable=True)
    news_type_justification_tra = Column(Text, nullable=True)
    purpose_objective_tra = Column(String(50), nullable=True)
    purpose_audience_tra = Column(String(50), nullable=True)
    context_temporality_tra = Column(String(50), nullable=True)
    context_location_tra = Column(String(255), nullable=True)
    content_facts_vs_opinions_tra = Column(String(50), nullable=True)
    content_precision_tra = Column(String(50), nullable=True)
    content_impartiality_tra = Column(String(50), nullable=True)
    structure_clarity_tra = Column(String(50), nullable=True)
    structure_key_data_tra = Column(String(50), nullable=True)
    tone_neutrality_tra = Column(String(50), nullable=True)
    tone_ethics_tra = Column(String(50), nullable=True)
    language = Column(Enum('en', 'es'), nullable=False)

    news = relationship('NewsModel', back_populates='translations')

class NewsModel(Base):
    __tablename__ = 'news'

    id = Column(Integer, primary_key=True, autoincrement=True)
    news_source = Column(String(255), nullable=True)
    title = Column(String(255), nullable=True)
    detail = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    author = Column(String(255), nullable=True)
    publish_datetime = Column(DateTime, nullable=True)
    location = Column(String(255), nullable=True)
    source_link = Column(String(255), nullable=False, unique=True)
    sentiment_category = Column(Enum(SentimentCategory), nullable=False)
    justification = Column(Text)
    sentiment_score = Column(Numeric(5, 5), nullable=False)
    news_type_category = Column(String(50), nullable=True)
    news_type_justification = Column(Text, nullable=True)
    purpose_objective = Column(String(50), nullable=True)
    purpose_audience = Column(String(50), nullable=True)
    context_temporality = Column(String(50), nullable=True)
    context_location = Column(String(255), nullable=True)
    content_facts_vs_opinions = Column(String(50), nullable=True)
    content_precision = Column(String(50), nullable=True)
    content_impartiality = Column(String(50), nullable=True)
    structure_clarity = Column(String(50), nullable=True)
    structure_key_data = Column(String(50), nullable=True)
    tone_neutrality = Column(String(50), nullable=True)
    tone_ethics = Column(String(50), nullable=True)

    tag_associations = relationship("NewsTagAssociation", back_populates="news", overlaps="tags")
    tags = relationship("TagsModel", secondary='news_tag', back_populates="news", overlaps="tag_associations", viewonly=True)
    favorites = relationship("FavoritesModel", back_populates="news", cascade="all, delete-orphan")
    translations = relationship('NewsTranslationModel', back_populates='news')
    characters = relationship('NewsCharactersModel', back_populates='news')

    @staticmethod
    def from_bank_new(bank_new: BankNew) -> 'NewsModel':
        return NewsModel(
            news_source=bank_new.news_source if pd.notna(bank_new.news_source) else None,
            title=bank_new.title if pd.notna(bank_new.title) else None,
            detail=bank_new.detail if pd.notna(bank_new.detail) else None,
            image_url=bank_new.image_url if pd.notna(bank_new.image_url) else None,
            content=bank_new.content if pd.notna(bank_new.content) else None,
            author=bank_new.author if pd.notna(bank_new.author) else None,
            publish_datetime=bank_new.publish_datetime if pd.notna(bank_new.publish_datetime) else None,
            location=bank_new.location if pd.notna(bank_new.location) else None,
            source_link=bank_new.source_link,
            sentiment_category=bank_new.sentiment_category,
            sentiment_score=bank_new.sentiment_score,
        )

class NewsCharactersModel(Base):
    __tablename__ = 'news_characters'

    id = Column(Integer, primary_key=True, autoincrement=True)
    news_id = Column(Integer, ForeignKey('news.id'), nullable=False)
    character_name = Column(String(255, collation='utf8mb4_unicode_ci'), nullable=False)
    character_description = Column(Text(collation='utf8mb4_unicode_ci'), nullable=False)

    news = relationship('NewsModel', back_populates='characters')

class NewsTransCharactersModel(Base):
    __tablename__ = 'news_trans_characters'

    id = Column(Integer, primary_key=True, autoincrement=True)
    news_characters_id = Column(Integer, ForeignKey('news_characters.id'), nullable=False)
    character_description_tra = Column(Text, nullable=False)
    language = Column(Enum('en', 'es'), nullable=False)

    news_character = relationship('NewsCharactersModel')