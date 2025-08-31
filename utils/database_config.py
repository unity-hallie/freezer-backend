"""
Database configuration utilities for environment separation.
"""

import os
from typing import Dict, Literal
from decouple import config


DatabaseType = Literal['sqlite', 'postgresql']
Environment = Literal['development', 'test', 'production']


def get_current_environment() -> Environment:
    """Get the current environment setting."""
    env = config('ENVIRONMENT', default='development').lower()
    if env in ['development', 'test', 'production']:
        return env
    raise ValueError(f"Invalid ENVIRONMENT value: {env}. Must be 'development', 'test', or 'production'")


def is_test_mode() -> bool:
    """Check if test mode is enabled."""
    return config('TEST_MODE', default='false').lower() == 'true'


def validate_production_config() -> None:
    """Validate production database configuration."""
    if get_current_environment() != 'production':
        return
        
    database_url = config('DATABASE_URL', default=None)
    if not database_url:
        raise ValueError(
            "Production environment requires explicit DATABASE_URL configuration. "
            "Please set DATABASE_URL environment variable."
        )
    
    if database_url.startswith('sqlite'):
        raise ValueError(
            "SQLite databases are not allowed in production environment. "
            "Use PostgreSQL for production deployments."
        )


def get_database_info() -> Dict[str, str]:
    """Get current database configuration info for debugging."""
    from database import db_config, DATABASE_URL
    
    return {
        'environment': get_current_environment(),
        'test_mode': str(is_test_mode()),
        'database_type': db_config['type'],
        'database_url_scheme': DATABASE_URL.split('://')[0] if '://' in DATABASE_URL else 'unknown',
        'config_source': 'environment variables'
    }


def ensure_test_database_isolation() -> None:
    """Ensure test database is properly isolated from production data."""
    if not (get_current_environment() == 'test' or is_test_mode()):
        return
    
    from database import DATABASE_URL
    
    # Verify test database is separate
    if 'test' not in DATABASE_URL.lower():
        raise ValueError(
            "Test database URL should contain 'test' to ensure isolation from production data. "
            f"Current: {DATABASE_URL}"
        )
    
    # For SQLite, ensure test DB file is separate
    if DATABASE_URL.startswith('sqlite') and not any(x in DATABASE_URL.lower() for x in ['test', ':memory:']):
        raise ValueError(
            "SQLite test database should use separate file or in-memory database. "
            f"Current: {DATABASE_URL}"
        )