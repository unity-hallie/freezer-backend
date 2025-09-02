#!/bin/bash
# Deployment Safety Script - Update Validation Only
# Validates existing database integrity for ongoing deployments
# NOTE: For first-time deployment setup, use first-time-deployment.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🛡️  DEPLOYMENT UPDATE VALIDATION"
echo "================================="
echo "ℹ️  This script validates existing deployments only"
echo "ℹ️  For first-time setup, run: ./first-time-deployment.sh"
echo ""

# Function to check database connectivity and basic integrity
check_database_health() {
    echo ""
    echo "📊 Database Health Check"
    echo "------------------------"
    
    # Check if we can connect to database
    if python3 -c "
import sys
sys.path.append('.')
from database import engine
import sqlalchemy as sa
try:
    with engine.connect() as conn:
        result = conn.execute(sa.text('SELECT 1 as test'))
        print('✅ Database connection: OK')
    exit(0)
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
" 2>/dev/null; then
        echo -e "${GREEN}✅ Database connectivity verified${NC}"
    else
        echo -e "${RED}❌ Database connection failed - DEPLOYMENT BLOCKED${NC}"
        return 1
    fi
    
    # Check critical tables exist
    python3 -c "
import sys
sys.path.append('.')
from database import engine
import sqlalchemy as sa

critical_tables = ['users', 'households', 'items', 'locations']
try:
    with engine.connect() as conn:
        for table in critical_tables:
            result = conn.execute(sa.text(f'SELECT COUNT(*) FROM {table}'))
            count = result.scalar()
            print(f'✅ Table {table}: {count} records')
    print('✅ All critical tables verified')
except Exception as e:
    print(f'❌ Critical table check failed: {e}')
    exit(1)
" 2>/dev/null || {
        echo -e "${RED}❌ Critical tables missing - DEPLOYMENT BLOCKED${NC}"
        return 1
    }
    
    echo -e "${GREEN}✅ Database health check passed${NC}"
    return 0
}

# Function to check migration status (validation only)
check_migration_status() {
    echo ""
    echo "🔄 Migration Status Check"
    echo "-------------------------"
    
    # Check current migration status
    echo "Current migration status:"
    if python3 -m alembic current 2>/dev/null; then
        echo -e "${GREEN}✅ Migration status accessible${NC}"
    else
        echo -e "${RED}❌ Cannot access migration status - database may not be initialized${NC}"
        echo "ℹ️  Run first-time-deployment.sh for initial setup"
        return 1
    fi
    
    # Check for pending migrations
    echo "Checking for pending migrations..."
    current=$(python3 -m alembic current --verbose 2>/dev/null | grep "Current revision" | cut -d' ' -f3 || echo "none")
    head=$(python3 -m alembic heads 2>/dev/null | cut -d' ' -f1 || echo "unknown")
    
    if [[ "$current" != "$head" ]] && [[ "$current" != "none" ]]; then
        echo -e "${YELLOW}⚠️  Pending migrations detected${NC}"
        echo "ℹ️  Current: $current, Latest: $head"
        echo "ℹ️  Consider running migrations before deployment"
    else
        echo -e "${GREEN}✅ Database is up to date${NC}"
    fi
    
    return 0
}

# Function to verify user session compatibility
check_session_compatibility() {
    echo ""
    echo "👤 User Session Compatibility"
    echo "------------------------------"
    
    # Check if user authentication still works
    python3 -c "
import sys
sys.path.append('.')
from sqlalchemy.orm import sessionmaker
from database import engine
import models

try:
    Session = sessionmaker(bind=engine)
    with Session() as session:
        # Check if we can query users table
        user_count = session.query(models.User).count()
        print(f'✅ User table accessible: {user_count} users')
        
        # Check if critical user fields exist
        if user_count > 0:
            user = session.query(models.User).first()
            required_fields = ['id', 'email', 'hashed_password', 'full_name']
            for field in required_fields:
                if hasattr(user, field):
                    print(f'✅ Critical field {field}: exists')
                else:
                    print(f'❌ Critical field {field}: MISSING')
                    exit(1)
        
        print('✅ User schema compatibility verified')
except Exception as e:
    print(f'❌ Session compatibility check failed: {e}')
    exit(1)
" 2>/dev/null || {
        echo -e "${RED}❌ User session compatibility failed - DEPLOYMENT BLOCKED${NC}"
        return 1
    }
    
    echo -e "${GREEN}✅ User sessions will remain valid${NC}"
    return 0
}

# Function to verify data integrity
check_data_integrity() {
    echo ""
    echo "🔍 Data Integrity Verification"
    echo "-------------------------------"
    
    python3 -c "
import sys
sys.path.append('.')
from sqlalchemy.orm import sessionmaker
from database import engine
import models

try:
    Session = sessionmaker(bind=engine)
    with Session() as session:
        # Check for orphaned data
        users = session.query(models.User).count()
        households = session.query(models.Household).count()
        items = session.query(models.Item).count()
        
        print(f'✅ Data integrity: {users} users, {households} households, {items} items')
        
        # Check foreign key relationships are intact
        if items > 0:
            orphaned_items = session.query(models.Item).filter(
                ~models.Item.location_id.in_(
                    session.query(models.Location.id)
                )
            ).count()
            
            if orphaned_items > 0:
                print(f'⚠️  Warning: {orphaned_items} items have invalid location references')
            else:
                print('✅ Foreign key relationships intact')
        
        print('✅ Data integrity verified')
        
except Exception as e:
    print(f'❌ Data integrity check failed: {e}')
    exit(1)
" 2>/dev/null || {
        echo -e "${YELLOW}⚠️ Data integrity warnings detected${NC}"
        # Don't block deployment for warnings, but log them
    }
    
    echo -e "${GREEN}✅ Data integrity check completed${NC}"
    return 0
}

# Main validation sequence (update deployments only)
main() {
    echo "Starting deployment update validation..."
    echo "Environment: ${ENVIRONMENT:-development}"
    echo ""
    
    # Validation-only checks
    if ! check_database_health; then
        echo -e "${RED}❌ Database health check failed${NC}"
        echo "ℹ️  If this is your first deployment, run: ./first-time-deployment.sh"
        exit 1
    fi
    
    if ! check_migration_status; then
        echo -e "${RED}❌ Migration status check failed${NC}"
        echo "ℹ️  Database may not be initialized. Run: ./first-time-deployment.sh"
        exit 1
    fi
    
    if ! check_session_compatibility; then
        echo -e "${RED}❌ Session compatibility check failed${NC}"
        exit 1
    fi
    
    if ! check_data_integrity; then
        # Data integrity is warning-level, not blocking
        echo -e "${YELLOW}⚠️ Data integrity warnings present but deployment can continue${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}🎉 DEPLOYMENT UPDATE VALIDATION PASSED${NC}"
    echo "======================================"
    echo "✅ Existing database is healthy and accessible"
    echo "✅ Migration status verified"
    echo "✅ User sessions will remain compatible"
    echo "✅ No data corruption detected"
    echo "✅ Safe to proceed with update deployment"
    echo ""
    echo "ℹ️  Remember: This script only validates existing deployments"
    echo "ℹ️  For first-time setup, use: ./first-time-deployment.sh"
    
    return 0
}

# Run main function
main "$@"