import os
from typing import Optional, Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Environment Configuration
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        default="development"
    )

    # Transport Configuration
    TRANSPORT_MODE: Optional[Literal["http", "stdio"]] = Field(
        default="http",
    )

    # API Configuration
    EXPRESS_API_BASE_URL: str = Field(default="https://dowhistle.herokuapp.com/v3")
    MCP_SERVER_PORT: int = Field(default=8000)
    HEALTH_PORT: int = Field(default=8080)

    # Authentication
    API_KEY: Optional[str] = Field(default=None)

    # Logging
    LOG_LEVEL: str = Field(default="INFO")

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)

    # Retry Configuration
    MAX_RETRIES: int = Field(default=3)
    RETRY_DELAY: float = Field(default=1.0)

    # Connection Configuration
    CONNECTION_TIMEOUT: int = Field(default=30)
    REQUEST_TIMEOUT: int = Field(default=30)

    # CORS Configuration (for HTTP transport)
    CORS_ORIGINS: str = Field(default="*")
    CORS_METHODS: str = Field(default="GET,POST,OPTIONS")
    CORS_HEADERS: str = Field(default="Content-Type,Authorization")

    @field_validator("TRANSPORT_MODE", mode="before")
    @classmethod
    def set_transport_mode(cls, v, info):
        """Auto-determine transport mode based on environment if not explicitly set"""
        if v is not None:
            return v.lower()

        # Get environment from the data being validated
        environment = info.data.get("ENVIRONMENT", "development")
        if environment == "production":
            return "http"
        else:
            return "stdio"

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def set_log_level(cls, v, info):
        """Auto-adjust log level based on environment if not explicitly set"""
        if v != "INFO":  # If explicitly set, keep it
            return v.upper()

        # Get environment from the data being validated
        environment = info.data.get("ENVIRONMENT", "development")
        if environment == "production":
            return "INFO"
        elif environment == "staging":
            return "DEBUG"
        else:
            return "DEBUG"

    @field_validator("HEALTH_PORT", mode="before")
    @classmethod
    def handle_render_port(cls, v, info):
        """Handle Render.com PORT environment variable"""
        # Render.com uses PORT env var, prioritize it for health checks
        render_port = os.getenv("PORT")
        if render_port:
            return int(render_port)
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.ENVIRONMENT == "production"

    @property
    def is_stdio_transport(self) -> bool:
        """Check if using stdio transport"""
        return self.TRANSPORT_MODE == "stdio"

    @property
    def is_http_transport(self) -> bool:
        """Check if using HTTP transport"""
        return self.TRANSPORT_MODE == "http"

    @property
    def server_info(self) -> dict:
        """Get server configuration info"""
        return {
            "environment": self.ENVIRONMENT,
            "transport_mode": self.TRANSPORT_MODE,
            "mcp_port": self.MCP_SERVER_PORT,
            "health_port": self.HEALTH_PORT,
            "api_base_url": self.EXPRESS_API_BASE_URL,
            "log_level": self.LOG_LEVEL,
        }

    def model_post_init(self, __context) -> None:
        """Post-initialization validation and logging"""
        print(f"🚀 Server Configuration:")
        print(f"   Environment: {self.ENVIRONMENT}")
        print(f"   Transport: {self.TRANSPORT_MODE}")
        print(f"   Health Port: {self.HEALTH_PORT}")
        print(f"   MCP Port: {self.MCP_SERVER_PORT}")
        print(f"   API Base URL: {self.EXPRESS_API_BASE_URL}")
        print(f"   Log Level: {self.LOG_LEVEL}")


settings = Settings()
