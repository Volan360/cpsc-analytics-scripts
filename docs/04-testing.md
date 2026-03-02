# Testing

## Running Tests

```powershell
# Activate the virtual environment first
.\venv\Scripts\Activate.ps1

# Run all tests
pytest

# Run with coverage report
pytest --cov=src tests/

# Generate HTML coverage report
pytest --cov=src --cov-report=html tests/
# → open htmlcov/index.html

# Run a specific test file
pytest tests/test_cash_flow.py

# Run with verbose output
pytest -v
```

## Test Suite

| Test file | Coverage target |
|-----------|----------------|
| `test_calculations.py` | `src/utils/calculations.py` |
| `test_date_utils.py` | `src/utils/date_utils.py` |
| `test_cash_flow.py` | `src/analytics/cash_flow.py` |
| `test_categories.py` | `src/analytics/categories.py` |
| `test_goals.py` | `src/analytics/goals.py` |
| `test_institutions.py` | `src/analytics/institutions.py` |
| `test_health_score.py` | `src/analytics/health_score.py` |
| `test_network.py` | `src/analytics/network.py` |
| `test_visualization.py` | `src/visualization/charts.py`, `reports.py`, `s3_uploader.py` |
| `test_lambda_handlers.py` | `src/lambda_handlers/analytics_handler.py`, `report_handler.py` |

> **Note:** `test_lambda_handlers.py` currently has an import error (`cannot import name 'handler'`). The Lambda entry point is `lambda_handler`, not `handler`. Tests in that file need to be updated to import `lambda_handler`.

Test fixtures and shared mock helpers are in `tests/conftest.py`.

## pytest Configuration

Configured in `setup.cfg`:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --verbose --color=yes --strict-markers -ra
```

## Coverage Configuration

```ini
[coverage:run]
source = src
omit = */tests/*, */conftest.py, */__init__.py

[coverage:report]
precision = 2
show_missing = True
```

## Code Quality

```powershell
# Auto-format (line length 120, per flake8 config)
black src/ tests/

# Lint
flake8 src/ tests/

# Type checking
mypy src/
```

**flake8 settings** (`setup.cfg`):
- Max line length: 120
- Ignored: `E203`, `W503`

**mypy settings**: Python 3.11, `ignore_missing_imports = True`

## Dependencies

All development and runtime dependencies are in `requirements.txt`:

| Package | Purpose |
|---------|---------|
| `boto3` | AWS SDK (DynamoDB, Lambda, S3) |
| `networkx` | Graph construction and analysis |
| `plotly` | Interactive chart generation (Plotly charts embedded in HTML reports) |
| `pandas` | Data manipulation in analytics modules |
| `numpy` | Numerical calculations |
| `scikit-learn` | Statistical helpers (anomaly detection) |
| `seaborn` / `matplotlib` | Additional chart styles |
| `python-dateutil` | Date parsing utilities |
| `jinja2` | HTML report templates |
| `kaleido` | Plotly static image export |
| `fpdf2` | PDF generation (available but not currently used in reports) |
| `pytest` | Test runner |
| `pytest-cov` | Coverage plugin |
| `pytest-mock` | Mock helpers |
| `black` | Code formatter |
| `flake8` | Linter |
| `mypy` | Type checker |
