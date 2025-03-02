from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Boolean, VARCHAR
from sqlalchemy.orm import relationship
from src.models.base_model import Base

class UserModel(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(VARCHAR(255), nullable=False, unique=True)
    name = Column(VARCHAR(255), nullable=True)
    phone = Column(String(20), nullable=True)
    picture = Column(VARCHAR(255), nullable=True)
    email_verified = Column(Boolean, nullable=False, default=False)
    country_code = Column(VARCHAR(5), nullable=True)

    firebase_tokens = relationship("FirebaseTokenModel", back_populates="user", cascade="all, delete-orphan")
    interests = relationship("InterestsModel", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("FavoritesModel", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("SubscriptionModel", back_populates="user", cascade="all, delete-orphan")

class FirebaseTokenModel(Base):
    __tablename__ = 'firebase_token'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    iss = Column(VARCHAR(255), nullable=False)
    aud = Column(VARCHAR(255), nullable=False)
    auth_time = Column(DateTime, nullable=False)
    iat = Column(DateTime, nullable=False)
    exp = Column(DateTime, nullable=False)

    user = relationship("UserModel", back_populates="firebase_tokens")
