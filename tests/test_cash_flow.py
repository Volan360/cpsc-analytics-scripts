"""Tests for cash flow analytics module."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock

from src.analytics.cash_flow import CashFlowAnalytics
from src.data.data_models import Transaction


@pytest.fixture
def mock_db_client():
    """Create a mocked DynamoDB client."""
    mock = Mock()
    return mock


@pytest.fixture
def analytics(mock_db_client):
    """Create cash flow analytics instance."""
    return CashFlowAnalytics(mock_db_client)


@pytest.fixture
def sample_transactions():
    """Create sample transaction data."""
    base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
    
    return [
        Transaction(
            institution_id='inst1',
            created_at=base_ts,
            transaction_id='txn1',
            user_id='user1',
            type='DEPOSIT',
            amount=1000.0,
            tags=['salary'],
            transaction_date=base_ts
        ),
        Transaction(
            institution_id='inst1',
            created_at=base_ts + 86400,  # +1 day
            transaction_id='txn2',
            user_id='user1',
            type='WITHDRAWAL',
            amount=200.0,
            tags=['groceries'],
            transaction_date=base_ts + 86400
        ),
        Transaction(
            institution_id='inst1',
            created_at=base_ts + 172800,  # +2 days
            transaction_id='txn3',
            user_id='user1',
            type='WITHDRAWAL',
            amount=150.0,
            tags=['utilities'],
            transaction_date=base_ts + 172800
        ),
        Transaction(
            institution_id='inst1',
            created_at=base_ts + 259200,  # +3 days
            transaction_id='txn4',
            user_id='user1',
            type='DEPOSIT',
            amount=500.0,
            tags=['freelance'],
            transaction_date=base_ts + 259200
        ),
        Transaction(
            institution_id='inst1',
            created_at=base_ts + 345600,  # +4 days
            transaction_id='txn5',
            user_id='user1',
            type='WITHDRAWAL',
            amount=100.0,
            tags=['entertainment'],
            transaction_date=base_ts + 345600
        )
    ]


class TestCashFlowAnalytics:
    """Test suite for cash flow analytics."""

    def test_analyze_basic_metrics(self, analytics, mock_db_client, sample_transactions):
        """Test basic cash flow metrics calculation."""
        mock_db_client.get_all_user_transactions.return_value = sample_transactions
        mock_db_client.get_institutions.return_value = []
        
        result = analytics.analyze('user1', '2024-01-01', '2024-01-31', group_by='month')
        
        assert result['user_id'] == 'user1'
        assert result['summary']['total_deposits'] == 1500.0
        assert result['summary']['total_withdrawals'] == 450.0
        assert result['summary']['net_cash_flow'] == 1050.0
        assert result['summary']['transaction_count'] == 5

    def test_analyze_no_transactions(self, analytics, mock_db_client):
        """Test analysis with no transactions."""
        mock_db_client.get_all_user_transactions.return_value = []
        mock_db_client.get_institutions.return_value = []
        
        result = analytics.analyze('user1', '2024-01-01', '2024-01-31')
        
        assert result['summary']['total_deposits'] == 0
        assert result['summary']['total_withdrawals'] == 0
        assert result['summary']['net_cash_flow'] == 0
        assert result['summary']['transaction_count'] == 0
        assert 'message' in result

    def test_analyze_deposits_only(self, analytics, mock_db_client):
        """Test analysis with only deposits."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        
        deposits = [
            Transaction(
                institution_id='inst1',
                created_at=base_ts + (i * 86400),
                transaction_id=f'txn{i}',
                user_id='user1',
                type='DEPOSIT',
                amount=300.0,
                tags=['salary'],
                transaction_date=base_ts + (i * 86400)
            )
            for i in range(5)
        ]
        
        mock_db_client.get_all_user_transactions.return_value = deposits
        mock_db_client.get_institutions.return_value = []
        
        result = analytics.analyze('user1', '2024-01-01', '2024-01-31')
        
        assert result['summary']['total_deposits'] == 1500.0
        assert result['summary']['total_withdrawals'] == 0
        assert result['summary']['net_cash_flow'] == 1500.0
        assert result['metrics']['savings_rate'] == 100.0

    def test_analyze_withdrawals_only(self, analytics, mock_db_client):
        """Test analysis with only withdrawals."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        
        withdrawals = [
            Transaction(
                institution_id='inst1',
                created_at=base_ts + (i * 86400),
                transaction_id=f'txn{i}',
                user_id='user1',
                type='WITHDRAWAL',
                amount=40.0,
                tags=['groceries'],
                transaction_date=base_ts + (i * 86400)
            )
            for i in range(5)
        ]
        
        mock_db_client.get_all_user_transactions.return_value = withdrawals
        mock_db_client.get_institutions.return_value = []
        
        result = analytics.analyze('user1', '2024-01-01', '2024-01-31')
        
        assert result['summary']['total_deposits'] == 0
        assert result['summary']['total_withdrawals'] == 200.0
        assert result['summary']['net_cash_flow'] == -200.0

    def test_grouping_by_month(self, analytics, mock_db_client, sample_transactions):
        """Test monthly grouping."""
        mock_db_client.get_all_user_transactions.return_value = sample_transactions
        mock_db_client.get_institutions.return_value = []
        
        result = analytics.analyze('user1', '2024-01-01', '2024-01-31', group_by='month')
        
        assert 'trends' in result
        # All transactions are in same month
        assert len(result['trends']['periods']) > 0

    def test_grouping_by_week(self, analytics, mock_db_client, sample_transactions):
        """Test weekly grouping."""
        mock_db_client.get_all_user_transactions.return_value = sample_transactions
        mock_db_client.get_institutions.return_value = []
        
        result = analytics.analyze('user1', '2024-01-01', '2024-01-31', group_by='week')
        
        assert 'trends' in result
        # All transactions are in same week
        assert len(result['trends']['periods']) > 0

    def test_grouping_by_day(self, analytics, mock_db_client, sample_transactions):
        """Test daily grouping."""
        mock_db_client.get_all_user_transactions.return_value = sample_transactions
        mock_db_client.get_institutions.return_value = []
        
        result = analytics.analyze('user1', '2024-01-01', '2024-01-31', group_by='day')
        
        assert 'trends' in result
        # 5 different days (one per transaction)
        assert len(result['trends']['periods']) == 5

    def test_cash_flow_with_tags(self, analytics, mock_db_client, sample_transactions):
        """Test that tags are included in transaction data."""
        mock_db_client.get_all_user_transactions.return_value = sample_transactions
        mock_db_client.get_institutions.return_value = []
        
        result = analytics.analyze('user1', '2024-01-01', '2024-01-31')
        
        # Check that analysis succeeded
        assert 'summary' in result
        assert result['summary']['transaction_count'] == 5

    def test_savings_rate_calculation(self, analytics, mock_db_client):
        """Test savings rate calculation."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        
        transactions = [
            Transaction(
                institution_id='inst1',
                created_at=base_ts + (i * 86400),
                transaction_id=f'deposit{i}',
                user_id='user1',
                type='DEPOSIT',
                amount=200.0,
                tags=['income'],
                transaction_date=base_ts + (i * 86400)
            )
            for i in range(3)
        ] + [
            Transaction(
                institution_id='inst1',
                created_at=base_ts + ((i + 3) * 86400),
                transaction_id=f'withdrawal{i}',
                user_id='user1',
                type='WITHDRAWAL',
                amount=120.0,
                tags=['expenses'],
                transaction_date=base_ts + ((i + 3) * 86400)
            )
            for i in range(2)
        ]
        
        mock_db_client.get_all_user_transactions.return_value = transactions
        mock_db_client.get_institutions.return_value = []
        
        result = analytics.analyze('user1', '2024-01-01', '2024-01-31')
        
        # Savings rate should be 60% ((600-240)/600)
        assert result['metrics']['savings_rate'] == 60.0

    def test_burn_rate_calculation(self, analytics, mock_db_client):
        """Test burn rate calculation."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        
        transactions = [
            Transaction(
                institution_id='inst1',
                created_at=base_ts + (i * 86400),
                transaction_id=f'txn{i}',
                user_id='user1',
                type='WITHDRAWAL',
                amount=60.0,
                tags=['expenses'],
                transaction_date=base_ts + (i * 86400)
            )
            for i in range(5)
        ]
        
        mock_db_client.get_all_user_transactions.return_value = transactions
        mock_db_client.get_institutions.return_value = []
        
        result = analytics.analyze('user1', '2024-01-01', '2024-01-31')
        
        # Burn rate should be 300/days
        assert result['metrics']['daily_burn_rate'] > 0


class TestCashFlowProjection:
    """Test cash flow projection calculations."""
    
    def test_calculate_projection_basic(self, analytics, mock_db_client):
        """Test basic 3-month projection."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        
        # Create 6 months of historical data (for projection base)
        transactions = []
        for month in range(6):
            # Add deposits and withdrawals for each month
            transactions.append(
                Transaction(
                    institution_id='inst1',
                    created_at=base_ts + (month * 30 * 86400),
                    transaction_id=f'deposit_{month}',
                    user_id='user1',
                    type='DEPOSIT',
                    amount=1000.0,
                    tags=['salary'],
                    transaction_date=base_ts + (month * 30 * 86400)
                )
            )
            transactions.append(
                Transaction(
                    institution_id='inst1',
                    created_at=base_ts + (month * 30 * 86400) + 43200,
                    transaction_id=f'withdrawal_{month}',
                    user_id='user1',
                    type='WITHDRAWAL',
                    amount=600.0,
                    tags=['expenses'],
                    transaction_date=base_ts + (month * 30 * 86400) + 43200
                )
            )
        
        mock_db_client.get_all_user_transactions.return_value = transactions
        mock_db_client.get_institutions.return_value = [
            MagicMock(current_balance=5000.0)
        ]
        
        result = analytics.calculate_projection('user1', months_ahead=3)
        
        assert 'current_balance' in result
        assert result['current_balance'] == 5000.0
        assert 'historical_monthly_average' in result
        assert 'projections' in result
        assert len(result['projections']) == 3
        
        # Check that projections have required fields
        for projection in result['projections']:
            assert 'month' in projection
            assert 'projected_deposits' in projection
            assert 'projected_withdrawals' in projection
            assert 'projected_net_flow' in projection
            assert 'projected_balance' in projection
    
    def test_calculate_projection_no_data(self, analytics, mock_db_client):
        """Test projection with no historical data."""
        mock_db_client.get_all_user_transactions.return_value = []
        
        result = analytics.calculate_projection('user1', months_ahead=3)
        
        assert 'error' in result
    
    def test_calculate_projection_positive_trend(self, analytics, mock_db_client):
        """Test projection with positive cash flow."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        
        transactions = []
        for month in range(6):
            transactions.append(
                Transaction(
                    institution_id='inst1',
                    created_at=base_ts + (month * 30 * 86400),
                    transaction_id=f'deposit_{month}',
                    user_id='user1',
                    type='DEPOSIT',
                    amount=2000.0,
                    tags=['salary'],
                    transaction_date=base_ts + (month * 30 * 86400)
                )
            )
            transactions.append(
                Transaction(
                    institution_id='inst1',
                    created_at=base_ts + (month * 30 * 86400) + 43200,
                    transaction_id=f'withdrawal_{month}',
                    user_id='user1',
                    type='WITHDRAWAL',
                    amount=800.0,
                    tags=['expenses'],
                    transaction_date=base_ts + (month * 30 * 86400) + 43200
                )
            )
        
        mock_db_client.get_all_user_transactions.return_value = transactions
        mock_db_client.get_institutions.return_value = [
            MagicMock(current_balance=10000.0)
        ]
        
        result = analytics.calculate_projection('user1', months_ahead=3)
        
        # Balance should be increasing each month
        balances = [p['projected_balance'] for p in result['projections']]
        assert balances[0] > 10000.0  # First projection higher than current
        assert balances[1] > balances[0]  # Increasing trend
        assert balances[2] > balances[1]
    
    def test_calculate_projection_negative_trend(self, analytics, mock_db_client):
        """Test projection with negative cash flow."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        
        transactions = []
        for month in range(6):
            transactions.append(
                Transaction(
                    institution_id='inst1',
                    created_at=base_ts + (month * 30 * 86400),
                    transaction_id=f'deposit_{month}',
                    user_id='user1',
                    type='DEPOSIT',
                    amount=500.0,
                    tags=['income'],
                    transaction_date=base_ts + (month * 30 * 86400)
                )
            )
            transactions.append(
                Transaction(
                    institution_id='inst1',
                    created_at=base_ts + (month * 30 * 86400) + 43200,
                    transaction_id=f'withdrawal_{month}',
                    user_id='user1',
                    type='WITHDRAWAL',
                    amount=1000.0,
                    tags=['expenses'],
                    transaction_date=base_ts + (month * 30 * 86400) + 43200
                )
            )
        
        mock_db_client.get_all_user_transactions.return_value = transactions
        mock_db_client.get_institutions.return_value = [
            MagicMock(current_balance=8000.0)
        ]
        
        result = analytics.calculate_projection('user1', months_ahead=3)
        
        # Balance should be decreasing each month
        balances = [p['projected_balance'] for p in result['projections']]
        assert balances[0] < 8000.0  # First projection lower than current
        assert balances[1] < balances[0]  # Decreasing trend
        assert balances[2] < balances[1]
