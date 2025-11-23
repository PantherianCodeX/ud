# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Configuration management with Pydantic settings."""

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "uDocket API"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = Field(default="development", pattern="^(development|staging|production)$")

    # Database
    database_url: PostgresDsn
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_echo: bool = False
    database_healthcheck_timeout: float = 1.0

    # Auth
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Logging
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    log_json: bool = True


# Global settings instance
# Pydantic Settings loads required fields from environment variables,
# making constructor arguments optional at instantiation despite required field annotations
settings = Settings()  # pyright: ignore[reportCallIssue]
