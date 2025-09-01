import pytest
from sqlalchemy import inspect
from database import engine

def test_users_table_exists():
    """
    Tests that the users table exists in the database.
    This is a basic check to ensure that deployments don't accidentally
    drop or rename critical tables.
    """
    inspector = inspect(engine)
    assert "users" in inspector.get_table_names()

def test_users_table_has_critical_columns():
    """
    Tests that the users table has critical columns like email and hashed_password.
    This prevents accidental removal of columns that would break user authentication.
    """
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns('users')]
    assert 'email' in columns
    assert 'hashed_password' in columns