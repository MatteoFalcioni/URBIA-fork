# GitHub Actions CI/CD Setup Guide

This guide will walk you through setting up GitHub Actions for your LG-Urban project.

## 📋 What the Workflow Does

The CI/CD pipeline includes:

1. **Change Detection**: Only runs relevant tests based on what files changed
2. **Modal Function Tests**: Tests your Modal runtime integration
3. **Database Migration Tests**: Validates Alembic migrations with Docker Postgres
4. **API Health Tests**: Tests core API endpoints
5. **Code Linting**: Checks code quality with ruff and black
6. **Automatic Modal Deployment**: Deploys Modal functions when changes are pushed to main


## 🧪 Test Locally (Optional but Recommended)

Before pushing to GitHub, you can test parts of the workflow locally:

### Test API endpoints with local Docker Postgres:

```bash
# Start Postgres
cd infra
docker compose up -d db

# Wait for it to be ready
docker exec chat_pg pg_isready -U postgres

# Run migrations
cd ..
export ALEMBIC_DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/chat"
alembic upgrade head

# Run API tests
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/chat"
pytest tests/api/ -v

# Cleanup
cd infra
docker compose down -v
```

### Test Modal functions:

```bash
# Make sure you have Modal tokens in .env
export MODAL_TOKEN_ID="your-token-id"
export MODAL_TOKEN_SECRET="your-token-secret"

# Run Modal tests
pytest backend/modal_runtime/tests/ -v
```

### Test migrations:

```bash
cd infra
docker compose up -d db

# Wait and run migrations
cd ..
export ALEMBIC_DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/chat"
alembic upgrade head
alembic current

# Test downgrade/upgrade cycle
alembic downgrade -1
alembic upgrade head

# Cleanup
cd infra
docker compose down -v
```

## 🎯 How Different Triggers Work

### On Pull Request:
- ✅ Runs tests for changed components only
- ❌ Does NOT deploy to Modal
- Fast feedback for code review

### On Push to Main:
- ✅ Runs all tests
- ✅ Deploys Modal functions (only if Modal files changed)
- ✅ Railway auto-deploys backend (separate from this workflow)

## 🔧 Workflow Behavior

### Smart Change Detection

The workflow only runs tests for the parts you changed:

- **Modal tests** run if: `backend/modal_runtime/**` changed
- **Migration tests** run if: `backend/db/alembic/versions/**` or `backend/db/models.py` changed
- **API tests** run if: `backend/**` or `requirements.txt` changed
- **All tests** run on push to main (safety check)

### Modal Deployment

Modal functions are deployed **only when**:
1. Push is to `main` branch (not PRs)
2. Files in `backend/modal_runtime/` have changed
3. All Modal tests pass

This prevents unnecessary deployments and keeps Modal in sync with your backend.

## 🐛 Troubleshooting

### "Modal tokens not configured"

Add `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` to GitHub secrets.

### "Migration tests failing"

Check that your migration files are valid:
```bash
alembic check  # locally
```

### "API tests failing"

Ensure the database schema is up to date:
- Check if you need to create a new migration
- Verify all models are properly imported in `backend/db/models.py`

### "Workflow not appearing"

- Make sure the file is at `.github/workflows/ci-cd.yml`
- Check for YAML syntax errors: https://www.yamllint.com/

### "Docker Compose failing in CI"

The workflow uses `infra/docker-compose.yml`. If you change the compose file, make sure it still works with default values (no custom .env needed in CI).

