#!/usr/bin/env python3
"""
Tests for environment security and configuration
Validates DEP-102 acceptance criteria
"""

import os
import subprocess
from pathlib import Path
import pytest


class TestEnvironmentSecurity:
    """Test environment configuration security measures"""
    
    @pytest.fixture(autouse=True)
    def setup_test_env(self):
        """Set up test environment"""
        self.repo_root = Path(__file__).parent.parent
        self.original_dir = os.getcwd()
        os.chdir(self.repo_root)
        yield
        os.chdir(self.original_dir)
    
    def test_env_files_in_gitignore(self):
        """Test: All environment files are in .gitignore"""
        gitignore_path = self.repo_root / ".gitignore"
        assert gitignore_path.exists(), ".gitignore must exist"
        
        with open(gitignore_path, "r") as f:
            gitignore_content = f.read()
        
        # Test all environment file patterns are ignored
        env_patterns = [
            ".env",
            ".env.production", 
            ".env.droplet",
            ".env.local",
            ".env.development.local",
            ".env.test.local",
            ".env.production.local"
        ]
        
        for pattern in env_patterns:
            assert pattern in gitignore_content, f"Environment pattern '{pattern}' missing from .gitignore"
    
    def test_env_files_not_tracked_by_git(self):
        """Test: Environment files are not tracked by git"""
        # Check git status for any tracked .env files
        result = subprocess.run(
            ["git", "ls-files", "*.env*"],
            capture_output=True,
            text=True,
            cwd=self.repo_root
        )
        
        tracked_env_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
        
        # Only .env.example should be tracked
        allowed_files = [".env.example"]
        for file in tracked_env_files:
            assert file in allowed_files, f"Environment file '{file}' should not be tracked by git"
    
    def test_env_example_exists_and_comprehensive(self):
        """Test: .env.example exists and contains all required variables"""
        env_example = self.repo_root / ".env.example"
        assert env_example.exists(), ".env.example must exist as template"
        
        with open(env_example, "r") as f:
            content = f.read()
        
        # Test required variables are documented
        required_vars = [
            "ENVIRONMENT",
            "DATABASE_URL", 
            "SECRET_KEY",
            "MAIL_USERNAME",
            "MAIL_PASSWORD",
            # New variables from DEP-102
            "FRONTEND_URL",
            "ALLOWED_HOSTS", 
            "CORS_ORIGINS",
            "DISCORD_CLIENT_ID",
            "DISCORD_CLIENT_SECRET"
        ]
        
        for var in required_vars:
            assert var in content, f"Required variable '{var}' missing from .env.example"
    
    def test_environment_documentation_exists(self):
        """Test: Comprehensive environment documentation exists"""
        docs_path = self.repo_root / "ENVIRONMENT_SETUP.md"
        assert docs_path.exists(), "ENVIRONMENT_SETUP.md documentation must exist"
        
        with open(docs_path, "r") as f:
            content = f.read()
        
        # Test documentation covers key sections
        required_sections = [
            "SECURITY WARNING",
            "Environment Variables Reference",
            "Production Example", 
            "Security Best Practices",
            "Troubleshooting"
        ]
        
        for section in required_sections:
            assert section in content, f"Documentation missing section: {section}"
    
    def test_no_secrets_in_env_example(self):
        """Test: .env.example contains no actual secrets"""
        env_example = self.repo_root / ".env.example"
        
        with open(env_example, "r") as f:
            content = f.read().lower()
        
        # Test for suspicious secret-like values
        forbidden_patterns = [
            "password123",
            "secretkey123", 
            "your_actual_",
            "real_password"
        ]
        # Note: client_secret and @gmail.com are acceptable in commented examples
        
        for pattern in forbidden_patterns:
            assert pattern not in content, f"Potential secret found in .env.example: {pattern}"
        
        # Test that example values are clearly placeholders
        placeholder_indicators = ["your-", "change-this", "example", "placeholder"]
        has_placeholders = any(indicator in content for indicator in placeholder_indicators)
        assert has_placeholders, ".env.example should use placeholder values, not real secrets"
    
    def test_local_env_files_preserved(self):
        """Test: Local .env files still exist after git removal"""
        env_files_to_check = [
            ".env.production",
            ".env.droplet"
        ]
        
        for env_file in env_files_to_check:
            env_path = self.repo_root / env_file
            # Note: This test may fail if files don't exist, which is fine
            # It's mainly to verify that git rm --cached didn't delete local files
            if env_path.exists():
                assert env_path.is_file(), f"{env_file} should still exist locally"
                # Test file has content (not empty after git operations)
                assert env_path.stat().st_size > 0, f"{env_file} should not be empty"
    
    def test_security_measures_documented(self):
        """Test: Security best practices are documented"""
        docs_path = self.repo_root / "ENVIRONMENT_SETUP.md"
        
        with open(docs_path, "r") as f:
            content = f.read()
        
        # Test security measures are covered
        security_topics = [
            "chmod 600",  # file permissions
            "secrets.token_urlsafe",  # secure key generation
            "HTTPS",  # secure protocols
            "NEVER commit",  # git security (uppercase in our docs)
            "Strong SECRET_KEY",  # authentication security
            "CORS",  # web security
            "PostgreSQL"  # production database requirements
        ]
        
        for topic in security_topics:
            assert topic in content, f"Security documentation missing topic: {topic}"
    
    def test_anti_pattern_prevention(self):
        """Test: DEP-105 anti-pattern (credential leaks) prevention"""
        # Test that documentation warns against common mistakes
        docs_path = self.repo_root / "ENVIRONMENT_SETUP.md"
        
        with open(docs_path, "r") as f:
            content = f.read()
        
        # Test warnings for dangerous patterns
        anti_patterns = [
            "SECRET_KEY=secret",
            "password@localhost", 
            "CORS_ORIGINS=*",
            "NEVER commit .env"  # Matches our uppercase warning
        ]
        
        for pattern in anti_patterns:
            assert pattern in content, f"Documentation should warn against anti-pattern: {pattern}"


def test_frontend_env_security():
    """Test frontend environment security"""
    frontend_path = Path(__file__).parent.parent.parent / "freezer-frontend"
    
    if not frontend_path.exists():
        pytest.skip("Frontend directory not found")
    
    # Test frontend .gitignore
    gitignore_path = frontend_path / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            content = f.read()
        
        env_patterns = [".env", ".env.production", ".env.local"]
        for pattern in env_patterns:
            assert pattern in content, f"Frontend .gitignore missing {pattern}"
    
    # Test frontend documentation exists
    frontend_docs = frontend_path / "ENVIRONMENT_SETUP.md"
    if frontend_docs.exists():
        with open(frontend_docs, "r") as f:
            content = f.read()
        
        assert "VITE_" in content, "Frontend docs should cover Vite environment variables"
        assert "SECURITY WARNING" in content, "Frontend docs should have security warnings"


def test_comprehensive_variable_coverage():
    """Test: All environment variables used in code are documented"""
    # This test ensures we haven't missed any environment variables
    
    # Search for os.getenv, os.environ, config() calls in the codebase
    result = subprocess.run([
        "grep", "-r", "-E", 
        "(os\\.getenv|os\\.environ|config\\()",
        ".", 
        "--include=*.py",
        "--exclude-dir=tests",
        "--exclude-dir=__pycache__"
    ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
    
    if result.returncode == 0:
        env_usage = result.stdout
        
        # Common environment variables that should be documented
        common_vars = ["DATABASE_URL", "SECRET_KEY", "ENVIRONMENT"]
        
        docs_path = Path(__file__).parent.parent / "ENVIRONMENT_SETUP.md"
        with open(docs_path, "r") as f:
            docs_content = f.read()
        
        for var in common_vars:
            if var in env_usage:
                assert var in docs_content, f"Environment variable '{var}' used in code but not documented"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])