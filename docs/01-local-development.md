# Local Development

## Prerequisites

| Tool | Required Version |
|------|-----------------|
| Python | 3.11 or higher |
| AWS CLI | Configured with `cpsc-devops` profile |

The analytics scripts connect to real AWS DynamoDB tables even locally. Ensure your `cpsc-devops` AWS profile has read access to `Institutions-devl`, `Transactions-devl`, and `Goals-devl`.

---

## First-Time Setup

```powershell
# Navigate into the analytics directory
cd cpsc-analytics-scripts

# Create a virtual environment
python -m venv venv

# Activate it (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install all dependencies
pip install -r requirements.txt
```

---

## Running the Local Lambda Server

The analytics scripts run as Lambda functions. For local development, `local_lambda_server.py` simulates the Lambda runtime on `http://localhost:9001`.

**Recommended**: use the included PowerShell script, which handles environment variables and venv activation automatically:

```powershell
.\run-local.ps1
```

On first run, if `.env.local` is not present, the script creates a template and exits. Edit the file, then run again.

**Manual start** (if you prefer):

```powershell
.\venv\Scripts\Activate.ps1
python local_lambda_server.py --port 9001 --log-level INFO
```

The server accepts `POST /2015-03-31/functions/{functionName}/invocations` — the exact path used by the AWS SDK. The Spring Boot backend forwards analytics requests here when `LAMBDA_ENDPOINT_URL=http://localhost:9001` is set.

### Function name routing

| Lambda function name pattern | Handler |
|------------------------------|---------|
| Contains `"report"` | `report_handler.lambda_handler` |
| Contains `"generate"` or `"analytics"` | `analytics_handler.lambda_handler` |

---

## Environment Configuration

Create a `.env.local` file in the `cpsc-analytics-scripts/` directory (or let `run-local.ps1` generate the template):

```dotenv
AWS_PROFILE=cpsc-devops
AWS_REGION=us-east-1
ENVIRONMENT=devl
LOCAL_REPORTS_DIR=./reports
```

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_PROFILE` | AWS named profile for DynamoDB access | `cpsc-devops` |
| `AWS_REGION` | AWS region | `us-east-1` |
| `ENVIRONMENT` | Determines DynamoDB table suffix (`devl`, `acpt`, `prod`) | `devl` |
| `LOCAL_REPORTS_DIR` | When set, HTML reports are saved here instead of uploading to S3 | _(not set → uses S3)_ |
| `ANALYTICS_S3_BUCKET` | S3 bucket for report uploads (Lambda env, not local) | `cpsc-analytics-{env}` |

### How `ENVIRONMENT` affects DynamoDB table names

| `ENVIRONMENT` | Tables accessed |
|---------------|----------------|
| `devl` | `Institutions-devl`, `Transactions-devl`, `Goals-devl` |
| `acpt` | `Institutions-acpt`, `Transactions-acpt`, `Goals-acpt` |
| `prod` | `Institutions-prod`, `Transactions-prod`, `Goals-prod` |

---

## Three-Terminal Startup (Full Stack)

```powershell
# Terminal 1 — Analytics Lambda server
cd cpsc-analytics-scripts
.\run-local.ps1

# Terminal 2 — Spring Boot backend
cd cpsc-backend-api
.\run-local.ps1

# Terminal 3 — Angular frontend
cd cpsc-frontend-ui
npm start
```

The backend reads `LAMBDA_ENDPOINT_URL` from its own `.env.local` or environment — make sure it points to `http://localhost:9001`.

---

## Troubleshooting

### `ImportError: cannot import name 'handler'`
The Lambda entry point is `lambda_handler`, not `handler`. If a test or external script imports `handler`, update the import:
```python
from src.lambda_handlers.analytics_handler import lambda_handler
```

### `ModuleNotFoundError: No module named 'src'`
Run `local_lambda_server.py` from the `cpsc-analytics-scripts/` directory, or ensure `src/` is on `PYTHONPATH`.

### `botocore.exceptions.NoCredentialsError`
Ensure `AWS_PROFILE=cpsc-devops` is set and the profile exists in `~/.aws/credentials`.

### Cold-start slowness
Libraries like Plotly and scikit-learn take a moment to import on first request. Subsequent calls are fast.
