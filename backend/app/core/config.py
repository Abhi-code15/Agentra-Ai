"""Central configuration management using Pydantic Settings."""
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Application
    APP_ENV: str = Field(default="development", description="Runtime environment")
    APP_NAME: str = Field(default="Agentra", description="Application name")
    API_V1_PREFIX: str = Field(default="/api/v1", description="API v1 prefix")
    LOG_LEVEL: str = Field(default="INFO", description="Log level")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://postgres@localhost:5432/agentra_db",
        description="PostgreSQL connection string"
    )
    TEST_DATABASE_URL: str = Field(
        default="postgresql+psycopg2://postgres@localhost:5432/agentra_test_db",
        description="PostgreSQL connection string for testing"
    )

    # Security
    JWT_SECRET_KEY: str = Field(
        default="agentra_dev_jwt_secret_key_needs_to_be_at_least_32_characters_long_for_security!",
        description="Secret key for signing JWTs"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, description="Access token expiry in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiry in days")

    # Gemini AI
    GEMINI_API_KEY: str = Field(default="dummy_key", description="Google Gemini API key")
    GEMINI_MODEL: str = Field(default="gemini-3.5-flash", description="Gemini model name")

    # Storage
    STORAGE_DIRECTORY: str = Field(default="storage/documents", description="Storage directory for uploaded files")
    MAX_UPLOAD_SIZE_BYTES: int = Field(default=26214400, description="Max upload size (25MB)")

    # CORS
    CORS_ALLOWED_ORIGINS: str = Field(
        default="http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173",
        description="Comma-separated CORS allowed origins"
    )

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()
