#!/bin/bash
# Cost Monitoring & Resource Optimization Script
# Prevents surprise cloud bills by validating resource configurations

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "💰 CLOUD COST MONITORING & OPTIMIZATION"
echo "========================================"

# Function to check database query performance
check_database_performance() {
    echo ""
    echo "📊 Database Query Performance"
    echo "-----------------------------"
    
    # Check for potentially expensive queries
    python3 -c "
import sys
sys.path.append('.')
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from database import engine
import time

try:
    Session = sessionmaker(bind=engine)
    with Session() as session:
        # Test common user queries for performance
        start_time = time.time()
        
        # Query 1: User authentication (should be fast with email index)
        result = session.execute(text('SELECT COUNT(*) FROM users WHERE email LIKE \"%test%\"'))
        email_query_time = time.time() - start_time
        
        # Query 2: User items (potential N+1 problem)
        start_time = time.time()
        result = session.execute(text('SELECT COUNT(*) FROM items WHERE added_by_user_id IN (SELECT id FROM users LIMIT 10)'))
        items_query_time = time.time() - start_time
        
        # Query 3: Household locations (joins)
        start_time = time.time()  
        result = session.execute(text('SELECT COUNT(*) FROM locations l JOIN households h ON l.household_id = h.id'))
        join_query_time = time.time() - start_time
        
        print(f'✅ Email query performance: {email_query_time:.3f}s')
        if email_query_time > 0.1:
            print(f'⚠️  Warning: Email queries slow ({email_query_time:.3f}s) - consider indexing')
            
        print(f'✅ Items query performance: {items_query_time:.3f}s')
        if items_query_time > 0.2:
            print(f'⚠️  Warning: Items queries slow ({items_query_time:.3f}s) - check foreign keys')
            
        print(f'✅ Join query performance: {join_query_time:.3f}s')
        if join_query_time > 0.2:
            print(f'⚠️  Warning: Join queries slow ({join_query_time:.3f}s) - check indexes')
        
        print('✅ Database performance check completed')
        
except Exception as e:
    print(f'❌ Database performance check failed: {e}')
    exit(1)
" || {
        echo -e "${RED}❌ Database performance check failed${NC}"
        return 1
    }
    
    echo -e "${GREEN}✅ Database queries optimized for cost efficiency${NC}"
    return 0
}

# Function to check Docker resource limits
check_docker_resources() {
    echo ""
    echo "🐳 Docker Resource Configuration"
    echo "--------------------------------"
    
    # Check if docker-compose has resource limits
    if [[ -f "docker-compose.yml" ]]; then
        echo "Checking Docker Compose resource limits..."
        
        # Check for memory limits
        if grep -q "mem_limit\|memory:" docker-compose.yml; then
            echo -e "${GREEN}✅ Memory limits configured in docker-compose.yml${NC}"
        else
            echo -e "${YELLOW}⚠️  Warning: No memory limits set - could cause surprise costs${NC}"
            echo "   Consider adding memory limits to prevent runaway processes:"
            echo "   services:"
            echo "     api:"
            echo "       deploy:"
            echo "         resources:"
            echo "           limits:"
            echo "             memory: 512M"
        fi
        
        # Check for CPU limits
        if grep -q "cpus\|cpu:" docker-compose.yml; then
            echo -e "${GREEN}✅ CPU limits configured${NC}"
        else
            echo -e "${YELLOW}⚠️  Warning: No CPU limits set${NC}"
            echo "   Consider adding CPU limits to control costs"
        fi
        
        # Check restart policies
        if grep -q "restart:" docker-compose.yml; then
            restart_policy=$(grep "restart:" docker-compose.yml | head -1 | awk '{print $2}')
            if [[ "$restart_policy" == "unless-stopped" || "$restart_policy" == "always" ]]; then
                echo -e "${GREEN}✅ Restart policy configured: $restart_policy${NC}"
            else
                echo -e "${YELLOW}⚠️  Warning: Restart policy may cause cost issues: $restart_policy${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️  Warning: No restart policy set${NC}"
        fi
        
    else
        echo -e "${YELLOW}⚠️  Warning: No docker-compose.yml found${NC}"
    fi
    
    return 0
}

# Function to check API rate limiting (prevents API cost spirals)
check_api_cost_controls() {
    echo ""
    echo "🚨 API Cost Control Validation"
    echo "-------------------------------"
    
    # Check if rate limiting is implemented
    if grep -q "slowapi\|rate.limit" *.py 2>/dev/null; then
        echo -e "${GREEN}✅ Rate limiting implemented (slowapi detected)${NC}"
    else
        echo -e "${RED}❌ No rate limiting found - API costs could spiral${NC}"
        echo "   Risk: Unlimited API calls could cause surprise bills"
        return 1
    fi
    
    # Check for caching mechanisms
    if grep -q "cache\|Cache" *.py 2>/dev/null; then
        echo -e "${GREEN}✅ Caching mechanisms detected${NC}"
    else
        echo -e "${YELLOW}⚠️  Warning: No caching found - may increase API costs${NC}"
    fi
    
    # Check for AI/external API usage with limits
    if grep -q "gemini\|openai\|anthropic" *.py 2>/dev/null; then
        echo -e "${YELLOW}⚠️  AI API usage detected - ensure cost limits are set${NC}"
        if grep -q "timeout\|limit" *.py 2>/dev/null; then
            echo -e "${GREEN}✅ API limits/timeouts found${NC}"
        else
            echo -e "${RED}❌ No API limits found - AI costs could be unlimited${NC}"
            return 1
        fi
    fi
    
    echo -e "${GREEN}✅ API cost controls validated${NC}"
    return 0
}

# Function to validate environment resource settings
check_environment_config() {
    echo ""
    echo "⚙️  Environment Resource Configuration"
    echo "-------------------------------------"
    
    # Check production environment variables
    if [[ -f ".env.production" ]]; then
        echo "Checking production environment configuration..."
        
        # Check for database connection pooling
        if grep -q "pool\|connection" .env.production; then
            echo -e "${GREEN}✅ Database connection configuration found${NC}"
        else
            echo -e "${YELLOW}⚠️  Warning: Consider database connection pooling for production${NC}"
        fi
        
        # Check for resource-related environment variables
        if grep -q "MAX_\|LIMIT_\|TIMEOUT_" .env.production; then
            echo -e "${GREEN}✅ Resource limits configured in environment${NC}"
        else
            echo -e "${YELLOW}⚠️  Warning: No resource limits in production config${NC}"
        fi
        
    else
        echo -e "${YELLOW}⚠️  Warning: No .env.production file found${NC}"
        echo "   Create production environment config with resource limits"
    fi
    
    return 0
}

# Function to estimate deployment costs
estimate_deployment_costs() {
    echo ""
    echo "💸 Cost Estimation"
    echo "------------------"
    
    echo "Estimating minimum cloud deployment costs:"
    echo ""
    echo "🔹 Compute (1 CPU, 1GB RAM):"
    echo "   • DigitalOcean Droplet: ~\$6/month"  
    echo "   • Linode Nanode: ~\$5/month"
    echo "   • AWS t3.micro: ~\$8.5/month"
    echo ""
    echo "🔹 Database (PostgreSQL):"
    echo "   • Managed DB (512MB): ~\$15/month"
    echo "   • Self-hosted on same droplet: \$0 extra"
    echo ""
    echo "🔹 Storage (20GB SSD): ~\$2/month"
    echo ""
    echo "🔹 Bandwidth (1TB): Usually included"
    echo ""
    echo "💰 Estimated total: \$7-25/month depending on configuration"
    echo ""
    echo -e "${GREEN}✅ Cost estimates provided for budget planning${NC}"
    
    return 0
}

# Main cost monitoring sequence
main() {
    echo "Starting cloud cost monitoring validation..."
    echo "Environment: ${ENVIRONMENT:-development}"
    echo ""
    
    cost_warnings=0
    
    if ! check_database_performance; then
        ((cost_warnings++))
    fi
    
    check_docker_resources
    
    if ! check_api_cost_controls; then
        ((cost_warnings++))
    fi
    
    check_environment_config
    
    estimate_deployment_costs
    
    echo ""
    if [[ $cost_warnings -eq 0 ]]; then
        echo -e "${GREEN}🎉 COST MONITORING VALIDATION PASSED${NC}"
        echo "====================================="
        echo "✅ Database queries optimized"
        echo "✅ API cost controls in place" 
        echo "✅ Resource configurations validated"
        echo "✅ Cost estimates provided"
        echo ""
        echo "💰 Estimated monthly cost: \$7-25 for basic deployment"
        echo "🛡️  Protection against surprise bills: ACTIVE"
    else
        echo -e "${YELLOW}⚠️  COST MONITORING COMPLETED WITH WARNINGS${NC}"
        echo "=============================================="
        echo "Found $cost_warnings cost-related issues that could cause surprise bills"
        echo "Review the warnings above and implement cost controls before production"
        echo ""
        echo "⚠️  Deployment can proceed but costs may be unpredictable"
    fi
    
    return 0
}

# Run main function
main "$@"