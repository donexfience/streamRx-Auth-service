from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI GraphQL Clean Architecture"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "A FastAPI application with GraphQL using clean architecture"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://posgres:postgres@localhost:5432/auth_database"

    # Security
    SECRET_KEY: str = "podaenvnokkanvannekannalle"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 5
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_DECODE_RESPONSES: bool

    # Email
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_USE_TLS: bool  
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # React frontend
        "http://localhost:8000",  # FastAPI backend
    ]

    # Configuration for Pydantic
    model_config = {
        "case_sensitive": True,  # Case-sensitive environment variables
        "env_file": ".env",      # Load variables from a .env file
    }


# Create the settings instance
settings = Settings()
