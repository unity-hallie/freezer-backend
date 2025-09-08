#!/bin/bash
# Automated deployment update script for freaziepeazie.app
# Run this on the production server to deploy updates

set -e

echo "🚀 FREAZIEPEAZIE.APP DEPLOYMENT UPDATE"
echo "===================================="
echo "Started at: $(date)"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Check if running on production server
if [[ ! -f ".env.production" ]]; then
    log_error "This script should be run from the production server in the app directory"
    exit 1
fi

# Store current commit hash for rollback
PREVIOUS_COMMIT=$(git rev-parse HEAD)
log_info "Current commit: $PREVIOUS_COMMIT"

# Pull latest code
log_info "Pulling latest code from repository..."
if git pull origin main; then
    log_success "Code updated successfully"
else
    log_error "Failed to pull latest code"
    exit 1
fi

# Get new commit hash
NEW_COMMIT=$(git rev-parse HEAD)
log_info "New commit: $NEW_COMMIT"

# Check what changed
CHANGED_FILES=$(git diff --name-only $PREVIOUS_COMMIT $NEW_COMMIT)
log_info "Changed files:"
echo "$CHANGED_FILES" | sed 's/^/  - /'

# Determine what needs to be rebuilt
REBUILD_FRONTEND=false
REBUILD_BACKEND=false

if echo "$CHANGED_FILES" | grep -q "freezer-frontend/"; then
    REBUILD_FRONTEND=true
    log_info "Frontend changes detected"
fi

if echo "$CHANGED_FILES" | grep -q -E "\.(py|txt|sh|Dockerfile)$"; then
    REBUILD_BACKEND=true
    log_info "Backend changes detected"
fi

# Rebuild frontend if needed
if [ "$REBUILD_FRONTEND" = true ]; then
    log_info "Rebuilding frontend..."
    if [ -d "freezer-frontend" ]; then
        cd freezer-frontend
        if npm run build; then
            log_success "Frontend build completed"
        else
            log_error "Frontend build failed"
            exit 1
        fi
        cd ..
    else
        log_warning "Frontend directory not found, skipping frontend build"
    fi
fi

# Rebuild backend if needed
if [ "$REBUILD_BACKEND" = true ]; then
    log_info "Rebuilding backend container..."
    if docker-compose build api; then
        log_success "Backend container rebuilt"
    else
        log_error "Backend container build failed"
        exit 1
    fi
fi

# Create backup before deployment
log_info "Creating backup..."
BACKUP_DIR="/opt/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp data/production_freezer_app.db "$BACKUP_DIR/" 2>/dev/null || log_warning "No database to backup"
cp .env.production "$BACKUP_DIR/"
log_success "Backup created: $BACKUP_DIR"

# Deploy with rolling restart
log_info "Deploying with rolling restart..."

# Start services
if docker-compose up -d --no-deps api; then
    log_success "API service restarted"
else
    log_error "Failed to restart API service"
    exit 1
fi

# Give API time to start
sleep 5

if docker-compose up -d --no-deps nginx; then
    log_success "Nginx service restarted"
else
    log_error "Failed to restart Nginx service"
    exit 1
fi

# Health check with retry
log_info "Performing health check..."
for i in {1..5}; do
    if curl -f -s https://freaziepeazie.app/health > /dev/null 2>&1; then
        log_success "Health check passed!"
        break
    elif curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
        log_success "API health check passed (HTTP)!"
        break
    else
        log_warning "Health check failed (attempt $i/5)"
        if [ $i -eq 5 ]; then
            log_error "All health checks failed - rolling back..."
            
            # Rollback
            git reset --hard $PREVIOUS_COMMIT
            docker-compose restart
            
            # Restore backup
            cp "$BACKUP_DIR/production_freezer_app.db" data/ 2>/dev/null || true
            
            log_error "Rollback completed"
            exit 1
        fi
        sleep 10
    fi
done

# Final verification
log_info "Running final verification..."

# Check container status
if docker-compose ps | grep -q "Up"; then
    log_success "All containers are running"
else
    log_warning "Some containers may not be running properly"
    docker-compose ps
fi

# Test key endpoints
if curl -f -s https://freaziepeazie.app/api/health > /dev/null 2>&1; then
    log_success "API endpoint is healthy"
else
    log_warning "API endpoint health check failed"
fi

# Check logs for errors
ERROR_COUNT=$(docker-compose logs --tail=50 api 2>&1 | grep -i error | wc -l)
if [ "$ERROR_COUNT" -gt 0 ]; then
    log_warning "Found $ERROR_COUNT error(s) in recent logs"
    log_info "Recent logs:"
    docker-compose logs --tail=10 api
else
    log_success "No recent errors in logs"
fi

# Cleanup old backups (keep last 30 days)
log_info "Cleaning up old backups..."
find /opt/backups -type d -mtime +30 -exec rm -rf {} \; 2>/dev/null || true

# Success summary
echo ""
echo "🎉 DEPLOYMENT SUCCESSFUL!"
echo "========================"
echo "✅ Deployed commit: $NEW_COMMIT"
echo "✅ Site: https://freaziepeazie.app"
echo "✅ Backup: $BACKUP_DIR"
echo "✅ Completed at: $(date)"
echo ""

# Send notification (if mail is configured)
if command -v mail >/dev/null 2>&1; then
    echo "Deployment successful for freaziepeazie.app at $(date)" | \
        mail -s "Deployment Success" admin@freaziepeazie.app 2>/dev/null || true
fi

log_success "freaziepeazie.app updated successfully!"