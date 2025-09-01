#!/bin/bash
# Full-Stack Production Publish Pipeline
# Tests backend + frontend, builds, deploys with Docker, validates health, auto-reverts on failure

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

BACKUP_TAG="backup-$(date +%Y%m%d-%H%M%S)"

echo "🚀 FREEZER APP DEPLOYMENT PIPELINE"
echo "=================================="

# Step 1: Backend Tests
echo ""
echo "📋 STEP 1: Backend Test Suite"
echo "------------------------------"
# Test backend first since it's critical - ensure we're in backend directory
cd /Users/hallie/Documents/repos/freezer-backend
if ENVIRONMENT=test python3 -m pytest test_api_flow.py test_ai_shopping.py test_rate_limiting.py test_fallback_parsing.py --tb=short >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend tests passed${NC}"
else
    echo -e "${RED}❌ Backend tests failed - DEPLOYMENT BLOCKED${NC}"
    exit 1
fi

# Step 2: Frontend Tests  
echo ""
echo "📋 STEP 2: Frontend Test Suite"
echo "-------------------------------"
cd ../freezer-frontend
npm test || {
    echo -e "${RED}❌ Frontend tests failed - DEPLOYMENT BLOCKED${NC}"
    exit 1
}
echo -e "${GREEN}✅ Frontend tests passed${NC}"

# Step 3: Build Frontend  
echo ""
echo "🔧 STEP 3: Building Frontend"
echo "-----------------------------"
npm run build || {
    echo -e "${RED}❌ Frontend build failed - DEPLOYMENT BLOCKED${NC}"
    exit 1
}
echo -e "${GREEN}✅ Frontend built successfully${NC}"

# Step 4: Pre-flight Check
cd ../freezer-backend
echo ""
echo "🔍 STEP 4: Pre-flight Validation"
echo "---------------------------------"
chmod +x deploy-check.sh
./deploy-check.sh || {
    echo -e "${RED}❌ Pre-flight check failed - DEPLOYMENT BLOCKED${NC}"
    exit 1
}
echo -e "${GREEN}✅ Pre-flight checks passed${NC}"

# Step 5: Backup Current State
echo ""
echo "💾 STEP 5: Creating Backup"
echo "---------------------------"
if docker images freezer-api:latest >/dev/null 2>&1; then
    docker tag freezer-api:latest "freezer-api:$BACKUP_TAG"
    echo -e "${GREEN}✅ Backup created: freezer-api:$BACKUP_TAG${NC}"
else
    echo -e "${YELLOW}⚠️ No existing image to backup${NC}"
fi

# Step 6: Full-Stack Deploy
echo ""
echo "🚀 STEP 6: Full-Stack Deployment"
echo "---------------------------------"
echo "Building backend API container..."
docker-compose down || true
docker-compose up -d --build

echo "Deploying frontend to container..."
# Nginx container mounts ../freezer-frontend/dist to serve static frontend

# Step 7: Health Check
echo ""
echo "🔍 STEP 7: Full-Stack Health Check"
echo "-----------------------"
echo "Waiting for service to start..."
sleep 10

# Check if API is responding
for i in {1..30}; do
    if curl -f http://localhost:8000/ >/dev/null 2>&1; then
        echo -e "${GREEN}✅ API health check passed${NC}"
        break
    elif [ $i -eq 30 ]; then
        echo -e "${RED}❌ Health check failed - ROLLING BACK${NC}"
        
        # Rollback
        echo "🔄 Rolling back to previous version..."
        docker-compose down
        if docker images "freezer-api:$BACKUP_TAG" >/dev/null 2>&1; then
            docker tag "freezer-api:$BACKUP_TAG" freezer-api:latest
            docker-compose up -d
            echo -e "${YELLOW}⚠️ Rolled back to previous version${NC}"
        fi
        exit 1
    else
        echo "Attempt $i/30 - waiting..."
        sleep 2
    fi
done

# Step 8: Frontend Health Check
echo ""
echo "🌐 STEP 8: Frontend Check"
echo "-------------------------"
if curl -f http://localhost:8000/ | grep -q "Freezer"; then
    echo -e "${GREEN}✅ Frontend serving correctly${NC}"
else
    echo -e "${RED}❌ Frontend not loading properly${NC}"
    exit 1
fi

echo ""
echo "🎉 DEPLOYMENT SUCCESSFUL!"
echo "========================"
echo -e "${GREEN}✅ All systems operational${NC}"
echo "📍 API: http://localhost:8000"
echo "📍 App: http://localhost:8000"
echo "💾 Backup available: freezer-api:$BACKUP_TAG"
echo ""
echo "To rollback if issues arise:"
echo "  docker-compose down"
echo "  docker tag freezer-api:$BACKUP_TAG freezer-api:latest" 
echo "  docker-compose up -d"