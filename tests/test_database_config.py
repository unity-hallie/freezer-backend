"""
Tests for database configuration environment separation.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

# Mock decouple before importing our modules
with patch('database.config') as mock_config, \
     patch('utils.database_config.config') as mock_util_config:
    
    def setup_config_mock(mock_obj, env_vars):
        """Setup config mock to return specified environment variables."""
        def config_side_effect(key, default=None):
            return env_vars.get(key, default)
        mock_obj.side_effect = config_side_effect
    
    class TestDatabaseConfiguration:
        
        def test_test_environment_forces_sqlite(self):
            """Test environment should force SQLite database."""
            env_vars = {
                'ENVIRONMENT': 'test',
                'TEST_DATABASE_URL': 'sqlite:///./test_app.db'
            }
            
            setup_config_mock(mock_config, env_vars)
            setup_config_mock(mock_util_config, env_vars)
            
            # Import after mocking
            from utils.database_config import get_current_environment, get_database_info
            
            assert get_current_environment() == 'test'
            
            # Re-import database module to test configuration
            import importlib
            import database
            importlib.reload(database)
            
            assert database.db_config['type'] == 'sqlite'
            assert 'test' in database.DATABASE_URL
        
        def test_production_requires_postgresql(self):
            """Production environment should require PostgreSQL and reject SQLite."""
            env_vars = {
                'ENVIRONMENT': 'production',
                'DATABASE_URL': 'sqlite:///./app.db'
            }
            
            setup_config_mock(mock_config, env_vars)
            setup_config_mock(mock_util_config, env_vars)
            
            # Should raise error when trying to use SQLite in production
            with pytest.raises(ValueError, match="SQLite databases are not allowed in production"):
                import importlib
                import database
                importlib.reload(database)
        
        def test_production_with_postgresql_succeeds(self):
            """Production environment should accept PostgreSQL configuration."""
            env_vars = {
                'ENVIRONMENT': 'production',
                'DATABASE_URL': 'postgresql://user:pass@localhost/freezer_prod'
            }
            
            setup_config_mock(mock_config, env_vars)
            setup_config_mock(mock_util_config, env_vars)
            
            import importlib
            import database
            importlib.reload(database)
            
            assert database.db_config['type'] == 'postgresql'
            assert database.DATABASE_URL.startswith('postgresql')
        
        def test_development_sqlite_with_warning(self):
            """Development environment should allow SQLite but warn."""
            env_vars = {
                'ENVIRONMENT': 'development',
                'DATABASE_URL': 'sqlite:///./freezer_app.db'
            }
            
            setup_config_mock(mock_config, env_vars)
            setup_config_mock(mock_util_config, env_vars)
            
            with patch('warnings.warn') as mock_warn:
                import importlib
                import database
                importlib.reload(database)
                
                # Should warn about using SQLite in development
                mock_warn.assert_called_once()
                warning_message = mock_warn.call_args[0][0]
                assert 'SQLite in development' in warning_message
                assert 'PostgreSQL' in warning_message
        
        def test_test_mode_override(self):
            """TEST_MODE=true should force test configuration regardless of ENVIRONMENT."""
            env_vars = {
                'ENVIRONMENT': 'development',
                'TEST_MODE': 'true',
                'TEST_DATABASE_URL': 'sqlite:///./override_test.db'
            }
            
            setup_config_mock(mock_config, env_vars)
            setup_config_mock(mock_util_config, env_vars)
            
            from utils.database_config import is_test_mode
            assert is_test_mode() == True
            
            import importlib
            import database
            importlib.reload(database)
            
            assert database.db_config['type'] == 'sqlite'
            assert 'override_test' in database.DATABASE_URL


if __name__ == '__main__':
    pytest.main([__file__])