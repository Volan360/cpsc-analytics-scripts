"""Tests for Lambda handler functions."""

import json
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timezone

from src.lambda_handlers.analytics_handler import handler as analytics_handler, _validate_request as validate_analytics
from src.lambda_handlers.report_handler import handler as report_handler, _validate_request as validate_report


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def cognito_event_base():
    """Base API Gateway event with Cognito claims."""
    return {
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': 'test-user-123',
                    'email': 'test@example.com',
                }
            }
        }
    }


def _make_analytics_event(body: dict, user_id: str = 'test-user-123') -> dict:
    """Create an API Gateway analytics event."""
    return {
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': user_id
                }
            }
        },
        'body': json.dumps(body)
    }


def _make_report_event(body: dict, user_id: str = 'test-user-123') -> dict:
    """Create an API Gateway report event."""
    return {
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': user_id
                }
            }
        },
        'body': json.dumps(body)
    }


# ---------------------------------------------------------------------------
# Analytics handler validation tests
# ---------------------------------------------------------------------------

class TestAnalyticsValidation:
    """Test input validation for analytics handler."""

    def test_valid_cash_flow_request(self):
        body = {
            'analyticsType': 'cash_flow',
            'dateRange': {'start': '2025-01-01', 'end': '2025-12-31'}
        }
        assert validate_analytics(body) is None

    def test_valid_all_analytics_types(self):
        for analytics_type in ['cash_flow', 'categories', 'goals', 'institutions', 'network', 'health']:
            body = {
                'analyticsType': analytics_type,
                'dateRange': {'start': '2025-01-01', 'end': '2025-12-31'}
            }
            assert validate_analytics(body) is None, f"Failed for type: {analytics_type}"

    def test_missing_analytics_type(self):
        body = {'dateRange': {'start': '2025-01-01', 'end': '2025-12-31'}}
        error = validate_analytics(body)
        assert error is not None
        assert 'analyticsType' in error

    def test_invalid_analytics_type(self):
        body = {
            'analyticsType': 'invalid_type',
            'dateRange': {'start': '2025-01-01', 'end': '2025-12-31'}
        }
        error = validate_analytics(body)
        assert error is not None
        assert 'invalid_type' in error

    def test_missing_date_range(self):
        body = {'analyticsType': 'cash_flow'}
        error = validate_analytics(body)
        assert error is not None
        assert 'dateRange' in error

    def test_missing_start_date(self):
        body = {
            'analyticsType': 'cash_flow',
            'dateRange': {'end': '2025-12-31'}
        }
        error = validate_analytics(body)
        assert error is not None

    def test_missing_end_date(self):
        body = {
            'analyticsType': 'cash_flow',
            'dateRange': {'start': '2025-01-01'}
        }
        error = validate_analytics(body)
        assert error is not None

    def test_invalid_date_format(self):
        body = {
            'analyticsType': 'cash_flow',
            'dateRange': {'start': '01/01/2025', 'end': '2025-12-31'}
        }
        error = validate_analytics(body)
        assert error is not None
        assert 'YYYY-MM-DD' in error

    def test_start_after_end_date(self):
        body = {
            'analyticsType': 'cash_flow',
            'dateRange': {'start': '2025-12-31', 'end': '2025-01-01'}
        }
        error = validate_analytics(body)
        assert error is not None
        assert 'before' in error.lower()

    def test_equal_start_and_end_date(self):
        body = {
            'analyticsType': 'cash_flow',
            'dateRange': {'start': '2025-06-01', 'end': '2025-06-01'}
        }
        error = validate_analytics(body)
        assert error is not None

    def test_goals_does_not_require_date_range(self):
        """Goals analytics is a snapshot — dateRange should be optional."""
        body = {'analyticsType': 'goals'}
        assert validate_analytics(body) is None

    def test_goals_accepts_date_range_when_provided(self):
        """dateRange is still accepted for goals if the caller includes it."""
        body = {
            'analyticsType': 'goals',
            'dateRange': {'start': '2025-01-01', 'end': '2025-12-31'}
        }
        assert validate_analytics(body) is None

    def test_other_types_still_require_date_range(self):
        """Non-goals and non-network types must still provide dateRange."""
        for analytics_type in ['cash_flow', 'categories', 'health']:
            body = {'analyticsType': analytics_type}
            error = validate_analytics(body)
            assert error is not None, f"Expected error for {analytics_type} without dateRange"

    def test_network_does_not_require_date_range(self):
        """Network analytics is all-time and should not require dateRange."""
        body = {'analyticsType': 'network'}
        assert validate_analytics(body) is None


# ---------------------------------------------------------------------------
# Report handler validation tests
# ---------------------------------------------------------------------------

class TestReportValidation:
    """Test input validation for report handler."""

    def test_valid_cash_flow_report(self):
        body = {
            'reportType': 'cash_flow',
            'dateRange': {'start': '2025-01-01', 'end': '2025-12-31'}
        }
        assert validate_report(body) is None

    def test_valid_all_report_types(self):
        for report_type in ['cash_flow', 'category', 'goal', 'network', 'health_score', 'comprehensive']:
            body = {
                'reportType': report_type,
                'dateRange': {'start': '2025-01-01', 'end': '2025-12-31'}
            }
            assert validate_report(body) is None, f"Failed for type: {report_type}"

    def test_missing_report_type(self):
        body = {'dateRange': {'start': '2025-01-01', 'end': '2025-12-31'}}
        error = validate_report(body)
        assert error is not None
        assert 'reportType' in error

    def test_invalid_report_type(self):
        body = {
            'reportType': 'invalid_type',
            'dateRange': {'start': '2025-01-01', 'end': '2025-12-31'}
        }
        error = validate_report(body)
        assert error is not None
        assert 'invalid_type' in error

    def test_missing_date_range(self):
        body = {'reportType': 'cash_flow'}
        error = validate_report(body)
        assert error is not None

    def test_invalid_date_format(self):
        body = {
            'reportType': 'cash_flow',
            'dateRange': {'start': 'not-a-date', 'end': '2025-12-31'}
        }
        error = validate_report(body)
        assert error is not None


# ---------------------------------------------------------------------------
# Analytics handler integration tests (with mocked dependencies)
# ---------------------------------------------------------------------------

class TestAnalyticsHandler:
    """Test analytics Lambda handler with mocked DynamoDB."""

    def test_unauthorized_no_user_id(self):
        """Return 401 when no user identity in event."""
        event = {'body': '{}', 'requestContext': {}}
        response = analytics_handler(event, None)
        assert response['statusCode'] == 401
        body = json.loads(response['body'])
        assert 'Unauthorized' in body['error']

    def test_invalid_json_body(self):
        """Return 400 for malformed JSON body."""
        event = _make_analytics_event({})
        event['body'] = 'not-valid-json'
        response = analytics_handler(event, None)
        assert response['statusCode'] == 400

    def test_validation_error_returned(self):
        """Return 400 for invalid request body."""
        body = {
            'analyticsType': 'bad_type',
            'dateRange': {'start': '2025-01-01', 'end': '2025-12-31'}
        }
        event = _make_analytics_event(body)
        response = analytics_handler(event, None)
        assert response['statusCode'] == 400
        resp_body = json.loads(response['body'])
        assert 'error' in resp_body

    @patch('src.lambda_handlers.analytics_handler.DynamoDBClient')
    def test_db_initialization_failure(self, mock_db_cls):
        """Return 500 when DynamoDB client cannot be initialized."""
        mock_db_cls.side_effect = Exception("Connection refused")
        body = {
            'analyticsType': 'cash_flow',
            'dateRange': {'start': '2025-01-01', 'end': '2025-12-31'}
        }
        event = _make_analytics_event(body)
        response = analytics_handler(event, None)
        assert response['statusCode'] == 500
        resp_body = json.loads(response['body'])
        assert 'database' in resp_body['error'].lower()

    @patch('src.lambda_handlers.analytics_handler.DynamoDBClient')
    @patch('src.lambda_handlers.analytics_handler.CashFlowAnalytics')
    def test_cash_flow_success(self, mock_analytics_cls, mock_db_cls):
        """Return 200 with analytics data for cash_flow type."""
        mock_db = MagicMock()
        mock_db_cls.return_value = mock_db

        mock_analytics = MagicMock()
        mock_analytics.analyze.return_value = {
            'summary': {'total_deposits': 5000, 'total_withdrawals': 3000},
            'period': {'start': '2025-01-01', 'end': '2025-12-31'},
            'periods': []
        }
        mock_analytics_cls.return_value = mock_analytics

        body = {
            'analyticsType': 'cash_flow',
            'dateRange': {'start': '2025-01-01', 'end': '2025-12-31'}
        }
        event = _make_analytics_event(body)
        response = analytics_handler(event, None)

        assert response['statusCode'] == 200
        resp_body = json.loads(response['body'])
        assert resp_body['analyticsType'] == 'cash_flow'
        assert resp_body['userId'] == 'test-user-123'
        assert 'generatedAt' in resp_body
        assert 'data' in resp_body

    @patch('src.lambda_handlers.analytics_handler.DynamoDBClient')
    @patch('src.lambda_handlers.analytics_handler.HealthScoreAnalytics')
    def test_health_analytics_success(self, mock_health_cls, mock_db_cls):
        """Return 200 with health score data."""
        mock_db = MagicMock()
        mock_db.get_all_user_transactions.return_value = []
        mock_db.get_institutions.return_value = []
        mock_db.get_goals.return_value = []
        mock_db_cls.return_value = mock_db

        mock_health = MagicMock()
        mock_health.analyze.return_value = {
            'overall_score': 75.0,
            'rating': 'Good',
            'components': {},
            'recommendations': []
        }
        mock_health_cls.return_value = mock_health

        body = {
            'analyticsType': 'health',
            'dateRange': {'start': '2025-01-01', 'end': '2025-12-31'}
        }
        event = _make_analytics_event(body)
        response = analytics_handler(event, None)

        assert response['statusCode'] == 200
        resp_body = json.loads(response['body'])
        assert resp_body['analyticsType'] == 'health'
        assert resp_body['data']['overall_score'] == 75.0

    @patch('src.lambda_handlers.analytics_handler.DynamoDBClient')
    @patch('src.lambda_handlers.analytics_handler.GoalAnalytics')
    def test_goals_analytics_success(self, mock_analytics_cls, mock_db_cls):
        """Goals handler passes only user_id to GoalAnalytics.analyze() (no date range)."""
        mock_db = MagicMock()
        mock_db_cls.return_value = mock_db

        mock_analytics = MagicMock()
        mock_analytics.analyze.return_value = {
            'summary': {'total_goals': 3, 'active_goals': 2, 'completed_goals': 1},
            'goals': [],
            'insights': {'at_risk': [], 'near_completion': [], 'priorities': []}
        }
        mock_analytics_cls.return_value = mock_analytics

        body = {
            'analyticsType': 'goals'
        }
        event = _make_analytics_event(body)
        response = analytics_handler(event, None)

        assert response['statusCode'] == 200
        resp_body = json.loads(response['body'])
        assert resp_body['analyticsType'] == 'goals'
        assert resp_body['userId'] == 'test-user-123'
        assert 'data' in resp_body
        # Verify analyze() was called with ONLY user_id — no start_date/end_date
        mock_analytics.analyze.assert_called_once_with('test-user-123')

    @patch('src.lambda_handlers.analytics_handler.DynamoDBClient')
    @patch('src.lambda_handlers.analytics_handler.CashFlowAnalytics')
    def test_analytics_computation_failure(self, mock_analytics_cls, mock_db_cls):
        """Return 500 when analytics computation throws unexpected exception."""
        mock_db = MagicMock()
        mock_db_cls.return_value = mock_db

        mock_analytics = MagicMock()
        mock_analytics.analyze.side_effect = RuntimeError("DynamoDB scan failed")
        mock_analytics_cls.return_value = mock_analytics

        body = {
            'analyticsType': 'cash_flow',
            'dateRange': {'start': '2025-01-01', 'end': '2025-12-31'}
        }
        event = _make_analytics_event(body)
        response = analytics_handler(event, None)

        assert response['statusCode'] == 500

    @patch('src.lambda_handlers.analytics_handler.DynamoDBClient')
    @patch('src.lambda_handlers.analytics_handler.CashFlowAnalytics')
    def test_options_passed_to_analytics(self, mock_analytics_cls, mock_db_cls):
        """Verify groupBy option is forwarded to CashFlowAnalytics."""
        mock_db = MagicMock()
        mock_db_cls.return_value = mock_db

        mock_analytics = MagicMock()
        mock_analytics.analyze.return_value = {'summary': {}, 'periods': [], 'period': {}}
        mock_analytics_cls.return_value = mock_analytics

        body = {
            'analyticsType': 'cash_flow',
            'dateRange': {'start': '2025-01-01', 'end': '2025-12-31'},
            'options': {'groupBy': 'week'}
        }
        event = _make_analytics_event(body)
        analytics_handler(event, None)

        mock_analytics.analyze.assert_called_once_with(
            'test-user-123', '2025-01-01', '2025-12-31', group_by='week'
        )

    def test_response_headers_include_cors(self):
        """Verify CORS headers are included in response."""
        event = {'body': '{}', 'requestContext': {}}
        response = analytics_handler(event, None)
        assert 'Access-Control-Allow-Origin' in response['headers']


# ---------------------------------------------------------------------------
# Report handler integration tests
# ---------------------------------------------------------------------------

class TestReportHandler:
    """Test report Lambda handler with mocked dependencies."""

    def test_unauthorized_no_user_id(self):
        """Return 401 when no user identity in event."""
        event = {'body': '{}', 'requestContext': {}}
        response = report_handler(event, None)
        assert response['statusCode'] == 401

    def test_invalid_json_body(self):
        """Return 400 for malformed JSON body."""
        event = _make_report_event({})
        event['body'] = 'not-json!!!'
        response = report_handler(event, None)
        assert response['statusCode'] == 400

    def test_validation_error_returned(self):
        """Return 400 for invalid report type."""
        body = {
            'reportType': 'nonexistent_type',
            'dateRange': {'start': '2025-01-01', 'end': '2025-12-31'}
        }
        event = _make_report_event(body)
        response = report_handler(event, None)
        assert response['statusCode'] == 400

    @patch('src.lambda_handlers.report_handler.DynamoDBClient')
    def test_db_initialization_failure(self, mock_db_cls):
        """Return 500 when DynamoDB client cannot be initialized."""
        mock_db_cls.side_effect = Exception("AWS credentials not found")
        body = {
            'reportType': 'cash_flow',
            'dateRange': {'start': '2025-01-01', 'end': '2025-12-31'}
        }
        event = _make_report_event(body)
        response = report_handler(event, None)
        assert response['statusCode'] == 500

    @patch('src.lambda_handlers.report_handler.S3Uploader')
    @patch('src.lambda_handlers.report_handler.DynamoDBClient')
    @patch('src.lambda_handlers.report_handler.CashFlowAnalytics')
    def test_cash_flow_report_success(self, mock_analytics_cls, mock_db_cls, mock_s3_cls):
        """Return 200 with report URL for cash_flow report."""
        mock_db = MagicMock()
        mock_db_cls.return_value = mock_db

        mock_analytics = MagicMock()
        mock_analytics.analyze.return_value = {
            'summary': {'total_deposits': 5000, 'total_withdrawals': 3000, 'net_cash_flow': 2000, 'savings_rate': 40},
            'period': {'start': '2025-01-01', 'end': '2025-12-31'},
            'periods': [],
            'trends': {}
        }
        mock_analytics_cls.return_value = mock_analytics

        mock_s3 = MagicMock()
        mock_s3.upload_report.return_value = {
            'bucket': 'cpsc-analytics-devl',
            'key': 'reports/test-user-123/2025/01/01/cash_flow_report_100000.html',
            'presigned_url': 'https://s3.amazonaws.com/presigned-url'
        }
        mock_s3_cls.return_value = mock_s3

        body = {
            'reportType': 'cash_flow',
            'dateRange': {'start': '2025-01-01', 'end': '2025-12-31'},
            'options': {'userName': 'John Doe'}
        }
        event = _make_report_event(body)
        response = report_handler(event, None)

        assert response['statusCode'] == 200
        resp_body = json.loads(response['body'])
        assert resp_body['reportType'] == 'cash_flow'
        assert resp_body['userId'] == 'test-user-123'
        assert 'reportUrl' in resp_body
        assert resp_body['reportUrl'] == 'https://s3.amazonaws.com/presigned-url'
        assert 's3Key' in resp_body

    @patch('src.lambda_handlers.report_handler.S3Uploader')
    @patch('src.lambda_handlers.report_handler.DynamoDBClient')
    @patch('src.lambda_handlers.report_handler.CashFlowAnalytics')
    def test_s3_upload_failure(self, mock_analytics_cls, mock_db_cls, mock_s3_cls):
        """Return 500 when S3 upload fails."""
        mock_db = MagicMock()
        mock_db_cls.return_value = mock_db

        mock_analytics = MagicMock()
        mock_analytics.analyze.return_value = {
            'summary': {'total_deposits': 5000, 'total_withdrawals': 3000, 'net_cash_flow': 2000, 'savings_rate': 40},
            'period': {'start': '2025-01-01', 'end': '2025-12-31'},
            'periods': [],
            'trends': {}
        }
        mock_analytics_cls.return_value = mock_analytics

        mock_s3 = MagicMock()
        mock_s3.upload_report.side_effect = Exception("S3 bucket not found")
        mock_s3_cls.return_value = mock_s3

        body = {
            'reportType': 'cash_flow',
            'dateRange': {'start': '2025-01-01', 'end': '2025-12-31'}
        }
        event = _make_report_event(body)
        response = report_handler(event, None)

        assert response['statusCode'] == 500
        resp_body = json.loads(response['body'])
        assert 'store' in resp_body['error'].lower() or 'Failed' in resp_body['error']

    @patch('src.lambda_handlers.report_handler.S3Uploader')
    @patch('src.lambda_handlers.report_handler.DynamoDBClient')
    @patch('src.lambda_handlers.report_handler.HealthScoreAnalytics')
    def test_health_score_report_success(self, mock_health_cls, mock_db_cls, mock_s3_cls):
        """Return 200 for health_score report type."""
        mock_db = MagicMock()
        mock_db.get_all_user_transactions.return_value = []
        mock_db.get_institutions.return_value = []
        mock_db.get_goals.return_value = []
        mock_db_cls.return_value = mock_db

        mock_health = MagicMock()
        mock_health.analyze.return_value = {
            'overall_score': 80.0,
            'rating': 'Good',
            'period_days': 365,
            'computed_at': '2025-01-01T00:00:00',
            'components': {
                'savings_rate': {'score': 85, 'weight': 0.25, 'contribution': 21.25},
            },
            'recommendations': []
        }
        mock_health_cls.return_value = mock_health

        mock_s3 = MagicMock()
        mock_s3.upload_report.return_value = {
            'bucket': 'cpsc-bucket',
            'key': 'reports/test/health.html',
            'presigned_url': 'https://s3.example.com/health-report'
        }
        mock_s3_cls.return_value = mock_s3

        body = {
            'reportType': 'health_score',
            'dateRange': {'start': '2025-01-01', 'end': '2025-12-31'}
        }
        event = _make_report_event(body)
        response = report_handler(event, None)

        assert response['statusCode'] == 200
        resp_body = json.loads(response['body'])
        assert resp_body['reportType'] == 'health_score'

    def test_response_headers_include_cors(self):
        """Verify CORS headers are set."""
        event = {'body': '{}', 'requestContext': {}}
        response = report_handler(event, None)
        assert 'Access-Control-Allow-Origin' in response['headers']
