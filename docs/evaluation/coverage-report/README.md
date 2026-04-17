# Coverage Report

This project generates coverage with `pytest-cov` from the backend test suite.

## Local generation

From `backend/`:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -p pytest_cov --cov=. --cov-config=.coveragerc --cov-report=term-missing --cov-report=html --cov-report=xml tests
```

Generated files:
- `coverage.xml`
- `htmlcov/index.html`

## CI artifact

Each CI run uploads a `backend-coverage` artifact containing:
- `backend/coverage.xml`
- `backend/htmlcov/`

Open the Actions run, then download `backend-coverage` to view the HTML report.
