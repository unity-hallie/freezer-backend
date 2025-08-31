#!/bin/bash
# Docker entrypoint script for production deployment

set -e

echo "🚀 Starting Freezer API..."

# Wait for database to be ready
echo "⏳ Waiting for database..."
while ! nc -z db 5432; do
  sleep 1
done
echo "✅ Database is ready!"

# Run database migrations
echo "🗄️ Running database migrations..."
python -c "
import models
import database
print('Creating tables...')
models.Base.metadata.create_all(bind=database.engine)
print('✅ Database tables ready!')
"

echo "🌐 Starting FastAPI server..."
exec "$@"