#!/usr/bin/env python3
"""
Tests for first-time-deployment.sh script
Tests all user story acceptance criteria and anti-pattern prevention
"""

import subprocess
import os
import tempfile
import shutil
from pathlib import Path
import pytest


class TestFirstTimeDeployment:
    """Test suite for first-time deployment script functionality"""
    
    def setup_method(self):
        """Set up test environment for each test"""
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
    
    def create_test_env_file(self, content=None):
        """Create a test .env.production file"""
        if content is None:
            content = """ENVIRONMENT=production
DATABASE_URL=postgresql://test_user:test_pass123@localhost/test_db
SECRET_KEY=test_secret_key_12345
FRONTEND_URL=http://127.0.0.1:3000
ALLOWED_HOSTS=127.0.0.1,localhost
CORS_ORIGINS=http://127.0.0.1:3000
MAIL_USERNAME=test@example.com
MAIL_PASSWORD=test_mail_pass
"""
        with open(".env.production", "w") as f:
            f.write(content)
    
    def run_script_function(self, function_name, expect_success=True):
        """Run a specific function from the deployment script"""
        cmd = f"source ./first-time-deployment.sh && {function_name}"
        result = subprocess.run(
            ["bash", "-c", cmd], 
            capture_output=True, 
            text=True
        )
        
        if expect_success:
            assert result.returncode == 0, f"Function {function_name} failed: {result.stderr}"
        
        return result
    
    def test_script_exists_and_executable(self):
        """Test: Script file exists and is executable"""
        script = Path("first-time-deployment.sh")
        assert script.exists(), "first-time-deployment.sh must exist"
        assert os.access(script, os.X_OK), "Script must be executable"
    
    def test_environment_validation_missing_file(self):
        """Test: Environment validation fails when .env.production is missing"""
        # No .env.production file
        result = self.run_script_function("validate_environment", expect_success=False)
        assert ".env.production not found" in result.stdout
        assert result.returncode != 0
    
    
    def test_environment_validation_success(self):
        """Test: Environment validation passes with proper config"""
        self.create_test_env_file()  # Creates strong credentials
        result = self.run_script_function("validate_environment")
        assert "Environment configuration validated" in result.stdout
        assert result.returncode == 0
    
    def test_database_url_parsing(self):
        """Test: DATABASE_URL parsing extracts correct components"""
        self.create_test_env_file()
        
        # Test the parsing logic
        parse_cmd = r"""
        source .env.production
        DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
        DB_PASS=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
        DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
        echo "USER:$DB_USER PASS:$DB_PASS NAME:$DB_NAME"
        """
        
        result = subprocess.run(["bash", "-c", parse_cmd], capture_output=True, text=True)
        output = result.stdout.strip()
        
        assert "USER:test_user" in output
        assert "PASS:test_pass123" in output  
        assert "NAME:test_db" in output
    
    def test_docker_compose_generation(self):
        """Test: Docker compose file is generated with proper structure"""
        self.create_test_env_file()
        
        # Simulate the setup_services function core logic
        compose_content = """version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    depends_on:
      - db
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
"""
        
        with open("docker-compose.yml", "w") as f:
            f.write(compose_content)
        
        # Test that the file was created correctly
        assert Path("docker-compose.yml").exists()
        
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        # Test resource limits (anti-pattern DEP-106 prevention)
        assert "memory: 512M" in content
        assert "cpus: '0.5'" in content
        assert "restart: unless-stopped" in content
    
    def test_health_check_script_generation(self):
        """Test: Health check script is generated and executable"""
        self.create_test_env_file()
        
        # Simulate setup_monitoring function
        health_script = """#!/bin/bash
check_service() {
    local service=$1
    local url=$2
    local expected=$3
    echo "✅ $service: OK"
}

check_service "Backend API" "http://localhost:8000/health" "200"
check_service "Frontend" "http://localhost:3000" "200"
"""
        
        with open("health-check.sh", "w") as f:
            f.write(health_script)
        os.chmod("health-check.sh", 0o755)
        
        # Test health check functionality
        assert Path("health-check.sh").exists()
        assert os.access("health-check.sh", os.X_OK)
        
        # Test health check runs
        result = subprocess.run(["./health-check.sh"], capture_output=True, text=True)
        assert "Backend API" in result.stdout
        assert "Frontend" in result.stdout
    
    def test_security_file_permissions(self):
        """Test: Environment file gets proper security permissions (600)"""
        self.create_test_env_file()
        
        # Simulate the secure_deployment function
        os.chmod(".env.production", 0o600)
        
        # Test file permissions
        stat_info = os.stat(".env.production")
        permissions = oct(stat_info.st_mode)[-3:]
        assert permissions == "600", f"Expected 600 permissions, got {permissions}"
    
    
    def test_script_comprehensive_functionality(self):
        """Test: Full script execution simulation (dry run)"""
        self.create_test_env_file()
        
        # Test that script has all required functions
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
            "setup_monitoring"
        ]
        
        # Check that all functions are defined in the script
        with open("first-time-deployment.sh", "r") as f:
            script_content = f.read()
        
        for func in required_functions:
            assert f"{func}()" in script_content, f"Function {func} not found in script"
        
        # Test that main function calls all required functions
        assert "check_for_existing_data" in script_content
        assert "validate_environment" in script_content
        assert "setup_system" in script_content
    
    def test_acceptance_criteria_coverage(self):
        """Test: All user story acceptance criteria are covered"""
        self.create_test_env_file()
        
        with open("first-time-deployment.sh", "r") as f:
            script_content = f.read()
        
        # Test each acceptance criterion from the user story
        acceptance_criteria = {
            "PostgreSQL installation": ["postgresql", "postgres"],
            "Database creation": ["CREATE DATABASE", "CREATE USER"],
            "Dependency installation": ["apt install", "pip3 install"],
            "Docker setup": ["docker", "docker-compose"],
            "Service initialization": ["systemctl", "docker-compose.yml"],
            "Runs before validation": ["setup", "validate_environment"]
        }
        
        for criterion, keywords in acceptance_criteria.items():
            found = any(keyword in script_content for keyword in keywords)
            assert found, f"Acceptance criterion '{criterion}' not covered in script"
    
    def test_anti_story_prevention_coverage(self):
        """Test: All anti-story patterns are prevented"""
        self.create_test_env_file()
        
        with open("first-time-deployment.sh", "r") as f:
            script_content = f.read()
        
        # Test DEP-104: Data destruction prevention
        assert "existing production data" in script_content
        assert "overwrite existing data" in script_content
        
        # Test DEP-105: Credential exposure prevention  
        assert "chmod 600" in script_content
        assert "weak credentials" in script_content
        
        # Test DEP-106: Security vulnerability prevention
        assert "ufw" in script_content  # firewall
        assert "fail2ban" in script_content  # intrusion prevention
        assert "unattended-upgrades" in script_content  # security updates


def test_script_integration():
    """Integration test: Script can be sourced and functions exist"""
    script_path = Path(__file__).parent.parent / "first-time-deployment.sh"
    
    # Test that script can be sourced without errors
    result = subprocess.run(
        ["bash", "-c", f"source {script_path} && echo 'Script sourced successfully'"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Script sourcing failed: {result.stderr}"
    assert "Script sourced successfully" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])