from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base


class User(Base):
    """
    User model synced from Auth0.
    
    Preferences JSON Structure:
    {
        "price_sensitivity": 0.8,    # 0.0 (price doesn't matter) to 1.0 (very price conscious)
        "durability": 0.9,           # 0.0 to 1.0
        "brand_reputation": 0.5,     # 0.0 to 1.0
        "environmental_impact": 0.3  # 0.0 to 1.0
    }
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    auth0_id = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True)
    name = Column(String, nullable=True)
    
    # Weighted preferences for personalization (used by Analysis Node)
    preferences = Column(JSON, default={
        "price_sensitivity": 0.5,
        "durability": 0.5,
        "brand_reputation": 0.5,
        "environmental_impact": 0.5
    })
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to search history
    searches = relationship("SearchHistory", back_populates="user", cascade="all, delete-orphan")
    
    # Relationship to chat sessions
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
