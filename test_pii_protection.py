"""
Test PII protection and volume control utilities.
"""

import pytest
import time
from utils.test_data import (
    PIIProtector, 
    TestDataLimiter, 
    create_test_user_data,
    get_test_performance_config
)
from utils.test_performance import test_timeout, TestPerformanceContext
import os

# Set test environment
os.environ['ENVIRONMENT'] = 'test'
os.environ['TEST_MODE'] = 'true'


class TestPIIProtection:
    """Test PII protection utilities."""
    
    def test_email_anonymization(self):
        """Test email anonymization works correctly."""
        # Test with base email
        anon_email = PIIProtector.anonymize_email("realuser@gmail.com")
        assert anon_email.startswith("re***")
        assert anon_email.endswith("@test.example.local")
        assert "@" in anon_email
        
        # Test without base email
        anon_email2 = PIIProtector.anonymize_email()
        assert anon_email2.startswith("testuser")
        assert "@test.example.local" in anon_email2
    
    def test_name_anonymization(self):
        """Test name anonymization works correctly."""
        # Test with real name
        anon_name = PIIProtector.anonymize_name("John Smith")
        assert anon_name == "J*** S***"
        
        # Test single name
        anon_name2 = PIIProtector.anonymize_name("John")
        assert anon_name2 == "J***"
        
        # Test without real name
        anon_name3 = PIIProtector.anonymize_name()
        assert "Test" in anon_name3 or "Demo" in anon_name3 or "Mock" in anon_name3 or "Sample" in anon_name3
    
    def test_create_test_user_data(self):
        """Test test user data creation with PII protection."""
        user_data = create_test_user_data()
        
        # Check required fields exist
        assert "email" in user_data
        assert "password" in user_data
        assert "full_name" in user_data
        
        # Check email is anonymized
        assert "@test.example.local" in user_data["email"]
        
        # Check name is anonymized or test name
        assert len(user_data["full_name"]) > 0


class TestVolumeControls:
    """Test volume control utilities."""
    
    def test_user_volume_limits(self):
        """Test user creation volume limits."""
        # Should create limited number of users
        users = TestDataLimiter.create_limited_users(2)
        assert len(users) == 2
        
        # Should respect maximum limits
        users_max = TestDataLimiter.create_limited_users(100)
        config = get_test_performance_config()
        assert len(users_max) <= config['max_users']
    
    def test_household_volume_limits(self):
        """Test household creation volume limits."""
        households = TestDataLimiter.create_limited_households(2)
        assert len(households) == 2
        
        # Each household should have required fields
        for household in households:
            assert "name" in household
            assert "invite_code" in household
    
    def test_volume_validation(self):
        """Test volume validation catches excessive data."""
        with pytest.raises(ValueError, match="Test data volume exceeded"):
            TestDataLimiter.validate_test_volume("users", 1000)


class TestPerformanceControls:
    """Test performance control utilities."""
    
    @test_timeout(2)  # 2 second timeout
    def test_fast_operation(self):
        """Test that fast operations pass timeout checks."""
        time.sleep(0.1)  # Fast operation
        assert True  # Test passed
    
    def test_performance_context_manager(self):
        """Test performance context manager."""
        with TestPerformanceContext("test_operation", max_time=2):
            time.sleep(0.1)  # Fast operation
    
    def test_performance_context_timeout(self):
        """Test performance context manager catches slow operations."""
        with pytest.raises(TimeoutError):
            with TestPerformanceContext("slow_operation", max_time=1):
                time.sleep(1.5)  # Slow operation
    
    def test_performance_config(self):
        """Test performance configuration is loaded."""
        config = get_test_performance_config()
        
        assert "max_execution_time" in config
        assert "max_users" in config
        assert "max_households" in config
        assert config["max_execution_time"] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])