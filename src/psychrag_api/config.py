"""
API Configuration settings.

Uses pydantic-settings for environment variable support.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    """API configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="PSYCHRAG_API_",
        env_file=".env",
        extra="ignore",  # Ignore extra env vars from .env
    )

    # API metadata
    api_title: str = "PsychRAG API"
    api_description: str = """
## PsychRAG REST API

A Retrieval-Augmented Generation system for psychology literature.

### Features

* **Document Conversion** - Convert EPUBs, PDFs to markdown
* **Sanitization** - Clean and normalize content
* **Chunking** - Split documents into semantic chunks
* **Vectorization** - Generate embeddings for chunks
* **RAG** - Query and generate responses with context

### Authentication

Currently no authentication required (development mode).
"""
    api_version: str = "0.1.0"

    # Server settings
    debug: bool = False
    
    # CORS settings
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]


@lru_cache
def get_settings() -> APISettings:
    """Get cached settings instance."""
    return APISettings()

