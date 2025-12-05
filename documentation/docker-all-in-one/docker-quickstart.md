# Docker Deployment - Quick Start Guide

This is a simplified guide to get you started. For full details, see [docker-deployment-guide.md](docker-deployment-guide.md).

## What You're Building

A **single Docker container** that includes everything:
- PostgreSQL 16 + pgvector + Apache AGE (from your existing setup)
- Python FastAPI backend
- Next.js frontend
- Supervisord (manages all 3 services)

**Result**: Users run one command and get the entire system running.

---

## Step-by-Step Implementation

### Step 1: Create Docker Directory

```bash
cd c:\code\python\psychRAG-test
mkdir docker
```

### Step 2: Copy Your PostgreSQL Extensions File

```bash
copy c:\code\data\pgvectory\enable-extensions.sql docker\enable-extensions.sql
```

### Step 3: Create These 7 New Files

#### 1. `.dockerignore` (in project root)

```
__pycache__/
*.py[cod]
venv/
*.egg-info/
node_modules/
.next/
data/
output/
raw/
.env
.env.local
.git/
.vscode/
tests/
documentation/
```

#### 2. `Dockerfile.allinone` (in project root)

```dockerfile
# Base: PostgreSQL with pgvector
FROM pgvector/pgvector:pg16 as base

# Install Python, Node.js, Supervisor
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git ca-certificates libreadline-dev zlib1g-dev flex bison \
    postgresql-server-dev-16 \
    python3.11 python3-pip python3-venv python3-dev \
    curl supervisor wget \
    && rm -rf /var/lib/apt/lists/*

# Install Apache AGE extension
RUN git clone --depth 1 --branch PG16/v1.5.0-rc0 https://github.com/apache/age.git /tmp/age && \
    cd /tmp/age && make install && rm -rf /tmp/age

# Install Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && rm -rf /var/lib/apt/lists/*

# Clean up to save space
RUN apt-get purge -y build-essential git postgresql-server-dev-16 flex bison && \
    apt-get autoremove -y

# Python dependencies
FROM base as python-deps
WORKDIR /app
COPY pyproject.toml ./
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -e .
RUN python -m spacy download en_core_web_sm

# Frontend build
FROM python-deps as frontend-build
WORKDIR /app/psychrag_ui
COPY psychrag_ui/package.json psychrag_ui/package-lock.json ./
RUN npm ci --only=production
COPY psychrag_ui/ ./
RUN npm run build

# Final image
FROM python-deps as final
COPY src/ /app/src/
COPY psychrag.config.docker.json /app/psychrag.config.json
COPY --from=frontend-build /app/psychrag_ui/.next /app/psychrag_ui/.next
COPY --from=frontend-build /app/psychrag_ui/public /app/psychrag_ui/public
COPY --from=frontend-build /app/psychrag_ui/node_modules /app/psychrag_ui/node_modules
COPY --from=frontend-build /app/psychrag_ui/package.json /app/psychrag_ui/

RUN mkdir -p /app/data/input /app/data/output /var/log/supervisor

COPY docker/init-db.sh /docker-entrypoint-initdb.d/
COPY docker/enable-extensions.sql /docker-entrypoint-initdb.d/
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh /docker-entrypoint-initdb.d/init-db.sh

EXPOSE 3000

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app/src \
    NODE_ENV=production \
    NEXT_PUBLIC_API_URL=http://localhost:8000

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
```

#### 3. `supervisord.conf` (in project root)

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

#### 4. `docker-entrypoint.sh` (in project root)

```bash
#!/bin/bash
set -e

if [ ! -s "/var/lib/postgresql/data/PG_VERSION" ]; then
    echo "Initializing PostgreSQL database..."

    su - postgres -c "/usr/lib/postgresql/16/bin/initdb -D /var/lib/postgresql/data"
    su - postgres -c "/usr/lib/postgresql/16/bin/pg_ctl -D /var/lib/postgresql/data -w start"

    until su - postgres -c "psql -U postgres -c '\l'" > /dev/null 2>&1; do
        echo "Waiting for PostgreSQL to start..."
        sleep 1
    done

    for f in /docker-entrypoint-initdb.d/*; do
        case "$f" in
            *.sh)     echo "Running $f"; bash "$f" ;;
            *.sql)    echo "Running $f"; su - postgres -c "psql -U postgres < $f" ;;
            *)        echo "Ignoring $f" ;;
        esac
    done

    su - postgres -c "/usr/lib/postgresql/16/bin/pg_ctl -D /var/lib/postgresql/data -m fast -w stop"

    echo "PostgreSQL initialization complete!"
fi

exec "$@"
```

#### 5. `docker/init-db.sh`

```bash
#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "postgres" <<-EOSQL
    CREATE DATABASE ${POSTGRES_DB:-psych_rag_test};
EOSQL

psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "${POSTGRES_DB:-psych_rag_test}" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE EXTENSION IF NOT EXISTS age;
    LOAD 'age';
    ALTER DATABASE ${POSTGRES_DB:-psych_rag_test} SET search_path = ag_catalog, "\$user", public;

    CREATE USER ${POSTGRES_APP_USER:-psych_rag_app_user_test} WITH PASSWORD '${POSTGRES_APP_PASSWORD}';
    GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DB:-psych_rag_test} TO ${POSTGRES_APP_USER:-psych_rag_app_user_test};
    GRANT ALL ON SCHEMA public TO ${POSTGRES_APP_USER:-psych_rag_app_user_test};
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${POSTGRES_APP_USER:-psych_rag_app_user_test};
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ${POSTGRES_APP_USER:-psych_rag_app_user_test};
EOSQL

echo "Database initialized with pgvector and AGE extensions"
```

#### 6. `psychrag.config.docker.json` (in project root)

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

#### 7. `.env.docker` (in project root)

```bash
# PostgreSQL Configuration
POSTGRES_DB=psych_rag_test
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_APP_USER=psych_rag_app_user_test
POSTGRES_APP_PASSWORD=your_secure_app_password_here

# LLM API Keys (at least one required)
LLM_GOOGLE_API_KEY=your_google_api_key_here
LLM_OPENAI_API_KEY=your_openai_api_key_here
```

### Step 4: Build the Docker Image

```bash
docker build -f Dockerfile.allinone -t psychrag:latest .
```

**Note**: This will take 20-30 minutes and create an ~8-10GB image.

### Step 5: Test Run

```bash
# Create data directories
mkdir data\input
mkdir data\output

# Edit .env.docker with your real API keys
notepad .env.docker

# Run container (Windows)
docker run -d ^
  --name psychrag ^
  -p 3000:3000 ^
  -v psychrag_data:/var/lib/postgresql/data ^
  -v %cd%\data\input:/app/data/input ^
  -v %cd%\data\output:/app/data/output ^
  --env-file .env.docker ^
  psychrag:latest

# Check if services are running
docker exec psychrag supervisorctl status

# Initialize database (first time only)
docker exec psychrag /opt/venv/bin/python -m psychrag.data.init_db -v

# Open browser
start http://localhost:3000
```

---

## File Structure After Implementation

```
psychRAG-test/
├── Dockerfile.allinone          ← NEW
├── supervisord.conf             ← NEW
├── docker-entrypoint.sh         ← NEW
├── .env.docker                  ← NEW
├── .dockerignore                ← NEW
├── psychrag.config.docker.json  ← NEW
│
├── docker/
│   ├── init-db.sh               ← NEW
│   └── enable-extensions.sql    ← COPIED from pgvectory
│
├── src/
│   ├── psychrag/
│   └── psychrag_api/
│
└── psychrag_ui/
```

---

## Quick Commands Reference

### Build
```bash
docker build -f Dockerfile.allinone -t psychrag:latest .
```

### Run
```bash
docker run -d --name psychrag -p 3000:3000 \
  -v psychrag_data:/var/lib/postgresql/data \
  --env-file .env.docker \
  psychrag:latest
```

### Check Status
```bash
docker ps
docker logs psychrag
docker exec psychrag supervisorctl status
```

### Troubleshoot
```bash
# View service logs
docker exec psychrag tail -f /var/log/supervisor/backend.log
docker exec psychrag tail -f /var/log/supervisor/frontend.log
docker exec psychrag tail -f /var/log/supervisor/postgresql.log

# Restart a service
docker exec psychrag supervisorctl restart backend
docker exec psychrag supervisorctl restart frontend

# Get shell access
docker exec -it psychrag bash
```

### Stop/Start
```bash
docker stop psychrag
docker start psychrag
docker restart psychrag
```

### Clean Up
```bash
# Remove container (keeps data)
docker rm psychrag

# Remove container and data
docker rm psychrag
docker volume rm psychrag_data
```

---

## Distribution

Once tested and working, you can share it:

### Option 1: Save to File
```bash
docker save psychrag:latest | gzip > psychrag-v1.0.tar.gz
```

Users load it with:
```bash
docker load -i psychrag-v1.0.tar.gz
```

### Option 2: Push to Docker Hub
```bash
docker tag psychrag:latest yourusername/psychrag:latest
docker push yourusername/psychrag:latest
```

Users pull it with:
```bash
docker pull yourusername/psychrag:latest
```

---

## Common Issues

### Build Fails at Python Dependencies
- **Cause**: Not enough disk space
- **Fix**: Free up at least 20GB before building

### Container Exits Immediately
- **Cause**: Missing environment variables
- **Fix**: Check `.env.docker` has all required values

### Frontend Can't Connect to Backend
- **Cause**: Services not started yet
- **Fix**: Wait 30-60 seconds after container starts, check logs

### Database Connection Refused
- **Cause**: PostgreSQL hasn't initialized
- **Fix**: Check logs: `docker exec psychrag supervisorctl status postgresql`

### Out of Memory
- **Cause**: Docker Desktop memory limit too low
- **Fix**: Increase to 16GB in Docker Desktop settings

---

## Next Steps

1. ✅ Create all 7 files listed above
2. ✅ Build the Docker image
3. ✅ Test locally with real API keys
4. ✅ Document any issues you encounter
5. 🚀 Share with users!

For detailed explanations, troubleshooting, and advanced configurations, see the full [docker-deployment-guide.md](docker-deployment-guide.md).
