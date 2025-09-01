# Environment Configuration Guide

This guide documents ALL environment variables needed for the Freezer App deployment.

## ⚠️ SECURITY WARNING

**NEVER commit .env files to git!** This repository has the following environment files in `.gitignore`:
- `.env`
- `.env.production` 
- `.env.droplet`
- `.env.local`
- `.env.development.local`
- `.env.test.local`
- `.env.production.local`

Only `.env.example` should be committed to provide a template.

## Quick Setup

1. **Development**: Copy `.env.example` to `.env` and customize
2. **Production**: Create `.env.production` with production values
3. **Testing**: Environment automatically uses test database when `ENVIRONMENT=test`

## Environment Variables Reference

### Core Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENVIRONMENT` | ✅ | `development` | Environment mode: `development`, `production`, `test` |
| `TEST_MODE` | ❌ | `false` | Force test mode regardless of ENVIRONMENT |

### Database Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ | `sqlite:///./freezer_app.db` | Database connection string |
| `TEST_DATABASE_URL` | ❌ | `sqlite:///./test_freezer_app.db` | Test database (auto-used in test mode) |

**Database URL Formats:**
- **SQLite**: `sqlite:///./database.db`
- **PostgreSQL**: `postgresql://username:password@host:port/database`

**Production Requirements:**
- Must use PostgreSQL (SQLite not allowed in production)
- Example: `postgresql://freezer_user:SecurePass123@localhost/freezer_db`

### Authentication & Security

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | ✅ | `change-this` | JWT signing key - **MUST be unique and secure in production** |
| `ALGORITHM` | ❌ | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ❌ | `30` | JWT token expiration time |

**Generating Secure Keys:**
```bash
# Generate a secure secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Web Server Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FRONTEND_URL` | ❌ | Auto-detected | Frontend URL for CORS and redirects |
| `ALLOWED_HOSTS` | ❌ | `localhost` | Comma-separated allowed hostnames |
| `CORS_ORIGINS` | ❌ | `http://localhost:3000,http://127.0.0.1:3000` | Comma-separated CORS origins |

**Production Example:**
```bash
FRONTEND_URL=https://yourdomain.com
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ORIGINS=https://yourdomain.com
```

**IP-only Deployment Example:**
```bash
FRONTEND_URL=http://143.198.123.45:3000
ALLOWED_HOSTS=143.198.123.45,localhost
CORS_ORIGINS=http://143.198.123.45:3000,http://localhost:3000
```

### Email Configuration (Optional)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MAIL_USERNAME` | ❌ | - | Email account username |
| `MAIL_PASSWORD` | ❌ | - | Email account password/app-password |
| `MAIL_FROM` | ❌ | `noreply@freezerapp.com` | From email address |
| `MAIL_FROM_NAME` | ❌ | `Freezer App` | From name |
| `MAIL_SERVER` | ❌ | `smtp.gmail.com` | SMTP server |
| `MAIL_PORT` | ❌ | `587` | SMTP port |
| `MAIL_STARTTLS` | ❌ | `True` | Enable STARTTLS |
| `MAIL_SSL_TLS` | ❌ | `False` | Enable SSL/TLS |
| `USE_CREDENTIALS` | ❌ | `True` | Use SMTP authentication |
| `VALIDATE_CERTS` | ❌ | `True` | Validate SSL certificates |

**Gmail Setup:**
1. Enable 2-Factor Authentication
2. Generate App Password: Account → Security → 2-Step Verification → App passwords
3. Use app password in `MAIL_PASSWORD`

### Discord Integration (Optional)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_CLIENT_ID` | ❌ | - | Discord OAuth2 Client ID |
| `DISCORD_CLIENT_SECRET` | ❌ | - | Discord OAuth2 Client Secret |

**Discord Setup:**
1. Go to https://discord.com/developers/applications
2. Create New Application → OAuth2 → Copy Client ID and Secret
3. Add redirect URL: `{FRONTEND_URL}/auth/discord/callback`

### Test Configuration (Development Only)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MAX_TEST_USERS` | ❌ | `5` | Maximum test users to create |
| `MAX_TEST_HOUSEHOLDS` | ❌ | `3` | Maximum test households |
| `MAX_TEST_ITEMS` | ❌ | `10` | Maximum test items |
| `TEST_MAX_EXECUTION_TIME` | ❌ | `30` | Test timeout in seconds |
| `TEST_TIMEOUT_WARNING` | ❌ | `20` | Test warning threshold |

## Environment Examples

### Development (.env)
```bash
# Development Configuration
ENVIRONMENT=development
DATABASE_URL=sqlite:///./freezer_app.db
SECRET_KEY=dev-secret-key-not-for-production
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Optional: Enable Discord in development
# VITE_DISCORD_CLIENT_ID=your_dev_discord_client_id

# Optional: Email testing
MAIL_USERNAME=your.email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
```

### Production (.env.production)
```bash
# Production Configuration - KEEP THIS FILE SECURE!
ENVIRONMENT=production
DATABASE_URL=postgresql://freezer_user:SecurePassword123!@localhost/freezer_db
SECRET_KEY=super-secure-randomly-generated-key-32-chars-min
FRONTEND_URL=https://yourdomain.com
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ORIGINS=https://yourdomain.com

# Email Configuration
MAIL_USERNAME=noreply@yourdomain.com
MAIL_PASSWORD=secure-email-app-password
MAIL_FROM=noreply@yourdomain.com
MAIL_FROM_NAME=Your Freezer App

# Discord (Optional)
# DISCORD_CLIENT_ID=your_production_discord_client_id
# DISCORD_CLIENT_SECRET=your_production_discord_secret
```

### IP-Only Deployment (.env.production for droplet)
```bash
# Production Configuration for IP-only deployment
ENVIRONMENT=production
DATABASE_URL=postgresql://freezer_user:SecurePassword123!@localhost/freezer_db
SECRET_KEY=super-secure-randomly-generated-key-32-chars-min
FRONTEND_URL=http://YOUR_DROPLET_IP:3000
ALLOWED_HOSTS=YOUR_DROPLET_IP,localhost
CORS_ORIGINS=http://YOUR_DROPLET_IP:3000,http://localhost:3000

# Email Configuration
MAIL_USERNAME=your.email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
MAIL_FROM=noreply@freezerapp.com
MAIL_FROM_NAME=Freezer App

# Discord disabled for IP deployment
# DISCORD_CLIENT_ID=
# DISCORD_CLIENT_SECRET=
```

## Security Best Practices

### 🔒 Production Security Checklist

- [ ] **Strong SECRET_KEY**: Generated with `secrets.token_urlsafe(32)` or similar
- [ ] **Secure Database Password**: Random, 16+ characters, mixed case, numbers, symbols
- [ ] **HTTPS Only**: All URLs use `https://` in production
- [ ] **Restricted CORS**: Only allow necessary origins, no wildcards (`*`)
- [ ] **Email App Passwords**: Use app-specific passwords, not account passwords
- [ ] **File Permissions**: `chmod 600 .env.production` (owner read/write only)
- [ ] **No Git Commits**: Verify `.env*` files are in `.gitignore`
- [ ] **Regular Rotation**: Change secrets periodically

### 🚨 Security Red Flags

❌ **Never do this:**
- `SECRET_KEY=secret` or `SECRET_KEY=password`
- `DATABASE_URL=postgresql://user:password@localhost/db`
- `CORS_ORIGINS=*` (wildcard in production)
- Committing `.env.production` to git
- Using development keys in production
- Sharing environment files via email/chat

✅ **Do this instead:**
- `SECRET_KEY=kJ8xZ2vB9mN4pQ7wR3tY6uI1oP5sA8dF2gH4jK7lM9nQ`
- `DATABASE_URL=postgresql://app_user:Zx9#mK8@pL2$nQ5w@localhost/prod_db`
- `CORS_ORIGINS=https://yourdomain.com`
- Keep `.env.production` local and secure
- Generate production-specific secrets
- Use secure password managers for sharing

## Deployment Integration

This configuration integrates with:

- **first-time-deployment.sh**: Reads `.env.production` for database setup
- **deployment-safety.sh**: Validates environment before updates  
- **Docker Compose**: Uses env_file directive to load variables
- **Alembic**: Uses DATABASE_URL for migrations

## Troubleshooting

### Database Connection Issues
```bash
# Test database connection
python3 -c "
from database import engine
try:
    with engine.connect() as conn:
        print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database error: {e}')
"
```

### Environment Loading Issues
```bash
# Check if environment file is loaded
python3 -c "
import os
print('ENVIRONMENT:', os.getenv('ENVIRONMENT', 'NOT SET'))
print('DATABASE_URL:', 'SET' if os.getenv('DATABASE_URL') else 'NOT SET')
print('SECRET_KEY:', 'SET' if os.getenv('SECRET_KEY') else 'NOT SET')
"
```

### CORS Issues
- Check `CORS_ORIGINS` includes your frontend URL exactly
- Ensure no trailing slashes: `https://domain.com` not `https://domain.com/`
- For IP deployments, use `http://` not `https://`

---

**Questions?** Check the deployment logs or run the health check script after deployment.