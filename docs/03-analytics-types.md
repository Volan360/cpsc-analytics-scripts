# Analytics Types and Data Models

## Overview

| `analyticsType` | Date Range | Source module | Description |
|----------------|:----------:|---------------|-------------|
| `cash_flow` | Required | `analytics/cash_flow.py` | Income vs. spending over time |
| `categories` | Required | `analytics/categories.py` | Spending breakdown by transaction tags |
| `goals` | Not used (snapshot) | `analytics/goals.py` | Current goal progress |
| `institutions` | Optional | `analytics/institutions.py` | Per-account balance and activity |
| `network` | Not used (all-time) | `analytics/network.py` | Relationship graph between accounts, goals, categories |
| `health` | Required | `analytics/health_score.py` | Composite financial health score (0–100) |

---

## 1. Cash Flow (`cash_flow`)

Module: `src/analytics/cash_flow.py` — `CashFlowAnalytics.analyze(user_id, start_date, end_date, group_by='month')`

Fetches all transactions in the date range, groups them by period, and calculates key metrics.

**`options.groupBy`**: `"day"`, `"week"`, or `"month"` (default `"month"`)

### Response `data` shape

```json
{
  "date_range": { "start": "2025-01-01", "end": "2025-12-31", "days": 365 },
  "summary": {
    "total_deposits": 12000.00,
    "total_withdrawals": 6600.00,
    "net_cash_flow": 5400.00,
    "transaction_count": 48,
    "deposit_count": 24,
    "withdrawal_count": 24
  },
  "metrics": {
    "savings_rate": 45.0,
    "daily_burn_rate": 18.08,
    "average_deposit": 500.00,
    "average_withdrawal": 275.00,
    "median_deposit": 450.00,
    "median_withdrawal": 250.00,
    "deposit_volatility": 0.15,
    "withdrawal_volatility": 0.22
  },
  "balance": {
    "current_total": 8500.00,
    "runway_days": 470
  },
  "trends": {
    "periods": ["2025-01", "2025-02", "..."],
    "net_flows": [450.00, 525.00, "..."],
    "deposits": [1000.00, 1050.00, "..."],
    "withdrawals": [550.00, 525.00, "..."],
    "moving_average": [470.00, 485.00, "..."],
    "trend_direction": "improving",
    "best_period": "2025-07",
    "worst_period": "2025-03"
  },
  "anomalies": [
    {
      "transaction_id": "...",
      "amount": 2500.00,
      "type": "WITHDRAWAL",
      "description": "Car repair",
      "z_score": 3.4,
      "transaction_date": "2025-06-15"
    }
  ]
}
```

---

## 2. Categories (`categories`)

Module: `src/analytics/categories.py` — `CategoryAnalytics.analyze(user_id, start_date, end_date)`

Groups transactions by their tags (a transaction can have multiple tags). Calculates totals, counts, averages, percentages, and co-occurrence patterns.

### Response `data` shape

```json
{
  "date_range": { "start": "2025-01-01", "end": "2025-12-31" },
  "summary": {
    "total_amount": 6600.00,
    "transaction_count": 24,
    "unique_categories": 8,
    "transaction_type": "WITHDRAWAL"
  },
  "categories": {
    "totals": { "groceries": 1200.00, "rent": 2400.00, "..." : "..." },
    "counts": { "groceries": 12, "rent": 12, "...": "..." },
    "averages": { "groceries": 100.00, "rent": 200.00, "...": "..." },
    "percentages": { "groceries": 18.2, "rent": 36.4, "...": "..." }
  },
  "top_categories": [
    { "category": "rent", "total": 2400.00, "count": 12, "percentage": 36.4 }
  ],
  "trends": { "...": "..." },
  "diversity": { "gini_coefficient": 0.42, "...": "..." },
  "co_occurrences": []
}
```

---

## 3. Goals (`goals`)

Module: `src/analytics/goals.py` — `GoalAnalytics.analyze(user_id)`

Snapshot of all goals and their current progress. Date range is not used — progress is calculated from current institution balances.

### Response `data` shape

```json
{
  "summary": {
    "total_goals": 5,
    "active_goals": 3,
    "completed_goals": 2,
    "total_target_amount": 25000.00,
    "total_current_amount": 14500.00,
    "overall_progress": 58.0
  },
  "goals": [
    {
      "goal_id": "...",
      "name": "Emergency Fund",
      "target_amount": 5000.00,
      "current_amount": 3200.00,
      "progress_percent": 64.0,
      "remaining_amount": 1800.00,
      "is_completed": false,
      "is_active": true,
      "recommendation": "Increase monthly contribution by $150 to reach goal in 12 months",
      "monthly_contribution": 266.67,
      "months_to_completion": 6.75,
      "linked_institutions_count": 2
    }
  ],
  "insights": {
    "at_risk": [ "..." ],
    "near_completion": [ "..." ],
    "priorities": []
  }
}
```

---

## 4. Institutions (`institutions`)

Module: `src/analytics/institutions.py` — `InstitutionAnalytics.analyze(user_id, start_date, end_date)`

Per-account balance analysis, transaction activity, and goal linkage. `dateRange` is optional — when omitted, all-time transaction history is used.

### Response `data` shape

```json
{
  "summary": {
    "total_institutions": 3,
    "total_balance": 18500.00,
    "total_starting_balance": 15000.00,
    "total_growth": 3500.00,
    "average_balance": 6166.67
  },
  "institutions": [
    {
      "institution_id": "...",
      "institution_name": "Chase Checking",
      "balances": {
        "starting": 5000.00,
        "current": 6200.00,
        "change": 1200.00,
        "growth_rate": 24.0
      },
      "transactions": {
        "total_count": 18,
        "deposit_count": 10,
        "withdrawal_count": 8,
        "total_deposits": 5500.00,
        "total_withdrawals": 4300.00,
        "net_flow": 1200.00,
        "avg_per_month": 3.0
      },
      "goals": {
        "linked_count": 2,
        "total_allocated_percent": 60,
        "linked_goal_names": ["Emergency Fund", "Vacation"]
      },
      "metrics": {
        "utilization_score": 0.75,
        "activity_level": "high"
      }
    }
  ],
  "rankings": { "...": "..." },
  "underutilized": [],
  "portfolio": { "...": "..." }
}
```

---

## 5. Network (`network`)

Module: `src/analytics/network.py` — `NetworkAnalytics.analyze(user_id, graph_type='goal_institution')`

Builds a graph of relationships between institutions, goals, and spending categories using NetworkX. Always all-time; no date range.

### Response `data` shape

```json
{
  "graph_type": "goal_institution",
  "graph_stats": {
    "nodes": 8,
    "edges": 12,
    "density": 0.21,
    "is_connected": true
  },
  "nodes": [
    {
      "id": "inst_<uuid>",
      "attributes": {
        "node_type": "institution",
        "label": "Chase Checking",
        "balance": 6200.00,
        "color": "#4A90E2"
      }
    },
    {
      "id": "goal_<uuid>",
      "attributes": {
        "node_type": "goal",
        "label": "Emergency Fund",
        "total_flow": 3200.00,
        "color": "#7B68EE"
      }
    }
  ],
  "edges": [
    {
      "source": "inst_<uuid>",
      "target": "goal_<uuid>",
      "attributes": {
        "weight": 3200.00,
        "label": "40%",
        "flow_direction": "institution_to_goal"
      }
    }
  ],
  "centrality": {
    "degree": { "inst_<uuid>": 0.43, "...": "..." },
    "betweenness": { "...": "..." }
  },
  "communities": { "...": "..." }
}
```

The report handler's network report additionally generates a Sankey diagram combining institution→goal flows (from graph edges) and institution→category flows (from withdrawal tags).

---

## 6. Health Score (`health`)

Module: `src/analytics/health_score.py` — `HealthScoreAnalytics.analyze(transactions, institutions, goals, period_days, include_recommendations)`

Calculates a composite 0–100 score across 5 weighted dimensions. Unlike other analytics, this module takes raw data objects (not a `DynamoDBClient`) — the handler fetches data from DynamoDB itself before calling the module.

### Score dimensions

| Dimension | Weight | What it measures |
|-----------|:------:|-----------------|
| `savings_rate` | 25% | Net savings as % of income; 20%+ = 100 pts |
| `goal_progress` | 25% | Average completion % across all active goals |
| `spending_diversity` | 20% | Gini coefficient of spending categories (lower = more diverse) |
| `account_utilization` | 15% | % of institutions with at least one transaction in the period |
| `transaction_regularity` | 15% | Consistency of daily transaction activity (lower CoV = higher score) |

### Ratings

| Score | Rating |
|-------|--------|
| ≥ 90 | Excellent |
| ≥ 75 | Good |
| ≥ 60 | Fair |
| ≥ 45 | Poor |
| < 45 | Needs Improvement |

### Response `data` shape

```json
{
  "overall_score": 78.5,
  "rating": "Good",
  "components": {
    "savings_rate": { "score": 85.0, "weight": 0.25, "contribution": 21.25 },
    "goal_progress": { "score": 64.0, "weight": 0.25, "contribution": 16.0 },
    "spending_diversity": { "score": 80.0, "weight": 0.20, "contribution": 16.0 },
    "account_utilization": { "score": 100.0, "weight": 0.15, "contribution": 15.0 },
    "transaction_regularity": { "score": 69.0, "weight": 0.15, "contribution": 10.35 }
  },
  "recommendations": [
    "Diversify spending across more categories to improve spending diversity score.",
    "Increase goal contributions to accelerate progress."
  ],
  "period_days": 365,
  "computed_at": "2026-03-02T14:30:00+00:00",
  "user_id": "<cognito-sub>"
}
```

---

## Data Models (`src/data/data_models.py`)

Python dataclasses used internally throughout the analytics modules:

### `Institution`

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | `str` | Cognito user sub |
| `institution_id` | `str` | DynamoDB partition key |
| `institution_name` | `str` | Display name |
| `starting_balance` | `float` | Original balance |
| `current_balance` | `float` | Current balance |
| `created_at` | `int` | UNIX timestamp |
| `allocated_percent` | `int?` | % allocated to goals |
| `linked_goals` | `List[str]` | Goal IDs |

Computed properties: `balance_change`, `growth_rate`

### `Transaction`

| Field | Type | Description |
|-------|------|-------------|
| `institution_id` | `str` | Parent institution ID |
| `transaction_id` | `str` | Unique ID |
| `user_id` | `str` | Cognito user sub |
| `type` | `str` | `"DEPOSIT"` or `"WITHDRAWAL"` |
| `amount` | `float` | Absolute value |
| `created_at` | `int` | UNIX timestamp (sort key) |
| `transaction_date` | `int` | UNIX timestamp of when it occurred |
| `tags` | `List[str]` | Category tags |
| `description` | `str?` | Optional notes |

Computed properties: `is_deposit`, `is_withdrawal`, `signed_amount`

### `Goal`

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | `str` | Cognito user sub |
| `goal_id` | `str` | Unique ID |
| `name` | `str` | Display name |
| `target_amount` | `float` | Target savings amount |
| `created_at` | `int` | UNIX timestamp |
| `is_completed` | `bool` | Has been completed |
| `is_active` | `bool` | Currently active (false after completion) |
| `description` | `str?` | Optional notes |
| `linked_institutions` | `Dict[str, int]` | `{institution_id: allocation_percent}` |
| `linked_transactions` | `List[str]` | Transaction IDs from goal completion |
| `completed_at` | `int?` | UNIX timestamp of completion |

---

## DynamoDB Client (`src/data/dynamodb_client.py`)

`DynamoDBClient(environment, profile=None, region='us-east-1')` provides:

| Method | Description |
|--------|-------------|
| `get_institutions(user_id)` | All institutions for a user |
| `get_transactions(institution_id, user_id, start_date?, end_date?)` | Transactions for one institution, optional date filter (UNIX timestamps) |
| `get_all_user_transactions(user_id, start_date?, end_date?)` | Transactions across all user's institutions |
| `get_goals(user_id)` | All goals for a user |

On Lambda, `profile` is left as `None` so boto3 uses the execution role. Locally, set `AWS_PROFILE` in `.env.local` and optionally pass `profile='cpsc-devops'`.
