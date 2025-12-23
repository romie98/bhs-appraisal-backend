"""Application configuration"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = "sqlite:///./markbook.db"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PRICE_PREMIUM: Optional[str] = None
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:5173"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields from .env file
    )


settings = Settings()

