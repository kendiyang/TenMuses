#!/usr/bin/env bash
set -euo pipefail

# Usage: RUN_LANGGRAPH_INTEGRATION=1 OPENAI_API_KEY=... ./scripts/run-integration.sh
# This script runs the integration tests locally. It can auto-start Postgres/Redis/MinIO via Docker or use existing services.

# Optionally load variables from .env.integration if present
if [ -f .env.integration ]; then
  echo "Loading .env.integration"
  # shellcheck disable=SC1091
  source .env.integration
fi

# Configuration (override via env or .env.integration)
POSTGRES_CONTAINER=${POSTGRES_CONTAINER:-tenmuses-integration-db}
POSTGRES_IMAGE=${POSTGRES_IMAGE:-postgres:15}
REDIS_CONTAINER=${REDIS_CONTAINER:-tenmuses-integration-redis}
REDIS_IMAGE=${REDIS_IMAGE:-redis:7}
MINIO_CONTAINER=${MINIO_CONTAINER:-tenmuses-integration-minio}
MINIO_IMAGE=${MINIO_IMAGE:-minio/minio:latest}
MINIO_ROOT_USER=${MINIO_ROOT_USER:-minioadmin}
MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD:-minioadmin}

if [ -z "${RUN_LANGGRAPH_INTEGRATION:-}" ]; then
  echo "RUN_LANGGRAPH_INTEGRATION not set; skipping. Set RUN_LANGGRAPH_INTEGRATION=1 to run integrations."
  exit 1
fi

if [ -z "${OPENAI_API_KEY:-}" ] && [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "No LLM API key set (OPENAI_API_KEY or ANTHROPIC_API_KEY). Export one and retry."
  exit 1
fi

# Optional: check Postgres connectivity
DB_OK=0
if command -v psql >/dev/null 2>&1; then
  if psql "${DATABASE_URL:-postgresql+asyncpg://postgres:password@localhost:5432/tenmuses}" -c '\l' >/dev/null 2>&1; then
    DB_OK=1
  fi
fi

STARTED_POSTGRES=0

if [ "$DB_OK" -ne 1 ]; then
  echo "Postgres not reachable on DATABASE_URL. Attempting to start Docker Postgres container named $POSTGRES_CONTAINER..."
  if ! command -v docker >/dev/null 2>&1; then
    echo "Docker not installed or not on PATH. Please start Postgres manually and re-run this script."
    exit 1
  fi

  # Check if container exists
  if ! docker ps -a --format '{{.Names}}' | grep -qw "$POSTGRES_CONTAINER"; then
    docker run -d --name "$POSTGRES_CONTAINER" -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=password -e POSTGRES_DB=tenmuses -p 5432:5432 "$POSTGRES_IMAGE"
    STARTED_POSTGRES=1
  else
    # If exists but not running, start it
    if [ "$(docker ps --format '{{.Names}}' | grep -w "$POSTGRES_CONTAINER")" = "" ]; then
      docker start "$POSTGRES_CONTAINER"
      STARTED_POSTGRES=1
    fi
  fi

  echo "Waiting for Postgres to accept connections..."
  for i in {1..30}; do
    if docker exec "$POSTGRES_CONTAINER" pg_isready -U postgres >/dev/null 2>&1; then
      DB_OK=1
      break
    fi
    sleep 1
  done

  if [ "$DB_OK" -ne 1 ]; then
    echo "Failed to start or connect to Docker Postgres container. Please start Postgres manually and retry."
    if [ "$STARTED_POSTGRES" -eq 1 ]; then
      docker rm -f "$POSTGRES_CONTAINER" >/dev/null 2>&1 || true
    fi
    exit 1
  fi
fi

# Ensure Redis
REDIS_OK=0
if command -v redis-cli >/dev/null 2>&1; then
  if redis-cli -h localhost -p 6379 ping >/dev/null 2>&1; then
    REDIS_OK=1
  fi
fi

STARTED_REDIS=0
if [ "$REDIS_OK" -ne 1 ]; then
  echo "Redis not reachable; attempting to start Docker Redis container named $REDIS_CONTAINER..."
  if ! command -v docker >/dev/null 2>&1; then
    echo "Docker not installed or not on PATH. Please start Redis manually and re-run this script."
    exit 1
  fi

  if ! docker ps -a --format '{{.Names}}' | grep -qw "$REDIS_CONTAINER"; then
    docker run -d --name "$REDIS_CONTAINER" -p 6379:6379 "$REDIS_IMAGE"
    STARTED_REDIS=1
  else
    if [ "$(docker ps --format '{{.Names}}' | grep -w "$REDIS_CONTAINER")" = "" ]; then
      docker start "$REDIS_CONTAINER"
      STARTED_REDIS=1
    fi
  fi

  echo "Waiting for Redis to accept connections..."
  for i in {1..30}; do
    if docker exec "$REDIS_CONTAINER" redis-cli ping >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
fi

# Ensure MinIO
MINIO_OK=0
if curl -s http://localhost:9000/minio/health/ready >/dev/null 2>&1; then
  MINIO_OK=1
fi

STARTED_MINIO=0
if [ "$MINIO_OK" -ne 1 ]; then
  echo "MinIO not reachable; attempting to start Docker MinIO container named $MINIO_CONTAINER..."
  if ! command -v docker >/dev/null 2>&1; then
    echo "Docker not installed or not on PATH. Please start MinIO manually and re-run this script."
    exit 1
  fi

  if ! docker ps -a --format '{{.Names}}' | grep -qw "$MINIO_CONTAINER"; then
    docker run -d --name "$MINIO_CONTAINER" -e MINIO_ROOT_USER="$MINIO_ROOT_USER" -e MINIO_ROOT_PASSWORD="$MINIO_ROOT_PASSWORD" -p 9000:9000 "$MINIO_IMAGE" server /data
    STARTED_MINIO=1
  else
    if [ "$(docker ps --format '{{.Names}}' | grep -w "$MINIO_CONTAINER")" = "" ]; then
      docker start "$MINIO_CONTAINER"
      STARTED_MINIO=1
    fi
  fi

  echo "Waiting for MinIO to be ready..."
  for i in {1..30}; do
    if curl -s http://localhost:9000/minio/health/ready >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
fi

# Register cleanup to remove started services
if [ "$STARTED_POSTGRES" -eq 1 ] || [ "$STARTED_REDIS" -eq 1 ] || [ "$STARTED_MINIO" -eq 1 ]; then
  cleanup() {
    echo "Cleaning up started containers..."
    if [ "$STARTED_MINIO" -eq 1 ]; then
      docker rm -f "$MINIO_CONTAINER" >/dev/null 2>&1 || true
    fi
    if [ "$STARTED_REDIS" -eq 1 ]; then
      docker rm -f "$REDIS_CONTAINER" >/dev/null 2>&1 || true
    fi
    if [ "$STARTED_POSTGRES" -eq 1 ]; then
      docker rm -f "$POSTGRES_CONTAINER" >/dev/null 2>&1 || true
    fi
  }
  trap cleanup EXIT
fi


echo "Running integration tests..."
cd backend
pytest -q -m integration
