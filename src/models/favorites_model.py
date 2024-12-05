from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from src.models.base_model import Base

class FavoritesModel(Base):
    __tablename__ = 'favorites'

    user_id = Column(Integer, ForeignKey('user.id', ondelete="CASCADE"), primary_key=True)
    news_id = Column(Integer, ForeignKey('news.id', ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=None)

    user = relationship("UserModel", back_populates="favorites")
    news = relationship("NewsModel", back_populates="favorites")
