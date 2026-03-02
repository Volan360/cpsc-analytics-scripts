# Deployment

## Overview

Both Lambda functions deploy from a single ZIP artifact containing the `src/` directory and runtime dependencies.

| Function name | Handler | Trigger |
|---------------|---------|---------|
| `cpsc-analytics-generate-{env}` | `lambda_handlers.analytics_handler.lambda_handler` | API Gateway POST `/api/analytics/generate` |
| `cpsc-analytics-report-{env}` | `lambda_handlers.report_handler.lambda_handler` | API Gateway POST `/api/analytics/report` |

Environments: `devl`, `stag`, `prod`

---

## CI/CD Pipeline (Normal Deployments)

Deployments are automated via AWS CodePipeline using `buildspec.yml`. Pushing to the `main` branch triggers the pipeline, which:

1. Installs `requirements-lambda.txt` into the package directory
2. Copies `src/` into the package
3. Creates `lambda-deployment-{env}.zip`
4. Uploads the ZIP to S3 (`codepipeline-us-east-1-411077442627`)
5. Calls `aws lambda update-function-code` for both functions
6. Waits for each function update to complete

---

## Manual Deployment

### 1. Create the deployment package

**Windows:**
```powershell
# Package name is lambda-analytics_handler.zip or lambda-report_handler.zip
# but both functions use the same src/ — you can use either name
.\lambda_package.ps1 analytics_handler
```

**Unix/Linux:**
```bash
./lambda_package.sh analytics_handler
```

> **Note:** The `lambda_package.ps1`/`.sh` scripts install from `requirements.txt` (includes dev dependencies). For a production-equivalent package, install `requirements-lambda.txt` instead — it excludes `boto3` (provided by the Lambda runtime) and dev tools, producing a smaller artifact.

### 2. Deploy to AWS

```powershell
$env = "devl"  # or stag, prod
$zip = "lambda-analytics_handler.zip"

# Deploy analytics/generate function
aws lambda update-function-code `
  --profile cpsc-devops `
  --function-name "cpsc-analytics-generate-$env" `
  --zip-file "fileb://$zip" `
  --region us-east-1

# Wait for update to complete
aws lambda wait function-updated `
  --profile cpsc-devops `
  --function-name "cpsc-analytics-generate-$env" `
  --region us-east-1

# Deploy report function (same package)
aws lambda update-function-code `
  --profile cpsc-devops `
  --function-name "cpsc-analytics-report-$env" `
  --zip-file "fileb://$zip" `
  --region us-east-1
```

---

## Lambda Configuration

### Runtime

- **Python version:** 3.12
- **Architecture:** x86_64

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENVIRONMENT` | Yes | `devl` | Deployment environment (`devl`, `stag`, `prod`) |
| `ANALYTICS_S3_BUCKET` | No | `cpsc-analytics-{ENVIRONMENT}` | S3 bucket for HTML report storage |

> `LOCAL_REPORTS_DIR` is for local development only. Do not set it on Lambda.

### Permissions (IAM Role)

The Lambda execution role must have:
- **DynamoDB:** `GetItem`, `Query` on `Institutions-{env}`, `Transactions-{env}`, `Goals-{env}` tables
- **S3:** `PutObject`, `GetObject` on `cpsc-analytics-{env}` bucket (report_handler only)

---

## AWS Resources

| Resource | Name pattern |
|----------|-------------|
| Lambda (analytics) | `cpsc-analytics-generate-{env}` |
| Lambda (reports) | `cpsc-analytics-report-{env}` |
| DynamoDB (institutions) | `Institutions-{env}` |
| DynamoDB (transactions) | `Transactions-{env}` |
| DynamoDB (goals) | `Goals-{env}` |
| S3 (reports) | `cpsc-analytics-{env}` |
| S3 (pipeline artifacts) | `codepipeline-us-east-1-411077442627` |

---

## Dependencies

### `requirements-lambda.txt` (Lambda deployment)

Only the packages actually imported by Lambda source code. `boto3` is excluded (provided by the Lambda runtime). Dev and optional science packages are excluded to minimize package size.

```
numpy
plotly
networkx
jinja2
```

### `requirements.txt` (local development)

Full dependency list including dev tools (`pytest`, `black`, `flake8`, `mypy`), `boto3`, and optional analytics libraries used in tests.
