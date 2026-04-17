# Coverage Report

This project generates code coverage with `pytest-cov` for backend tests.

## Local Generation

From `backend/`:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -p pytest_cov --cov=. --cov-config=.coveragerc --cov-report=term-missing --cov-report=html --cov-report=xml tests
```

Generated outputs:
- `coverage.xml`
- `htmlcov/index.html`

## CI Artifact

Each CI run uploads coverage artifacts.

- Artifact name: `backend-coverage`
- Includes:
  - `backend/coverage.xml`
  - `backend/htmlcov/`

Open the GitHub Actions run and download `backend-coverage` to view the HTML report.
