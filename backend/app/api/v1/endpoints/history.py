from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.search_history import SearchHistory

router = APIRouter()


class SearchHistorySchema(BaseModel):
    id: int
    query_text: Optional[str] = None
    identified_product: Optional[str] = None
    result_json: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SearchHistoryListItem(BaseModel):
    """Lightweight schema for list view (excludes full result_json)."""
    id: int
    query_text: Optional[str] = None
    identified_product: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[SearchHistoryListItem])
def list_search_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0
):
    """
    List the current user's past searches.
    Returns a lightweight list (without full result JSON).
    """
    searches = (
        db.query(SearchHistory)
        .filter(SearchHistory.user_id == current_user.id)
        .order_by(SearchHistory.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return searches


@router.get("/{search_id}", response_model=SearchHistorySchema)
def get_search_history_detail(
    search_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the full details of a specific past search, including the result JSON.
    """
    search = (
        db.query(SearchHistory)
        .filter(
            SearchHistory.id == search_id,
            SearchHistory.user_id == current_user.id
        )
        .first()
    )
    
    if not search:
        raise HTTPException(status_code=404, detail="Search not found")
    
    return search
