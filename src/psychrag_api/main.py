"""
PsychRAG API - Main FastAPI Application.

Usage:
    # Development server with auto-reload
    venv\\Scripts\\uvicorn psychrag_api.main:app --reload

    # Production server
    venv\\Scripts\\uvicorn psychrag_api.main:app --host 0.0.0.0 --port 8000

Interactive Documentation:
    Swagger UI: http://localhost:8000/docs
    ReDoc:      http://localhost:8000/redoc
    OpenAPI:    http://localhost:8000/openapi.json
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from psychrag_api.config import get_settings
from psychrag_api.routers import (
    chunking,
    conversion,
    corpus,
    init,
    rag,
    sanitization,
    settings,
    templates,
    vectorization,
)

settings_config = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events for startup/shutdown."""
    # Startup
    print("PsychRAG API starting up...")
    yield
    # Shutdown
    print("PsychRAG API shutting down...")


# Create FastAPI application with comprehensive OpenAPI configuration
app = FastAPI(
    title=settings_config.api_title,
    description=settings_config.api_description,
    version=settings_config.api_version,
    lifespan=lifespan,
    # OpenAPI configuration
    openapi_url="/openapi.json",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    # OpenAPI tags for organization
    openapi_tags=[
        {
            "name": "Init",
            "description": "Initialization and setup operations. Database setup, system health checks.",
        },
        {
            "name": "Settings",
            "description": "Configuration and settings management. View and modify system settings.",
        },
        {
            "name": "Conversion",
            "description": "Document conversion operations. Convert EPUBs, PDFs to markdown format.",
        },
        {
            "name": "Sanitization",
            "description": "Content sanitization operations. Clean, normalize, and validate content.",
        },
        {
            "name": "Chunking",
            "description": "Document chunking operations. Split documents into semantic chunks.",
        },
        {
            "name": "Vectorization",
            "description": "Vectorization operations. Generate embeddings for document chunks.",
        },
        {
            "name": "Corpus",
            "description": "Corpus management. Read-only access to works with completed chunking.",
        },
        {
            "name": "RAG",
            "description": "Retrieval, Augmentation and Generation. Query documents and generate responses.",
        },
    ],
    # Additional metadata
    contact={
        "name": "PsychRAG Team",
    },
    license_info={
        "name": "MIT",
    },
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings_config.cors_origins,
    allow_credentials=settings_config.cors_allow_credentials,
    allow_methods=settings_config.cors_allow_methods,
    allow_headers=settings_config.cors_allow_headers,
)

# Include routers with prefixes
app.include_router(init.router, prefix="/init", tags=["Init"])
app.include_router(settings.router, prefix="/settings", tags=["Settings"])
app.include_router(templates.router)  # Templates router has its own prefix
app.include_router(conversion.router, prefix="/conv", tags=["Conversion"])
app.include_router(sanitization.router, prefix="/sanitization", tags=["Sanitization"])
app.include_router(chunking.router, prefix="/chunk", tags=["Chunking"])
app.include_router(vectorization.router, prefix="/vec", tags=["Vectorization"])
app.include_router(corpus.router, prefix="/corpus", tags=["Corpus"])
app.include_router(rag.router, prefix="/rag", tags=["RAG"])


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - redirect info to docs."""
    return {
        "message": "Welcome to PsychRAG API",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
    }


@app.get("/health", tags=["Init"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "version": settings_config.api_version}

