"""Tests for category analytics module."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock

from src.analytics.categories import CategoryAnalytics
from src.data.data_models import Transaction


class TestCategoryAnalytics:
    """Test suite for category analytics."""

    @pytest.fixture
    def mock_db_client(self):
        """Create a mocked DynamoDB client."""
        return Mock()

    @pytest.fixture
    def analytics(self, mock_db_client):
        """Create category analytics instance."""
        return CategoryAnalytics(mock_db_client)

    @pytest.fixture
    def sample_transactions(self):
        """Create sample transaction data with various tags."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        
        return [
            Transaction(
                institution_id='inst1',
                created_at=base_ts,
                transaction_id='txn1',
                user_id='user1',
                type='WITHDRAWAL',
                amount=200.0,
                tags=['groceries', 'food'],
                transaction_date=base_ts
            ),
            Transaction(
                institution_id='inst1',
                created_at=base_ts + 86400,
                transaction_id='txn2',
                user_id='user1',
                type='WITHDRAWAL',
                amount=150.0,
                tags=['groceries'],
                transaction_date=base_ts + 86400
            ),
            Transaction(
                institution_id='inst1',
                created_at=base_ts + 172800,
                transaction_id='txn3',
                user_id='user1',
                type='WITHDRAWAL',
                amount=100.0,
                tags=['utilities'],
                transaction_date=base_ts + 172800
            ),
            Transaction(
                institution_id='inst1',
                created_at=base_ts + 259200,
                transaction_id='txn4',
                user_id='user1',
                type='WITHDRAWAL',
                amount=50.0,
                tags=['entertainment', 'food'],
                transaction_date=base_ts + 259200
            ),
            Transaction(
                institution_id='inst1',
                created_at=base_ts + 345600,
                transaction_id='txn5',
                user_id='user1',
                type='WITHDRAWAL',
                amount=75.0,
                tags=['transportation'],
                transaction_date=base_ts + 345600
            )
        ]

    def test_analyze_basic_categories(self, analytics, mock_db_client, sample_transactions):
        """Test basic category spending analysis."""
        mock_db_client.get_all_user_transactions.return_value = sample_transactions
        
        result = analytics.analyze('user1', '2024-01-01', '2024-01-31')
        
        assert result['user_id'] == 'user1'
        # Total is 575 (sum of all 5 transaction amounts)
        assert result['summary']['total_amount'] == 575.0
        assert result['summary']['unique_categories'] == 5
        assert result['summary']['transaction_count'] == 5

    def test_analyze_no_transactions(self, analytics, mock_db_client):
        """Test analysis with no transactions."""
        mock_db_client.get_all_user_transactions.return_value = []
        
        result = analytics.analyze('user1', '2024-01-01', '2024-01-31')
        
        assert result['summary']['total_amount'] == 0
        assert result['summary']['unique_categories'] == 0
        assert 'message' in result

    def test_top_categories(self, analytics, mock_db_client, sample_transactions):
        """Test top category identification."""
        mock_db_client.get_all_user_transactions.return_value = sample_transactions
        
        result = analytics.analyze('user1', '2024-01-01', '2024-01-31')
        
        # Groceries should be top category (200 + 150 = 350)
        top_category = result['top_categories'][0]
        assert top_category['amount'] == 350.0
        assert top_category['name'] == 'groceries'
        assert top_category['rank'] == 1

    def test_category_percentages(self, analytics, mock_db_client, sample_transactions):
        """Test category percentage calculations."""
        mock_db_client.get_all_user_transactions.return_value = sample_transactions
        
        result = analytics.analyze('user1', '2024-01-01', '2024-01-31')
        
        # Groceries: 350/500 = 70%
        groceries_percent = result['categories']['percentages']['groceries']
        # groceries is 350 out of 575 total = 60.87%
        assert round(groceries_percent, 2) == 60.87

    def test_spending_diversity(self, analytics, mock_db_client, sample_transactions):
        """Test spending diversity metric (HHI)."""
        mock_db_client.get_all_user_transactions.return_value = sample_transactions
        
        result = analytics.analyze('user1', '2024-01-01', '2024-01-31')
        
        assert 'diversity' in result
        diversity = result['diversity']
        
        # HHI should be between 0 and 1
        assert 0 <= diversity['hhi'] <= 1
        assert 'description' in diversity

    def test_co_occurrences(self, analytics, mock_db_client, sample_transactions):
        """Test category co-occurrence analysis."""
        mock_db_client.get_all_user_transactions.return_value = sample_transactions
        
        result = analytics.analyze('user1', '2024-01-01', '2024-01-31')
        
        assert 'co_occurrences' in result
        co_occurrences = result['co_occurrences']
        
        # 'groceries' and 'food' appear together
        assert any(
            (co['category_1'] == 'groceries' and co['category_2'] == 'food') or
            (co['category_1'] == 'food' and co['category_2'] == 'groceries')
            for co in co_occurrences
        )

    def test_single_tag_transactions(self, analytics, mock_db_client):
        """Test transactions with single tags."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        
        transactions = [
            Transaction(
                institution_id='inst1',
                created_at=base_ts + (i * 86400),
                transaction_id=f'txn{i}',
                user_id='user1',
                type='WITHDRAWAL',
                amount=100.0,
                tags=['groceries'],
                transaction_date=base_ts + (i * 86400)
            )
            for i in range(5)
        ]
        
        mock_db_client.get_all_user_transactions.return_value = transactions
        
        result = analytics.analyze('user1', '2024-01-01', '2024-01-31')
        
        assert result['summary']['unique_categories'] == 1
        assert 'groceries' in result['categories']['totals']

    def test_untagged_transactions(self, analytics, mock_db_client):
        """Test handling of transactions without tags."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        
        transactions = [
            Transaction(
                institution_id='inst1',
                created_at=base_ts + (i * 86400),
                transaction_id=f'txn{i}',
                user_id='user1',
                type='WITHDRAWAL',
                amount=100.0,
                tags=[],
                transaction_date=base_ts + (i * 86400)
            )
            for i in range(5)
        ]
        
        mock_db_client.get_all_user_transactions.return_value = transactions
        
        result = analytics.analyze('user1', '2024-01-01', '2024-01-31')
        
        # Should handle gracefully with low transaction count
        assert result['summary']['total_amount'] >= 0

    def test_deposits_excluded(self, analytics, mock_db_client):
        """Test that deposits are excluded from spending analysis."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        
        transactions = [
            Transaction(
                institution_id='inst1',
                created_at=base_ts,
                transaction_id='txn1',
                user_id='user1',
                type='DEPOSIT',
                amount=1000.0,
                tags=['salary'],
                transaction_date=base_ts
            )
        ] + [
            Transaction(
                institution_id='inst1',
                created_at=base_ts + (i * 86400),
                transaction_id=f'txn{i+2}',
                user_id='user1',
                type='WITHDRAWAL',
                amount=40.0,
                tags=['groceries'],
                transaction_date=base_ts + (i * 86400)
            )
            for i in range(5)
        ]
        
        mock_db_client.get_all_user_transactions.return_value = transactions
        
        result = analytics.analyze('user1', '2024-01-01', '2024-01-31', transaction_type='WITHDRAWAL')
        
        # Only withdrawals should count (5 * 40 = 200)
        assert result['summary']['total_amount'] == 200.0
        assert result['summary']['transaction_count'] == 5

    def test_period_comparison(self, analytics, mock_db_client):
        """Test period comparison functionality."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        period2_ts = int(datetime(2024, 2, 1, tzinfo=timezone.utc).timestamp())
        
        period1_transactions = [
            Transaction(
                institution_id='inst1',
                created_at=base_ts + (i * 86400),
                transaction_id=f'txn1_{i}',
                user_id='user1',
                type='WITHDRAWAL',
                amount=40.0,
                tags=['groceries'],
                transaction_date=base_ts + (i * 86400)
            )
            for i in range(5)
        ]
        
        period2_transactions = [
            Transaction(
                institution_id='inst1',
                created_at=period2_ts + (i * 86400),
                transaction_id=f'txn2_{i}',
                user_id='user1',
                type='WITHDRAWAL',
                amount=60.0,
                tags=['groceries'],
                transaction_date=period2_ts + (i * 86400)
            )
            for i in range(5)
        ]
        
        # First call returns period1 transactions, second call returns period2
        mock_db_client.get_all_user_transactions.side_effect = [period1_transactions, period2_transactions]
        
        result = analytics.compare_periods(
            'user1',
            '2024-01-01',
            '2024-01-31',
            '2024-02-01',
            '2024-02-29'
        )
        
        assert 'period1' in result
        assert 'period2' in result
        assert 'total_change' in result
        assert 'category_changes' in result
        # Period1: 5 * 40 = 200, Period2: 5 * 60 = 300
        assert result['total_change'] == 100.0
