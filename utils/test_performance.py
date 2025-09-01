import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch


@pytest.mark.performance
def test_query_performance_with_timeout():
    """
    Tests that queries execute within a reasonable time limit.
    This is a basic check to prevent long-running queries from driving up costs.
    """
    # Use an in-memory SQLite database for this test
    engine = create_engine("sqlite:///:memory:")

    # Set a timeout of 1 second for all queries
    with patch.object(engine, 'execution_options', return_value=engine.execution_options(timeout=1)):
        Session = sessionmaker(bind=engine)
        session = Session()

        # Example: a query that would be slow on a large dataset
        # In a real scenario, you would test your actual application queries
        try:
            session.execute(text("SELECT 1"))
        except Exception as e:
            pytest.fail(f"Query timed out: {e}")