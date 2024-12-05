from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from src.models.base_model import Base

class InterestsModel(Base):
    __tablename__ = 'interests'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    keyword = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default="CURRENT_TIMESTAMP")

    # Relación con el usuario
    user = relationship("UserModel", back_populates="interests")
