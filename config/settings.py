import os
from typing import Optional
from pydantic import  Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    # API Configuration
    EXPRESS_API_BASE_URL: str = Field(default="https://dowhistle.herokuapp.com/v3")
    MCP_SERVER_PORT: int = Field(default=8000)

    HEALTH_PORT:int = Field(default=8080)
    
    # Authentication
    API_KEY: Optional[str] = Field(default=None)
    JWT_SECRET: Optional[str] = Field(default=None)
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)
    
    # Retry Configuration
    MAX_RETRIES: int = Field(default=3)
    RETRY_DELAY: float = Field(default=1.0)
    
settings = Settings()