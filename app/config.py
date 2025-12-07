from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Supabase Configuration
    supabase_url: str = ""
    supabase_service_key: str = ""
    
    # OpenAI Configuration
    openai_api_key: str = ""
    
    # JWT Configuration
    jwt_secret: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    
    # Server Configuration
    api_host: str = "0.0.0.0"
    api_port: int = int(os.getenv("PORT", "8000"))  # Render uses $PORT
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # CORS Origins
    cors_origins: str = "http://localhost:3000,http://localhost:8081"
    
    # Payment Configuration - COMMENTED OUT (not using payment systems)
    # PayTR Configuration (optional)
    # paytr_merchant_id: str = ""
    # paytr_merchant_key: str = ""
    # paytr_merchant_salt: str = ""
    # paytr_mode: str = "test"  # test or live
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

