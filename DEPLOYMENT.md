# 🚀 Production Deployment Guide

This guide prevents last-minute deployment issues by providing a clear checklist and automated validation.

## Pre-Deployment Checklist

### 1. Run Deployment Check
```bash
./deploy-check.sh
```
**❗ DO NOT DEPLOY** until all checks pass!

### 2. Critical Configuration

#### Environment Variables (.env.production)
```bash
# Required - Update with real values:
CORS_ORIGINS=https://yourdomain.com
DB_PASSWORD=your-secure-db-password
JWT_SECRET_KEY=your-64-char-jwt-secret

# Optional but recommended:
RATE_LIMIT_PER_MINUTE=100
LOG_LEVEL=INFO
```

#### Domain Configuration
Update these files with your actual domain:
- `docker-compose.yml`: Replace `your-domain.com` 
- `nginx.conf`: Replace `your-domain.com`

### 3. Frontend Build
```bash
cd ../freezer-frontend
npm run build
# Ensure dist/ directory exists
```

## Deployment Process

### Option A: Docker Droplet ($6/month)

1. **Server Setup**
   ```bash
   # On your droplet:
   sudo apt update
   sudo apt install docker.io docker-compose
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

2. **Deploy**
   ```bash
   # Copy files to server
   scp -r . user@your-server:/path/to/app/
   
   # On server:
   docker-compose up -d
   ```

3. **SSL Setup**
   ```bash
   # Run certbot once containers are up:
   docker-compose run --rm certbot
   ```

### Option B: Digital Ocean App Platform

1. **Create App**
   - Connect GitHub repo
   - Use Dockerfile deployment
   - Add managed PostgreSQL database

2. **Environment Variables**
   Copy from `.env.production` to App Platform settings

### Common Deployment Issues PREVENTED

✅ **Fixed PATH issues** in Dockerfile (non-root user access)  
✅ **Added netcat** dependency for database health checks  
✅ **Created nginx.conf** for proper proxy configuration  
✅ **Added DB_PASSWORD** variable for Docker Compose  
✅ **Validation script** catches misconfigurations early  
✅ **Security headers** and SSL configuration included  
✅ **Rate limiting** configured at nginx level  
✅ **CORS** properly configured for production  

## Post-Deployment Verification

```bash
# Health check
curl https://yourdomain.com/health

# API test  
curl https://yourdomain.com/api/

# Frontend load
curl https://yourdomain.com/
```

## Rollback Plan

```bash
# Keep previous image tagged
docker tag freezer-api freezer-api:backup

# Quick rollback
docker-compose down
docker tag freezer-api:backup freezer-api
docker-compose up -d
```

## Monitoring

- Check logs: `docker-compose logs -f`
- Database: Monitor connection pool usage
- Rate limiting: Watch nginx access logs
- SSL: Set up renewal reminders (90 days)

---

**🔥 CRITICAL:** Always run `./deploy-check.sh` before deployment!