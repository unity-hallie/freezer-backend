#!/bin/bash
# Docker entrypoint script for production deployment

set -e

echo "🚀 Starting Freezer API..."

# Create data directory for SQLite
mkdir -p data

# Setup database (SQLite - no external dependency)
echo "🗄️ Setting up database..."
python3 -c "
import models
import database
print('Creating SQLite database tables...')
models.Base.metadata.create_all(bind=database.engine)
print('✅ Database tables ready!')
"

echo "🌐 Starting FastAPI server..."
exec "$@"