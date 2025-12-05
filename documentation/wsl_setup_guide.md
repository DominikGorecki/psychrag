# Running PsychRAG in WSL (Windows Subsystem for Linux)

This guide outlines the steps to set up and run the PsychRAG solution within a WSL environment (e.g., Ubuntu).

## 1. System Dependencies used by PsychRAG

Before installing the Python project, ensure your WSL instance has the necessary system packages.

```bash
sudo apt update
sudo apt install python3-venv python3-pip python3-dev libpq-dev build-essential
```

## 2. Database Setup (PostgreSQL)

PsychRAG requires PostgreSQL with the `pgvector` extension.

### Install PostgreSQL
```bash
# Install Postgres
sudo apt install postgresql postgresql-contrib
```

### Install pgvector Extension
You need to install the vector extension for your specific Postgres version (check with `psql --version`).
```bash
# Example for PostgreSQL 16 (adjust version number as needed)
# You may need to add the pgdg repository first if this package isn't found
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh
sudo apt update
sudo apt install postgresql-16-pgvector
```

### Start the Service
In WSL, services often don't start automatically.
```bash
sudo service postgresql start
```

### Create User and Database
Create a user and database matching your `psychrag.config.json` (or update the config to match this).

```bash
# Switch to postgres user
sudo -i -u postgres

# Create user (prompt for password)
createuser --interactive --pwprompt
# > Enter name of role to add: psych_rag_app_user_test
# > Enter password for new role: [YOUR_PASSWORD]
# > Shall the new role be a superuser? n
# > Shall the new role be allowed to create databases? y
# > Shall the new role be allowed to create more new roles? n

# Create database
createdb -O psych_rag_app_user_test psych_rag_test

# Enable pgvector extension
psql -d psych_rag_test -c "CREATE EXTENSION vector;"

# Exit postgres user session
exit
```

## 3. Project Setup

### Virtual Environment
```bash
# Create venv
python3 -m venv venv

# Activate venv
source venv/bin/activate
```

### Install Project Dependencies
```bash
# Install in editable mode
pip install -e .
```
*Note: This might take a few minutes as it downloads large dependencies (Torch, etc).*

## 4. Configuration

### Environment Variables
Create your secrets file:
```bash
cp .env.example .env
nano .env
```
Update `POSTGRES_APP_PASSWORD` with the password you created in step 2.

### Validate Config
Run the validation tool to ensure everything is connected:
```bash
python -m psychrag.data.validate_config_cli
```

### Initialize Database Schema
```bash
python -m psychrag.data.init_db -v
```

## 5. Running the Application

### Start the API Server
```bash
uvicorn psychrag_api.main:app --reload
```

### Running Tests
```bash
pytest
```

## Troubleshooting WSL Specifics

*   **Service Status**: heavy I/O in WSL can sometimes cause services to hiccup. Always check `sudo service postgresql status` if DB connection fails.
*   **Memory**: AI models (Torch, Transformers) can consume significant RAM. Ensure your `.wslconfig` (in Windows user profile) permits enough memory for WSL if you run into OOM errors.
