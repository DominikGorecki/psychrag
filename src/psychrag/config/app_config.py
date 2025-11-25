"""Application configuration loaded from JSON file.

This module manages non-secret application settings stored in psychrag.config.json.
Secrets like API keys and passwords remain in .env for security.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    """Database configuration settings."""

    admin_user: str = Field(default="postgres", description="PostgreSQL admin username")
    host: str = Field(default="127.0.0.1", description="Database host")
    port: int = Field(default=5432, description="Database port")
    db_name: str = Field(default="psych_rag_test", description="Application database name")
    app_user: str = Field(
        default="psych_rag_app_user_test", description="Application user name"
    )


class ModelConfig(BaseModel):
    """Model configuration for a specific provider."""

    light: str = Field(description="Light/fast model name")
    full: str = Field(description="Full/complex model name")


class LLMModelsConfig(BaseModel):
    """LLM models configuration for all providers."""

    openai: ModelConfig = Field(
        default=ModelConfig(light="gpt-4o-mini", full="gpt-4o")
    )
    gemini: ModelConfig = Field(
        default=ModelConfig(light="gemini-flash-latest", full="gemini-2.5-pro")
    )


class LLMConfig(BaseModel):
    """LLM configuration settings."""

    provider: Literal["openai", "gemini"] = Field(
        default="gemini", description="Active LLM provider"
    )
    models: LLMModelsConfig = Field(default_factory=LLMModelsConfig)


class AppConfig(BaseModel):
    """Root application configuration."""

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)


# Singleton instance
_config_cache: AppConfig | None = None


def get_config_path() -> Path:
    """Get the path to the configuration file.

    Returns:
        Path to psychrag.config.json in project root
    """
    # Start from this file's location and search up for the config file
    current = Path(__file__).resolve().parent
    for _ in range(10):  # Limit search depth
        config_file = current / "psychrag.config.json"
        if config_file.exists():
            return config_file
        if current.parent == current:
            break
        current = current.parent

    # Default to project root (3 levels up from this file)
    return Path(__file__).resolve().parent.parent.parent.parent / "psychrag.config.json"


def load_config(force_reload: bool = False) -> AppConfig:
    """Load application configuration from JSON file.

    Uses singleton pattern to cache the loaded configuration.

    Args:
        force_reload: Force reload from file even if cached

    Returns:
        AppConfig instance with loaded settings

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file is invalid JSON or doesn't match schema
    """
    global _config_cache

    if _config_cache is not None and not force_reload:
        return _config_cache

    config_path = get_config_path()

    if not config_path.exists():
        # Return default config if file doesn't exist
        _config_cache = AppConfig()
        return _config_cache

    try:
        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)
        _config_cache = AppConfig(**data)
        return _config_cache
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {e}") from e
    except Exception as e:
        raise ValueError(f"Error loading config: {e}") from e


def save_config(config: AppConfig) -> None:
    """Save application configuration to JSON file.

    Args:
        config: AppConfig instance to save
    """
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w", encoding="utf-8") as f:
        # Use model_dump() to convert to dict, then save as JSON
        json.dump(config.model_dump(), f, indent=2)

    # Update cache
    global _config_cache
    _config_cache = config


def get_default_config() -> AppConfig:
    """Get default configuration without loading from file.

    Returns:
        AppConfig instance with default values
    """
    return AppConfig()
