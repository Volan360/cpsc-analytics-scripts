"""Constants used throughout the analytics system."""

# Analytics types
ANALYTICS_CASH_FLOW = "cash_flow"
ANALYTICS_CATEGORIES = "categories"
ANALYTICS_GOALS = "goals"
ANALYTICS_INSTITUTIONS = "institutions"
ANALYTICS_NETWORK = "network"
ANALYTICS_HEALTH = "health"

ANALYTICS_TYPES = [
    ANALYTICS_CASH_FLOW,
    ANALYTICS_CATEGORIES,
    ANALYTICS_GOALS,
    ANALYTICS_INSTITUTIONS,
    ANALYTICS_NETWORK,
    ANALYTICS_HEALTH
]

# Transaction types
TRANSACTION_DEPOSIT = "DEPOSIT"
TRANSACTION_WITHDRAWAL = "WITHDRAWAL"

# Output formats
FORMAT_JSON = "json"
FORMAT_HTML = "html"
FORMAT_PDF = "pdf"

OUTPUT_FORMATS = [FORMAT_JSON, FORMAT_HTML, FORMAT_PDF]

# Date format constants
DATE_FORMAT_ISO = "%Y-%m-%d"
DATE_FORMAT_DISPLAY = "%B %d, %Y"
DATE_FORMAT_SHORT = "%m/%d/%Y"
DATETIME_FORMAT_ISO = "%Y-%m-%dT%H:%M:%S"

# Time periods
SECONDS_PER_DAY = 86400
SECONDS_PER_WEEK = 604800
SECONDS_PER_MONTH = 2592000  # Approximate (30 days)
SECONDS_PER_YEAR = 31536000  # Approximate (365 days)

# Visualization types
VIZ_LINE_CHART = "line_chart"
VIZ_BAR_CHART = "bar_chart"
VIZ_PIE_CHART = "pie_chart"
VIZ_SCATTER_PLOT = "scatter_plot"
VIZ_HEATMAP = "heatmap"
VIZ_NETWORK_GRAPH = "network_graph"
VIZ_SANKEY_DIAGRAM = "sankey_diagram"
VIZ_GAUGE_CHART = "gauge_chart"
VIZ_RADAR_CHART = "radar_chart"

# Health score thresholds
HEALTH_SCORE_EXCELLENT = 90
HEALTH_SCORE_GOOD = 75
HEALTH_SCORE_FAIR = 60
HEALTH_SCORE_POOR = 45

# Health score weights
HEALTH_WEIGHT_SAVINGS_RATE = 0.25
HEALTH_WEIGHT_GOAL_PROGRESS = 0.25
HEALTH_WEIGHT_SPENDING_DIVERSITY = 0.20
HEALTH_WEIGHT_ACCOUNT_UTILIZATION = 0.15
HEALTH_WEIGHT_TRANSACTION_REGULARITY = 0.15

# Color schemes
COLORS_PRIMARY = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
COLORS_DEPOSIT = '#2ca02c'  # Green
COLORS_WITHDRAWAL = '#d62728'  # Red
COLORS_NEUTRAL = '#1f77b4'  # Blue

# Thresholds and limits
MAX_CATEGORIES_DISPLAY = 10
MIN_TRANSACTIONS_FOR_ANALYSIS = 5
DEFAULT_QUERY_LIMIT = 1000
OUTLIER_THRESHOLD_STD_DEV = 2.0

# S3 configuration
S3_BUCKET_PREFIX = "cpsc-analytics-outputs"
S3_PRESIGNED_URL_EXPIRATION = 3600  # 1 hour

# Cache settings
CACHE_TTL_SECONDS = 300  # 5 minutes

# Error messages
ERROR_INVALID_USER_ID = "Invalid user ID provided"
ERROR_INVALID_DATE_RANGE = "Invalid date range: start date must be before end date"
ERROR_INVALID_ANALYTICS_TYPE = "Invalid analytics type"
ERROR_INSUFFICIENT_DATA = "Insufficient data for analysis"
ERROR_DATABASE_CONNECTION = "Failed to connect to database"
ERROR_S3_UPLOAD = "Failed to upload visualization to S3"

# Success messages
SUCCESS_ANALYTICS_GENERATED = "Analytics generated successfully"
SUCCESS_REPORT_GENERATED = "Report generated successfully"

# Environment names
ENV_DEVELOPMENT = "devl"
ENV_ACCEPTANCE = "acpt"
ENV_PRODUCTION = "prod"

ENVIRONMENTS = [ENV_DEVELOPMENT, ENV_ACCEPTANCE, ENV_PRODUCTION]

# AWS regions
AWS_REGION_US_EAST_1 = "us-east-1"
DEFAULT_AWS_REGION = AWS_REGION_US_EAST_1

# DynamoDB table suffixes
TABLE_INSTITUTIONS = "Institutions"
TABLE_TRANSACTIONS = "Transactions"
TABLE_GOALS = "Goals"

# Lambda function names
LAMBDA_ANALYTICS_GENERATOR = "cpsc-analytics-generator"
LAMBDA_REPORT_GENERATOR = "cpsc-report-generator"

# NetworkX configuration
NETWORK_MIN_NODE_SIZE = 100
NETWORK_MAX_NODE_SIZE = 1000
NETWORK_EDGE_WIDTH_SCALE = 0.01
NETWORK_LAYOUT_ITERATIONS = 50

# Report configuration
REPORT_TITLE_FONT_SIZE = 24
REPORT_HEADER_FONT_SIZE = 18
REPORT_BODY_FONT_SIZE = 12
REPORT_PAGE_WIDTH = 210  # A4 width in mm
REPORT_PAGE_HEIGHT = 297  # A4 height in mm
