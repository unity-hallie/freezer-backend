#!/bin/bash
# Production Environment Setup Script
# Safely creates .env.production on production server without committing secrets

set -e

echo "🔧 PRODUCTION ENVIRONMENT SETUP"
echo "================================"

# Check if running on production server
if [[ ! -f "/etc/os-release" ]]; then
    echo "⚠️  This script should be run on the production server"
    exit 1
fi

# Create .env.production with production values
cat > .env.production << 'EOF'
# Production Environment Configuration for freeziepeazie.app
# ⚠️ SECURITY: This file contains production secrets - keep secure!

# Core Configuration
ENVIRONMENT=production

# Database Configuration (SQLite for MVP - simple and reliable for <100 users)
DATABASE_URL=sqlite:///./data/production_freezer_app.db
# DB_PASSWORD only needed for PostgreSQL - not used with SQLite
DB_PASSWORD=unused_for_sqlite

# Authentication & Security (REPLACE THESE WITH SECURE VALUES)
SECRET_KEY=REPLACE_WITH_SECURE_JWT_SECRET_64_CHARS_MIN
JWT_SECRET_KEY=REPLACE_WITH_SECURE_JWT_SECRET_64_CHARS_MIN
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Web Server Configuration
FRONTEND_URL=https://freeziepeazie.app
ALLOWED_HOSTS=freeziepeazie.app,www.freeziepeazie.app
CORS_ORIGINS=https://freeziepeazie.app

# Email Configuration (Production)
MAIL_USERNAME=your.email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
MAIL_FROM=noreply@freeziepeazie.app
MAIL_FROM_NAME=Freezer App
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_STARTTLS=True
MAIL_SSL_TLS=False
USE_CREDENTIALS=True
VALIDATE_CERTS=True

# Discord OAuth2 (Disabled for production launch)
DISCORD_CLIENT_ID=
DISCORD_CLIENT_SECRET=

# Performance & Monitoring
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
LOG_LEVEL=INFO
RATE_LIMIT_PER_MINUTE=100

# Test Configuration (Not used in production)
TEST_MODE=false
EOF

# Secure file permissions
chmod 600 .env.production

echo "✅ Created .env.production template"
echo ""
echo "🔒 SECURITY REMINDERS:"
echo "1. Update SECRET_KEY and JWT_SECRET_KEY with secure values:"
echo "   python3 -c \"import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(64))\""
echo ""
echo "2. Update email credentials if needed"
echo ""
echo "3. Run ./rotate-secrets.sh to generate secure secrets automatically"
echo ""
echo "4. File permissions secured to 600 (owner read/write only)"
echo ""

echo "📁 File created: $(pwd)/.env.production"