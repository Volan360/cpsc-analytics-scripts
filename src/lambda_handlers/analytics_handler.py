"""Lambda handler for POST /api/analytics/generate."""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.analytics.cash_flow import CashFlowAnalytics
from src.analytics.categories import CategoryAnalytics
from src.analytics.goals import GoalAnalytics
from src.analytics.health_score import HealthScoreAnalytics
from src.analytics.institutions import InstitutionAnalytics
from src.analytics.network import NetworkAnalytics
from src.data.dynamodb_client import DynamoDBClient
from src.utils import date_utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Valid analytics types
ANALYTICS_TYPES = {
    'cash_flow',
    'categories',
    'goals',
    'institutions',
    'network',
    'health',
}


def _get_environment() -> str:
    """Get current deployment environment from env variable."""
    return os.environ.get('ENVIRONMENT', 'devl')


def _get_user_id_from_event(event: Dict[str, Any]) -> Optional[str]:
    """
    Extract user_id from the Cognito JWT claims in the API Gateway event.

    API Gateway (with Cognito authorizer) populates:
      event['requestContext']['authorizer']['claims']['sub']
    """
    try:
        claims = (
            event.get('requestContext', {})
                 .get('authorizer', {})
                 .get('claims', {})
        )
        user_id = claims.get('sub')
        if not user_id:
            # Fallback: try custom authorizer context
            user_id = (
                event.get('requestContext', {})
                     .get('authorizer', {})
                     .get('userId')
            )
        return user_id
    except Exception as exc:
        logger.error(f"Failed to extract user_id from event: {exc}")
        return None


def _build_response(status_code: int, body: Any) -> Dict[str, Any]:
    """Build a standard API Gateway proxy response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(body, default=str),
    }


def _validate_request(body: Dict[str, Any]) -> Optional[str]:
    """
    Validate request body fields.

    Returns an error message string if invalid, otherwise None.
    """
    analytics_type = body.get('analyticsType')
    if not analytics_type:
        return "Missing required field: analyticsType"
    if analytics_type not in ANALYTICS_TYPES:
        return (
            f"Invalid analyticsType '{analytics_type}'. "
            f"Must be one of: {', '.join(sorted(ANALYTICS_TYPES))}"
        )

    # dateRange is not required for 'goals' (snapshot) or 'institutions' (optional time window)
    if analytics_type not in ('goals', 'institutions'):
        date_range = body.get('dateRange', {})
        start_date = date_range.get('start')
        end_date = date_range.get('end')
        if not start_date or not end_date:
            return "Missing required fields: dateRange.start and dateRange.end"

        # Validate ISO date format
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return "dateRange dates must be in YYYY-MM-DD format"

        if start_date >= end_date:
            return "dateRange.start must be before dateRange.end"

    return None


def _run_analytics(
    analytics_type: str,
    user_id: str,
    start_date: str,
    end_date: str,
    options: Dict[str, Any],
    db_client: DynamoDBClient,
) -> Dict[str, Any]:
    """
    Dispatch analytics request to the appropriate module.

    Args:
        analytics_type: Type of analytics ('cash_flow', 'categories', etc.)
        user_id: Cognito user sub
        start_date: ISO date string (YYYY-MM-DD)
        end_date: ISO date string (YYYY-MM-DD)
        options: Additional options (groupBy, includeVisualizations, etc.)
        db_client: Initialized DynamoDB client

    Returns:
        Analytics result dictionary
    """
    if analytics_type == 'cash_flow':
        group_by = options.get('groupBy', 'month')
        analytics = CashFlowAnalytics(db_client)
        return analytics.analyze(user_id, start_date, end_date, group_by=group_by)

    elif analytics_type == 'categories':
        analytics = CategoryAnalytics(db_client)
        return analytics.analyze(user_id, start_date, end_date)

    elif analytics_type == 'goals':
        analytics = GoalAnalytics(db_client)
        return analytics.analyze(user_id)

    elif analytics_type == 'institutions':
        analytics = InstitutionAnalytics(db_client)
        return analytics.analyze(user_id, start_date, end_date)

    elif analytics_type == 'network':
        analytics = NetworkAnalytics(db_client)
        return analytics.analyze(user_id, start_date, end_date)

    elif analytics_type == 'health':
        # HealthScoreAnalytics works with raw data (no DynamoDB dependency)
        start_ts, end_ts = date_utils.get_date_range(start_date, end_date)
        transactions = db_client.get_all_user_transactions(
            user_id=user_id,
            start_date=start_ts,
            end_date=end_ts,
        )
        institutions = db_client.get_institutions(user_id)
        goals = db_client.get_goals(user_id)

        period_days = (
            datetime.strptime(end_date, '%Y-%m-%d')
            - datetime.strptime(start_date, '%Y-%m-%d')
        ).days

        include_recommendations = options.get('includeRecommendations', True)
        analytics = HealthScoreAnalytics()
        return analytics.analyze(
            transactions=transactions,
            institutions=institutions,
            goals=goals,
            period_days=period_days,
            include_recommendations=include_recommendations,
        )

    raise ValueError(f"Unsupported analytics type: {analytics_type}")


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda entry point for POST /api/analytics/generate.

    Expected event structure (API Gateway proxy integration):
    {
        "body": "{\"analyticsType\": \"cash_flow\", \"dateRange\": {\"start\": \"2025-01-01\", \"end\": \"2025-12-31\"}, \"options\": {}}",
        "requestContext": {
            "authorizer": {
                "claims": {"sub": "<cognito-user-id>"}
            }
        }
    }
    """
    logger.info("analytics_handler invoked")

    # --- Extract user identity ---
    user_id = _get_user_id_from_event(event)
    if not user_id:
        return _build_response(401, {'error': 'Unauthorized: missing user identity'})

    # --- Parse request body ---
    try:
        raw_body = event.get('body') or '{}'
        body = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        return _build_response(400, {'error': f'Invalid JSON body: {exc}'})

    # --- Validate ---
    validation_error = _validate_request(body)
    if validation_error:
        return _build_response(400, {'error': validation_error})

    analytics_type = body['analyticsType']
    date_range = body.get('dateRange', {})
    start_date = date_range.get('start')
    end_date = date_range.get('end')
    options = body.get('options', {})

    logger.info(
        f"Running {analytics_type} analytics for user {user_id} "
        f"({start_date} → {end_date})" if start_date else
        f"Running {analytics_type} analytics for user {user_id}"
    )

    # --- Initialize DynamoDB client ---
    environment = _get_environment()
    try:
        db_client = DynamoDBClient(environment=environment)
    except Exception as exc:
        logger.error(f"Failed to initialize DynamoDB client: {exc}")
        return _build_response(500, {'error': 'Failed to connect to database'})

    # --- Run analytics ---
    try:
        result = _run_analytics(
            analytics_type=analytics_type,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            options=options,
            db_client=db_client,
        )
    except ValueError as exc:
        return _build_response(400, {'error': str(exc)})
    except Exception as exc:
        logger.error(f"Analytics failed: {exc}", exc_info=True)
        return _build_response(500, {'error': 'Analytics computation failed'})

    # --- Build response ---
    response_body = {
        'analyticsType': analytics_type,
        'userId': user_id,
        'generatedAt': datetime.now(timezone.utc).isoformat(),
        'data': result,
    }
    if start_date and end_date:
        response_body['dateRange'] = {'start': start_date, 'end': end_date}

    return _build_response(200, response_body)
