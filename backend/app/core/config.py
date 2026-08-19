import os
from pydantic_settings import BaseSettings # allows Pydantic to read configuration values from environment variables, especially from a .env file. #
#if we use this base setting we dont need to hard cord the important key like everytime we dont need to call the url of mongo db and othere skey

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
