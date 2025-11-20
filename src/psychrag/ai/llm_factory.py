"""Factory functions for creating PydanticAI and LangChain instances."""

from dataclasses import dataclass

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic_ai import Agent

from .config import LLMProvider, LLMSettings, ModelTier


@dataclass
class PydanticAIStack:
    """Container for PydanticAI Agent."""

    agent: Agent


@dataclass
class LangChainStack:
    """Container for LangChain ChatModel."""

    chat: BaseChatModel


@dataclass
class LLMStack:
    """Combined stack with both PydanticAI and LangChain instances."""

    settings: LLMSettings
    pydantic_ai: PydanticAIStack
    langchain: LangChainStack


def create_pydantic_agent(
    settings: LLMSettings,
    tier: ModelTier = ModelTier.LIGHT,
) -> PydanticAIStack:
    """Create a PydanticAI Agent based on the configured provider.

    Args:
        settings: LLM settings with provider and API keys
        tier: Model tier to use (LIGHT or FULL)
    """
    model_name = settings.get_model(tier)

    if settings.provider == LLMProvider.OPENAI:
        model_str = f"openai:{model_name}"
    elif settings.provider == LLMProvider.GEMINI:
        model_str = f"google-gla:{model_name}"
    else:
        raise ValueError(f"Unsupported provider: {settings.provider}")

    agent = Agent(
        model_str,
        instructions="You are a helpful assistant.",
    )
    return PydanticAIStack(agent=agent)


def create_langchain_chat(
    settings: LLMSettings | None = None,
    tier: ModelTier = ModelTier.LIGHT,
    search: bool = False,
    temperature: float = 0.2
) -> LangChainStack:
    """Create a LangChain ChatModel based on the configured provider.

    Args:
        settings: LLM settings with provider and API keys (default: load from .env)
        tier: Model tier to use (LIGHT or FULL)
        search: Enable web search capability (default: False)
        temperature: Model temperature (default 0.2)
    """
    if settings is None:
        settings = LLMSettings()

    model_name = settings.get_model(tier)

    if settings.provider == LLMProvider.OPENAI:
        chat = ChatOpenAI(
            model=model_name,
            api_key=settings.openai_api_key,
            temperature=temperature,
        )
        # Note: OpenAI web search would require additional tools/plugins
        # This is a placeholder for future implementation
        if search:
            # Web search for OpenAI would be implemented via function calling
            pass
    elif settings.provider == LLMProvider.GEMINI:
        if search:
            # Enable Google Search grounding for Gemini
            chat = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=settings.google_api_key,
                temperature=temperature,
                extra_body={"tools": [{"google_search": {}}]},
            )
        else:
            chat = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=settings.google_api_key,
                temperature=temperature,
            )
    else:
        raise ValueError(f"Unsupported provider: {settings.provider}")

    return LangChainStack(chat=chat)


def create_llm_stack(
    tier: ModelTier = ModelTier.LIGHT,
    search: bool = False,
    temperature: float = 0.2
) -> LLMStack:
    """Create a complete LLM stack with both PydanticAI and LangChain.

    Args:
        tier: Model tier to use (LIGHT or FULL)
        search: Enable web search capability (default: False)
        temperature: Model temperature for LangChain (default 0.2)

    Examples:
        # Use default light models from .env
        stack = create_llm_stack()

        # Use full models for complex tasks
        stack = create_llm_stack(tier=ModelTier.FULL)

        # Enable web search
        stack = create_llm_stack(tier=ModelTier.LIGHT, search=True)
    """
    settings = LLMSettings()
    pydantic_stack = create_pydantic_agent(settings, tier=tier)
    langchain_stack = create_langchain_chat(settings, tier=tier, search=search, temperature=temperature)
    return LLMStack(
        settings=settings,
        pydantic_ai=pydantic_stack,
        langchain=langchain_stack,
    )
