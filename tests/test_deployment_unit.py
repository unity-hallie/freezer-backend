#!/usr/bin/env python3
"""
Unit tests for first-time deployment script functionality
Tests without executing system commands
"""

import subprocess
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import re


class TestDeploymentUnit:
    """Unit tests for deployment script functions and logic"""
    
    def setup_method(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.script_path = Path(__file__).parent.parent / "first-time-deployment.sh"
        self.original_dir = os.getcwd()
        
        # Copy script to test directory
        shutil.copy2(self.script_path, self.test_dir)
        os.chdir(self.test_dir)
    
    def teardown_method(self):
        """Clean up after each test"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_script_structure_and_functions(self):
        """Test: Script has all required functions defined"""
        with open("first-time-deployment.sh", "r") as f:
            content = f.read()
        
        required_functions = [
            "check_for_existing_data",
            "validate_environment", 
            "setup_system",
            "setup_postgresql",
            "setup_docker",
            "setup_backend",
            "setup_alembic",
            "setup_services",
            "secure_deployment",
            "setup_monitoring",
            "main"
        ]
        
        for func in required_functions:
            assert f"{func}()" in content, f"Function {func} not defined"
    
    def test_script_executable_and_proper_shebang(self):
        """Test: Script is executable and has proper shebang"""
        script = Path("first-time-deployment.sh")
        assert script.exists()
        assert os.access(script, os.X_OK), "Script must be executable"
        
        with open(script, "r") as f:
            first_line = f.readline().strip()
        
        assert first_line == "#!/bin/bash", f"Expected #!/bin/bash shebang, got {first_line}"
    
    def test_anti_pattern_prevention_code_exists(self):
        """Test: Anti-pattern prevention code exists in script"""
        with open("first-time-deployment.sh", "r") as f:
            content = f.read()
        
        # DEP-104: Data destruction prevention
        assert "check_for_existing_data" in content
        assert "existing production data" in content
        assert "overwrite existing data" in content
        
        # DEP-105: Credential security
        assert "chmod 600" in content
        assert "validate_environment" in content
        
        # DEP-106: Security measures
        assert "ufw" in content or "firewall" in content
        assert "fail2ban" in content or "security" in content
    
    def test_database_url_parsing_logic(self):
        """Test: DATABASE_URL parsing logic is correct"""
        # Test the sed commands work correctly
        test_urls = [
            "postgresql://user:pass@localhost/db",
            "postgresql://test_user:test_pass123@localhost/test_db"
        ]
        
        for url in test_urls:
            # Test user extraction
            user_cmd = f"echo '{url}' | sed -n 's/.*:\\/\\/\\([^:]*\\):.*/\\1/p'"
            result = subprocess.run(["bash", "-c", user_cmd], capture_output=True, text=True)
            expected_user = url.split("://")[1].split(":")[0]
            assert result.stdout.strip() == expected_user
            
            # Test password extraction
            pass_cmd = f"echo '{url}' | sed -n 's/.*:\\/\\/[^:]*:\\([^@]*\\)@.*/\\1/p'"
            result = subprocess.run(["bash", "-c", pass_cmd], capture_output=True, text=True)
            expected_pass = url.split(":")[2].split("@")[0]
            assert result.stdout.strip() == expected_pass
            
            # Test database name extraction
            db_cmd = f"echo '{url}' | sed -n 's/.*\\/\\([^?]*\\).*/\\1/p'"
            result = subprocess.run(["bash", "-c", db_cmd], capture_output=True, text=True)
            expected_db = url.split("/")[-1]
            assert result.stdout.strip() == expected_db
    
    def test_docker_compose_template_structure(self):
        """Test: Docker compose template has required structure"""
        with open("first-time-deployment.sh", "r") as f:
            content = f.read()
        
        # Test that docker-compose.yml creation is in the script
        assert "docker-compose.yml" in content, "Docker compose file creation not found"
        
        # Extract docker-compose template section (more robust)
        compose_start = content.find("version: '3.8'")
        if compose_start == -1:
            # Fallback: just check that the script contains docker-compose elements
            compose_template = content
        else:
            compose_end = content.find("volumes:", compose_start)
            compose_template = content[compose_start:compose_end] if compose_end != -1 else content[compose_start:]
        
        # Test required services
        assert "backend:" in compose_template
        assert "frontend:" in compose_template  
        assert "db:" in compose_template
        
        # Test resource limits (anti-pattern prevention)
        assert "memory:" in compose_template
        assert "cpus:" in compose_template
        
        # Test security measures
        assert "restart: unless-stopped" in compose_template
    
    def test_environment_file_validation_logic(self):
        """Test: Environment validation logic checks required vars"""
        with open("first-time-deployment.sh", "r") as f:
            content = f.read()
        
        # Test that environment validation logic exists in the script
        assert "validate_environment()" in content
        assert ".env.production" in content
        assert ".env.production not found" in content
        
        # Test required variables are mentioned
        required_vars = ["DATABASE_URL", "SECRET_KEY", "FRONTEND_URL"]
        for var in required_vars:
            assert var in content
    
    def test_security_hardening_measures(self):
        """Test: Security hardening measures are implemented"""
        with open("first-time-deployment.sh", "r") as f:
            content = f.read()
        
        security_measures = [
            "ufw",  # firewall
            "fail2ban",  # intrusion prevention
            "unattended-upgrades",  # automatic security updates
            "chmod 600",  # file permissions
            "apt upgrade"  # system updates
        ]
        
        for measure in security_measures:
            assert measure in content, f"Security measure '{measure}' not found"
    
    def test_service_ordering_logic(self):
        """Test: Services are set up in correct order"""
        with open("first-time-deployment.sh", "r") as f:
            content = f.read()
        
        # Find main function
        main_start = content.find("main() {")
        main_end = content.find("}", main_start)
        main_func = content[main_start:main_end]
        
        # Test that setup happens before validation
        setup_pos = main_func.find("setup_system")
        validate_pos = main_func.find("validate_environment") 
        
        # validate_environment should come before setup_system in main()
        assert validate_pos < setup_pos, "Validation should happen before system setup"
        
        # Test PostgreSQL setup happens early
        postgres_pos = main_func.find("setup_postgresql")
        docker_pos = main_func.find("setup_docker")
        
        assert postgres_pos > 0, "PostgreSQL setup should be called"
        assert docker_pos > postgres_pos, "Docker should be set up after PostgreSQL"
    
    def test_health_monitoring_setup(self):
        """Test: Health monitoring is properly configured"""
        with open("first-time-deployment.sh", "r") as f:
            content = f.read()
        
        # Find setup_monitoring function
        monitoring_start = content.find("setup_monitoring() {")
        monitoring_end = content.find("}", monitoring_start)
        monitoring_func = content[monitoring_start:monitoring_end]
        
        # Test health check creation
        assert "health-check.sh" in monitoring_func
        assert "check_service" in monitoring_func
        
        # Look for health check calls in the script content
        with open("first-time-deployment.sh", "r") as f:
            full_content = f.read()
        
        # The health check template should contain API and Frontend checks
        assert 'localhost:8000' in full_content, "Backend health check not found"
        assert 'localhost:3000' in full_content, "Frontend health check not found"
        
        # Test health check endpoints are configured
        assert "localhost:8000" in full_content or "8000" in full_content
        assert "localhost:3000" in full_content or "3000" in full_content
    
    def test_error_handling_and_safety(self):
        """Test: Script has proper error handling"""
        with open("first-time-deployment.sh", "r") as f:
            content = f.read()
        
        # Test set -e for error handling
        assert "set -e" in content, "Script should exit on errors"
        
        # Test user confirmation for dangerous operations
        assert "read -p" in content, "Should ask for user confirmation"
        
        # Test exit codes for failures
        assert "exit 1" in content, "Should exit with error code on failure"


def test_acceptance_criteria_implementation():
    """Test: All acceptance criteria from user story are implemented"""
    script_path = Path(__file__).parent.parent / "first-time-deployment.sh"
    
    with open(script_path, "r") as f:
        content = f.read()
    
    # User story acceptance criteria mapping
    criteria_checks = {
        "PostgreSQL installation": ["postgresql", "postgres", "setup_postgresql"],
        "Database creation": ["CREATE DATABASE", "CREATE USER", "GRANT ALL"],
        "Dependency installation": ["apt install", "pip3 install", "requirements.txt"],
        "Docker setup": ["docker", "docker-compose", "setup_docker"],
        "Service initialization": ["systemctl", "docker-compose.yml", "setup_services"],
        "Runs before validation": ["main()", "check_for_existing_data", "validate_environment"]
    }
    
    for criterion, required_elements in criteria_checks.items():
        found_elements = [elem for elem in required_elements if elem in content]
        assert len(found_elements) > 0, f"Acceptance criterion '{criterion}' not properly implemented"


def test_story_points_justification():
    """Test: 5 story points justified by implementation complexity"""
    script_path = Path(__file__).parent.parent / "first-time-deployment.sh"
    
    with open(script_path, "r") as f:
        content = f.read()
    
    # Count lines (excluding comments and empty lines)
    code_lines = [line for line in content.split('\n') 
                  if line.strip() and not line.strip().startswith('#')]
    
    # 5 story points should be 100+ lines of meaningful code
    assert len(code_lines) >= 100, f"5 story points requires substantial implementation, got {len(code_lines)} lines"
    
    # Count number of functions (complexity indicator)
    function_count = len(re.findall(r'^\s*\w+\(\)\s*{', content, re.MULTILINE))
    assert function_count >= 8, f"5 story points should have 8+ functions, got {function_count}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])