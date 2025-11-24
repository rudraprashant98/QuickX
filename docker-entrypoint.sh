#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h postgres -p 5432 -U robotics; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "PostgreSQL is up - initializing database..."

export PYTHONPATH=/code

# Clear database if CLEAR_DB_ON_START is set
if [ "${CLEAR_DB_ON_START:-false}" = "true" ]; then
  echo "Clearing database (CLEAR_DB_ON_START=true)..."
  python scripts/clear_db.py
else
  echo "Initializing database (keeping existing data)..."
  python scripts/init_db.py
fi

echo "Starting application..."
exec "$@"

