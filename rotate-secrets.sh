#!/bin/bash
# Secret Key Rotation Script
# Run this script to generate new production secrets securely
# Usage: ./rotate-secrets.sh

set -e

echo "🔐 PRODUCTION SECRET ROTATION"
echo "============================="
echo ""

# Check if .env.production exists
if [[ ! -f ".env.production" ]]; then
    echo "❌ .env.production not found!"
    echo "Please run this script from the freezer-backend directory"
    exit 1
fi

# Generate new secrets
echo "🔄 Generating new secure secrets..."
NEW_JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
NEW_DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

echo "✅ New secrets generated"
echo ""

# Create backup
BACKUP_FILE=".env.production.backup.$(date +%Y%m%d_%H%M%S)"
cp .env.production "$BACKUP_FILE"
echo "📋 Backup created: $BACKUP_FILE"

# Update JWT secret
sed -i.tmp "s/^SECRET_KEY=.*/SECRET_KEY=$NEW_JWT_SECRET/" .env.production
sed -i.tmp "s/^JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$NEW_JWT_SECRET/" .env.production
rm -f .env.production.tmp

# Update database password
sed -i.tmp "s/^DB_PASSWORD=.*/DB_PASSWORD=$NEW_DB_PASSWORD/" .env.production
sed -i.tmp "s|^DATABASE_URL=postgresql://freezer_user:[^@]*@|DATABASE_URL=postgresql://freezer_user:$NEW_DB_PASSWORD@|" .env.production
rm -f .env.production.tmp

# Secure file permissions
chmod 600 .env.production

echo "🔒 Updated .env.production with new secrets"
echo "🔒 File permissions secured (600)"
echo ""

echo "⚠️  IMPORTANT NEXT STEPS:"
echo "1. If database is already deployed, update the database user password:"
echo "   Check .env.production for new DB_PASSWORD, then run:"
echo "   sudo -u postgres psql -c \"ALTER USER freezer_user PASSWORD '<new_password>';\""
echo ""
echo "2. Restart all services to use new secrets:"
echo "   docker-compose down && docker-compose up -d"
echo ""
echo "3. Test that everything still works after restart"
echo ""

# Don't echo the actual secrets to terminal
echo "✅ Secret rotation complete!"
echo "📁 Old secrets backed up to: $BACKUP_FILE"