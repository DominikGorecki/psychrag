# PsychRAG Docker Deployment Guide

**Goal**: Run the entire PsychRAG system in one Docker container with a simple installation.

**Status**: Design Document
**Last Updated**: 2025-12-05
**Preferred LLM**: Gemini

---

## Table of Contents

- [Overview](#overview)
- [Current Architecture](#current-architecture)
- [All-in-One Container Design](#all-in-one-container-design)
- [Implementation Plan](#implementation-plan)
- [What You Need to Do](#what-you-need-to-do)
- [Installation Guide (End User)](#installation-guide-end-user)
- [Alternative: Multi-Container Approach](#alternative-multi-container-approach)

---

## Overview

### What We're Building

A single Docker container that includes:

1. **PostgreSQL 16** with pgvector + Apache AGE extensions (your existing setup)
2. **Python FastAPI backend** for the API server
3. **Next.js frontend** for the web UI
4. **Supervisord** to manage all three processes

### Why Single Container?

- ✅ **Dead simple installation**: `docker run -p 3000:3000 psychrag`
- ✅ **No networking complexity**: Everything runs on localhost inside the container
- ✅ **Easy to share**: Single image to distribute
- ✅ **Perfect for end users**: They don't need to understand Docker Compose

### Trade-offs

- ❌ Larger image size (~8-12GB with all dependencies)
- ❌ Can't scale services independently
- ⚠️ Best for single-user or development use cases
- ℹ️ For production with multiple users, use the multi-container approach (see end of document)

---

## Current Architecture

### What You Have Now

**Existing PostgreSQL Setup** (`c:\code\data\pgvectory\`):

- Custom Dockerfile based on `pgvector/pgvector:pg16`
- Apache AGE extension for graph database capabilities
- Extensions enabled via `enable-extensions.sql`
- Running on port 5432

**Backend** (`src/psychrag_api/`):

- FastAPI application
- Runs on port 8000
- Connects to PostgreSQL
- Requires ~15GB including AI models

**Frontend** (`psychrag_ui/`):

- Next.js 16 application
- Runs on port 3000
- Connects to backend at `localhost:8000`

---

## All-in-One Container Design

### Base Image Strategy

Start from your existing PostgreSQL image and layer everything on top:

```dockerfile
# Start with your existing pgvector + AGE image
FROM pgvector/pgvector:pg16

# Add Python
# Add Node.js
# Add application code
# Add supervisord to run all services
```

### Service Management with Supervisord

Supervisord will manage three processes:

1. **PostgreSQL** - Database service
2. **Uvicorn** - Python FastAPI backend
3. **Next.js** - Frontend server

All services start automatically when container starts.

### Internal Architecture

```
┌─────────────────────────────────────────────────┐
│  Docker Container (psychrag-all-in-one)         │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │ Supervisord (Process Manager)              │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌────────┐│
│  │ PostgreSQL   │  │ FastAPI      │  │Next.js ││
│  │ Port: 5432   │  │ Port: 8000   │  │Port:   ││
│  │ (internal)   │  │ (internal)   │  │3000    ││
│  └──────────────┘  └──────────────┘  └────────┘│
│         ▲                ▲                 ▲     │
│         │                │                 │     │
│         └────localhost───┴─────localhost───┘     │
│                                                  │
└─────────────────────────────────────────────────┘
                       │
                  Port 3000 (exposed)
                       │
                   User Browser
```

### File Structure

```
psychRAG-test/
├── Dockerfile.allinone          # New: Single container Dockerfile
├── supervisord.conf             # New: Process manager config
├── docker-entrypoint.sh         # New: Startup script
├── .env.docker                  # New: Docker-specific env vars
├── psychrag.config.docker.json  # New: Docker-specific config
│
├── src/
│   ├── psychrag/                # Python package
│   └── psychrag_api/            # FastAPI app
│
├── psychrag_ui/                 # Next.js app
│
└── docker/
    ├── init-db.sh               # Database initialization
    └── enable-extensions.sql    # From your pgvectory setup
```

---

## Implementation Plan

### Phase 1: Create Core Files

#### 1.1 Main Dockerfile (`Dockerfile.allinone`)

```dockerfile
# ============================================================================
# Stage 1: Base - PostgreSQL with extensions
# ============================================================================
FROM pgvector/pgvector:pg16 as base

# Install system dependencies for Python, Node.js, and Supervisor
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build tools for AGE extension
    build-essential \
    git \
    ca-certificates \
    libreadline-dev \
    zlib1g-dev \
    flex \
    bison \
    postgresql-server-dev-16 \
    # Python
    python3.11 \
    python3-pip \
    python3-venv \
    python3-dev \
    # Node.js
    curl \
    # Process manager
    supervisor \
    # Utilities
    wget \
    && rm -rf /var/lib/apt/lists/*

# Build and install Apache AGE extension
RUN git clone --depth 1 --branch PG16/v1.5.0-rc0 https://github.com/apache/age.git /tmp/age && \
    cd /tmp/age && \
    make install && \
    rm -rf /tmp/age

# Install Node.js 20.x
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Clean up build dependencies (optional, saves ~500MB)
RUN apt-get purge -y build-essential git postgresql-server-dev-16 flex bison && \
    apt-get autoremove -y

# ============================================================================
# Stage 2: Python Dependencies
# ============================================================================
FROM base as python-deps

WORKDIR /app

# Copy Python requirements
COPY pyproject.toml ./

# Create virtual environment and install Python packages
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir -e .

# Download spaCy model (large, so do it during build)
RUN python -m spacy download en_core_web_sm

# ============================================================================
# Stage 3: Frontend Build
# ============================================================================
FROM python-deps as frontend-build

WORKDIR /app/psychrag_ui

# Copy frontend package files
COPY psychrag_ui/package.json psychrag_ui/package-lock.json ./

# Install Node.js dependencies
RUN npm ci --only=production

# Copy frontend source
COPY psychrag_ui/ ./

# Build Next.js for production
RUN npm run build

# ============================================================================
# Stage 4: Final Application
# ============================================================================
FROM python-deps as final

# Copy backend source code
COPY src/ /app/src/
COPY psychrag.config.docker.json /app/psychrag.config.json

# Copy built frontend from build stage
COPY --from=frontend-build /app/psychrag_ui/.next /app/psychrag_ui/.next
COPY --from=frontend-build /app/psychrag_ui/public /app/psychrag_ui/public
COPY --from=frontend-build /app/psychrag_ui/node_modules /app/psychrag_ui/node_modules
COPY --from=frontend-build /app/psychrag_ui/package.json /app/psychrag_ui/

# Create data directories
RUN mkdir -p /app/data/input /app/data/output /var/log/supervisor

# Copy Docker-specific files
COPY docker/init-db.sh /docker-entrypoint-initdb.d/
COPY docker/enable-extensions.sql /docker-entrypoint-initdb.d/
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh /docker-entrypoint-initdb.d/init-db.sh

# Expose only the frontend port
EXPOSE 3000

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app/src \
    NODE_ENV=production \
    NEXT_PUBLIC_API_URL=http://localhost:8000

# Use custom entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
```

#### 1.2 Supervisord Configuration (`supervisord.conf`)

```ini
[supervisord]
nodaemon=true
user=root
logfile=/var/log/supervisor/supervisord.log
pidfile=/var/run/supervisord.pid

[program:postgresql]
command=/usr/lib/postgresql/16/bin/postgres -D /var/lib/postgresql/data
user=postgres
autostart=true
autorestart=true
priority=1
stdout_logfile=/var/log/supervisor/postgresql.log
stderr_logfile=/var/log/supervisor/postgresql_error.log

[program:backend]
command=/opt/venv/bin/uvicorn psychrag_api.main:app --host 0.0.0.0 --port 8000
directory=/app
user=root
autostart=true
autorestart=true
priority=10
stdout_logfile=/var/log/supervisor/backend.log
stderr_logfile=/var/log/supervisor/backend_error.log
environment=PYTHONPATH="/app/src",PATH="/opt/venv/bin:/usr/local/bin:/usr/bin:/bin"

[program:frontend]
command=npm start
directory=/app/psychrag_ui
user=root
autostart=true
autorestart=true
priority=20
stdout_logfile=/var/log/supervisor/frontend.log
stderr_logfile=/var/log/supervisor/frontend_error.log
environment=NODE_ENV="production",NEXT_PUBLIC_API_URL="http://localhost:8000"
```

#### 1.3 Docker Entrypoint Script (`docker-entrypoint.sh`)

```bash
#!/bin/bash
set -e

# Initialize PostgreSQL data directory if it doesn't exist
if [ ! -s "/var/lib/postgresql/data/PG_VERSION" ]; then
    echo "Initializing PostgreSQL database..."

    # Initialize database cluster
    su - postgres -c "/usr/lib/postgresql/16/bin/initdb -D /var/lib/postgresql/data"

    # Start PostgreSQL temporarily for setup
    su - postgres -c "/usr/lib/postgresql/16/bin/pg_ctl -D /var/lib/postgresql/data -w start"

    # Wait for PostgreSQL to be ready
    until su - postgres -c "psql -U postgres -c '\l'" > /dev/null 2>&1; do
        echo "Waiting for PostgreSQL to start..."
        sleep 1
    done

    # Run initialization scripts
    for f in /docker-entrypoint-initdb.d/*; do
        case "$f" in
            *.sh)     echo "Running $f"; bash "$f" ;;
            *.sql)    echo "Running $f"; su - postgres -c "psql -U postgres < $f" ;;
            *)        echo "Ignoring $f" ;;
        esac
    done

    # Stop PostgreSQL (supervisord will start it properly)
    su - postgres -c "/usr/lib/postgresql/16/bin/pg_ctl -D /var/lib/postgresql/data -m fast -w stop"

    echo "PostgreSQL initialization complete!"
fi

# Execute the main command (supervisord)
exec "$@"
```

#### 1.4 Database Initialization Script (`docker/init-db.sh`)

```bash
#!/bin/bash
set -e

# This runs inside PostgreSQL context during first-time setup

# Create database
psql -v ON_ERROR_STOP=1 --username "postgres" <<-EOSQL
    CREATE DATABASE ${POSTGRES_DB:-psych_rag_test};
EOSQL

# Connect to the new database and set up extensions
psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "${POSTGRES_DB:-psych_rag_test}" <<-EOSQL
    -- Enable pgvector extension
    CREATE EXTENSION IF NOT EXISTS vector;

    -- Enable Apache AGE extension
    CREATE EXTENSION IF NOT EXISTS age;

    -- Load AGE shared library
    LOAD 'age';

    -- Set search path for AGE
    ALTER DATABASE ${POSTGRES_DB:-psych_rag_test} SET search_path = ag_catalog, "\$user", public;

    -- Create application user
    CREATE USER ${POSTGRES_APP_USER:-psych_rag_app_user_test} WITH PASSWORD '${POSTGRES_APP_PASSWORD}';

    -- Grant privileges
    GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DB:-psych_rag_test} TO ${POSTGRES_APP_USER:-psych_rag_app_user_test};
    GRANT ALL ON SCHEMA public TO ${POSTGRES_APP_USER:-psych_rag_app_user_test};

    -- Grant permissions on future objects
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${POSTGRES_APP_USER:-psych_rag_app_user_test};
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ${POSTGRES_APP_USER:-psych_rag_app_user_test};
EOSQL

echo "Database '${POSTGRES_DB:-psych_rag_test}' initialized with pgvector and AGE extensions"
```

#### 1.5 Docker-Specific Configuration (`psychrag.config.docker.json`)

```json
{
  "database": {
    "admin_user": "postgres",
    "host": "localhost",
    "port": 5432,
    "db_name": "psych_rag_test",
    "app_user": "psych_rag_app_user_test"
  },
  "llm": {
    "provider": "gemini",
    "models": {
      "openai": {
        "light": "gpt-4o-mini",
        "full": "gpt-4o"
      },
      "gemini": {
        "light": "gemini-flash-latest",
        "full": "gemini-2.5-pro"
      }
    }
  },
  "paths": {
    "input_dir": "/app/data/input",
    "output_dir": "/app/data/output"
  }
}
```

#### 1.6 Docker Environment Template (`.env.docker`)

```bash
# PostgreSQL Configuration
POSTGRES_DB=psych_rag_test
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_APP_USER=psych_rag_app_user_test
POSTGRES_APP_PASSWORD=your_secure_app_password_here

# LLM API Keys
LLM_GOOGLE_API_KEY=your_google_api_key_here
LLM_OPENAI_API_KEY=your_openai_api_key_here
```

#### 1.7 Copy Extensions SQL (`docker/enable-extensions.sql`)

Copy from your existing setup:

```bash
cp c:\code\data\pgvectory\enable-extensions.sql docker/enable-extensions.sql
```

### Phase 2: Build and Test

#### 2.1 Create Docker Directory

```bash
cd c:\code\python\psychRAG-test
mkdir docker
```

#### 2.2 Build the Image

```bash
docker build -f Dockerfile.allinone -t psychrag:latest .
```

**Expected build time**: 15-30 minutes (downloading and compiling dependencies)

**Expected image size**: 8-12 GB

#### 2.3 Run the Container

```bash
docker run -d \
  --name psychrag \
  -p 3000:3000 \
  -v psychrag_data:/var/lib/postgresql/data \
  -v ./data/input:/app/data/input \
  -v ./data/output:/app/data/output \
  --env-file .env.docker \
  psychrag:latest
```

#### 2.4 Verify Services

```bash
# Check all services are running
docker exec psychrag supervisorctl status

# Expected output:
# postgresql    RUNNING   pid 10, uptime 0:01:23
# backend       RUNNING   pid 45, uptime 0:01:15
# frontend      RUNNING   pid 67, uptime 0:01:10

# Check logs
docker logs psychrag
docker exec psychrag tail -f /var/log/supervisor/backend.log
docker exec psychrag tail -f /var/log/supervisor/frontend.log

# Test the UI
# Open browser: http://localhost:3000
```

### Phase 3: Initialize Application

```bash
# Run database initialization from inside container
docker exec psychrag /opt/venv/bin/python -m psychrag.data.init_db -v

# Verify configuration
docker exec psychrag /opt/venv/bin/python -m psychrag.data.validate_config_cli
```

---

## What You Need to Do

Here's your step-by-step implementation guide:

### Step 1: Prepare Directory Structure

```bash
cd c:\code\python\psychRAG-test

# Create docker directory
mkdir docker

# Copy your extension SQL
cp c:\code\data\pgvectory\enable-extensions.sql docker\enable-extensions.sql
```

### Step 2: Create Configuration Files

Create these 7 new files in your project root:

1. **`Dockerfile.allinone`** - Main container definition (see Phase 1.1)
2. **`supervisord.conf`** - Process manager config (see Phase 1.2)
3. **`docker-entrypoint.sh`** - Startup script (see Phase 1.3)
4. **`docker/init-db.sh`** - Database setup (see Phase 1.4)
5. **`psychrag.config.docker.json`** - Docker config (see Phase 1.5)
6. **`.env.docker`** - Environment variables (see Phase 1.6)
7. **`.dockerignore`** - Build optimization (see below)

### Step 3: Create .dockerignore

Create `.dockerignore` in project root:

```
# Python
__pycache__/
*.py[cod]
venv/
*.egg-info/

# Node
node_modules/
.next/

# Data (will be mounted as volumes)
data/
output/
raw/

# Secrets
.env
.env.local

# Development
.git/
.vscode/
tests/
documentation/
```

### Step 4: Update Next.js Config for Standalone Build (Optional)

Edit `psychrag_ui/next.config.js`:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',  // Add this line
  // ... rest of your config
};

module.exports = nextConfig;
```

If using standalone, update Dockerfile section:

```dockerfile
# Copy built frontend (standalone version)
COPY --from=frontend-build /app/psychrag_ui/.next/standalone /app/psychrag_ui
COPY --from=frontend-build /app/psychrag_ui/.next/static /app/psychrag_ui/.next/static
COPY --from=frontend-build /app/psychrag_ui/public /app/psychrag_ui/public
```

### Step 5: Build the Image

```bash
# Build (takes 15-30 minutes first time)
docker build -f Dockerfile.allinone -t psychrag:latest .

# Watch the build process
# It will:
# 1. Install PostgreSQL base
# 2. Compile Apache AGE extension
# 3. Install Python dependencies (~15GB)
# 4. Download spaCy model
# 5. Install Node.js dependencies
# 6. Build Next.js frontend
# 7. Assemble final image
```

### Step 6: Test Run

```bash
# Create data directories
mkdir -p data\input data\output

# Edit .env.docker with your API keys
notepad .env.docker

# Run container
docker run -d ^
  --name psychrag ^
  -p 3000:3000 ^
  -v psychrag_data:/var/lib/postgresql/data ^
  -v %cd%\data\input:/app/data/input ^
  -v %cd%\data\output:/app/data/output ^
  --env-file .env.docker ^
  psychrag:latest

# Check status
docker ps
docker logs psychrag

# Initialize database
docker exec psychrag /opt/venv/bin/python -m psychrag.data.init_db -v

# Access the UI
start http://localhost:3000
```

### Step 7: Create Distribution Package (Optional)

Once working, save the image for distribution:

```bash
# Save image to file
docker save psychrag:latest | gzip > psychrag-v1.0.tar.gz

# Users can load it with:
# docker load -i psychrag-v1.0.tar.gz
```

---

## Installation Guide (End User)

This is what you'll share with users who want to run PsychRAG:

### Prerequisites

1. **Docker Desktop** installed
   - Windows: https://docs.docker.com/desktop/install/windows-install/
   - Mac: https://docs.docker.com/desktop/install/mac-install/
   - Linux: https://docs.docker.com/engine/install/

2. **System Requirements**:
   - 16GB RAM minimum (32GB recommended)
   - 30GB free disk space
   - Modern multi-core CPU

3. **API Keys**:
   - Google Gemini API key (recommended): https://ai.google.dev/
   - OR OpenAI API key: https://platform.openai.com/api-keys

### Quick Start

#### Option A: Load Pre-built Image

```bash
# 1. Load the Docker image
docker load -i psychrag-v1.0.tar.gz

# 2. Create data directories
mkdir -p data/input data/output

# 3. Create .env file
cat > .env.docker << EOF
POSTGRES_PASSWORD=change_this_password
POSTGRES_APP_PASSWORD=change_this_password_too
LLM_GOOGLE_API_KEY=your_gemini_api_key_here
EOF

# 4. Run PsychRAG
docker run -d \
  --name psychrag \
  -p 3000:3000 \
  -v psychrag_data:/var/lib/postgresql/data \
  -v $(pwd)/data/input:/app/data/input \
  -v $(pwd)/data/output:/app/data/output \
  --env-file .env.docker \
  psychrag:latest

# 5. Initialize database (first time only)
docker exec psychrag /opt/venv/bin/python -m psychrag.data.init_db -v

# 6. Open browser
# Navigate to: http://localhost:3000
```

#### Option B: Build from Source

```bash
# 1. Clone repository
git clone <repository-url>
cd psychRAG-test

# 2. Create .env.docker with your API keys
cp .env.docker.example .env.docker
# Edit .env.docker with your credentials

# 3. Build image
docker build -f Dockerfile.allinone -t psychrag:latest .

# 4. Run (same as Option A steps 4-6)
```

### Managing PsychRAG

```bash
# Stop PsychRAG
docker stop psychrag

# Start PsychRAG again
docker start psychrag

# View logs
docker logs -f psychrag

# Access shell (for troubleshooting)
docker exec -it psychrag bash

# Remove container (data persists in volume)
docker rm psychrag

# Remove everything including data
docker rm psychrag
docker volume rm psychrag_data
```

### Adding Documents

```bash
# Copy PDF to input directory
cp my_document.pdf data/input/

# Access PsychRAG UI
# Go to: http://localhost:3000
# Navigate to Conversion tab
# Process your document
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs psychrag

# Check individual services
docker exec psychrag supervisorctl status

# Restart specific service
docker exec psychrag supervisorctl restart backend
docker exec psychrag supervisorctl restart frontend
docker exec psychrag supervisorctl restart postgresql
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker exec psychrag supervisorctl status postgresql

# Test connection
docker exec psychrag psql -U postgres -d psych_rag_test -c "SELECT version();"

# Check extensions
docker exec psychrag psql -U postgres -d psych_rag_test -c "SELECT * FROM pg_extension;"
```

### Backend API Not Responding

```bash
# Check backend logs
docker exec psychrag tail -f /var/log/supervisor/backend.log
docker exec psychrag tail -f /var/log/supervisor/backend_error.log

# Test API endpoint
docker exec psychrag curl http://localhost:8000/health

# Restart backend
docker exec psychrag supervisorctl restart backend
```

### Frontend Issues

```bash
# Check frontend logs
docker exec psychrag tail -f /var/log/supervisor/frontend.log

# Verify API connection
docker exec psychrag curl http://localhost:8000/health

# Restart frontend
docker exec psychrag supervisorctl restart frontend
```

### Out of Memory

```bash
# Check resource usage
docker stats psychrag

# Increase Docker Desktop memory
# Settings > Resources > Memory > 16GB or higher
```

---

## Alternative: Multi-Container Approach

For production deployments or when you need to scale services independently, use the multi-container approach with Docker Compose.

### Quick Overview

```yaml
# docker-compose.yml
services:
  postgres:
    # Your existing pgvectory setup

  backend:
    # Python FastAPI container

  frontend:
    # Next.js container
```

See the original sections "Approach 2: Multi-Container Setup" below for full implementation.

### When to Use Multi-Container

- ✅ Production deployment with multiple users
- ✅ Need to scale backend independently
- ✅ Want to update services without rebuilding everything
- ✅ Running on cloud infrastructure (AWS, GCP, Azure)

### When to Use All-in-One

- ✅ Development environment
- ✅ Single-user installation
- ✅ Easy distribution to end users
- ✅ Simplicity is priority

---

## Next Steps

### Immediate Tasks

1. **Create the 7 configuration files** listed in "What You Need to Do"
2. **Build the Docker image** (will take 20-30 minutes)
3. **Test locally** to ensure all services start correctly
4. **Document any issues** you encounter for troubleshooting section

### Future Enhancements

- [ ] Add health check endpoint that verifies all services
- [ ] Create GitHub Actions workflow for automated builds
- [ ] Add docker-compose.yml for easier volume management
- [ ] Create installation wizard for first-time setup
- [ ] Add backup/restore scripts
- [ ] Optimize image size (currently ~10GB, can reduce to ~8GB)
- [ ] Add support for GPU acceleration (for model inference)
- [ ] Create Kubernetes manifests for cloud deployment

### Distribution

Once tested and working:

1. **Push to Docker Hub**:
   ```bash
   docker tag psychrag:latest yourusername/psychrag:latest
   docker push yourusername/psychrag:latest
   ```

2. **Create releases**:
   - Version tags: `v1.0.0`, `v1.1.0`, etc.
   - Save images: `docker save psychrag:v1.0.0 > psychrag-v1.0.0.tar.gz`
   - GitHub releases with installation instructions

3. **Documentation**:
   - Create user guide with screenshots
   - Video walkthrough of installation
   - Troubleshooting FAQ

---

## Summary

### What This Gives You

**Single Command Installation**:

```bash
docker run -p 3000:3000 -v psychrag_data:/var/lib/postgresql/data --env-file .env psychrag:latest
```

**Everything Included**:

- ✅ PostgreSQL 16 with pgvector + Apache AGE
- ✅ Python FastAPI backend with all dependencies
- ✅ Next.js frontend pre-built
- ✅ All services auto-start and auto-restart
- ✅ Data persistence via Docker volumes

**User Experience**:

- No Python environment setup
- No Node.js installation
- No manual database configuration
- Just Docker + API keys = Running system

---

## Questions?

Before implementation, clarify:

1. **Do you want standalone mode for Next.js?** (smaller image, faster startup)
2. **Should we cache AI models in the image?** (larger image but faster first run)
3. **Do you want both single-container and multi-container options?** (more work but flexible)
4. **Target distribution method?** (Docker Hub, file download, private registry)

Let me know and I'll adjust the implementation plan accordingly!
