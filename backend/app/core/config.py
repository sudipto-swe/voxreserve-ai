from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "VOXRESERVE"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite:///./voxreserve.db"  # Defaults to SQLite if PostgreSQL not running; supports postgresql://
    SECRET_KEY: str = "voxreserve-super-secret-jwt-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Restaurant defaults
    RESTAURANT_TIMEZONE: str = "UTC"
    RESERVATION_SLOT_MINUTES: int = 90  # Default duration of a meal
    RESERVATION_BUFFER_MINUTES: int = 15 # Cleaning buffer
    
    # Ollama / AI Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:latest"
    MOCK_LLM_IF_UNAVAILABLE: bool = True  # Fallback to intelligent deterministic rule engine if Ollama is not running
    
    # Voice adapters
    ENABLE_BROWSER_SPEECH: bool = True
    WHISPER_CPP_URL: Optional[str] = None
    PIPER_TTS_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
