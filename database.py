from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from decouple import config
import os
import warnings

# Environment configuration
ENVIRONMENT = config('ENVIRONMENT', default='development').lower()
TEST_MODE = config('TEST_MODE', default='false').lower() == 'true'

def get_database_config():
    """Get database configuration based on environment."""
    
    # Force SQLite for test environments
    if ENVIRONMENT == 'test' or TEST_MODE:
        return {
            'url': config('TEST_DATABASE_URL', default='sqlite:///./test_freezer_app.db'),
            'type': 'sqlite'
        }
    
    # Production environment - allow SQLite for MVP, PostgreSQL for scale
    elif ENVIRONMENT == 'production':
        database_url = config('DATABASE_URL', default=None)
        if not database_url:
            raise ValueError("DATABASE_URL must be explicitly set for production environment")
        
        db_type = 'sqlite' if database_url.startswith('sqlite') else 'postgresql'
        
        if db_type == 'sqlite':
            warnings.warn(
                "Using SQLite in production. Consider PostgreSQL for >100 concurrent users.",
                UserWarning
            )
        
        return {
            'url': database_url,
            'type': db_type
        }
    
    # Development environment - allow both but warn about production readiness
    else:  # development
        database_url = config('DATABASE_URL', default='sqlite:///./freezer_app.db')
        db_type = 'sqlite' if database_url.startswith('sqlite') else 'postgresql'
        
        if db_type == 'sqlite':
            warnings.warn(
                "Using SQLite in development. Consider using PostgreSQL to match production environment.",
                UserWarning
            )
        
        return {
            'url': database_url,
            'type': db_type
        }

# Get database configuration
db_config = get_database_config()
DATABASE_URL = db_config['url']

# Validate configuration
try:
    from utils.database_config import validate_production_config, ensure_test_database_isolation
    validate_production_config()
    ensure_test_database_isolation()
except ImportError:
    # utils module might not be available during initial setup
    pass

# Create engine based on database type
if db_config['type'] == 'sqlite':
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False, "timeout": 5},
        echo=ENVIRONMENT == 'development'
    )
else:  # postgresql
    engine = create_engine(
        DATABASE_URL,
        echo=ENVIRONMENT == 'development'
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Ensure SQLite uses WAL and reasonable sync settings for concurrency
try:
    from sqlalchemy import event
    if db_config['type'] == 'sqlite':
        @event.listens_for(engine, "connect")
        def set_sqlite_pragmas(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA journal_mode=WAL;")
                cursor.execute("PRAGMA synchronous=NORMAL;")
            finally:
                cursor.close()
except Exception:
    pass
