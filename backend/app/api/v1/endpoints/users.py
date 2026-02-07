from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()


class UserSchema(BaseModel):
    id: int
    email: Optional[str] = None
    auth0_id: str
    name: Optional[str] = None
    preferences: dict

    class Config:
        from_attributes = True


class PreferencesUpdate(BaseModel):
    """
    User preference weights (0.0 to 1.0 scale).
    These weights are used by the Analysis Node to personalize recommendations.
    """
    price_sensitivity: Optional[float] = None
    durability: Optional[float] = None
    brand_reputation: Optional[float] = None
    environmental_impact: Optional[float] = None


@router.get("/me", response_model=UserSchema)
def read_users_me(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return current_user


@router.patch("/preferences", response_model=UserSchema)
def update_user_preferences(
    prefs: PreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the current user's preference weights.
    Only provided fields will be updated; others remain unchanged.
    """
    # Merge new preferences with existing ones
    current_prefs = current_user.preferences or {}
    
    if prefs.price_sensitivity is not None:
        current_prefs["price_sensitivity"] = prefs.price_sensitivity
    if prefs.durability is not None:
        current_prefs["durability"] = prefs.durability
    if prefs.brand_reputation is not None:
        current_prefs["brand_reputation"] = prefs.brand_reputation
    if prefs.environmental_impact is not None:
        current_prefs["environmental_impact"] = prefs.environmental_impact
    
    current_user.preferences = current_prefs
    db.commit()
    db.refresh(current_user)
    return current_user
