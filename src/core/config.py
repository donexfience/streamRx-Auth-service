from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from typing import ClassVar

class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI GraphQL Clean Architecture"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "A FastAPI application with GraphQL using clean architecture"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/dbname"

    # Security
    SECRET_KEY: str = "43sdfdaslfhljrrjfrlahfdfsf"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 5
    REFRESH_TOKEN_EXPIRE_DAYS: int =7
    JWT_ALGORITHM: str = "HS256"

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # React frontend
        "http://localhost:8000",  # FastAPI backend
    ]

    model_config = {
        "case_sensitive": True,  # Case-sensitive environment variables
        "env_file": ".env",      # Load variables from a .env file
    }

settings = Settings()