"""
Unified environment configuration loader
Consolidates inconsistent env loading across the application
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from decouple import config as decouple_config

def load_environment():
    """
    Load environment variables with proper priority:
    1. System environment (highest priority)
    2. .env.production (if ENVIRONMENT=production) 
    3. .env.local (if exists)
    4. .env (fallback)
    """
    # Get base environment setting (could come from system env or .env)
    env = os.getenv('ENVIRONMENT', 'development').lower()
    
    # Load environment files in priority order
    env_files_to_try = []
    
    if env == 'production':
        env_files_to_try.extend(['.env.production', '.env.local', '.env'])
    elif env == 'test':
        env_files_to_try.extend(['.env.test', '.env.local', '.env'])
    else:  # development
        env_files_to_try.extend(['.env.local', '.env'])
    
    # Load each file that exists (later files don't override earlier ones)
    for env_file in reversed(env_files_to_try):
        if Path(env_file).exists():
            load_dotenv(env_file, override=False)
            print(f"🔧 Loaded environment from {env_file}")

def get_config(key: str, default=None, cast=None):
    """
    Unified config getter that ensures environment is loaded
    Drop-in replacement for decouple.config()
    """
    # Ensure environment is loaded
    if not hasattr(get_config, '_loaded'):
        load_environment()
        get_config._loaded = True
    
    # Use decouple for consistent behavior
    if cast is not None:
        return decouple_config(key, default=default, cast=cast)
    else:
        return decouple_config(key, default=default)

# Auto-load on module import for backwards compatibility
load_environment()