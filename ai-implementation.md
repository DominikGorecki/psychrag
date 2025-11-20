The cleanest way to do this is:

* **One config-driven “LLM provider” layer**,
* That can spit out:

  * a **PydanticAI Agent** wired to Gemini *or* ChatGPT, and
  * a **LangChain ChatModel** wired to the *same* provider,
* While the rest of your code never cares which one is underneath.

Think **adapter/factory pattern**, not sprinkling `if provider == "gemini"` all over the place.

---

## 1. Define a single config for your LLM provider

Use Pydantic Settings (fits nicely with PydanticAI anyway):

```python
# config.py
from enum import Enum
from pydantic_settings import BaseSettings

class LLMProvider(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"

class LLMSettings(BaseSettings):
    provider: LLMProvider = LLMProvider.OPENAI

    # OpenAI
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"

    # Gemini
    google_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"

    class Config:
        env_prefix = "LLM_"   # e.g. LLM_PROVIDER, LLM_OPENAI_API_KEY, etc.
        case_sensitive = False
```

Then in your app:

```python
settings = LLMSettings()
```

Now flipping between Gemini and ChatGPT = changing `LLM_PROVIDER` env var.

---

## 2. Build a small LLM “factory” for **both** PydanticAI and LangChain

### 2.1 PydanticAI side

PydanticAI lets you pass a **model string** like `'openai:gpt-4.1-mini'` or `'google-gla:gemini-2.5-pro'` directly to `Agent`.

We’ll wrap that:

```python
# llm_factory.py
from dataclasses import dataclass

from pydantic_ai import Agent
from config import LLMSettings, LLMProvider

@dataclass
class PydanticAIStack:
    agent: Agent  # you can extend this later (tools, deps, etc.)

def create_pydantic_agent(settings: LLMSettings) -> PydanticAIStack:
    if settings.provider == LLMProvider.OPENAI:
        # expects OPENAI_API_KEY env var set OR pass via provider
        model_str = f"openai:{settings.openai_model}"
    elif settings.provider == LLMProvider.GEMINI:
        # uses google-genai under the hood
        model_str = f"google-gla:{settings.gemini_model}"
    else:
        raise ValueError(f"Unsupported provider: {settings.provider}")

    agent = Agent(
        model_str,
        instructions="You are a helpful assistant.",
    )
    return PydanticAIStack(agent=agent)
```

You could also build the `GoogleModel` / `OpenAIChatModel` objects explicitly, but the string-based syntax is enough and officially supported.

---

### 2.2 LangChain side

LangChain already has separate chat classes for OpenAI and Gemini:

```python
# llm_factory.py (continued)
from dataclasses import dataclass

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

@dataclass
class LangChainStack:
    chat: BaseChatModel  # could also add embeddings, tools, etc.

def create_langchain_chat(settings: LLMSettings) -> LangChainStack:
    if settings.provider == LLMProvider.OPENAI:
        chat = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,  # or rely on env
            temperature=0.2,
        )
    elif settings.provider == LLMProvider.GEMINI:
        chat = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,  # or env GOOGLE_API_KEY
            temperature=0.2,
        )
    else:
        raise ValueError(f"Unsupported provider: {settings.provider}")

    return LangChainStack(chat=chat)
```

Now you have **one place** in the code that knows about “OpenAI vs Gemini”.

---

## 3. Glue it together as a single “stack”

Make a single helper to build both:

```python
# llm_factory.py (continued)

from config import LLMSettings

@dataclass
class LLMStack:
    settings: LLMSettings
    pydantic_ai: PydanticAIStack
    langchain: LangChainStack

def create_llm_stack() -> LLMStack:
    settings = LLMSettings()
    pydantic_stack = create_pydantic_agent(settings)
    langchain_stack = create_langchain_chat(settings)
    return LLMStack(
        settings=settings,
        pydantic_ai=pydantic_stack,
        langchain=langchain_stack,
    )
```

Usage in the rest of your code:

```python
# app.py
from llm_factory import create_llm_stack

llm = create_llm_stack()

# PydanticAI usage
result = llm.pydantic_ai.agent.run_sync("Explain working memory in one paragraph.")
print(result.output)

# LangChain usage
lc_reply = llm.langchain.chat.invoke("Give me three key points about working memory.")
print(lc_reply.content)
```

Switching **Gemini ↔ ChatGPT** is now:

```bash
export LLM_PROVIDER=gemini
export LLM_GOOGLE_API_KEY=...
export LLM_GEMINI_MODEL=gemini-2.0-flash
# or
export LLM_PROVIDER=openai
export LLM_OPENAI_API_KEY=...
export LLM_OPENAI_MODEL=gpt-4.1-mini
```

No other code changes.

---

## 4. Where PydanticAI + LangChain actually meet

One straightforward pattern for you:

* Use **LangChain** for:

  * RAG pipeline
  * vector store integrations
  * retrievers/chains

* Use **PydanticAI** for:

  * tool-rich / agentic behavior
  * strongly typed outputs (Pydantic models)
  * “controller” logic

Example flow:

1. PydanticAI Agent decides *what to do* and calls a Python tool.
2. That tool internally uses a **LangChain Runnable** (with `llm.langchain.chat`) for retrieval or complex prompting.
3. Results come back to the Agent as structured data.

Your “LLMStack” abstraction means both layers always talk to the **same underlying provider**.

---

## 5. Extra niceties you can add later

* Add **embeddings** to `LangChainStack`:

  * `OpenAIEmbeddings` vs `GoogleGenerativeAIEmbeddings`
    And choose based on the same `LLMSettings.provider`.
* Add a **“provider capability”** enum if you start using features that differ (e.g., better tool-calling on Gemini, larger context on certain OpenAI models).
* Wrap common operations (e.g., `semantic_search`, `summarize_docs`) in your own functions that internally call LangChain Runnables but only accept `LLMStack` as a dependency.

---

If you want, I can take one of your actual projects (e.g., your RAG pipeline for psych papers) and show a concrete refactor where:

* PydanticAI is the agent / orchestrator,
* LangChain handles RAG,
* The provider switch is **one config flip**.
