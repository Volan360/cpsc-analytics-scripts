# CPSC Analytics Scripts

Financial analytics and reporting system for the CPSC Cornerstone Project. Python Lambda functions that generate analytics and HTML reports from financial data stored in DynamoDB.

**Stack:** Python 3.12 · AWS Lambda · DynamoDB · S3 · Plotly · Jinja2 · NetworkX

## Documentation

| Guide | Contents |
|-------|----------|
| [Local Development](docs/01-local-development.md) | Prerequisites, `run-local.ps1`, `.env.local`, troubleshooting |
| [Lambda Functions](docs/02-lambda-functions.md) | Request/response format, handler routing, visualization modules |
| [Analytics Types](docs/03-analytics-types.md) | All 6 analytics types with data shapes and data models |
| [Testing](docs/04-testing.md) | Running tests, coverage, code quality, dependencies |
| [Deployment](docs/05-deployment.md) | Lambda function names, packaging, CI/CD pipeline, AWS resources |

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Backend   │────────▶│    Lambda    │────────▶│  DynamoDB   │
│   API       │         │  Functions   │         │   Tables    │
└─────────────┘         └──────────────┘         └─────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  S3 Bucket   │
                        │  (Reports)   │
                        └──────────────┘
```

## Project Structure

```
cpsc-analytics-scripts/
├── src/
│   ├── analytics/           # Analytics calculation modules
│   │   ├── cash_flow.py
│   │   ├── categories.py
│   │   ├── goals.py
│   │   ├── institutions.py
│   │   ├── network.py
│   │   └── health_score.py
│   ├── data/                # Data access layer
│   │   ├── dynamodb_client.py
│   │   └── data_models.py
│   ├── visualization/       # Chart and report generation
│   │   ├── charts.py
│   │   ├── reports.py
│   │   └── s3_uploader.py
│   ├── lambda_handlers/     # AWS Lambda entry points
│   │   ├── analytics_handler.py
│   │   └── report_handler.py
│   └── utils/               # Utility functions
│       ├── date_utils.py
│       ├── calculations.py
│       └── constants.py
├── tests/                   # Unit tests (236 tests)
├── local_lambda_server.py   # Local Lambda simulator (port 9001)
├── run-local.ps1            # Local dev startup script
├── lambda_package.ps1       # Windows deployment packaging
├── lambda_package.sh        # Unix deployment packaging
├── buildspec.yml            # AWS CodeBuild CI/CD definition
├── requirements.txt         # All dependencies (dev + runtime)
└── requirements-lambda.txt  # Runtime-only dependencies (Lambda deploy)
```

## Quick Start

```powershell
cd cpsc-analytics-scripts
.\run-local.ps1
```

See [docs/01-local-development.md](docs/01-local-development.md) for full setup instructions.

## Analytics Types

| Type | `analyticsType` value | `dateRange` |
|------|----------------------|-------------|
| Cash Flow | `cash_flow` | Required |
| Category Spending | `categories` | Required |
| Goal Progress | `goals` | Not used |
| Institution Performance | `institutions` | Optional |
| Network Analysis | `network` | Not used |
| Financial Health Score | `health` | Required |

See [docs/03-analytics-types.md](docs/03-analytics-types.md) for full request/response shapes.
