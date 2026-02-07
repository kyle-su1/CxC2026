from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    TAVILY_API_KEY: str
    SERPAPI_API_KEY: str
    
    # Models
    MODEL_VISION: str = "gemini-1.5-flash"
    MODEL_REASONING: str = "gemini-1.5-pro"

    class Config:
        env_file = ".env"
        extra = "ignore" # Allow other env vars

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
