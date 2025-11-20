"""Configuration for LLM providers using Pydantic Settings."""

from enum import Enum
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"


class ModelTier(str, Enum):
    LIGHT = "light"
    FULL = "full"


# Find project root .env file
def _find_env_file() -> Path | None:
    """Find the .env file in the project root."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        env_file = parent / ".env"
        if env_file.exists():
            return env_file
    return None


class LLMSettings(BaseSettings):
    """LLM provider configuration loaded from .env file."""

    provider: LLMProvider = LLMProvider.GEMINI

    # OpenAI
    openai_api_key: str | None = None
    openai_light_model: str = "gpt-4.1-mini"
    openai_full_model: str = "gpt-4o"

    # Gemini
    google_api_key: str | None = None
    gemini_light_model: str = "gemini-flash-latest"
    gemini_full_model: str = "gemini-3-pro-preview"

    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        env_file=_find_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def get_model(self, tier: ModelTier = ModelTier.LIGHT) -> str:
        """Get the model name for the current provider and tier."""
        if self.provider == LLMProvider.OPENAI:
            return self.openai_light_model if tier == ModelTier.LIGHT else self.openai_full_model
        elif self.provider == LLMProvider.GEMINI:
            return self.gemini_light_model if tier == ModelTier.LIGHT else self.gemini_full_model
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
