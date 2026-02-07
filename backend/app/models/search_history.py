from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base


class SearchHistory(Base):
    """
    Stores past user searches and their results.
    Used for:
    - Quick recall of previous product analyses
    - Analytics on user behavior
    - Caching to avoid re-running expensive agent workflows
    """
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Input data
    query_text = Column(Text, nullable=True)  # User's original prompt (e.g., "Is this a good deal?")
    image_hash = Column(String(64), nullable=True, index=True)  # SHA-256 hash for deduplication
    
    # Output data
    identified_product = Column(String, nullable=True)  # What the "Eye" node identified
    result_json = Column(JSON, nullable=True)  # Full recommendation output (verdict, alternatives, etc.)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationship
    user = relationship("User", back_populates="searches")
