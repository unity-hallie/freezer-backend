# Database Environment Configuration

This document explains the environment-based database configuration system implemented to ensure proper separation between test, development, and production databases.

## Overview

The database configuration system automatically selects the appropriate database based on environment variables, preventing data contamination and ensuring production safety.

## Environment Variables

### Core Configuration
- `ENVIRONMENT`: Sets the runtime environment (`development`, `test`, `production`)
- `TEST_MODE`: Override to force test mode (`true`/`false`)

### Database URLs
- `DATABASE_URL`: Main database connection string
- `TEST_DATABASE_URL`: Test database connection string (auto-used in test mode)

## Environment Behavior

### Test Environment (`ENVIRONMENT=test` or `TEST_MODE=true`)
- **Database**: Forces SQLite with test-specific database file
- **Isolation**: Ensures test database is separate from production
- **Safety**: No risk of contaminating live data

```bash
ENVIRONMENT=test
TEST_DATABASE_URL=sqlite:///./test_freezer_app.db
```

### Development Environment (`ENVIRONMENT=development`)
- **Database**: SQLite by default, PostgreSQL optional
- **Warning**: Shows warning when using SQLite to encourage PostgreSQL adoption
- **Flexibility**: Allows both database types for development convenience

```bash
ENVIRONMENT=development
DATABASE_URL=sqlite:///./freezer_app.db
# or
DATABASE_URL=postgresql://user:pass@localhost/freezer_dev
```

### Production Environment (`ENVIRONMENT=production`)
- **Database**: Requires PostgreSQL exclusively
- **Validation**: Rejects SQLite configurations
- **Safety**: Requires explicit DATABASE_URL configuration

```bash
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

## Configuration Validation

The system includes several safety checks:

1. **Production Safety**: Prevents SQLite usage in production
2. **Test Isolation**: Ensures test databases are properly isolated
3. **Explicit Configuration**: Requires explicit DATABASE_URL in production
4. **Clear Error Messages**: Provides helpful error messages for misconfigurations

## Usage Examples

### Running Tests
```bash
ENVIRONMENT=test python -m pytest
```

### Development with SQLite
```bash
ENVIRONMENT=development python main.py
# Warning: Using SQLite in development. Consider using PostgreSQL...
```

### Development with PostgreSQL
```bash
ENVIRONMENT=development
DATABASE_URL=postgresql://user:pass@localhost/freezer_dev
python main.py
```

### Production Deployment
```bash
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@prod-host:5432/freezer_prod
python main.py
```

## Utilities

### Configuration Checker
Run the database configuration checker to verify your setup:

```bash
python check_db_config.py
```

This utility will:
- Display current configuration
- Run environment-specific validations
- Provide recommendations for your environment

### Programmatic Access
```python
from utils.database_config import (
    get_current_environment,
    is_test_mode,
    get_database_info
)

# Check current environment
env = get_current_environment()  # 'development', 'test', or 'production'

# Check if test mode is active
testing = is_test_mode()  # True/False

# Get detailed configuration info
info = get_database_info()  # Dict with configuration details
```

## Migration from Previous Setup

The previous setup used a simple `DATABASE_URL` with basic SQLite/PostgreSQL detection. The new system:

1. **Adds environment awareness**: Different behavior per environment
2. **Improves safety**: Prevents SQLite in production
3. **Enhances testing**: Automatic test database isolation
4. **Provides validation**: Clear error messages for misconfigurations

### Migration Steps
1. Update `.env` file with new environment variables
2. Set `ENVIRONMENT` variable appropriately
3. Use `TEST_DATABASE_URL` for test configurations
4. Run `python check_db_config.py` to verify setup

## Troubleshooting

### "SQLite databases are not allowed in production"
- Set `ENVIRONMENT=production` and use PostgreSQL `DATABASE_URL`

### "DATABASE_URL must be explicitly set for production"  
- Provide explicit `DATABASE_URL` in production environment

### "Test database URL should contain 'test'"
- Use test-specific database URL in `TEST_DATABASE_URL`

### Import errors for utils.database_config
- Ensure the utils directory exists and has proper `__init__.py`
- The validation will skip gracefully if utils are unavailable