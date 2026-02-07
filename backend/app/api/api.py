from fastapi import APIRouter
from app.api.v1.endpoints import agent, search, users

api_router = APIRouter()
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
