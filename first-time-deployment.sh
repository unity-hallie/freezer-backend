#!/bin/bash
# First-Time Deployment Script
# Handles initial deployment setup before any validation
# Run this ONCE on a fresh server, then use deployment-safety.sh for updates

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🚀 FIRST-TIME DEPLOYMENT SETUP"
echo "==============================="
echo ""

# Anti-pattern prevention checks
check_for_existing_data() {
    echo "🛡️  Checking for existing production data..."
    
    # Check if PostgreSQL is already running with data
    if systemctl is-active --quiet postgresql 2>/dev/null; then
        echo -e "${YELLOW}⚠️ PostgreSQL is already running${NC}"
        echo "This may indicate existing production data."
        echo ""
        read -p "Continue anyway? This could overwrite existing data. (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}❌ Deployment cancelled to protect existing data${NC}"
            echo "If this is a fresh server, stop PostgreSQL first: sudo systemctl stop postgresql"
            exit 1
        fi
    fi
}

# Environment validation
validate_environment() {
    echo "🔍 Validating environment configuration..."
    
    if [[ ! -f ".env.production" ]]; then
        echo -e "${RED}❌ .env.production not found${NC}"
        echo "Please create .env.production with required variables:"
        echo "  - DATABASE_URL"
        echo "  - SECRET_KEY"
        echo "  - FRONTEND_URL"
        echo "  - ALLOWED_HOSTS"
        echo "  - CORS_ORIGINS"
        echo "  - MAIL_USERNAME, MAIL_PASSWORD, etc."
        exit 1
    fi
    
    # Check for dangerous patterns in environment
    if grep -q "password.*=.*password\|secret.*=.*secret\|key.*=.*key" .env.production; then
        echo -e "${YELLOW}⚠️ Warning: Detected potentially weak credentials in .env.production${NC}"
        echo "Please ensure you're using strong, unique passwords and secrets."
        echo ""
        read -p "Continue with current credentials? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Please update your credentials in .env.production"
            exit 1
        fi
    fi
    
    echo -e "${GREEN}✅ Environment configuration validated${NC}"
}

# System updates and security
setup_system() {
    echo ""
    echo "🔧 Setting up system dependencies..."
    
    # Update system packages
    apt update
    apt upgrade -y
    
    # Install essential packages with security focus
    apt install -y \
        curl \
        wget \
        git \
        ufw \
        fail2ban \
        unattended-upgrades \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        netcat-openbsd \
        htop
    
    # Configure automatic security updates
    echo 'Unattended-Upgrade::Automatic-Reboot "false";' >> /etc/apt/apt.conf.d/50unattended-upgrades
    systemctl enable unattended-upgrades
    
    # Basic firewall setup (will be configured later)
    ufw --force enable
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 80
    ufw allow 443
    
    echo -e "${GREEN}✅ System dependencies installed with security hardening${NC}"
}

# PostgreSQL setup
setup_postgresql() {
    echo ""
    echo "🗄️  Setting up PostgreSQL..."
    
    # Install PostgreSQL
    apt install -y postgresql postgresql-contrib
    
    # Start and enable PostgreSQL
    systemctl start postgresql
    systemctl enable postgresql
    
    # Extract database config from .env.production
    source .env.production
    
    # Parse DATABASE_URL to extract components
    # Format: postgresql://user:password@host/database
    DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    DB_PASS=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
    DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
    
    if [[ -z "$DB_USER" || -z "$DB_PASS" || -z "$DB_NAME" ]]; then
        echo -e "${RED}❌ Failed to parse DATABASE_URL${NC}"
        echo "Expected format: postgresql://user:password@localhost/database"
        exit 1
    fi
    
    echo "Creating database: $DB_NAME"
    echo "Creating user: $DB_USER"
    
    # Create database and user
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || echo "Database $DB_NAME might already exist"
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" 2>/dev/null || echo "User $DB_USER might already exist"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
    sudo -u postgres psql -c "ALTER USER $DB_USER CREATEDB;"
    
    # Test connection
    export PGPASSWORD=$DB_PASS
    if psql -h localhost -U $DB_USER -d $DB_NAME -c "SELECT 1;" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PostgreSQL setup complete and connection verified${NC}"
    else
        echo -e "${RED}❌ PostgreSQL connection test failed${NC}"
        exit 1
    fi
    unset PGPASSWORD
}

# Docker setup
setup_docker() {
    echo ""
    echo "🐳 Setting up Docker..."
    
    # Install Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    chmod +x get-docker.sh
    ./get-docker.sh
    rm get-docker.sh
    
    # Install Docker Compose
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    # Add current user to docker group (if not root)
    if [[ $EUID -ne 0 ]]; then
        usermod -aG docker $USER
        echo -e "${YELLOW}⚠️ Please logout and login again for Docker permissions to take effect${NC}"
    fi
    
    echo -e "${GREEN}✅ Docker and Docker Compose installed${NC}"
}

# Python and backend dependencies
setup_backend() {
    echo ""
    echo "🐍 Setting up Python backend..."
    
    # Install Python and pip
    apt install -y python3 python3-pip python3-venv python3-dev
    
    # Install backend dependencies
    if [[ -f "requirements.txt" ]]; then
        pip3 install -r requirements.txt
        echo -e "${GREEN}✅ Backend dependencies installed${NC}"
    else
        echo -e "${YELLOW}⚠️ requirements.txt not found, skipping Python dependencies${NC}"
    fi
}

# Initialize Alembic for database migrations
setup_alembic() {
    echo ""
    echo "📊 Setting up database migrations..."
    
    # Check if alembic is already initialized
    if [[ -d "alembic" ]]; then
        echo "Alembic directory exists, running migrations..."
        python3 -m alembic upgrade head
    else
        echo "Initializing Alembic..."
        python3 -m alembic init alembic
        
        # Update alembic.ini to use our database
        sed -i "s|sqlalchemy.url = driver://user:pass@localhost/dbname|sqlalchemy.url = $(grep DATABASE_URL .env.production | cut -d'=' -f2-)|" alembic/alembic.ini
        
        echo "Please configure alembic/env.py to import your models, then run:"
        echo "  python3 -m alembic revision --autogenerate -m 'Initial migration'"
        echo "  python3 -m alembic upgrade head"
    fi
    
    echo -e "${GREEN}✅ Database migration system ready${NC}"
}

# Create initial Docker Compose setup
setup_services() {
    echo ""
    echo "🚢 Setting up service orchestration..."
    
    # Create docker-compose.yml if it doesn't exist
    if [[ ! -f "docker-compose.yml" ]]; then
        cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    depends_on:
      - db
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.3'

  frontend:
    build:
      context: ../freezer-frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.3'
        reservations:
          memory: 128M
          cpus: '0.1'

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: ${DB_NAME:-freezer_db}
      POSTGRES_USER: ${DB_USER:-freezer_user}
      POSTGRES_PASSWORD: ${DB_PASS:-secure_password}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.3'

volumes:
  postgres_data:
EOF
        echo "Created docker-compose.yml with resource limits"
    fi
    
    echo -e "${GREEN}✅ Service orchestration configured${NC}"
}

# File permissions and security
secure_deployment() {
    echo ""
    echo "🔒 Applying security measures..."
    
    # Secure environment file
    chmod 600 .env.production
    
    # Set proper ownership
    if [[ $EUID -ne 0 ]]; then
        chown $USER:$USER .env.production
    fi
    
    # Create deployment user if running as root
    if [[ $EUID -eq 0 ]]; then
        echo "Creating deployment user 'freezer'..."
        useradd -m -s /bin/bash freezer 2>/dev/null || echo "User 'freezer' already exists"
        usermod -aG docker freezer 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✅ Security measures applied${NC}"
}

# Health check setup
setup_monitoring() {
    echo ""
    echo "📊 Setting up health monitoring..."
    
    # Create simple health check script
    cat > health-check.sh << 'EOF'
#!/bin/bash
# Simple health check for the application

check_service() {
    local service=$1
    local url=$2
    local expected=$3
    
    response=$(curl -s -o /dev/null -w "%{http_code}" $url 2>/dev/null || echo "000")
    if [[ "$response" == "$expected" ]]; then
        echo "✅ $service: OK ($response)"
        return 0
    else
        echo "❌ $service: FAIL ($response)"
        return 1
    fi
}

echo "🏥 Health Check $(date)"
echo "========================"

check_service "Backend API" "http://localhost:8000/health" "200"
check_service "Frontend" "http://localhost:3000" "200"

echo ""
EOF
    
    chmod +x health-check.sh
    echo -e "${GREEN}✅ Health monitoring configured${NC}"
}

# Main execution
main() {
    echo "Starting first-time deployment setup..."
    echo "This script will set up your server from scratch."
    echo ""
    
    # Anti-pattern prevention
    check_for_existing_data
    validate_environment
    
    # Core setup
    setup_system
    setup_postgresql
    setup_docker
    setup_backend
    setup_alembic
    setup_services
    secure_deployment
    setup_monitoring
    
    echo ""
    echo -e "${GREEN}🎉 FIRST-TIME DEPLOYMENT SETUP COMPLETE!${NC}"
    echo "=================================="
    echo ""
    echo "Next steps:"
    echo "1. If you're not root: logout and login again for Docker permissions"
    echo "2. Configure Alembic migrations (if needed)"
    echo "3. Build and start services: docker-compose up --build -d"
    echo "4. Run health check: ./health-check.sh"
    echo "5. For future deployments, use: ./deployment-safety.sh"
    echo ""
    echo -e "${BLUE}Your app should be available at:${NC}"
    echo "  Frontend: http://$(curl -s ifconfig.me):3000"
    echo "  Backend:  http://$(curl -s ifconfig.me):8000"
    echo ""
}

# Run main function only if script is executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi