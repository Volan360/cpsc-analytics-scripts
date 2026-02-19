# CPSC Analytics Scripts - Implementation Plan

## 📊 Data Model Overview

Based on the backend entities, users have access to:

### **Institution Entity**
- Financial accounts with balances (starting/current)
- Linked goals with allocation percentages
- Creation timestamps

### **Transaction Entity**
- Deposits and withdrawals
- Tags for categorization
- Descriptions and dates
- Links to institutions

### **Goal Entity**
- Target amounts and progress tracking
- Links to institutions (with percentage allocations)
- Links to transactions
- Completion status

---

## 🎯 Proposed Analytics Categories

### **1. Cash Flow Analytics**
**Purpose**: Analyze income vs expenses over time

**Visualizations**:
- Time-series line charts showing deposits vs withdrawals
- Monthly/weekly cash flow summaries
- Running balance projections
- Seasonal spending patterns

**Metrics**:
- Net cash flow (deposits - withdrawals)
- Burn rate (average spending per day/week/month)
- Income variability coefficient
- Savings rate percentage

**Reports**:
- Cash Flow Statement (period-based)
- Trend Analysis Report
- Anomaly Detection (unusual spending spikes)

---

### **2. Transaction Category Analytics**
**Purpose**: Understand spending by category/tag

**Visualizations**:
- Pie/donut charts of spending by tag
- Bar charts comparing categories over time
- Sankey diagrams showing money flow from institutions → categories
- Heatmaps showing spending patterns by day/time

**Metrics**:
- Top spending categories
- Category growth rates
- Budget adherence by category
- Discretionary vs essential spending ratio

**Reports**:
- Category Breakdown Report
- Tag Frequency Analysis
- Category Trends Over Time

---

### **3. Goal Progress Analytics**
**Purpose**: Track and project goal achievement

**Visualizations**:
- Progress bars for each goal (current vs target)
- Timeline projection (estimated completion date)
- Contribution breakdown by institution
- Goal completion funnel

**Metrics**:
- Goal completion percentage
- Estimated days to completion
- Required monthly contribution
- Goal priority scoring (based on progress)

**Reports**:
- Goal Status Dashboard
- At-Risk Goals Report (slow progress)
- Goal Achievement Timeline

---

### **4. Institution Performance Analytics**
**Purpose**: Compare and analyze institutions

**Visualizations**:
- Bar charts comparing institutions by balance
- Growth rate line charts per institution
- Allocation pie chart (goal contributions)
- Institution network graph (using NetworkX)

**Metrics**:
- Balance growth rate per institution
- Transaction volume per institution
- Goal contribution efficiency
- Institution utilization score

**Reports**:
- Institution Comparison Report
- Balance Distribution Analysis
- Underutilized Accounts Report

---

### **5. Network Relationship Analytics (NetworkX)**
**Purpose**: Visualize relationships between entities

**Graph Types**:

**a) Financial Flow Network**
- Nodes: Users, Institutions, Goals, Transaction Categories
- Edges: Money flow connections weighted by amount
- Analysis: Identify central nodes, bottlenecks, flow patterns

**b) Goal-Institution Graph**
- Nodes: Goals and Institutions
- Edges: Percentage allocations
- Analysis: Diversification, risk concentration

**c) Transaction Tag Network**
- Nodes: Transaction tags/categories
- Edges: Co-occurrence in transactions
- Analysis: Spending pattern clustering, habit detection

**Visualizations**:
- Network diagrams with force-directed layouts
- Centrality heatmaps
- Shortest path analysis (e.g., from income to goal)
- Community detection (spending clusters)

**Metrics**:
- Degree centrality (most connected accounts)
- Betweenness centrality (critical flow points)
- Clustering coefficient (spending habit patterns)
- PageRank (importance of accounts/goals)

---

### **6. Financial Health Score**
**Purpose**: Overall financial wellness indicator

**Composite Score Based On**:
- Savings rate (deposits vs withdrawals)
- Goal progress rate
- Spending diversity (not over-concentrated)
- Account utilization
- Transaction regularity

**Visualizations**:
- Gauge chart showing health score (0-100)
- Radar chart with score dimensions
- Historical health score trend
- Comparison to benchmarks

**Reports**:
- Financial Health Report Card
- Improvement Recommendations
- Historical Health Trends

---

## 🛠️ Technical Implementation Plan

### **Phase 1: Project Setup**
**Directory Structure**:
```
cpsc-analytics-scripts/
├── src/
│   ├── analytics/
│   │   ├── cash_flow.py
│   │   ├── categories.py
│   │   ├── goals.py
│   │   ├── institutions.py
│   │   ├── network_analysis.py
│   │   └── health_score.py
│   ├── data/
│   │   ├── dynamodb_client.py
│   │   └── data_models.py
│   ├── visualizations/
│   │   ├── charts.py
│   │   ├── graphs.py
│   │   └── reports.py
│   ├── lambda_handlers/
│   │   ├── analytics_handler.py
│   │   └── report_handler.py
│   └── utils/
│       ├── date_utils.py
│       ├── calculations.py
│       └── constants.py
├── tests/
│   ├── test_analytics.py
│   └── test_data_client.py
├── requirements.txt
├── README.md
├── lambda_package.sh
└── deploy.sh
```

---

### **Phase 2: Dependencies**
**requirements.txt**:
```
boto3>=1.28.0              # AWS SDK
networkx>=3.1              # Network analysis
matplotlib>=3.7.0          # Basic plotting
plotly>=5.17.0             # Interactive charts
pandas>=2.0.0              # Data manipulation
numpy>=1.24.0              # Numerical computing
scikit-learn>=1.3.0        # ML for anomaly detection
seaborn>=0.12.0            # Statistical visualizations
python-dateutil>=2.8.0     # Date handling
fpdf>=1.7.2                # PDF report generation
```

---

### **Phase 3: Core Modules**

#### **3.1 DynamoDB Client**
- Fetch institutions, transactions, goals by userId
- Query with date ranges
- Batch processing for large datasets
- Caching layer for performance

#### **3.2 Analytics Modules**
Each module (cash_flow.py, categories.py, etc.) contains:
- Data aggregation functions
- Calculation methods
- Statistical analysis
- Metric computation

#### **3.3 Visualization Module**
- Chart generation functions (Plotly/Matplotlib)
- NetworkX graph rendering
- Export to PNG/SVG/HTML
- S3 upload for storage

#### **3.4 Report Generation**
- HTML report templates
- PDF generation
- Email formatting
- Summary statistics

---

### **Phase 4: Lambda Functions**

#### **Lambda 1: Generate Analytics**
**Endpoint**: `POST /api/analytics/generate`
**Input**:
```json
{
  "userId": "cognito-user-id",
  "analyticsType": "cash_flow|categories|goals|institutions|network|health",
  "dateRange": {
    "start": "2025-01-01",
    "end": "2025-12-31"
  },
  "options": {
    "includeVisualizations": true,
    "outputFormat": "json|html|pdf"
  }
}
```
**Output**:
```json
{
  "analyticsType": "cash_flow",
  "userId": "cognito-user-id",
  "generatedAt": "2026-02-19T10:30:00Z",
  "data": { /* computed metrics */ },
  "visualizations": [
    {
      "type": "line_chart",
      "title": "Monthly Cash Flow",
      "url": "s3://bucket/path/to/chart.png"
    }
  ]
}
```

#### **Lambda 2: Generate Report**
**Endpoint**: `POST /api/analytics/report`
**Input**:
```json
{
  "userId": "cognito-user-id",
  "reportType": "comprehensive|summary",
  "dateRange": {
    "start": "2025-01-01",
    "end": "2025-12-31"
  }
}
```
**Output**: PDF or HTML report URL in S3

---

### **Phase 5: Network Analysis Details (NetworkX)**

#### **Graph Construction**:
1. **Financial Flow Graph**
   ```python
   G = nx.DiGraph()
   # Add nodes for institutions, goals, categories
   # Add weighted edges for money flow
   # Calculate centrality metrics
   ```

2. **Goal-Institution Bipartite Graph**
   ```python
   B = nx.Graph()
   # Institution nodes on one side
   # Goal nodes on other side
   # Edges weighted by allocation percentage
   # Analyze: projection, connectivity
   ```

3. **Tag Co-occurrence Network**
   ```python
   T = nx.Graph()
   # Nodes = transaction tags
   # Edges = co-occur in same transaction
   # Community detection for spending clusters
   ```

#### **Analysis Functions**:
- `calculate_centrality()` - Find most important nodes
- `detect_communities()` - Identify spending clusters
- `find_shortest_paths()` - Money flow analysis
- `calculate_flow_efficiency()` - How well money reaches goals
- `identify_bottlenecks()` - Underutilized connections

#### **Visualizations**:
- Force-directed layout with Plotly
- Circular layout for bipartite graphs
- Heatmap of adjacency matrix
- Interactive HTML exports

---

### **Phase 6: Backend Integration**

#### **New Backend Endpoints**:
```yaml
/api/analytics/generate:
  post:
    summary: Generate analytics for user
    requestBody:
      $ref: '#/components/schemas/AnalyticsRequest'
    responses:
      200:
        $ref: '#/components/schemas/AnalyticsResponse'

/api/analytics/report:
  post:
    summary: Generate comprehensive report
    requestBody:
      $ref: '#/components/schemas/ReportRequest'
    responses:
      200:
        $ref: '#/components/schemas/ReportResponse'

/api/analytics/health-score:
  get:
    summary: Get current financial health score
    responses:
      200:
        $ref: '#/components/schemas/HealthScoreResponse'
```

#### **Backend Controller**:
- Invoke Lambda functions asynchronously
- Return Lambda response to frontend
- Cache recent analytics results
- Handle errors and timeouts

---

### **Phase 7: AWS Infrastructure**

**Resources Needed**:
1. **Lambda Functions** (2 functions)
   - Runtime: Python 3.11
   - Memory: 512-1024 MB
   - Timeout: 5 minutes
   - VPC: None (public Lambda)

2. **IAM Roles**:
   - DynamoDB read permissions (Institutions, Transactions, Goals)
   - S3 write permissions (for visualization storage)
   - CloudWatch Logs write

3. **S3 Bucket**:
   - `cpsc-analytics-outputs-{env}`
   - Store generated charts and reports
   - Presigned URL access for frontend

4. **API Gateway Integration**:
   - Lambda proxy integration
   - Cognito authorizer (same as backend)

5. **CloudWatch Alarms**:
   - Lambda errors
   - Execution time
   - Throttling

---

## 📋 Implementation Phases

### **Phase 1** (Foundation - Week 1) ✅ COMPLETED
- [x] Set up project structure
- [x] Install dependencies
- [x] Create DynamoDB client module
- [x] Basic data models
- [x] Unit test framework
- **Test Status**: 41/41 tests passing (100%)

### **Phase 2** (Core Analytics - Week 2-3) ✅ COMPLETED
- [x] Implement cash flow analytics
- [x] Implement category analytics
- [x] Implement goal analytics
- [x] Implement institution analytics
- [x] Unit tests for each module
- [x] Fixed double-counting bug in category totals calculation
- [x] Fixed cash flow projection calculation (monthly_change logic)
- [x] Fixed goal timeline calculation (months_remaining boundary condition)
- [x] Fixed runway calculation (return value for insufficient data)
- [x] Comprehensive code review of all analytical logic
- [x] Added 41 additional tests for improved coverage
  - Calculation utilities edge cases (variance, CAGR, percentile, weighted average, moving average, normalization)
  - Cash flow projection scenarios (basic, no data, positive/negative trends)
  - Date utility edge cases (month boundaries, year boundaries, formatting)
- **Quality Metrics**:
  - **Test Status**: 128/128 tests passing (100%)
  - **Code Coverage**: 85.83% (up from 77.63%)
    * calculations.py: 98.17% coverage
    * cash_flow.py: 83.93% coverage
    * categories.py: 93.85% coverage
    * goals.py: 90.79% coverage
    * institutions.py: 96.18% coverage
    * date_utils.py: 93.75% coverage
  - **Test Breakdown**:
    * Cash flow: 14/14 tests passing (added 4 projection tests)
    * Categories: 10/10 tests passing
    * Goals: 12/12 tests passing
    * Institutions: 14/14 tests passing
    * Calculations: 38/38 tests passing (added 8 test classes)
    * Date utilities: 40/40 tests passing (added 17 edge case tests)

### **Phase 3** (Network Analysis - Week 4) 🔜 NEXT
- [ ] Implement NetworkX graph construction
- [ ] Centrality calculations
- [ ] Community detection
- [ ] Graph visualizations
- [ ] Integration tests

### **Phase 4** (Visualizations - Week 5)
- [ ] Chart generation (Plotly/Matplotlib)
- [ ] Report templates
- [ ] PDF generation
- [ ] S3 upload integration

### **Phase 5** (Lambda Functions - Week 6)
- [ ] Lambda handler implementation
- [ ] Local testing with SAM
- [ ] Packaging script
- [ ] Deployment automation

### **Phase 6** (Backend Integration - Week 7)
- [ ] Update OpenAPI spec
- [ ] Add backend controllers
- [ ] Integration testing
- [ ] Error handling

### **Phase 7** (Deployment & Testing - Week 8)
- [ ] Deploy to AWS
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Documentation

---

## 🎨 Example Analytics Outputs

### **Cash Flow Chart**:
```
Monthly Net Cash Flow
│
│  ┌─┐
│  │ │     ┌─┐
│  │ │     │ │  ┌─┐
│  │ │  ┌─┐│ │  │ │
│──│ │──│ ││ │──│ │──
│  │ │  │ ││ │  │ │
│  └─┘  └─┘└─┘  └─┘
│  Jan  Feb Mar Apr
```

### **Goal Progress Network**:
```
    [Checking]──60%──>[Emergency Fund]
         │                    │
        40%                  ✓
         │                    │
         └──────>[Vacation]───┘
```

### **Financial Health Score**:
```
Overall Score: 78/100 ⭐⭐⭐⭐

Components:
- Savings Rate:        85/100 ██████████████████░░
- Goal Progress:       75/100 ███████████████░░░░░
- Spending Diversity:  70/100 ██████████████░░░░░░
- Account Utilization: 82/100 ████████████████░░░░
```

---

## ❓ Questions for Review

1. **Analytics Priorities**: Which analytics categories should we implement first?
2. **Visualization Preferences**: Prefer Plotly (interactive) or Matplotlib (static)?
3. **Report Format**: PDF, HTML, or both?
4. **Real-time vs Batch**: Should analytics be generated on-demand or pre-computed daily?
5. **Graph Complexity**: How detailed should the NetworkX visualizations be?
6. **Additional Metrics**: Any specific financial metrics you want to include?

---

## 📝 Notes

- All analytics will be user-scoped (filtered by userId from JWT token)
- Data will be fetched from DynamoDB tables: Institutions, Transactions, Goals
- Visualizations will be stored in S3 with presigned URLs for frontend access
- Lambda functions will be triggered by backend API endpoints
- Error handling and logging will use CloudWatch

---

This plan provides a comprehensive, scalable foundation for financial analytics. Implementation will proceed phase by phase with testing at each stage.
