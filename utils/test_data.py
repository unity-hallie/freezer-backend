"""
Test data utilities with PII protection and volume controls.
"""

import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from decouple import config


# Test data volume controls
MAX_TEST_USERS = config('MAX_TEST_USERS', default=5, cast=int)
MAX_TEST_HOUSEHOLDS = config('MAX_TEST_HOUSEHOLDS', default=3, cast=int)
MAX_TEST_ITEMS = config('MAX_TEST_ITEMS', default=10, cast=int)


class PIIProtector:
    """Utility for protecting PII in test data."""
    
    @staticmethod
    def anonymize_email(base_email: Optional[str] = None) -> str:
        """Generate anonymized email for testing."""
        if base_email and '@' in base_email:
            username = base_email.split('@')[0]
            # Keep first 2 chars, anonymize rest
            if len(username) > 2:
                username = username[:2] + '***'
        else:
            username = 'testuser'
        
        # Use valid test domain (RFC 2606 reserved for testing)
        domain = 'test.example.com'
        timestamp = str(int(datetime.utcnow().timestamp()))[-6:]
        return f"{username}{timestamp}@{domain}"
    
    @staticmethod
    def anonymize_name(real_name: Optional[str] = None) -> str:
        """Generate anonymized name for testing."""
        if real_name:
            parts = real_name.split()
            if len(parts) > 1:
                # Keep first char of each name part
                return ' '.join(f"{part[0]}***" for part in parts if part)
            else:
                return f"{real_name[0]}***" if real_name else "Test User"
        
        # Generate random test name
        first_names = ['Test', 'Demo', 'Sample', 'Mock']
        last_names = ['User', 'Person', 'Account', 'Profile']
        return f"{random.choice(first_names)} {random.choice(last_names)}"
    
    @staticmethod
    def generate_test_token() -> str:
        """Generate secure test token (non-sensitive)."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=32))


class TestDataLimiter:
    """Utility for controlling test data volume."""
    
    @staticmethod
    def validate_test_volume(record_type: str, count: int) -> bool:
        """Validate test data doesn't exceed volume limits."""
        limits = {
            'users': MAX_TEST_USERS,
            'households': MAX_TEST_HOUSEHOLDS,
            'items': MAX_TEST_ITEMS,
            'locations': 5,  # Max locations per test
        }
        
        limit = limits.get(record_type, 10)
        if count > limit:
            raise ValueError(
                f"Test data volume exceeded: {count} {record_type} > {limit} limit. "
                f"Use TestDataLimiter.create_limited_{record_type}() instead."
            )
        return True
    
    @staticmethod
    def create_limited_users(count: Optional[int] = None) -> List[Dict]:
        """Create limited test user data with PII protection."""
        count = min(count or 3, MAX_TEST_USERS)
        users = []
        
        for i in range(count):
            users.append({
                'email': PIIProtector.anonymize_email(),
                'password': f'testpass{i+1}',
                'full_name': PIIProtector.anonymize_name(),
                'is_verified': True
            })
        
        return users
    
    @staticmethod
    def create_limited_households(count: Optional[int] = None) -> List[Dict]:
        """Create limited test household data."""
        count = min(count or 2, MAX_TEST_HOUSEHOLDS)
        households = []
        
        for i in range(count):
            households.append({
                'name': f'Test Household {i+1}',
                'description': f'Test household for development #{i+1}',
                'invite_code': ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            })
        
        return households


def setup_test_environment_validation():
    """Validate test environment is properly configured."""
    from utils.database_config import get_current_environment, is_test_mode
    
    if not (get_current_environment() == 'test' or is_test_mode()):
        raise ValueError(
            "PII protection utilities should only be used in test environment. "
            "Set ENVIRONMENT=test or TEST_MODE=true"
        )


def get_test_performance_config() -> Dict:
    """Get test performance configuration."""
    return {
        'max_execution_time': config('TEST_MAX_EXECUTION_TIME', default=30, cast=int),
        'max_users': MAX_TEST_USERS,
        'max_households': MAX_TEST_HOUSEHOLDS,  
        'max_items': MAX_TEST_ITEMS,
        'timeout_warning_threshold': config('TEST_TIMEOUT_WARNING', default=20, cast=int)
    }


# Quick access functions for tests
def create_test_user_data(anonymize: bool = True) -> Dict:
    """Create single test user with PII protection."""
    setup_test_environment_validation()
    
    if anonymize:
        return {
            'email': PIIProtector.anonymize_email(),
            'password': 'testpass123',
            'full_name': PIIProtector.anonymize_name()
        }
    else:
        # For tests that specifically need non-anonymized data
        return {
            'email': 'test@test.example.com',
            'password': 'testpass123', 
            'full_name': 'Test User'
        }