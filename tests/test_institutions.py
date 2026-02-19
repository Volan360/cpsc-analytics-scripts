"""Tests for institution analytics module."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock

from src.analytics.institutions import InstitutionAnalytics
from src.data.data_models import Institution, Transaction, Goal


class TestInstitutionAnalytics:
    """Test suite for institution analytics."""

    @pytest.fixture
    def mock_db_client(self):
        """Create a mocked DynamoDB client."""
        return Mock()

    @pytest.fixture
    def analytics(self, mock_db_client):
        """Create institution analytics instance."""
        return InstitutionAnalytics(mock_db_client)

    @pytest.fixture
    def sample_institutions(self):
        """Create sample institution data."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        
        return [
            Institution(
                user_id='user1',
                institution_id='inst1',
                institution_name='Main Checking',
                starting_balance=1000.0,
                current_balance=3000.0,
                created_at=base_ts,
                allocated_percent=50,
                linked_goals=['goal1']
            ),
            Institution(
                user_id='user1',
                institution_id='inst2',
                institution_name='Savings Account',
                starting_balance=5000.0,
                current_balance=6000.0,
                created_at=base_ts,
                allocated_percent=75,
                linked_goals=['goal1', 'goal2']
            ),
            Institution(
                user_id='user1',
                institution_id='inst3',
                institution_name='Investment Account',
                starting_balance=10000.0,
                current_balance=12000.0,
                created_at=base_ts,
                allocated_percent=90,
                linked_goals=['goal2']
            )
        ]

    @pytest.fixture
    def sample_transactions(self):
        """Create sample transaction data."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        
        return [
            Transaction(
                institution_id='inst1',
                created_at=base_ts,
                transaction_id='txn1',
                user_id='user1',
                type='DEPOSIT',
                amount=500.0,
                tags=['salary'],
                transaction_date=base_ts
            ),
            Transaction(
                institution_id='inst1',
                created_at=base_ts + 86400,
                transaction_id='txn2',
                user_id='user1',
                type='WITHDRAWAL',
                amount=200.0,
                tags=['groceries'],
                transaction_date=base_ts + 86400
            )
        ]

    @pytest.fixture
    def sample_goals(self):
        """Create sample goal data."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        
        return [
            Goal(
                user_id='user1',
                goal_id='goal1',
                name='Emergency Fund',
                description='Save 6 months',
                linked_institutions={'inst1': 50, 'inst2': 75},
                target_amount=10000.0,
                is_completed=False,
                is_active=True,
                linked_transactions=[],
                completed_at=None,
                created_at=base_ts
            ),
            Goal(
                user_id='user1',
                goal_id='goal2',
                name='Vacation',
                description='Summer trip',
                linked_institutions={'inst2': 75, 'inst3': 90},
                target_amount=5000.0,
                is_completed=False,
                is_active=True,
                linked_transactions=[],
                completed_at=None,
                created_at=base_ts
            )
        ]

    def test_analyze_basic_metrics(self, analytics, mock_db_client, sample_institutions, sample_goals):
        """Test basic institution analysis metrics."""
        mock_db_client.get_institutions.return_value = sample_institutions
        mock_db_client.get_goals.return_value = sample_goals
        mock_db_client.get_transactions.return_value = []
        
        result = analytics.analyze('user1')
        
        assert result['user_id'] == 'user1'
        assert result['summary']['total_institutions'] == 3
        assert result['summary']['total_balance'] == 21000.0
        assert result['summary']['total_starting_balance'] == 16000.0
        assert result['summary']['total_growth'] == 5000.0

    def test_analyze_no_institutions(self, analytics, mock_db_client):
        """Test analysis with no institutions."""
        mock_db_client.get_institutions.return_value = []
        mock_db_client.get_goals.return_value = []
        
        result = analytics.analyze('user1')
        
        assert result['summary']['total_institutions'] == 0
        assert result['summary']['total_balance'] == 0
        assert 'message' in result

    def test_balance_growth_calculation(self, analytics, mock_db_client, sample_institutions, sample_goals):
        """Test balance growth rate calculation."""
        mock_db_client.get_institutions.return_value = sample_institutions
        mock_db_client.get_goals.return_value = sample_goals
        mock_db_client.get_transactions.return_value = []
        
        result = analytics.analyze('user1')
        
        # Main Checking: (3000-1000)/1000 = 200%
        checking = next(i for i in result['institutions'] if i['institution_name'] == 'Main Checking')
        assert checking['balances']['growth_rate'] == 200.0

    def test_transaction_metrics(self, analytics, mock_db_client, sample_institutions, sample_goals, sample_transactions):
        """Test transaction volume and metrics."""
        mock_db_client.get_institutions.return_value = sample_institutions[:1]  # Only first institution
        mock_db_client.get_goals.return_value = sample_goals
        mock_db_client.get_transactions.return_value = sample_transactions
        
        result = analytics.analyze('user1')
        
        inst = result['institutions'][0]
        assert inst['transactions']['total_count'] == 2
        assert inst['transactions']['deposit_count'] == 1
        assert inst['transactions']['withdrawal_count'] == 1
        assert inst['transactions']['total_deposits'] == 500.0
        assert inst['transactions']['total_withdrawals'] == 200.0
        assert inst['transactions']['net_flow'] == 300.0

    def test_utilization_score(self, analytics, mock_db_client, sample_institutions, sample_goals):
        """Test utilization score calculation."""
        mock_db_client.get_institutions.return_value = sample_institutions
        mock_db_client.get_goals.return_value = sample_goals
        mock_db_client.get_transactions.return_value = []
        
        result = analytics.analyze('user1')
        
        # All institutions should have utilization scores
        for inst in result['institutions']:
            assert 'utilization_score' in inst['metrics']
            assert 0 <= inst['metrics']['utilization_score'] <= 100

    def test_activity_level_categorization(self, analytics, mock_db_client):
        """Test activity level categories."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        
        # Create transactions spanning 30 days (15 transactions = 15/30*30 = 15 per month)
        transactions = [
            Transaction(
                institution_id='inst1',
                created_at=base_ts + (i * 86400 * 2),  # Every 2 days
                transaction_id=f'txn{i}',
                user_id='user1',
                type='WITHDRAWAL',
                amount=100.0,
                tags=['test'],
                transaction_date=base_ts + (i * 86400 * 2)
            )
            for i in range(15)
        ]
        
        institution = Institution(
            user_id='user1',
            institution_id='inst1',
            institution_name='Active Account',
            starting_balance=1000.0,
            current_balance=2000.0,
            created_at=base_ts,
            allocated_percent=50,
            linked_goals=[]
        )
        
        mock_db_client.get_institutions.return_value = [institution]
        mock_db_client.get_goals.return_value = []
        mock_db_client.get_transactions.return_value = transactions
        
        result = analytics.analyze('user1')
        
        inst = result['institutions'][0]
        # Should be "Very Active" (>10 per month)
        assert inst['metrics']['activity_level'] in ['Very Active', 'Active']

    def test_rankings(self, analytics, mock_db_client, sample_institutions, sample_goals):
        """Test institution rankings."""
        mock_db_client.get_institutions.return_value = sample_institutions
        mock_db_client.get_goals.return_value = sample_goals
        mock_db_client.get_transactions.return_value = []
        
        result = analytics.analyze('user1')
        
        assert 'rankings' in result
        rankings = result['rankings']
        
        # Should have rankings by balance, growth, activity, utilization
        assert 'by_balance' in rankings
        assert 'by_growth_rate' in rankings
        assert 'by_activity' in rankings
        assert 'by_utilization' in rankings
        
        # Top by balance should be Investment Account (12000)
        assert rankings['by_balance'][0]['institution_name'] == 'Investment Account'

    def test_underutilized_detection(self, analytics, mock_db_client, sample_goals):
        """Test detection of underutilized institutions."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        
        # Create an unused institution
        institutions = [
            Institution(
                user_id='user1',
                institution_id='inst1',
                institution_name='Unused Account',
                starting_balance=0.0,
                current_balance=0.0,
                created_at=base_ts,
                allocated_percent=0,
                linked_goals=[]
            )
        ]
        
        mock_db_client.get_institutions.return_value = institutions
        mock_db_client.get_goals.return_value = []
        mock_db_client.get_transactions.return_value = []
        
        result = analytics.analyze('user1')
        
        assert 'underutilized' in result
        assert len(result['underutilized']) > 0
        
        unused = result['underutilized'][0]
        assert unused['institution_name'] == 'Unused Account'
        assert 'reasons' in unused
        assert 'recommendations' in unused

    def test_portfolio_concentration(self, analytics, mock_db_client, sample_institutions, sample_goals):
        """Test portfolio concentration (HHI) calculation."""
        mock_db_client.get_institutions.return_value = sample_institutions
        mock_db_client.get_goals.return_value = sample_goals
        mock_db_client.get_transactions.return_value = []
        
        result = analytics.analyze('user1')
        
        assert 'portfolio' in result
        portfolio = result['portfolio']
        
        assert 'concentration' in portfolio
        assert 'hhi' in portfolio['concentration']
        assert 'level' in portfolio['concentration']
        assert 0 <= portfolio['concentration']['hhi'] <= 1

    def test_balance_distribution(self, analytics, mock_db_client, sample_institutions, sample_goals):
        """Test balance distribution across institutions."""
        mock_db_client.get_institutions.return_value = sample_institutions
        mock_db_client.get_goals.return_value = sample_goals
        mock_db_client.get_transactions.return_value = []
        
        result = analytics.analyze('user1')
        
        distribution = result['portfolio']['distribution']
        
        # Should have 3 institutions
        assert len(distribution) == 3
        
        # Percentages should sum to 100
        total_percent = sum(d['percent'] for d in distribution)
        assert abs(total_percent - 100.0) < 0.01

    def test_compare_institutions(self, analytics, mock_db_client, sample_institutions, sample_goals):
        """Test side-by-side institution comparison."""
        mock_db_client.get_institution.side_effect = lambda user_id, inst_id: next(
            i for i in sample_institutions if i.institution_id == inst_id
        )
        mock_db_client.get_goals.return_value = sample_goals
        mock_db_client.get_transactions.return_value = []
        
        result = analytics.compare_institutions('user1', 'inst1', 'inst2')
        
        assert 'institution1' in result
        assert 'institution2' in result
        assert 'comparison' in result
        
        comparison = result['comparison']
        assert 'balance_difference' in comparison
        assert 'growth_rate_difference' in comparison

    def test_institution_not_found(self, analytics, mock_db_client):
        """Test handling of non-existent institution."""
        mock_db_client.get_institution.return_value = None
        
        with pytest.raises(ValueError):
            analytics.compare_institutions('user1', 'invalid1', 'invalid2')

    def test_zero_balance_institution(self, analytics, mock_db_client):
        """Test institution with zero balance."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        
        institution = Institution(
            user_id='user1',
            institution_id='inst1',
            institution_name='Empty Account',
            starting_balance=0.0,
            current_balance=0.0,
            created_at=base_ts,
            allocated_percent=0,
            linked_goals=[]
        )
        
        mock_db_client.get_institutions.return_value = [institution]
        mock_db_client.get_goals.return_value = []
        mock_db_client.get_transactions.return_value = []
        
        result = analytics.analyze('user1')
        
        # Should handle gracefully
        inst = result['institutions'][0]
        assert inst['balances']['current'] == 0
        assert inst['balances']['growth_rate'] == 0

    def test_performance_metrics(self, analytics, mock_db_client, sample_institutions, sample_goals):
        """Test portfolio performance metrics."""
        mock_db_client.get_institutions.return_value = sample_institutions
        mock_db_client.get_goals.return_value = sample_goals
        mock_db_client.get_transactions.return_value = []
        
        result = analytics.analyze('user1')
        
        performance = result['portfolio']['performance']
        
        assert 'average_growth_rate' in performance
        assert 'best_performer' in performance
        assert 'worst_performer' in performance
        assert performance['best_performer'] == 'Main Checking'  # 200% growth
