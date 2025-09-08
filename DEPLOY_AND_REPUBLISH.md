# Deploy and Republish Process for freaziepeazie.app

## Overview
This document outlines the complete process for deploying and republishing the Freezer App to production. The process is designed for SQLite MVP deployment with future PostgreSQL scalability.

## Prerequisites
- DigitalOcean droplet with SSH access
- Domain `freaziepeazie.app` pointing to droplet IP
- Local development environment with changes committed

## Deployment Process

### Phase 1: Initial Production Deployment

#### 1.1 Prepare Local Environment
```bash
# Ensure all changes are committed
git status
git add -A
git commit -m "feat: production deployment changes"

# Build frontend
cd freezer-frontend
npm run build

# Verify backend tests pass
cd freezer-backend
ENVIRONMENT=test python3 -m pytest test_main.py -v
```

#### 1.2 Transfer Files to Production Server
```bash
# Option A: Direct SCP (if you have SSH key configured)
scp -r . user@freaziepeazie.app:/opt/freezer-app/

# Option B: Git clone on server
ssh user@freaziepeazie.app
cd /opt/
git clone https://github.com/your-username/freezer-backend.git freezer-app
cd freezer-app
git clone https://github.com/your-username/freezer-frontend.git
```

#### 1.3 Server Environment Setup
```bash
# On production server
cd /opt/freezer-app

# Run first-time deployment (installs Docker, creates directories)
sudo ./first-time-deployment.sh

# Create production environment (without committing secrets)
./setup-production-env.sh

# Generate secure secrets
./rotate-secrets.sh

# Manual step: Edit .env.production with actual email credentials
nano .env.production
# Update MAIL_USERNAME and MAIL_PASSWORD with real values
```

#### 1.4 Launch Production Stack
```bash
# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps
curl http://localhost:8000/health

# Generate SSL certificates
sudo docker-compose exec certbot certbot certonly \
  --webroot --webroot-path=/var/www/html \
  --email your-email@example.com \
  --agree-tos --no-eff-email \
  -d freaziepeazie.app

# Restart nginx with SSL
docker-compose restart nginx
```

#### 1.5 Verify Deployment
```bash
# Test all endpoints
curl https://freaziepeazie.app/health
curl https://freaziepeazie.app/api/health
curl https://freaziepeazie.app/

# Check logs
docker-compose logs -f api
docker-compose logs nginx
```

### Phase 2: Republish Process (Updates)

#### 2.1 Local Development
```bash
# Make changes locally
# Run tests: ENVIRONMENT=test python3 -m pytest
# Commit changes: git commit -m "feat: new feature"
```

#### 2.2 Deploy Updates
```bash
# On production server
cd /opt/freezer-app

# Pull latest changes
git pull origin main

# If frontend changes: rebuild
cd freezer-frontend && npm run build && cd ..

# If backend changes: rebuild containers
docker-compose build api

# If environment changes: rotate secrets (optional)
./rotate-secrets.sh

# Apply updates
docker-compose down
docker-compose up -d

# Verify
curl https://freaziepeazie.app/health
```

## Automation Opportunities

### High Priority (Can Implement Now)

#### 1. Deployment Script Automation
```bash
# deploy-update.sh
#!/bin/bash
set -e

echo "🚀 FREAZIEPEAZIE.APP DEPLOYMENT UPDATE"
echo "===================================="

# Pull latest code
git pull origin main

# Check if frontend changed
if git diff --name-only HEAD~1 HEAD | grep -q "freezer-frontend/"; then
    echo "📦 Rebuilding frontend..."
    cd freezer-frontend && npm run build && cd ..
fi

# Check if backend changed
if git diff --name-only HEAD~1 HEAD | grep -q -E "\.(py|txt|sh)$"; then
    echo "🐍 Rebuilding backend..."
    docker-compose build api
fi

# Deploy with zero-downtime
echo "🔄 Deploying with rolling restart..."
docker-compose up -d --no-deps api
docker-compose up -d --no-deps nginx

# Health check
sleep 5
if curl -f https://freaziepeazie.app/health > /dev/null; then
    echo "✅ Deployment successful!"
else
    echo "❌ Deployment failed - rolling back..."
    docker-compose restart
    exit 1
fi

echo "🎉 freaziepeazie.app updated successfully!"
```

#### 2. Backup Automation
```bash
# backup.sh
#!/bin/bash
BACKUP_DIR="/opt/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup SQLite database
cp data/production_freezer_app.db $BACKUP_DIR/
cp .env.production $BACKUP_DIR/

# Backup SSL certificates
cp -r ssl/ $BACKUP_DIR/

# Keep only last 30 days of backups
find /opt/backups -type d -mtime +30 -exec rm -rf {} \;

echo "✅ Backup completed: $BACKUP_DIR"
```

#### 3. Health Monitoring
```bash
# health-check.sh
#!/bin/bash
if ! curl -f https://freaziepeazie.app/health > /dev/null 2>&1; then
    echo "🚨 freaziepeazie.app is down!" | mail -s "Site Down Alert" admin@example.com
    
    # Auto-restart attempt
    docker-compose restart
    
    sleep 10
    if curl -f https://freaziepeazie.app/health > /dev/null 2>&1; then
        echo "✅ Site auto-recovered" | mail -s "Site Recovery" admin@example.com
    fi
fi
```

### Medium Priority (Future Automation)

#### 4. CI/CD Pipeline (GitHub Actions)
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to server
        run: |
          ssh ${{ secrets.SERVER_USER }}@${{ secrets.SERVER_HOST }} \
          'cd /opt/freezer-app && ./deploy-update.sh'
```

#### 5. Database Migration Automation
```bash
# migrate.sh (for future PostgreSQL upgrade)
#!/bin/bash
# Backup current SQLite
cp data/production_freezer_app.db backups/pre-migration-$(date +%Y%m%d).db

# Run migrations
python3 -m alembic upgrade head

echo "✅ Database migration completed"
```

### Low Priority (Advanced Automation)

#### 6. Blue-Green Deployment
- Dual server setup for zero-downtime deployments
- Load balancer switching between environments

#### 7. Infrastructure as Code
- Terraform for droplet provisioning
- Ansible for configuration management

#### 8. Monitoring Dashboard
- Grafana + Prometheus for metrics
- Log aggregation with ELK stack

## Security Considerations

### Production Secrets Management
- ✅ Never commit `.env.production` to git
- ✅ Use `setup-production-env.sh` to create environment files safely
- ✅ Rotate secrets regularly with `rotate-secrets.sh`
- 🔄 Consider HashiCorp Vault for advanced secret management

### Access Control
- ✅ SSH key-based authentication only
- ✅ Firewall rules (UFW) configured
- 🔄 Consider fail2ban for intrusion prevention

### SSL/TLS
- ✅ Automated certificate renewal with certbot
- ✅ HTTPS-only configuration
- 🔄 Consider certificate monitoring alerts

## Rollback Procedures

### Quick Rollback
```bash
# Rollback to previous git commit
git reset --hard HEAD~1
./deploy-update.sh

# Or rollback to specific commit
git reset --hard <commit-hash>
./deploy-update.sh
```

### Database Rollback
```bash
# Restore from backup
docker-compose down
cp backups/production_freezer_app_YYYYMMDD.db data/production_freezer_app.db
docker-compose up -d
```

## Cost Monitoring

### Current MVP Costs
- DigitalOcean Droplet: $6/month (Basic)
- Domain: ~$15/year
- Total: ~$87/year

### Scaling Cost Projections
- 100 users: Same setup ($87/year)
- 1000 users: Upgrade droplet to $12/month (~$159/year)
- 10,000 users: Multiple droplets + PostgreSQL (~$500/year)

## Next Steps Analysis

### Immediate (This Sprint)
1. **Execute S28-LAUNCH**: Run actual production deployment
2. **Create `deploy-update.sh`**: Automate future updates
3. **Setup monitoring**: Health check + backup scripts
4. **Document access**: SSH keys and server access procedures

### Near Term (Next Sprint)
1. **CI/CD Pipeline**: GitHub Actions for automated deployment
2. **Enhanced monitoring**: Uptime monitoring service
3. **Performance testing**: Load testing for scale validation
4. **User feedback collection**: Analytics and error reporting

### Long Term (Future Sprints)
1. **PostgreSQL migration**: When approaching 100+ users
2. **Multi-region deployment**: For improved performance
3. **Advanced monitoring**: Full observability stack
4. **Infrastructure as Code**: For disaster recovery

## Risk Assessment

### High Risk (Address Now)
- Single point of failure (one droplet)
- Manual deployment process
- No automated backups

### Medium Risk (Address Soon)
- No monitoring/alerting
- Manual SSL renewal
- No load testing performed

### Low Risk (Monitor)
- SQLite scaling limits (not relevant until 100+ users)
- Single region deployment
- Basic security setup

## Success Metrics

### Technical Metrics
- **Uptime**: >99.5% target
- **Response time**: <500ms average
- **Error rate**: <1% of requests
- **Deployment time**: <5 minutes for updates

### Business Metrics
- **User registration success rate**: >95%
- **Daily active users**: Track growth
- **Feature adoption**: Monitor usage patterns
- **Support ticket volume**: <1% of user base

---

**Status**: Ready for S28-LAUNCH execution
**Owner**: Development Team
**Last Updated**: 2025-09-06
**Next Review**: After first production deployment