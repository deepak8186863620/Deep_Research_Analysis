import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Deep Research Analysis API"
    MONGODB_URI: str = "mongodb://localhost:27017"
    GOOGLE_API_KEY: str = ""
    TAVILY_API_KEY: str = ""
    SEMANTIC_SCHOLAR_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-pro"

    class Config:
        env_file = ".env"

settings = Settings()
