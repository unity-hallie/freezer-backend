"""
Test performance monitoring utilities.
"""

import time
import warnings
from typing import Any, Callable, Optional
from functools import wraps
from utils.test_data import get_test_performance_config


def test_timeout(max_seconds: Optional[int] = None):
    """Decorator to enforce test execution time limits."""
    config = get_test_performance_config()
    max_time = max_seconds or config['max_execution_time']
    warning_threshold = config['timeout_warning_threshold']
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Warning for slow tests
                if execution_time > warning_threshold:
                    warnings.warn(
                        f"Test {func.__name__} took {execution_time:.2f}s "
                        f"(warning threshold: {warning_threshold}s)",
                        UserWarning
                    )
                
                # Fail for tests that exceed max time
                if execution_time > max_time:
                    raise TimeoutError(
                        f"Test {func.__name__} exceeded {max_time}s limit "
                        f"(took {execution_time:.2f}s). Consider optimizing test data volume."
                    )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                if execution_time > max_time:
                    raise TimeoutError(
                        f"Test {func.__name__} timed out at {execution_time:.2f}s "
                        f"due to error: {str(e)}"
                    ) from e
                raise
        
        return wrapper
    return decorator


class TestDataVolumeMonitor:
    """Monitor and enforce test data volume limits."""
    
    def __init__(self):
        self.config = get_test_performance_config()
        self.created_records = {
            'users': 0,
            'households': 0,
            'items': 0,
            'locations': 0
        }
    
    def record_created(self, record_type: str, count: int = 1):
        """Record that test data was created."""
        if record_type in self.created_records:
            self.created_records[record_type] += count
            self._check_limits(record_type)
    
    def _check_limits(self, record_type: str):
        """Check if we've exceeded volume limits."""
        current_count = self.created_records[record_type]
        limits = {
            'users': self.config['max_users'],
            'households': self.config['max_households'],
            'items': self.config['max_items'],
            'locations': 5
        }
        
        limit = limits.get(record_type, 10)
        if current_count > limit:
            raise ValueError(
                f"Test exceeded {record_type} limit: {current_count} > {limit}. "
                f"Use TestDataLimiter utilities to create controlled test data."
            )
    
    def get_summary(self) -> dict:
        """Get summary of test data creation."""
        return {
            'created_records': self.created_records.copy(),
            'limits': {
                'users': self.config['max_users'],
                'households': self.config['max_households'],
                'items': self.config['max_items']
            }
        }


# Global monitor instance for test sessions
test_monitor = TestDataVolumeMonitor()


def reset_test_monitor():
    """Reset the test monitor for new test session."""
    global test_monitor
    test_monitor = TestDataVolumeMonitor()


# Context manager for test performance tracking
class TestPerformanceContext:
    """Context manager for tracking test performance."""
    
    def __init__(self, test_name: str, max_time: Optional[int] = None):
        self.test_name = test_name
        self.max_time = max_time or get_test_performance_config()['max_execution_time']
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            execution_time = time.time() - self.start_time
            
            if execution_time > self.max_time:
                raise TimeoutError(
                    f"Test {self.test_name} exceeded {self.max_time}s limit "
                    f"(took {execution_time:.2f}s)"
                )


# Convenience function for quick performance checks
def assert_test_performance(start_time: float, test_name: str, max_seconds: Optional[int] = None):
    """Assert test completed within performance limits."""
    execution_time = time.time() - start_time
    max_time = max_seconds or get_test_performance_config()['max_execution_time']
    
    if execution_time > max_time:
        raise AssertionError(
            f"Performance test failed: {test_name} took {execution_time:.2f}s "
            f"(limit: {max_time}s)"
        )
    
    return execution_time