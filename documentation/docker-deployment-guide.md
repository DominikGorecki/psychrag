# PsychRAG Docker Deployment Guide

**Status**: Design Document
**Last Updated**: 2025-12-05

## Overview

This document outlines the complete Docker containerization strategy for the PsychRAG system. The goal is to provide a simple, one-command deployment that runs the entire stack:
- PostgreSQL with pgvector extension
- FastAPI backend (Python)
- Next.js frontend (UI)
- All necessary volumes and networking

## Current Architecture

### Components

1. **Backend API** (FastAPI + Python)
   - Located in: `src/psychrag_api/`
   - Entry point: `psychrag_api.main:app`
   - Port: 8000
   - Dependencies: ~15GB including models (spaCy, transformers, torch)

2. **Frontend UI** (Next.js + React)
   - Located in: `psychrag_ui/`
   - Framework: Next.js 16.0.4
   - Port: 3000
   - Build command: `npm run build && npm start`

3. **Database** (PostgreSQL + pgvector)
   - Database: `psych_rag_test`
   - Users: `postgres` (admin), `psych_rag_app_user_test` (app)
   - Extensions: pgvector for vector embeddings
   - Port: 5432

4. **File Storage**
   - Input directory: raw documents (PDFs, EPUBs)
   - Output directory: converted markdown, processed files
   - Currently configured as local paths

## Proposed Docker Architecture

### Multi-Container Setup with Docker Compose

```yaml
services:
  - postgres:     PostgreSQL 15+ with pgvector extension
  - backend:      Python FastAPI application
  - frontend:     Next.js application (production build)
```

### Container Details

#### 1. PostgreSQL Container

**Base Image**: `pgvector/pgvector:pg15` or `ankane/pgvector:latest`

**Environment Variables**:
- `POSTGRES_DB`: Database name
- `POSTGRES_USER`: Admin user
- `POSTGRES_PASSWORD`: Admin password (from .env)

**Volumes**:
- `postgres_data:/var/lib/postgresql/data` - Persist database
- `./init-scripts:/docker-entrypoint-initdb.d` - Initialization scripts

**Port**: 5432 (internal), not exposed externally

**Initialization**:
- Creates database and app user
- Enables pgvector extension
- Sets up permissions

#### 2. Backend Container

**Base Image**: `python:3.10-slim` or `python:3.11-slim`

**Build Context**: Root directory

**Key Requirements**:
- ~15GB for dependencies (spaCy models, transformers, torch)
- Model downloads on first run (can be cached in volume)
- Python package installation from `pyproject.toml`

**Environment Variables**:
- Database connection (host=postgres)
- API keys (OpenAI, Google)
- Passwords (from .env)

**Volumes**:
- `./data/input:/app/data/input` - Input documents
- `./data/output:/app/data/output` - Processed files
- `model_cache:/root/.cache` - Cache for downloaded models

**Port**: 8000 (internal), not exposed externally

**Health Check**: `curl http://localhost:8000/health`

**Startup Command**: `uvicorn psychrag_api.main:app --host 0.0.0.0 --port 8000`

#### 3. Frontend Container

**Base Image**: `node:20-alpine`

**Build Context**: `./psychrag_ui`

**Build Strategy**: Multi-stage build
- Stage 1: Install dependencies and build
- Stage 2: Production runtime with built assets

**Environment Variables**:
- `NEXT_PUBLIC_API_URL=http://backend:8000` - Backend connection

**Port**: 3000 (exposed externally)

**Startup Command**: `npm start` (production server)

**Note**: Next.js can run in standalone mode for smaller image size

### Network Configuration

```yaml
networks:
  psychrag_net:
    driver: bridge
```

All containers communicate on the same Docker network:
- Frontend → Backend: `http://backend:8000`
- Backend → Database: `postgresql://postgres:5432/psych_rag_test`
- Host → Frontend: `http://localhost:3000`

## Dockerfile Specifications

### Backend Dockerfile

```dockerfile
# Stage 1: Base image with system dependencies
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Stage 2: Install Python dependencies
FROM base as dependencies

# Copy dependency files
COPY pyproject.toml ./

# Install Python packages
RUN pip install --no-cache-dir -e .

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Stage 3: Application
FROM dependencies as application

# Copy source code
COPY src/ ./src/
COPY psychrag.config.json ./

# Create data directories
RUN mkdir -p /app/data/input /app/data/output

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "psychrag_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile

```dockerfile
# Stage 1: Build
FROM node:20-alpine as builder

WORKDIR /app

# Copy package files
COPY psychrag_ui/package.json psychrag_ui/package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY psychrag_ui/ ./

# Build application
RUN npm run build

# Stage 2: Production
FROM node:20-alpine as runner

WORKDIR /app

# Copy necessary files from builder
COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

# Expose port
EXPOSE 3000

# Set environment
ENV NODE_ENV=production
ENV NEXT_PUBLIC_API_URL=http://backend:8000

# Run application
CMD ["npm", "start"]
```

**Alternative**: Use Next.js standalone mode for smaller image:
```dockerfile
# In next.config.js, add:
# output: 'standalone'

# Then in Dockerfile:
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
CMD ["node", "server.js"]
```

## Docker Compose Configuration

### docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg15
    container_name: psychrag-postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-psych_rag_test}
      POSTGRES_USER: ${POSTGRES_ADMIN_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_ADMIN_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/init-db.sh:/docker-entrypoint-initdb.d/init-db.sh
    networks:
      - psychrag_net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: psychrag-backend
    environment:
      # Database configuration
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: ${POSTGRES_DB:-psych_rag_test}
      DB_ADMIN_USER: ${POSTGRES_ADMIN_USER:-postgres}
      DB_APP_USER: ${POSTGRES_APP_USER:-psych_rag_app_user_test}
      POSTGRES_ADMIN_PASSWORD: ${POSTGRES_ADMIN_PASSWORD}
      POSTGRES_APP_PASSWORD: ${POSTGRES_APP_PASSWORD}
      # API Keys
      LLM_OPENAI_API_KEY: ${LLM_OPENAI_API_KEY}
      LLM_GOOGLE_API_KEY: ${LLM_GOOGLE_API_KEY}
    volumes:
      - ./data/input:/app/data/input
      - ./data/output:/app/data/output
      - model_cache:/root/.cache
      - ./psychrag.config.json:/app/psychrag.config.json
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - psychrag_net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    restart: unless-stopped

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    container_name: psychrag-frontend
    environment:
      NEXT_PUBLIC_API_URL: http://backend:8000
      NODE_ENV: production
    ports:
      - "3000:3000"
    depends_on:
      - backend
    networks:
      - psychrag_net
    restart: unless-stopped

volumes:
  postgres_data:
    driver: local
  model_cache:
    driver: local

networks:
  psychrag_net:
    driver: bridge
```

### Database Initialization Script

Create `docker/init-db.sh`:

```bash
#!/bin/bash
set -e

# Enable pgvector extension
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS vector;

    -- Create application user
    CREATE USER ${POSTGRES_APP_USER} WITH PASSWORD '${POSTGRES_APP_PASSWORD}';

    -- Grant privileges
    GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DB} TO ${POSTGRES_APP_USER};
    GRANT ALL ON SCHEMA public TO ${POSTGRES_APP_USER};

    -- Grant sequence and table permissions (tables will be created by SQLAlchemy)
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${POSTGRES_APP_USER};
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ${POSTGRES_APP_USER};
EOSQL

echo "Database initialization completed"
```

Make it executable: `chmod +x docker/init-db.sh`

## Configuration Files

### Environment Variables (.env)

Create `.env` file in root directory:

```bash
# PostgreSQL Configuration
POSTGRES_DB=psych_rag_test
POSTGRES_ADMIN_USER=postgres
POSTGRES_ADMIN_PASSWORD=your_secure_admin_password
POSTGRES_APP_USER=psych_rag_app_user_test
POSTGRES_APP_PASSWORD=your_secure_app_password

# LLM API Keys
LLM_OPENAI_API_KEY=sk-your-openai-key
LLM_GOOGLE_API_KEY=your-google-api-key

# Optional: Override defaults
# DB_HOST=postgres
# DB_PORT=5432
```

### Application Configuration (psychrag.config.json)

Update for Docker environment:

```json
{
  "database": {
    "admin_user": "postgres",
    "host": "postgres",
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

**Note**: The `host` should be `postgres` (container name) instead of `127.0.0.1` or `localhost`.

### .dockerignore

Create `.dockerignore` to optimize build:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.egg-info/
dist/
build/

# Node
node_modules/
.next/
out/
*.log

# Data directories (mounted as volumes)
data/
output/
raw/

# Environment and secrets
.env
.env.local

# IDE
.vscode/
.idea/
*.swp

# Git
.git/
.gitignore

# Documentation
documentation/
docs/

# Tests
tests/
*.pytest_cache/

# OS
.DS_Store
Thumbs.db
```

## Installation and Usage

### Prerequisites

1. **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
   - Download from: https://www.docker.com/products/docker-desktop/
   - Ensure Docker Compose is included (v2.0+)

2. **Minimum System Requirements**:
   - 16GB RAM (32GB recommended)
   - 30GB free disk space
   - Multi-core CPU

3. **API Keys** (at least one):
   - OpenAI API key (for GPT models)
   - Google API key (for Gemini models)

### Quick Start

#### 1. Clone and Configure

```bash
# Clone repository
git clone <repository-url>
cd psychRAG-test

# Copy environment template
cp .env.example .env

# Edit .env and add your credentials
# - Set secure passwords for POSTGRES_ADMIN_PASSWORD and POSTGRES_APP_PASSWORD
# - Add at least one LLM API key (OpenAI or Google)
nano .env  # or use your preferred editor
```

#### 2. Create Data Directories

```bash
# Create host directories for volumes
mkdir -p data/input data/output
```

#### 3. Build and Start Services

```bash
# Build all containers
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

#### 4. Initialize Database

The database will be automatically initialized with pgvector extension and users. To create tables and seed data:

```bash
# Run database initialization
docker-compose exec backend python -m psychrag.data.init_db -v

# Verify initialization
docker-compose exec backend python -m psychrag.data.validate_config_cli
```

#### 5. Access the Application

Open your browser and navigate to:

```
http://localhost:3000
```

The UI will be available, connected to the backend API and database.

### Management Commands

```bash
# View running containers
docker-compose ps

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# Stop services (data persists)
docker-compose stop

# Start services again
docker-compose start

# Restart a specific service
docker-compose restart backend

# Stop and remove containers (data persists in volumes)
docker-compose down

# Stop and remove containers AND volumes (destroys all data)
docker-compose down -v

# Rebuild specific service
docker-compose build backend
docker-compose up -d backend

# Execute commands in containers
docker-compose exec backend bash
docker-compose exec postgres psql -U postgres -d psych_rag_test
docker-compose exec frontend sh

# View resource usage
docker stats
```

### Database Management

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d psych_rag_test

# Backup database
docker-compose exec postgres pg_dump -U postgres psych_rag_test > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T postgres psql -U postgres -d psych_rag_test

# Check pgvector extension
docker-compose exec postgres psql -U postgres -d psych_rag_test -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

### Data Management

```bash
# Add input documents
cp my_document.pdf data/input/

# The files will be available in the backend container at /app/data/input/

# Access output files
ls data/output/

# The processed files are stored in the backend container at /app/data/output/
```

## Implementation Checklist

### Phase 1: Docker Configuration Files
- [ ] Create `Dockerfile.backend`
- [ ] Create `Dockerfile.frontend`
- [ ] Create `docker-compose.yml`
- [ ] Create `docker/init-db.sh`
- [ ] Create `.dockerignore`
- [ ] Update `psychrag.config.json` for Docker networking

### Phase 2: Backend Container
- [ ] Set up Python base image
- [ ] Install system dependencies
- [ ] Install Python packages from `pyproject.toml`
- [ ] Download and cache spaCy models
- [ ] Configure environment variables
- [ ] Set up volume mounts for data directories
- [ ] Add health check endpoint
- [ ] Test container build and startup

### Phase 3: Database Container
- [ ] Select pgvector image
- [ ] Create initialization script
- [ ] Configure environment variables
- [ ] Set up persistent volume
- [ ] Test pgvector extension
- [ ] Test user creation and permissions
- [ ] Verify database connectivity from backend

### Phase 4: Frontend Container
- [ ] Set up Node.js base image
- [ ] Create multi-stage build
- [ ] Install dependencies
- [ ] Build Next.js application
- [ ] Configure API URL environment variable
- [ ] Test container build and startup
- [ ] Verify backend API connectivity

### Phase 5: Integration and Testing
- [ ] Test full stack startup with `docker-compose up`
- [ ] Verify network communication between containers
- [ ] Test database initialization
- [ ] Test API endpoints through frontend
- [ ] Test file upload and processing
- [ ] Test model downloads and caching
- [ ] Verify persistence after container restart
- [ ] Document any issues and solutions

### Phase 6: Documentation and Optimization
- [ ] Create user installation guide
- [ ] Document troubleshooting steps
- [ ] Add development vs production configurations
- [ ] Optimize Docker image sizes
- [ ] Add container resource limits
- [ ] Create backup and restore procedures
- [ ] Test on different platforms (Windows/Mac/Linux)

## Troubleshooting

### Common Issues

#### 1. Backend Container Fails to Start

**Symptoms**: Backend container exits immediately or shows import errors

**Solutions**:
```bash
# Check logs
docker-compose logs backend

# Verify Python installation
docker-compose exec backend python --version

# Check installed packages
docker-compose exec backend pip list

# Reinstall dependencies
docker-compose build --no-cache backend
```

#### 2. Database Connection Refused

**Symptoms**: Backend cannot connect to PostgreSQL

**Solutions**:
```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Verify environment variables
docker-compose exec backend env | grep DB_

# Test connection manually
docker-compose exec backend python -c "from psychrag.data.database import engine; print(engine.url)"
```

#### 3. Frontend Cannot Reach Backend

**Symptoms**: API calls fail with 404 or connection errors

**Solutions**:
```bash
# Verify backend is running
docker-compose ps backend

# Check backend health
curl http://localhost:8000/health  # from host
docker-compose exec frontend curl http://backend:8000/health  # from container

# Verify environment variable
docker-compose exec frontend env | grep NEXT_PUBLIC_API_URL

# Check network
docker network inspect psychrag-test_psychrag_net
```

#### 4. Models Not Downloading

**Symptoms**: Backend fails when trying to use spaCy or transformers models

**Solutions**:
```bash
# Check internet connectivity
docker-compose exec backend ping -c 3 google.com

# Manually download models
docker-compose exec backend python -m spacy download en_core_web_sm

# Check cache volume
docker volume inspect psychrag-test_model_cache

# Increase start period in health check if models are large
```

#### 5. Out of Memory

**Symptoms**: Containers crash or become unresponsive

**Solutions**:
```bash
# Check Docker resource limits
docker stats

# Increase Docker Desktop memory allocation (Settings > Resources)

# Add memory limits to docker-compose.yml:
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 4G
```

#### 6. Port Already in Use

**Symptoms**: Error binding to port 3000

**Solutions**:
```bash
# Check what's using the port
# Windows
netstat -ano | findstr :3000

# Linux/Mac
lsof -i :3000

# Change port in docker-compose.yml:
ports:
  - "3001:3000"  # Host:Container
```

### Debug Mode

Enable verbose logging:

```yaml
# In docker-compose.yml
services:
  backend:
    command: uvicorn psychrag_api.main:app --host 0.0.0.0 --port 8000 --log-level debug
    environment:
      - LOG_LEVEL=DEBUG
```

Access container shells:
```bash
# Backend (Python)
docker-compose exec backend bash

# Frontend (Node)
docker-compose exec frontend sh

# Database
docker-compose exec postgres bash
```

## Advanced Configuration

### Development vs Production

#### Development Mode

Use `docker-compose.dev.yml` for development:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
      target: dependencies  # Stop at dependencies stage
    volumes:
      - ./src:/app/src:ro  # Mount source code for hot reload
      - ./psychrag.config.json:/app/psychrag.config.json
    command: uvicorn psychrag_api.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./psychrag_ui
      dockerfile: Dockerfile.dev
    volumes:
      - ./psychrag_ui/src:/app/src:ro  # Mount source for hot reload
      - ./psychrag_ui/public:/app/public:ro
    command: npm run dev
    ports:
      - "3000:3000"
```

Start development mode:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

#### Production Mode

Add resource limits and security:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 8G
        reservations:
          cpus: '1'
          memory: 4G
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
```

### Scaling

To run multiple backend instances behind a load balancer:

```yaml
services:
  backend:
    deploy:
      replicas: 3

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    ports:
      - "80:80"
    depends_on:
      - backend
```

### Custom Networking

For external database or API gateway:

```yaml
networks:
  psychrag_net:
    external: true
    name: my-existing-network
```

### Environment-Specific Builds

Use build args:

```dockerfile
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim

ARG INSTALL_DEV_DEPS=false
RUN if [ "$INSTALL_DEV_DEPS" = "true" ]; then \
      pip install pytest ruff; \
    fi
```

Build with args:
```bash
docker-compose build --build-arg PYTHON_VERSION=3.12 --build-arg INSTALL_DEV_DEPS=true backend
```

## Security Considerations

### Secrets Management

**Current**: Uses `.env` file (good for development)

**Production Options**:
1. Docker secrets (Swarm mode)
2. External secret manager (HashiCorp Vault, AWS Secrets Manager)
3. Kubernetes secrets (if migrating to K8s)

### Network Isolation

- Database and backend are not exposed to host network
- Only frontend port (3000) is accessible
- Consider adding nginx reverse proxy for SSL/TLS

### User Permissions

- Run containers as non-root user:
```dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```

### Image Scanning

Scan images for vulnerabilities:
```bash
docker scan psychrag-backend:latest
docker scan psychrag-frontend:latest
```

## Performance Optimization

### Build Cache

Use BuildKit for faster builds:
```bash
export DOCKER_BUILDKIT=1
docker-compose build
```

### Layer Optimization

Order Dockerfile commands from least to most frequently changed:
1. System packages
2. Python/Node dependencies
3. Application code

### Multi-Stage Builds

Reduce final image size:
- Frontend: 1GB+ (with build tools) → ~200MB (standalone)
- Backend: Consider using `python:3.11-slim` instead of full Python image

### Volume Performance

Use delegated consistency for mounted volumes on Mac:
```yaml
volumes:
  - ./data:/app/data:delegated
```

## Migration from Current Setup

### For Existing Users

1. **Export existing data**:
```bash
# Backup database
pg_dump -U postgres psych_rag_test > backup.sql

# Copy output files
cp -r output data/output
```

2. **Start Docker stack**:
```bash
docker-compose up -d
```

3. **Import data**:
```bash
# Restore database
cat backup.sql | docker-compose exec -T postgres psql -U postgres -d psych_rag_test

# Verify data
docker-compose exec backend python -m psychrag.data.validate_config_cli
```

4. **Update workflows**:
   - Access UI at `http://localhost:3000` instead of separate backend/frontend
   - File paths remain the same (via volume mounts)
   - No need to manage venv or node_modules

## Future Enhancements

### Orchestration

**Kubernetes**: For production deployments at scale
- Helm charts for easy installation
- Auto-scaling based on load
- Rolling updates with zero downtime
- Integrated monitoring and logging

### Monitoring

Add observability stack:
```yaml
services:
  prometheus:
    image: prom/prometheus

  grafana:
    image: grafana/grafana

  loki:
    image: grafana/loki
```

### CI/CD Integration

Automated builds:
```yaml
# .github/workflows/docker.yml
name: Build and Push Docker Images
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build images
        run: docker-compose build
      - name: Push to registry
        run: docker-compose push
```

### Backup Automation

Scheduled database backups:
```yaml
services:
  backup:
    image: postgres:15
    volumes:
      - ./backups:/backups
      - postgres_data:/var/lib/postgresql/data
    command: >
      bash -c "while true; do
        pg_dump -U postgres -h postgres psych_rag_test > /backups/backup-$$(date +%Y%m%d-%H%M%S).sql
        sleep 86400
      done"
```

## Cost Considerations

### Resource Usage

**Estimated requirements per deployment**:
- CPU: 2-4 cores
- RAM: 8-16 GB
- Storage: 30-50 GB
- Network: Minimal (internal communication)

**Cloud hosting estimates** (monthly):
- AWS EC2 (t3.xlarge): ~$120/month
- Google Cloud (n2-standard-4): ~$140/month
- DigitalOcean (CPU-Optimized 4GB): ~$84/month

### Optimization Tips

1. Use spot/preemptible instances for development
2. Share model cache volume across deployments
3. Use S3/GCS for large file storage instead of volumes
4. Implement caching layers (Redis) for frequently accessed data

## Support and Contribution

### Getting Help

- Check logs: `docker-compose logs -f`
- Review this guide's troubleshooting section
- Open GitHub issue with:
  - Docker version: `docker --version`
  - Docker Compose version: `docker-compose --version`
  - Container logs
  - System specs

### Contributing

Areas for contribution:
- [ ] Windows-specific optimizations
- [ ] ARM64/M1 Mac support
- [ ] Kubernetes manifests
- [ ] Automated testing in containers
- [ ] Performance benchmarks
- [ ] Multi-architecture builds

## Conclusion

This Docker deployment strategy provides:
- ✅ **Simple installation**: Single command to start entire stack
- ✅ **Consistent environment**: Same setup across dev/staging/prod
- ✅ **Easy updates**: Rebuild and restart containers
- ✅ **Data persistence**: Volumes ensure data survives restarts
- ✅ **Isolation**: Services run in separate containers
- ✅ **Scalability**: Easy to add replicas or new services

**Next Steps**:
1. Implement Phase 1 (Docker configuration files)
2. Test on development environment
3. Iterate based on feedback
4. Document platform-specific issues
5. Release as v1.0 with Docker support

---

*This is a living document. Updates and feedback welcome.*
