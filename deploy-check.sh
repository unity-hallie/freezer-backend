#!/bin/bash
# Deployment Pre-Flight Check Script
# Prevents last-minute deployment issues by validating configuration

set -e

echo "🚀 DEPLOYMENT PRE-FLIGHT CHECK"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_passed=0
check_failed=0

check() {
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✅ $1${NC}"
        ((check_passed++))
    else
        echo -e "  ${RED}❌ $1${NC}"
        ((check_failed++))
    fi
}

echo ""
echo "📋 CONFIGURATION CHECKS"
echo "------------------------"

# 1. Check required files exist
echo "Checking required files..."
test -f Dockerfile && echo -e "  ${GREEN}✅ Dockerfile exists${NC}" || echo -e "  ${RED}❌ Dockerfile missing${NC}"
test -f docker-compose.yml && echo -e "  ${GREEN}✅ docker-compose.yml exists${NC}" || echo -e "  ${RED}❌ docker-compose.yml missing${NC}"
test -f nginx.conf && echo -e "  ${GREEN}✅ nginx.conf exists${NC}" || echo -e "  ${RED}❌ nginx.conf missing${NC}"
test -f docker-entrypoint.sh && echo -e "  ${GREEN}✅ docker-entrypoint.sh exists${NC}" || echo -e "  ${RED}❌ docker-entrypoint.sh missing${NC}"
test -f requirements.txt && echo -e "  ${GREEN}✅ requirements.txt exists${NC}" || echo -e "  ${RED}❌ requirements.txt missing${NC}"

# 2. Check environment files
echo ""
echo "Checking environment configuration..."
if [ -f ".env.production" ]; then
    echo -e "  ${GREEN}✅ .env.production exists${NC}"
    
    # Check required environment variables
    required_vars=("DB_PASSWORD" "JWT_SECRET_KEY" "CORS_ORIGINS")
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" .env.production; then
            echo -e "    ${GREEN}✅ ${var} is set${NC}"
        else
            echo -e "    ${RED}❌ ${var} is missing${NC}"
            ((check_failed++))
        fi
    done
else
    echo -e "  ${RED}❌ .env.production missing${NC}"
    ((check_failed++))
fi

# 3. Check Docker setup
echo ""
echo "Checking Docker setup..."
if command -v docker &> /dev/null; then
    echo -e "  ${GREEN}✅ Docker is installed${NC}"
    ((check_passed++))
else
    echo -e "  ${RED}❌ Docker is not installed${NC}"
    ((check_failed++))
fi

if command -v docker-compose &> /dev/null; then
    echo -e "  ${GREEN}✅ Docker Compose is installed${NC}"
    ((check_passed++))
else
    echo -e "  ${RED}❌ Docker Compose is not installed${NC}"
    ((check_failed++))
fi

# 4. Check if Docker daemon is running
if docker info &> /dev/null; then
    echo -e "  ${GREEN}✅ Docker daemon is running${NC}"
    ((check_passed++))
else
    echo -e "  ${YELLOW}⚠️ Docker daemon may not be running${NC}"
fi

# 5. Test Docker build
echo ""
echo "Testing Docker build..."
if docker build -t freezer-api-test . &> /dev/null; then
    echo -e "  ${GREEN}✅ Docker build successful${NC}"
    ((check_passed++))
    # Clean up test image
    docker rmi freezer-api-test &> /dev/null
else
    echo -e "  ${RED}❌ Docker build failed${NC}"
    ((check_failed++))
fi

# 6. Check Python requirements
echo ""
echo "Validating Python requirements..."
if python3 -c "
import sys
import subprocess
try:
    with open('requirements.txt', 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    print(f'📦 Found {len(requirements)} requirements')
    for req in requirements[:5]:  # Show first 5
        print(f'  - {req}')
    if len(requirements) > 5:
        print(f'  ... and {len(requirements) - 5} more')
except Exception as e:
    print(f'❌ Error reading requirements: {e}')
    sys.exit(1)
"; then
    echo -e "  ${GREEN}✅ Requirements file is valid${NC}"
    ((check_passed++))
else
    echo -e "  ${RED}❌ Requirements file has issues${NC}"
    ((check_failed++))
fi

# 7. Check frontend build
echo ""
echo "Checking frontend build..."
if [ -d "../freezer-frontend/dist" ]; then
    echo -e "  ${GREEN}✅ Frontend build directory exists${NC}"
    ((check_passed++))
else
    echo -e "  ${YELLOW}⚠️ Frontend build directory missing (run 'npm run build' in frontend)${NC}"
fi

# Summary
echo ""
echo "======================================"
echo "📊 DEPLOYMENT READINESS SUMMARY"
echo "======================================"
echo -e "  ${GREEN}Passed: ${check_passed}${NC}"
echo -e "  ${RED}Failed: ${check_failed}${NC}"
echo ""

if [ $check_failed -eq 0 ]; then
    echo -e "${GREEN}🎉 DEPLOYMENT READY! All checks passed.${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Set up your droplet/server"
    echo "2. Copy files to server"
    echo "3. Configure domain in nginx.conf and docker-compose.yml"
    echo "4. Run: docker-compose up -d"
    echo "5. Set up SSL with certbot"
    exit 0
else
    echo -e "${RED}🚨 DEPLOYMENT BLOCKED! Fix the issues above first.${NC}"
    echo ""
    echo "Common fixes:"
    echo "- Create missing .env.production with required variables"
    echo "- Install Docker and Docker Compose"
    echo "- Fix Dockerfile issues"
    echo "- Build frontend: cd ../freezer-frontend && npm run build"
    exit 1
fi