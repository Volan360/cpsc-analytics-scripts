# Lambda Functions

There are two Lambda handlers. Both are invoked by the Spring Boot backend via the AWS SDK Lambda client.

---

## `analytics_handler` — `src/lambda_handlers/analytics_handler.py`

**Entry point:** `lambda_handler(event, context)`  
**Invoked by:** `POST /api/analytics/generate`

Generates in-memory analytics and returns structured JSON data. No files are written; no S3 access.

### Request format (event body)

```json
{
  "analyticsType": "cash_flow",
  "dateRange": {
    "start": "2025-01-01",
    "end": "2025-12-31"
  },
  "options": {
    "groupBy": "month",
    "includeRecommendations": true
  }
}
```

- `analyticsType` — **required**. One of: `cash_flow`, `categories`, `goals`, `institutions`, `network`, `health`
- `dateRange` — required for `cash_flow`, `categories`, `health`; optional for `institutions`; **not used** for `goals` and `network` (snapshots)
- `options.groupBy` — `"day"`, `"week"`, or `"month"` (used by `cash_flow`)
- `options.includeRecommendations` — boolean, used by `health` (default `true`)

### Response format

```json
{
  "analyticsType": "cash_flow",
  "userId": "<cognito-sub>",
  "generatedAt": "2026-03-02T14:30:00+00:00",
  "dateRange": { "start": "2025-01-01", "end": "2025-12-31" },
  "data": { ... }
}
```

`data` shape varies by `analyticsType` — see [docs/03-analytics-types.md](03-analytics-types.md).

### Error responses

| HTTP | Body | Cause |
|------|------|-------|
| 401 | `{"error": "Unauthorized: missing user identity"}` | JWT `sub` claim not found |
| 400 | `{"error": "<validation message>"}` | Missing/invalid fields |
| 500 | `{"error": "Analytics computation failed"}` | Unhandled exception during computation |

---

## `report_handler` — `src/lambda_handlers/report_handler.py`

**Entry point:** `lambda_handler(event, context)`  
**Invoked by:** `POST /api/analytics/report`

Generates a styled HTML report, uploads it to S3 (or saves locally when `LOCAL_REPORTS_DIR` is set), and returns a presigned URL.

### Request format (event body)

```json
{
  "reportType": "cash_flow",
  "dateRange": {
    "start": "2025-01-01",
    "end": "2025-12-31"
  },
  "options": {
    "userName": "John"
  }
}
```

- `reportType` — **required**. One of: `cash_flow`, `category`, `goal`, `network`, `health_score`, `comprehensive`
- `dateRange` — required for most types; **not used** for `goal` and `network` (snapshots)
- `options.userName` — display name embedded in the report header

### Report types

| `reportType` | Date Range | Charts Included |
|-------------|:----------:|----------------|
| `cash_flow` | Required | Stacked bar: deposits vs. withdrawals over time |
| `category` | Required | Pie chart: top 10 spending categories |
| `goal` | No | Horizontal bar: goal progress (%) — green if complete, red if in-progress |
| `network` | No | Force-directed network graph + Sankey diagram (institution → goals & spending categories) |
| `health_score` | Required | Gauge chart (overall score) + radar chart (5 dimensions) |
| `comprehensive` | Required | Combines `cash_flow` + `category` + `goal` + `health_score` sections in one HTML page |

### Response format

```json
{
  "reportType": "cash_flow",
  "userId": "<cognito-sub>",
  "generatedAt": "2026-03-02T14:30:00+00:00",
  "dateRange": { "start": "2025-01-01", "end": "2025-12-31" },
  "reportUrl": "https://s3.amazonaws.com/.../cash_flow_report_1234567890.html?...",
  "s3Key": "reports/<userId>/2026/03/02/cash_flow_report_1234567890.html",
  "bucket": "cpsc-analytics-devl"
}
```

When `LOCAL_REPORTS_DIR` is set, `reportUrl` is a `file:///` path and `bucket` is the local directory.

### Error responses

Same structure as `analytics_handler`: 401, 400, 500.

---

## Authentication

Both handlers extract the user identity from the Cognito JWT claims injected by API Gateway:

```
event['requestContext']['authorizer']['claims']['sub']
```

Fallback: `event['requestContext']['authorizer']['userId']` (custom authorizer context).

If neither is present, the handler returns 401 immediately without touching DynamoDB.

---

## Internal Architecture

```
lambda_handler(event, context)
    │
    ├── _get_user_id_from_event()     — extract Cognito sub
    ├── _validate_request()           — check required fields and date formats
    ├── DynamoDBClient(environment)   — connect to appropriate tables
    │
    ├── analytics_handler:
    │       _run_analytics() ─────────────────────────┐
    │           ├── CashFlowAnalytics.analyze()        │
    │           ├── CategoryAnalytics.analyze()        │ each module fetches
    │           ├── GoalAnalytics.analyze()            │ its own data from
    │           ├── InstitutionAnalytics.analyze()     │ DynamoDB via the
    │           ├── NetworkAnalytics.analyze()         │ passed db_client
    │           └── HealthScoreAnalytics.analyze()  ───┘
    │
    └── report_handler:
            ChartGenerator()          — Plotly-based chart creation
            ReportGenerator()         — Jinja2 HTML templates
            _generate_single_report() or _generate_comprehensive_report()
            S3Uploader.upload_report() or _save_report_locally()
```

### Visualization modules (`src/visualization/`)

| Module | Purpose |
|--------|---------|
| `charts.py` (`ChartGenerator`) | Creates Plotly charts: bar, stacked bar, pie, gauge, radar, network graph, Sankey diagram |
| `reports.py` (`ReportGenerator`) | Renders Jinja2 HTML templates with embedded Plotly charts for each report type |
| `s3_uploader.py` (`S3Uploader`) | Uploads HTML reports to S3, generates presigned URLs (default 1-hour expiry) |
