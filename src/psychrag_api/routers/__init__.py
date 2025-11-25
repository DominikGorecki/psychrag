"""
API Routers package.

Each router handles a specific group of endpoints:
    - init: Initialization and setup
    - settings: Configuration management
    - conversion: Document conversion
    - sanitization: Content sanitization
    - chunking: Document chunking
    - vectorization: Embedding generation
    - rag: Retrieval and generation
"""

from psychrag_api.routers import (
    chunking,
    conversion,
    init,
    rag,
    sanitization,
    settings,
    vectorization,
)

__all__ = [
    "init",
    "settings",
    "conversion",
    "sanitization",
    "chunking",
    "vectorization",
    "rag",
]


