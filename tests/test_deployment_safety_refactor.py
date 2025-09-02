#!/usr/bin/env python3
"""
Tests for refactored deployment-safety.sh script
Validates DEP-103 acceptance criteria: validation-only, no setup
"""

import os
import subprocess
from pathlib import Path
import pytest


class TestDeploymentSafetyRefactor:
    """Test that deployment-safety.sh only validates, doesn't setup"""
    
    @pytest.fixture(autouse=True)
    def setup_test_env(self):
        """Set up test environment"""
        self.repo_root = Path(__file__).parent.parent
        self.original_dir = os.getcwd()
        os.chdir(self.repo_root)
        self.script_path = self.repo_root / "deployment-safety.sh"
        yield
        os.chdir(self.original_dir)
    
    def test_script_exists_and_executable(self):
        """Test: Refactored script exists and is executable"""
        assert self.script_path.exists(), "deployment-safety.sh must exist"
        assert os.access(self.script_path, os.X_OK), "Script must be executable"
    
    def test_script_header_indicates_validation_only(self):
        """Test: Script header clearly indicates validation-only purpose"""
        with open(self.script_path, 'r') as f:
            content = f.read()
        
        # Test header indicates validation purpose
        validation_indicators = [
            "Update Validation Only",
            "Validates existing database",
            "first-time-deployment.sh",
            "validation only"
        ]
        
        for indicator in validation_indicators:
            assert indicator in content, f"Missing validation indicator: {indicator}"
    
    def test_no_setup_operations_in_script(self):
        """Test: Script contains no setup/installation operations"""
        with open(self.script_path, 'r') as f:
            content = f.read()
        
        # Test that setup operations are NOT present
        forbidden_operations = [
            "apt install",
            "createdb",
            "CREATE DATABASE",
            "CREATE USER",
            "systemctl start",
            "docker-compose up",
            "pip install",
            "mkdir -p"
        ]
        
        for operation in forbidden_operations:
            assert operation not in content, f"Setup operation found in validation script: {operation}"
    
    def test_migration_function_is_check_only(self):
        """Test: Migration function only checks status, doesn't run migrations"""
        with open(self.script_path, 'r') as f:
            content = f.read()
        
        # Test migration function is check-only
        assert "check_migration_status" in content, "Should have check_migration_status function"
        assert "alembic current" in content, "Should check current migration"
        assert "alembic heads" in content, "Should check head migration"
        
        # Test it doesn't actually run migrations
        assert "alembic upgrade head" not in content, "Should NOT run migrations"
        assert "run_migrations" not in content, "Should not have run_migrations function"
    
    def test_helpful_first_time_guidance(self):
        """Test: Script provides helpful guidance for first-time deployment"""
        with open(self.script_path, 'r') as f:
            content = f.read()
        
        guidance_messages = [
            "first-time-deployment.sh",
            "For first-time setup",
            "database may not be initialized",
            "If this is your first deployment"
        ]
        
        for message in guidance_messages:
            assert message in content, f"Missing first-time guidance: {message}"
    
    def test_validation_functions_preserved(self):
        """Test: All validation functions are preserved"""
        with open(self.script_path, 'r') as f:
            content = f.read()
        
        # Test core validation functions exist
        validation_functions = [
            "check_database_health",
            "check_session_compatibility", 
            "check_data_integrity",
            "check_migration_status"  # New validation-only version
        ]
        
        for function in validation_functions:
            assert function in content, f"Missing validation function: {function}"
    
    def test_clear_separation_messaging(self):
        """Test: Script clearly communicates separation from first-time setup"""
        with open(self.script_path, 'r') as f:
            content = f.read()
        
        separation_messages = [
            "DEPLOYMENT UPDATE VALIDATION",
            "validates existing deployments only",
            "Remember: This script only validates",
            "For first-time setup, use:"
        ]
        
        for message in separation_messages:
            assert message in content, f"Missing separation message: {message}"
    
    def test_exit_codes_for_uninitialized_database(self):
        """Test: Script exits appropriately when database is not initialized"""
        with open(self.script_path, 'r') as f:
            content = f.read()
        
        # Test that script handles uninitialized database gracefully
        error_handling = [
            "exit 1",  # Should exit on database connection failure
            "database may not be initialized",
            "first-time-deployment.sh"  # Should suggest correct script
        ]
        
        for handling in error_handling:
            assert handling in content, f"Missing error handling: {handling}"
    
    def test_success_message_is_validation_focused(self):
        """Test: Success message reflects validation-only purpose"""
        with open(self.script_path, 'r') as f:
            content = f.read()
        
        # Test success message is appropriate for validation
        success_indicators = [
            "DEPLOYMENT UPDATE VALIDATION PASSED",
            "Existing database is healthy",
            "Migration status verified",
            "Safe to proceed with update deployment"
        ]
        
        for indicator in success_indicators:
            assert indicator in content, f"Missing validation success message: {indicator}"
        
        # Test success message doesn't claim to have done setup
        forbidden_success = [
            "Database migrations completed",
            "Installation completed",
            "Setup completed"
        ]
        
        for forbidden in forbidden_success:
            assert forbidden not in content, f"Success message incorrectly claims setup: {forbidden}"
    
    def test_script_dependency_separation(self):
        """Test: Script depends on first-time-deployment.sh for setup"""
        # This test verifies the architectural separation
        first_time_script = self.repo_root / "first-time-deployment.sh"
        assert first_time_script.exists(), "first-time-deployment.sh must exist for setup tasks"
        
        with open(self.script_path, 'r') as f:
            safety_content = f.read()
        
        with open(first_time_script, 'r') as f:
            setup_content = f.read()
        
        # Test that setup operations are in first-time script, not safety script
        setup_operations = ["createdb", "apt install", "systemctl"]
        
        for operation in setup_operations:
            if operation in setup_content:
                assert operation not in safety_content, f"Setup operation {operation} should only be in first-time-deployment.sh"


def test_acceptance_criteria_coverage():
    """Test: All DEP-103 acceptance criteria are met"""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "deployment-safety.sh"
    
    with open(script_path, 'r') as f:
        content = f.read()
    
    acceptance_criteria = {
        "Validation only": ["check_", "validate", "verify"],
        "No setup operations": ["apt install", "createdb", "systemctl start"],  # These should NOT be present
        "Clear separation messaging": ["first-time-deployment.sh", "validation only"],
        "Migration status check": ["alembic current", "check_migration_status"],
        "Helpful error messages": ["first deployment", "not initialized"]
    }
    
    for criteria, indicators in acceptance_criteria.items():
        if criteria == "No setup operations":
            # These should NOT be present
            for indicator in indicators:
                assert indicator not in content, f"Setup operation found (violates validation-only): {indicator}"
        else:
            # These should be present
            found = any(indicator in content for indicator in indicators)
            assert found, f"Acceptance criteria not met: {criteria}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])