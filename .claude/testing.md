# Testing Configuration

## Execution

```bash
# All tests
cd app && pytest

# Specific tests
pytest tests/test_example.py -v

# Only changed tests (fast)
pytest --testmon

# With coverage
pytest --cov=. --cov-report=html
```

## Fixtures

Defined in `conftest.py`:
- `db_session` — In-memory SQLite

## Test Categories

| Category | Files | External? | When? |
|----------|-------|-----------|-------|
| **Unit tests** | `test_*.py` | No | Always (`pytest`) |
| **Integration** | `test_*_integration.py` | Maybe | Marked with `@pytest.mark.integration` |

## Conventions

- Filename: `test_<feature>.py`
- Use fixtures from `conftest.py`
- Async tests with `@pytest.mark.asyncio`
- Use `@pytest.mark.parametrize` instead of loops
