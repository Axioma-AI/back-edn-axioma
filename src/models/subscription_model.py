from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
import enum
from src.models.base_model import Base

class SubscriptionStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    PENDING = "PENDING"

class SubscriptionTier(enum.Enum):
    FREE = "FREE"
    PRO = "PRO"
    ANALYST = "ANALYST"
    
    @classmethod
    def from_string(cls, value):
        """Convert a string to the appropriate enum value, case-insensitive"""
        if not value:
            return cls.FREE
            
        # Convert to uppercase to match enum values
        value = value.upper()
        
        for member in cls:
            if member.value.upper() == value:
                return member
        
        # Default to FREE if no match is found
        return cls.FREE

class SubscriptionAction(enum.Enum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    RENEWED = "RENEWED"

class SubscriptionModel(Base):
    __tablename__ = 'subscription'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    subscription_id = Column(String(255), nullable=False, unique=True)  # ID from payment provider
    tier = Column(Enum(SubscriptionTier), nullable=False, default=SubscriptionTier.FREE)
    status = Column(Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.ACTIVE)
    start_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    auto_renew = Column(Boolean, default=True)
    platform = Column(String(50), nullable=False)  # ios/android
    receipt_data = Column(String(2048), nullable=True)  # Store the receipt/token for verification
    product_id = Column(String(255), nullable=True)
    provider = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserModel", back_populates="subscriptions")
    history = relationship("SubscriptionHistoryModel", back_populates="subscription")

class SubscriptionHistoryModel(Base):
    __tablename__ = 'subscription_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    subscription_id = Column(Integer, ForeignKey('subscription.id', ondelete="CASCADE"), nullable=False)
    action = Column(Enum(SubscriptionAction), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    subscription = relationship("SubscriptionModel", back_populates="history") 