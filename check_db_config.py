#!/usr/bin/env python3
"""
Database configuration checker utility.

Usage:
    python check_db_config.py

This utility helps verify that your database configuration is correct
for the current environment and provides helpful debugging information.
"""

import sys
from pprint import pprint

try:
    from utils.database_config import (
        get_current_environment, 
        is_test_mode, 
        get_database_info,
        validate_production_config,
        ensure_test_database_isolation
    )
except ImportError as e:
    print(f"❌ Error importing database config utilities: {e}")
    sys.exit(1)


def main():
    """Check and display database configuration."""
    print("🔍 Database Configuration Checker")
    print("=" * 40)
    
    try:
        # Get basic info
        info = get_database_info()
        print("📊 Current Configuration:")
        pprint(info, width=60)
        print()
        
        # Run validations
        print("✅ Running Validations...")
        
        try:
            validate_production_config()
            print("   ✓ Production configuration valid")
        except ValueError as e:
            if get_current_environment() == 'production':
                print(f"   ❌ Production validation failed: {e}")
                return 1
            else:
                print("   ⚪ Production validation skipped (not in production)")
        
        try:
            ensure_test_database_isolation()
            print("   ✓ Test database isolation valid")
        except ValueError as e:
            if get_current_environment() == 'test' or is_test_mode():
                print(f"   ❌ Test isolation validation failed: {e}")
                return 1
            else:
                print("   ⚪ Test isolation validation skipped (not in test mode)")
        
        # Environment-specific advice
        env = get_current_environment()
        print(f"\n💡 Environment-Specific Advice ({env}):")
        
        if env == 'development':
            if info['database_type'] == 'sqlite':
                print("   • Consider using PostgreSQL to match production")
                print("   • Current SQLite setup is fine for development")
            else:
                print("   • Great! Using PostgreSQL matches production")
        
        elif env == 'test':
            print("   • Using isolated test database - good!")
            print("   • Make sure tests clean up after themselves")
        
        elif env == 'production':
            print("   • Production configuration validated ✓")
            print("   • Using PostgreSQL as required")
        
        print("\n🎉 Database configuration check completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Configuration check failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())