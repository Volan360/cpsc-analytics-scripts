# CPSC Analytics Scripts

Financial analytics and reporting system for the CPSC Cornerstone Project. This repository contains Python scripts that run as AWS Lambda functions to generate analytics, visualizations, and reports from financial data stored in DynamoDB.

## Overview

The analytics scripts provide comprehensive financial insights including:
- **Cash Flow Analysis** - Track income vs expenses over time
- **Category Analytics** - Spending patterns by transaction tags
- **Goal Progress Tracking** - Monitor progress toward financial goals
- **Institution Performance** - Compare accounts and balances
- **Network Analysis** - Relationship graphs using NetworkX
- **Financial Health Score** - Overall wellness indicator

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
                        │ (Charts/PDFs)│
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
│   │   ├── network_analysis.py
│   │   └── health_score.py
│   ├── data/                # Data access layer
│   │   ├── dynamodb_client.py
│   │   └── data_models.py
│   ├── visualizations/      # Chart and report generation
│   │   ├── charts.py
│   │   ├── graphs.py
│   │   └── reports.py
│   ├── lambda_handlers/     # AWS Lambda entry points
│   │   ├── analytics_handler.py
│   │   └── report_handler.py
│   └── utils/               # Utility functions
│       ├── date_utils.py
│       ├── calculations.py
│       └── constants.py
├── tests/                   # Unit and integration tests
├── requirements.txt         # Python dependencies
├── IMPLEMENTATION_PLAN.md   # Detailed implementation guide
└── README.md               # This file
```

## Prerequisites

- Python 3.11+
- AWS CLI configured with `cpsc-devops` profile
- Access to DynamoDB tables: Institutions, Transactions, Goals
- S3 bucket for output storage

## Installation

1. **Clone the repository** (if not already in monorepo):
   ```bash
   cd cpsc-analytics-scripts
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate.ps1  # Windows PowerShell
   # or
   source venv/bin/activate     # Unix/Mac
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Development

### Running Locally

```python
from src.data.dynamodb_client import DynamoDBClient
from src.analytics.cash_flow import CashFlowAnalytics

# Initialize client
client = DynamoDBClient(environment='devl', profile='cpsc-devops')

# Generate analytics
analytics = CashFlowAnalytics(client)
results = analytics.analyze(user_id='user-123', start_date='2025-01-01', end_date='2025-12-31')
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_analytics.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## Lambda Deployment

### Package Lambda Function

```bash
# Create deployment package
./lambda_package.sh analytics_handler

# This creates: lambda-analytics_handler.zip
```

### Deploy to AWS

```bash
# Deploy using AWS CLI
aws lambda update-function-code \
  --profile cpsc-devops \
  --function-name cpsc-analytics-generator-devl \
  --zip-file fileb://lambda-analytics_handler.zip
```

## API Integration

The analytics scripts are invoked by the backend API through Lambda functions:

### Generate Analytics Endpoint

```http
POST /api/analytics/generate
Authorization: Bearer <jwt-token>
Content-Type: application/json

{
  "analyticsType": "cash_flow",
  "dateRange": {
    "start": "2025-01-01",
    "end": "2025-12-31"
  },
  "options": {
    "includeVisualizations": true,
    "outputFormat": "json"
  }
}
```

**Response**:
```json
{
  "analyticsType": "cash_flow",
  "userId": "user-123",
  "generatedAt": "2026-02-19T10:30:00Z",
  "data": {
    "netCashFlow": 5400.00,
    "totalDeposits": 12000.00,
    "totalWithdrawals": 6600.00,
    "savingsRate": 45.0,
    "monthlyAverage": 450.00
  },
  "visualizations": [
    {
      "type": "line_chart",
      "title": "Monthly Cash Flow",
      "url": "https://s3.amazonaws.com/cpsc-analytics-outputs-devl/user-123/cash-flow-2026-02-19.png"
    }
  ]
}
```

## Environment Variables

Configure these environment variables for Lambda functions:

```bash
ENVIRONMENT=devl|acpt|prod
INSTITUTIONS_TABLE=Institutions-{env}
TRANSACTIONS_TABLE=Transactions-{env}
GOALS_TABLE=Goals-{env}
S3_BUCKET=cpsc-analytics-outputs-{env}
AWS_REGION=us-east-1
```

## Analytics Types

### 1. Cash Flow Analytics
- **Type**: `cash_flow`
- **Metrics**: Net flow, burn rate, savings rate, income variability
- **Charts**: Time-series line charts, bar charts

### 2. Category Analytics
- **Type**: `categories`
- **Metrics**: Spending by tag, category trends, budget adherence
- **Charts**: Pie charts, bar charts, Sankey diagrams

### 3. Goal Progress
- **Type**: `goals`
- **Metrics**: Progress %, estimated completion, required contribution
- **Charts**: Progress bars, timeline projections

### 4. Institution Performance
- **Type**: `institutions`
- **Metrics**: Balance growth, transaction volume, utilization score
- **Charts**: Comparison bars, growth trends

### 5. Network Analysis
- **Type**: `network`
- **Metrics**: Centrality, clustering, flow efficiency
- **Charts**: Network graphs, heatmaps (using NetworkX)

### 6. Financial Health Score
- **Type**: `health`
- **Metrics**: Composite score (0-100) across 5 weighted dimensions:
  - **Savings Rate** (25%) — Net savings as % of income; 20%+ = 100 pts
  - **Goal Progress** (25%) — Average completion % across active goals
  - **Spending Diversity** (20%) — Gini coefficient of spending categories
  - **Account Utilization** (15%) — % of institutions with recent transactions
  - **Transaction Regularity** (15%) — Coefficient of variation in daily activity
- **Ratings**: Excellent (≥90), Good (≥75), Fair (≥60), Poor (≥45), Needs Improvement (<45)
- **Charts**: Gauge chart (overall score), radar chart (dimension breakdown)
- **Reports**: Health Score Report Card with score breakdown table and recommendations
- **Usage**:
```python
from src.analytics.health_score import HealthScoreAnalytics

analytics = HealthScoreAnalytics()
result = analytics.analyze(
    transactions=transactions,
    institutions=institutions,
    goals=goals,
    period_days=30,
    include_recommendations=True
)

print(result['overall_score'])    # e.g. 78.5
print(result['rating'])           # e.g. 'Good'
print(result['recommendations'])  # List of improvement tips
```

## Testing

### Unit Tests
- Test individual analytics modules
- Mock DynamoDB responses
- Verify calculations

### Integration Tests
- Test with local DynamoDB instance
- End-to-end analytics generation
- Lambda handler testing

### Example Test
```python
def test_cash_flow_calculation():
    client = MockDynamoDBClient()
    analytics = CashFlowAnalytics(client)
    
    result = analytics.calculate_net_flow(
        deposits=[100, 200, 300],
        withdrawals=[50, 75, 100]
    )
    
    assert result == 375  # (600 - 225)
```

## Troubleshooting

### Common Issues

1. **Import Error: Module not found**
   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt`

2. **AWS Credentials Error**
   - Verify `cpsc-devops` profile is configured
   - Check `~/.aws/credentials`

3. **DynamoDB Access Denied**
   - Verify IAM permissions for Lambda role
   - Check table names match environment

4. **Lambda Timeout**
   - Increase timeout in Lambda configuration
   - Optimize queries with date range filters

## Performance Considerations

- **Caching**: Results cached for 5 minutes
- **Pagination**: Large datasets processed in batches
- **Indexes**: Use DynamoDB GSIs for efficient queries
- **Memory**: Lambda allocated 512-1024 MB

## Contributing

1. Create feature branch from `main`
2. Implement changes with tests
3. Run code quality checks
4. Submit pull request

## License

Proprietary - CPSC Cornerstone Project

## Contact

For questions or issues, contact the development team.

---

**Last Updated**: February 19, 2026
**Version**: 0.4.0
**Test Suite**: 259 tests passing | 86.49% coverage