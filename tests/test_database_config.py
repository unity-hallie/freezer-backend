"""
Tests for database configuration environment separation.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock


class TestDatabaseConfiguration:
        
    def test_test_environment_forces_sqlite(self):
        """Test environment should force SQLite database."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'test',
            'TEST_DATABASE_URL': 'sqlite:///./test_app.db'
        }):
            # Clear module cache to force reimport
            modules_to_clear = ['database', 'utils.database_config']
            for module in modules_to_clear:
                if module in sys.modules:
                    del sys.modules[module]
            
            # Import after setting environment
            from utils.database_config import get_current_environment
            import database
            
            assert get_current_environment() == 'test'
            assert database.db_config['type'] == 'sqlite'
            assert 'test' in database.DATABASE_URL
        
    def test_production_requires_postgresql(self):
        """Production environment should require PostgreSQL and reject SQLite."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'DATABASE_URL': 'sqlite:///./app.db'
        }):
            # Clear module cache to force reimport
            modules_to_clear = ['database', 'utils.database_config']
            for module in modules_to_clear:
                if module in sys.modules:
                    del sys.modules[module]
            
            # Should raise error when trying to use SQLite in production
            with pytest.raises(ValueError, match="SQLite databases are not allowed in production"):
                import database
        
    def test_production_with_postgresql_succeeds(self):
        """Production environment should accept PostgreSQL configuration."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'DATABASE_URL': 'postgresql://user:pass@localhost/freezer_prod'
        }):
            # Clear module cache to force reimport
            modules_to_clear = ['database', 'utils.database_config']
            for module in modules_to_clear:
                if module in sys.modules:
                    del sys.modules[module]
            
            import database
            
            assert database.db_config['type'] == 'postgresql'
            assert database.DATABASE_URL.startswith('postgresql')
        
    def test_development_sqlite_with_warning(self):
        """Development environment should allow SQLite but warn."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'development',
            'DATABASE_URL': 'sqlite:///./freezer_app.db'
        }):
            # Clear module cache to force reimport
            modules_to_clear = ['database', 'utils.database_config']
            for module in modules_to_clear:
                if module in sys.modules:
                    del sys.modules[module]
            
            with patch('warnings.warn') as mock_warn:
                import database
                
                # Should warn about using SQLite in development
                # Check that at least one call contains our warning
                warning_calls = [str(call) for call in mock_warn.call_args_list]
                sqlite_warnings = [call for call in warning_calls if 'SQLite in development' in call]
                assert len(sqlite_warnings) >= 1, f"Expected SQLite warning, got: {warning_calls}"
        
    def test_test_mode_override(self):
        """TEST_MODE=true should force test configuration regardless of ENVIRONMENT."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'development',
            'TEST_MODE': 'true',
            'TEST_DATABASE_URL': 'sqlite:///./override_test.db'
        }):
            # Clear module cache to force reimport
            modules_to_clear = ['database', 'utils.database_config']
            for module in modules_to_clear:
                if module in sys.modules:
                    del sys.modules[module]
            
            from utils.database_config import is_test_mode
            import database
            
            assert is_test_mode() == True
            assert database.db_config['type'] == 'sqlite'
            assert 'override_test' in database.DATABASE_URL


if __name__ == '__main__':
    pytest.main([__file__])