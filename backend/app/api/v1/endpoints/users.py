from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from pydantic import BaseModel

router = APIRouter()

class UserSchema(BaseModel):
    id: int
    email: str
    auth0_id: str
    preferences: dict

    class Config:
        from_attributes = True

@router.get("/me", response_model=UserSchema)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

class UserUpdate(BaseModel):
    preferences: dict

@router.patch("/me", response_model=UserSchema)
def update_user_me(user_update: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.preferences = user_update.preferences
    db.commit()
    db.refresh(current_user)
    return current_user
