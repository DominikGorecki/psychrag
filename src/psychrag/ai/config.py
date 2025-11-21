"""Configuration for LLM providers using Pydantic Settings."""

from enum import Enum
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_env_file() -> Path | None:
    """Find the .env file by searching up from this file's location."""
    current = Path(__file__).resolve().parent
    # Search up to find .env in project root
    for _ in range(10):  # Limit search depth
        env_file = current / ".env"
        if env_file.exists():
            return env_file
        if current.parent == current:
            break
        current = current.parent
    return None


# Cache the env file path at module load time
_ENV_FILE_PATH = _find_env_file()


class LLMProvider(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"


class ModelTier(str, Enum):
    LIGHT = "light"
    FULL = "full"


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
    gemini_full_model: str = "gemini-2.5-pro"

    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        env_file=_ENV_FILE_PATH,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def get_model(self, tier: ModelTier = ModelTier.LIGHT) -> str:
        """Get the model name for the current provider and tier."""
        if self.provider == LLMProvider.OPENAI:
            return self.openai_light_model if tier == ModelTier.LIGHT else self.openai_full_model
        elif self.provider == LLMProvider.GEMINI:
            return self.gemini_light_model if tier == ModelTier.LIGHT else "gemini-2.5-pro" #self.gemini_full_model
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
