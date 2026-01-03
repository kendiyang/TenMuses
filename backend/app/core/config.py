from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/tenmuses"
    
    # JWT
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    
    # Anthropic
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_BASE_URL: str = ""
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
