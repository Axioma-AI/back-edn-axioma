from __future__ import annotations

import pandas as pd
from sqlalchemy import Column, Integer, Numeric, String, ForeignKey, DateTime, Text, DECIMAL, Enum
from sqlalchemy.orm import DeclarativeBase, relationship
from src.schema.sentiment_category import SentimentCategory
from src.schema.bank_new import BankNew

class Base(DeclarativeBase):
    pass

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
    news = relationship('NewsModel', secondary='news_tag', back_populates='tags', overlaps="tag_associations")

class NewsModel(Base):
    __tablename__ = 'news'

    id = Column(Integer, primary_key=True, autoincrement=True)
    news_source = Column(String(255), nullable=True)
    title = Column(String(255), nullable=True)
    detail = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    author = Column(String(255), nullable=True)
    publish_datetime = Column(DateTime, nullable=True)
    location = Column(String(255), nullable=True)
    source_link = Column(String(255), nullable=False, unique=True)
    sentiment_category = Column(Enum(SentimentCategory), nullable=False)
    sentiment_score = Column(Numeric(5, 5), nullable=False)
    tag_associations = relationship('NewsTagAssociation', back_populates='news', overlaps="tags")
    tags = relationship('TagsModel', secondary='news_tag', back_populates='news', overlaps="tag_associations")

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
