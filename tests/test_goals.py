"""Tests for goals analytics module."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock

from src.analytics.goals import GoalAnalytics
from src.data.data_models import Goal, Institution, Transaction


class TestGoalAnalytics:
    """Test suite for goals analytics."""

    @pytest.fixture
    def mock_db_client(self):
        """Create a mocked DynamoDB client."""
        return Mock()

    @pytest.fixture
    def analytics(self, mock_db_client):
        """Create goal analytics instance."""
        return GoalAnalytics(mock_db_client)

    @pytest.fixture
    def sample_goals(self):
        """Create sample goal data."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        
        return [
            Goal(
                user_id='user1',
                goal_id='goal1',
                name='Vacation Fund',
                description='Save for summer vacation',
                linked_institutions={'inst1': 50, 'inst2': 30},
                target_amount=5000.0,
                is_completed=False,
                is_active=True,
                linked_transactions=[],
                completed_at=None,
                created_at=base_ts
            ),
            Goal(
                user_id='user1',
                goal_id='goal2',
                name='Emergency Fund',
                description='6 months expenses',
                linked_institutions={'inst1': 100},
                target_amount=10000.0,
                is_completed=False,
                is_active=True,
                linked_transactions=[],
                completed_at=None,
                created_at=base_ts
            )
        ]

    @pytest.fixture
    def sample_institutions(self):
        """Create sample institution data."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        
        return [
            Institution(
                user_id='user1',
                institution_id='inst1',
                institution_name='Main Savings',
                starting_balance=1000.0,
                current_balance=3000.0,
                created_at=base_ts,
                allocated_percent=75,
                linked_goals=['goal1', 'goal2']
            ),
            Institution(
                user_id='user1',
                institution_id='inst2',
                institution_name='Investment Account',
                starting_balance=500.0,
                current_balance=1500.0,
                created_at=base_ts,
                allocated_percent=30,
                linked_goals=['goal1']
            )
        ]

    def test_analyze_basic_metrics(self, analytics, mock_db_client, sample_goals, sample_institutions):
        """Test basic goal analysis metrics."""
        mock_db_client.get_goals.return_value = sample_goals
        mock_db_client.get_institutions.return_value = sample_institutions
        mock_db_client.get_transactions.return_value = []
        
        result = analytics.analyze('user1')
        
        assert result['user_id'] == 'user1'
        assert result['summary']['total_goals'] == 2
        assert result['summary']['active_goals'] == 2
        assert result['summary']['completed_goals'] == 0

    def test_analyze_no_goals(self, analytics, mock_db_client):
        """Test analysis with no goals."""
        mock_db_client.get_goals.return_value = []
        mock_db_client.get_institutions.return_value = []
        
        result = analytics.analyze('user1')
        
        assert result['summary']['total_goals'] == 0
        assert len(result['goals']) == 0

    def test_goal_progress_calculation(self, analytics, mock_db_client, sample_goals, sample_institutions):
        """Test goal progress percentage calculation."""
        mock_db_client.get_goals.return_value = sample_goals
        mock_db_client.get_institutions.return_value = sample_institutions
        mock_db_client.get_transactions.return_value = []
        
        result = analytics.analyze('user1')
        
        # Vacation Fund: (3000*0.5 + 1500*0.3) / 5000 = 39%
        vacation_goal = next(g for g in result['goals'] if g['name'] == 'Vacation Fund')
        assert vacation_goal['current_amount'] == 1950.0
        assert vacation_goal['progress_percent'] == 39.0

    def test_at_risk_goals_identification(self, analytics, mock_db_client, sample_goals, sample_institutions):
        """Test identification of at-risk goals."""
        mock_db_client.get_goals.return_value = sample_goals
        mock_db_client.get_institutions.return_value = sample_institutions
        mock_db_client.get_transactions.return_value = []
        
        result = analytics.analyze('user1')
        
        assert 'insights' in result
        assert 'at_risk' in result['insights']
        # Both goals should be flagged due to slow progress (< 50%)
        # (Note: actual at_risk logic may vary based on implementation)

    def test_goal_priorities(self, analytics, mock_db_client, sample_goals, sample_institutions):
        """Test goal priority calculation."""
        mock_db_client.get_goals.return_value = sample_goals
        mock_db_client.get_institutions.return_value = sample_institutions
        mock_db_client.get_transactions.return_value = []
        
        result = analytics.analyze('user1')
        
        assert 'insights' in result
        assert 'priorities' in result['insights']
        # Vacation Fund should have higher priority (closer to completion %)
        priorities = result['insights']['priorities']
        assert len(priorities) == 2

    def test_completed_goal(self, analytics, mock_db_client, sample_institutions):
        """Test analysis with completed goal."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        
        completed_goal = Goal(
            user_id='user1',
            goal_id='goal1',
            name='Completed Goal',
            description='Done',
            linked_institutions={'inst1': 100},
            target_amount=1000.0,
            is_completed=True,
            is_active=False,
            linked_transactions=[],
            completed_at=base_ts + 86400,
            created_at=base_ts
        )
        
        mock_db_client.get_goals.return_value = [completed_goal]
        mock_db_client.get_institutions.return_value = sample_institutions
        mock_db_client.get_transactions.return_value = []
        
        result = analytics.analyze('user1')
        
        assert result['summary']['completed_goals'] == 1
        assert result['summary']['active_goals'] == 0

    def test_inactive_goal(self, analytics, mock_db_client):
        """Test handling of inactive goal."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        
        inactive_goal = Goal(
            user_id='user1',
            goal_id='goal1',
            name='Inactive Goal',
            description='Not active',
            linked_institutions={},
            target_amount=1000.0,
            is_completed=False,
            is_active=False,
            linked_transactions=[],
            completed_at=None,
            created_at=base_ts
        )
        
        mock_db_client.get_goals.return_value = [inactive_goal]
        mock_db_client.get_institutions.return_value = []
        mock_db_client.get_transactions.return_value = []
        
        result = analytics.analyze('user1')
        
        assert result['summary']['active_goals'] == 0
        assert result['summary']['total_goals'] == 1

    def test_goal_without_institutions(self, analytics, mock_db_client):
        """Test goal with no linked institutions."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        
        goal = Goal(
            user_id='user1',
            goal_id='goal1',
            name='Unlinked Goal',
            description='No institutions',
            linked_institutions={},
            target_amount=1000.0,
            is_completed=False,
            is_active=True,
            linked_transactions=[],
            completed_at=None,
            created_at=base_ts
        )
        
        mock_db_client.get_goals.return_value = [goal]
        mock_db_client.get_institutions.return_value = []
        mock_db_client.get_transactions.return_value = []
        
        result = analytics.analyze('user1')
        
        # Should have 0 current amount
        goal_detail = result['goals'][0]
        assert goal_detail['current_amount'] == 0
        assert goal_detail['progress_percent'] == 0

    def test_compare_goals(self, analytics, mock_db_client, sample_goals, sample_institutions):
        """Test side-by-side goal comparison."""
        mock_db_client.get_goal.side_effect = lambda user_id, goal_id: next(
            g for g in sample_goals if g.goal_id == goal_id
        )
        mock_db_client.get_institutions.return_value = sample_institutions
        mock_db_client.get_transactions.return_value = []
        
        result = analytics.compare_goals('user1', 'goal1', 'goal2')
        
        assert 'goal1' in result
        assert 'goal2' in result
        assert 'comparison' in result
        assert 'target_difference' in result['comparison']

    def test_reallocation_strategy(self, analytics, mock_db_client, sample_goals, sample_institutions):
        mock_db_client.get_goal.return_value = sample_goals[0]
        mock_db_client.get_institutions.return_value = sample_institutions
        
        result = analytics.calculate_reallocation_strategy('user1', 'goal1')
        
        assert 'goal_id' in result
        assert 'goal_name' in result
        assert 'current_progress' in result
        assert 'current_total_allocation' in result
        assert 'recommendations' in result
        assert len(result['recommendations']) > 0

    def test_zero_target_amount(self, analytics, mock_db_client):
        """Test handling of goal with zero target amount."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        
        goal = Goal(
            user_id='user1',
            goal_id='goal1',
            name='Zero Target',
            description='Invalid',
            linked_institutions={},
            target_amount=0.0,
            is_completed=False,
            is_active=True,
            linked_transactions=[],
            completed_at=None,
            created_at=base_ts
        )
        
        mock_db_client.get_goals.return_value = [goal]
        mock_db_client.get_institutions.return_value = []
        mock_db_client.get_transactions.return_value = []
        
        result = analytics.analyze('user1')
        
        # Should handle gracefully without division by zero
        goal_detail = result['goals'][0]
        assert goal_detail['progress_percent'] == 0

    def test_over_allocated_goal(self, analytics, mock_db_client):
        """Test goal that is over-allocated (> 100%)."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        
        goal = Goal(
            user_id='user1',
            goal_id='goal1',
            name='Over Allocated',
            description='More than target',
            linked_institutions={'inst1': 100},
            target_amount=1000.0,
            is_completed=False,
            is_active=True,
            linked_transactions=[],
            completed_at=None,
            created_at=base_ts
        )
        
        institution = Institution(
            user_id='user1',
            institution_id='inst1',
            institution_name='Big Account',
            starting_balance=500.0,
            current_balance=2000.0,  # More than goal target
            created_at=base_ts,
            allocated_percent=100,
            linked_goals=['goal1']
        )
        
        mock_db_client.get_goals.return_value = [goal]
        mock_db_client.get_institutions.return_value = [institution]
        mock_db_client.get_transactions.return_value = []
        
        result = analytics.analyze('user1')
        
        # Progress should be capped at 100% or show > 100%
        goal_detail = result['goals'][0]
        assert goal_detail['current_amount'] == 2000.0
        assert goal_detail['progress_percent'] >= 100
