# Testing Guide

## Test Categories

### 🟢 Unit Tests (Fast, Isolated)
```bash
# Run only unit tests - no external dependencies
pytest -m unit

# Examples: Pure logic, utilities, schema validation
pytest tests/test_auth.py::test_password_hashing
```

### 🟡 Integration Tests (Database Required)  
```bash
# Run integration tests - requires database setup
ENVIRONMENT=test pytest -m integration

# Examples: API endpoints, database operations, full workflows
pytest tests/test_items.py tests/test_households.py
```

### 🔴 Script Tests (Brittle, Shell Dependencies)
```bash
# Run script tests - requires shell scripts, external commands
pytest -m script

# WARNING: These tests are brittle and test implementation details
# Consider replacing with behavior-focused integration tests
```

## Quick Commands

```bash
# Fast feedback loop - unit tests only
pytest -m "unit"

# Standard test run - skip brittle script tests  
pytest -m "not script"

# Full test suite (may have brittle failures)
pytest

# Specific test file
ENVIRONMENT=test pytest tests/test_households.py -v
```

## Frontend Tests

### Unit Tests (No Backend Required)
```bash
cd freezer-frontend
npm test -- --run tests/unit/
```

### Integration Tests (Backend Required)
```bash
# Terminal 1: Start backend
cd freezer-backend && ENVIRONMENT=test python -m uvicorn main:app --reload

# Terminal 2: Run frontend integration tests
cd freezer-frontend && npm test -- --run tests/integration/
```

## Test Environment Setup

**Backend:**
- Uses SQLite test database automatically
- `ENVIRONMENT=test` forces test mode
- Database isolated per test run

**Frontend:**  
- Integration tests expect backend running on localhost:8000
- Unit tests run standalone with mocked services

## Best Practices

1. **Write unit tests first** - fast feedback
2. **Integration tests for workflows** - real database behavior  
3. **Avoid script tests** - brittle and implementation-focused
4. **Separate unit vs integration** - clear dependencies