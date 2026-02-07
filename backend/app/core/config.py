from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    TAVILY_API_KEY: str
    SERPAPI_API_KEY: str
    
    # Database (optional - graceful fallback if not set)
    DATABASE_URL: str = "sqlite:///./test.db"
    
    # Models
    MODEL_VISION: str = "gemini-flash-latest"
    MODEL_REASONING: str = "gemini-flash-latest"

    class Config:
        env_file = ".env"
        extra = "ignore" # Allow other env vars

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
