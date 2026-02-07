from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/cxc_db"
    
    # Auth0
    AUTH0_DOMAIN: str = "placeholder.auth0.com"
    AUTH0_CLIENT_ID: Optional[str] = None
    AUTH0_AUDIENCE: Optional[str] = None
    AUTH0_ALGORITHM: str = "RS256"
    
    # API Keys
    GOOGLE_API_KEY: str
    TAVILY_API_KEY: str
    SERPAPI_API_KEY: str
    
    # Models
    MODEL_VISION: str = "gemini-2.0-flash"
    MODEL_REASONING: str = "gemini-2.0-flash"

    class Config:
        env_file = ".env"
        extra = "ignore" # Allow other env vars

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
