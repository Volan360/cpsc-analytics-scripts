"""Tests for health score analytics."""

import pytest
from datetime import datetime, timedelta, timezone
from src.analytics.health_score import HealthScoreAnalytics
from src.data.data_models import Transaction, Institution, Goal


class TestHealthScoreCalculation:
    """Test health score calculation."""
    
    @pytest.fixture
    def health_analytics(self):
        """Create health analytics instance."""
        return HealthScoreAnalytics()
    
    @pytest.fixture
    def sample_transactions(self):
        """Create sample transactions."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        transactions = []
        
        # Regular deposits and withdrawals
        for i in range(30):
            day_ts = base_ts + (i * 86400)  # Add days in seconds
            
            # Deposits every week
            if i % 7 == 0:
                transactions.append(Transaction(
                    transaction_id=f"txn_dep_{i}",
                    user_id="user1",
                    institution_id="inst1",
                    type="DEPOSIT",
                    amount=1000.0,
                    transaction_date=day_ts,
                    created_at=day_ts,
                    description="Paycheck",
                    tags=["income"]
                ))
            
            # Regular withdrawals
            transactions.append(Transaction(
                transaction_id=f"txn_with_{i}",
                user_id="user1",
                institution_id="inst1",
                type="WITHDRAWAL",
                amount=30.0,
                transaction_date=day_ts,
                created_at=day_ts,
                description="Daily expense",
                tags=["groceries", "food"]
            ))
        
        return transactions
    
    @pytest.fixture
    def sample_institutions(self):
        """Create sample institutions."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        return [
            Institution(
                institution_id="inst1",
                user_id="user1",
                institution_name="Checking",
                starting_balance=5000.0,
                current_balance=6000.0,
                created_at=base_ts
            ),
            Institution(
                institution_id="inst2",
                user_id="user1",
                institution_name="Savings",
                starting_balance=10000.0,
                current_balance=12000.0,
                created_at=base_ts
            )
        ]
    
    @pytest.fixture
    def sample_goals(self):
        """Create sample goals."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        return [
            Goal(
                goal_id="goal1",
                user_id="user1",
                name="Emergency Fund",
                target_amount=10000.0,
                created_at=base_ts,
                is_active=True,
                linked_institutions={'inst1': 70}  # 70% of inst1 balance = 4200
            ),
            Goal(
                goal_id="goal2",
                user_id="user1",
                name="Vacation",
                target_amount=5000.0,
                created_at=base_ts,
                is_active=True,
                linked_institutions={'inst2': 25}  # 25% of inst2 balance = 3000
            )
        ]
    
    def test_calculate_health_score_basic(
        self,
        health_analytics,
        sample_transactions,
        sample_institutions,
        sample_goals
    ):
        """Test basic health score calculation."""
        result = health_analytics.calculate_health_score(
            sample_transactions,
            sample_institutions,
            sample_goals
        )
        
        assert 'overall_score' in result
        assert 'rating' in result
        assert 'components' in result
        assert 0 <= result['overall_score'] <= 100
    
    def test_health_score_components(
        self,
        health_analytics,
        sample_transactions,
        sample_institutions,
        sample_goals
    ):
        """Test all health score components are present."""
        result = health_analytics.calculate_health_score(
            sample_transactions,
            sample_institutions,
            sample_goals
        )
        
        components = result['components']
        assert 'savings_rate' in components
        assert 'goal_progress' in components
        assert 'spending_diversity' in components
        assert 'account_utilization' in components
        assert 'transaction_regularity' in components
        
        # Check each component has required fields
        for comp_data in components.values():
            assert 'score' in comp_data
            assert 'weight' in comp_data
            assert 'contribution' in comp_data
    
    def test_health_score_no_data(self, health_analytics):
        """Test health score with no data."""
        result = health_analytics.calculate_health_score([], [], [])
        
        assert result['overall_score'] == 50.0  # Neutral score
        assert result['rating'] == 'Poor'  # 50 < HEALTH_SCORE_FAIR(60), >= HEALTH_SCORE_POOR(45)
    
    def test_savings_score_positive(self, health_analytics):
        """Test savings score with positive savings rate."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        transactions = [
            Transaction(
                transaction_id="txn1",
                user_id="user1",
                institution_id="inst1",
                type="DEPOSIT",
                amount=1000.0,
                transaction_date=base_ts,
                created_at=base_ts,
                description="Income",
                tags=[]
            ),
            Transaction(
                transaction_id="txn2",
                user_id="user1",
                institution_id="inst1",
                type="WITHDRAWAL",
                amount=800.0,
                transaction_date=base_ts + 86400,
                created_at=base_ts + 86400,
                description="Expenses",
                tags=[]
            )
        ]
        
        score = health_analytics._calculate_savings_score(transactions)
        
        # 20% savings rate should give 100 score
        assert score > 0
    
    def test_savings_score_negative(self, health_analytics):
        """Test savings score with negative savings."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        transactions = [
            Transaction(
                transaction_id="txn1",
                user_id="user1",
                institution_id="inst1",
                type="DEPOSIT",
                amount=1000.0,
                transaction_date=base_ts,
                created_at=base_ts,
                description="Income",
                tags=[]
            ),
            Transaction(
                transaction_id="txn2",
                user_id="user1",
                institution_id="inst1",
                type="WITHDRAWAL",
                amount=1200.0,
                transaction_date=base_ts + 86400,
                created_at=base_ts + 86400,
                description="Expenses",
                tags=[]
            )
        ]
        
        score = health_analytics._calculate_savings_score(transactions)
        
        assert score == 0.0  # Negative savings = 0 score
    
    def test_goal_score_calculation(self, health_analytics, sample_goals, sample_institutions):
        """Test goal progress score calculation."""
        score = health_analytics._calculate_goal_score(sample_goals, sample_institutions)
        
        # inst1 balance=6000, inst2 balance=12000
        # goal1: 70% of inst1 = 4200 / 10000 = 42%
        # goal2: 25% of inst2 = 3000 / 5000 = 60%
        # avg = (42 + 60) / 2 = 51%
        assert 40 <= score <= 65
    
    def test_goal_score_no_goals(self, health_analytics):
        """Test goal score with no goals."""
        score = health_analytics._calculate_goal_score([], [])
        
        assert score == 50.0  # Neutral score
    
    def test_goal_score_inactive_goals(self, health_analytics):
        """Test goal score with only inactive goals."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        goals = [
            Goal(
                goal_id="goal1",
                user_id="user1",
                name="Inactive",
                target_amount=1000.0,
                created_at=base_ts,
                is_active=False
            )
        ]
        
        score = health_analytics._calculate_goal_score(goals, [])
        
        assert score == 50.0  # Neutral for no active goals
    
    def test_diversity_score_diverse_spending(self, health_analytics):
        """Test diversity score with diverse spending."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        transactions = [
            Transaction(
                transaction_id=f"txn_{i}",
                user_id="user1",
                institution_id="inst1",
                type="WITHDRAWAL",
                amount=100.0,
                transaction_date=base_ts + (i * 3600),
                created_at=base_ts + (i * 3600),
                description=f"Expense {i}",
                tags=[f"category_{i % 5}"]
            )
            for i in range(20)
        ]
        
        score = health_analytics._calculate_diversity_score(transactions)
        
        # Diverse spending should have high score
        assert score > 50
    
    def test_diversity_score_concentrated_spending(self, health_analytics):
        """Test diversity score with concentrated spending."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        transactions = [
            Transaction(
                transaction_id=f"txn_{i}",
                user_id="user1",
                institution_id="inst1",
                type="WITHDRAWAL",
                amount=100.0,
                transaction_date=base_ts + (i * 3600),
                created_at=base_ts + (i * 3600),
                description=f"Expense {i}",
                tags=["same_category"]
            )
            for i in range(20)
        ]
        
        score = health_analytics._calculate_diversity_score(transactions)
        
        # Concentrated spending should have lower score
        assert score < 50
    
    def test_utilization_score_all_active(
        self,
        health_analytics,
        sample_institutions,
        sample_transactions
    ):
        """Test utilization score when all accounts are active."""
        score = health_analytics._calculate_utilization_score(
            sample_institutions,
            sample_transactions
        )
        
        assert score >= 0
    
    def test_utilization_score_no_institutions(self, health_analytics):
        """Test utilization score with no institutions."""
        score = health_analytics._calculate_utilization_score([], [])
        
        assert score == 50.0  # Neutral score
    
    def test_regularity_score_regular_transactions(self, health_analytics):
        """Test regularity score with regular transactions."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        transactions = [
            Transaction(
                transaction_id=f"txn_{i}",
                user_id="user1",
                institution_id="inst1",
                type="WITHDRAWAL",
                amount=50.0,
                transaction_date=base_ts + (i * 86400),
                created_at=base_ts + (i * 86400),
                description=f"Daily expense {i}",
                tags=[]
            )
            for i in range(30)
        ]
        
        score = health_analytics._calculate_regularity_score(transactions, 30)
        
        # Regular daily transactions should score high
        assert score > 60
    
    def test_regularity_score_irregular_transactions(self, health_analytics):
        """Test regularity score with irregular transactions."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        # Create highly irregular pattern: most transactions clustered on one day,
        # one outlier on another day. This creates high variability.
        transactions = []
        # 20 transactions on day 0 (burst)
        for i in range(20):
            transactions.append(Transaction(
                transaction_id=f"txn_burst_{i}",
                user_id="user1",
                institution_id="inst1",
                type="WITHDRAWAL",
                amount=10.0,
                transaction_date=base_ts + i,  # Same day, different seconds
                created_at=base_ts,
                description="Burst expense",
                tags=[]
            ))
        # 1 transaction on day 14
        transactions.append(Transaction(
            transaction_id="txn_lone",
            user_id="user1",
            institution_id="inst1",
            type="WITHDRAWAL",
            amount=10.0,
            transaction_date=base_ts + (14 * 86400),
            created_at=base_ts + (14 * 86400),
            description="Lone expense",
            tags=[]
        ))
        
        score = health_analytics._calculate_regularity_score(transactions, 30)
        
        # Very irregular (20 on one day, 1 on another) should score lower than regular pattern
        assert score < 80
    
    def test_health_rating_excellent(self, health_analytics):
        """Test excellent health rating."""
        rating = health_analytics._get_health_rating(95.0)
        assert rating == 'Excellent'
    
    def test_health_rating_good(self, health_analytics):
        """Test good health rating."""
        rating = health_analytics._get_health_rating(80.0)
        assert rating == 'Good'
    
    def test_health_rating_fair(self, health_analytics):
        """Test fair health rating."""
        rating = health_analytics._get_health_rating(65.0)
        assert rating == 'Fair'
    
    def test_health_rating_poor(self, health_analytics):
        """Test poor health rating."""
        rating = health_analytics._get_health_rating(50.0)
        assert rating == 'Poor'
    
    def test_health_rating_needs_improvement(self, health_analytics):
        """Test needs improvement rating."""
        rating = health_analytics._get_health_rating(30.0)
        assert rating == 'Needs Improvement'


class TestHealthRecommendations:
    """Test health recommendation generation."""
    
    @pytest.fixture
    def health_analytics(self):
        """Create health analytics instance."""
        return HealthScoreAnalytics()
    
    def test_recommendations_low_savings(self, health_analytics):
        """Test recommendations for low savings rate."""
        health_data = {
            'overall_score': 50.0,
            'components': {
                'savings_rate': {'score': 30.0},
                'goal_progress': {'score': 70.0},
                'spending_diversity': {'score': 70.0},
                'account_utilization': {'score': 70.0},
                'transaction_regularity': {'score': 70.0}
            }
        }
        
        recommendations = health_analytics.get_health_recommendations(health_data)
        
        assert len(recommendations) > 0
        assert any('Savings' in rec or 'savings' in rec for rec in recommendations)
    
    def test_recommendations_low_goal_progress(self, health_analytics):
        """Test recommendations for low goal progress."""
        health_data = {
            'overall_score': 50.0,
            'components': {
                'savings_rate': {'score': 70.0},
                'goal_progress': {'score': 30.0},
                'spending_diversity': {'score': 70.0},
                'account_utilization': {'score': 70.0},
                'transaction_regularity': {'score': 70.0}
            }
        }
        
        recommendations = health_analytics.get_health_recommendations(health_data)
        
        assert any('Goal' in rec or 'goal' in rec for rec in recommendations)
    
    def test_recommendations_excellent_score(self, health_analytics):
        """Test recommendations for excellent health score."""
        health_data = {
            'overall_score': 95.0,
            'components': {
                'savings_rate': {'score': 95.0},
                'goal_progress': {'score': 95.0},
                'spending_diversity': {'score': 95.0},
                'account_utilization': {'score': 95.0},
                'transaction_regularity': {'score': 95.0}
            }
        }
        
        recommendations = health_analytics.get_health_recommendations(health_data)
        
        assert any('Excellent' in rec for rec in recommendations)
    
    def test_recommendations_multiple_low_areas(self, health_analytics):
        """Test recommendations when multiple areas are low."""
        health_data = {
            'overall_score': 40.0,
            'components': {
                'savings_rate': {'score': 30.0},
                'goal_progress': {'score': 40.0},
                'spending_diversity': {'score': 50.0},
                'account_utilization': {'score': 35.0},
                'transaction_regularity': {'score': 45.0}
            }
        }
        
        recommendations = health_analytics.get_health_recommendations(health_data)
        
        # Should have multiple recommendations
        assert len(recommendations) >= 3


class TestPeriodComparison:
    """Test period-to-period comparison."""
    
    @pytest.fixture
    def health_analytics(self):
        """Create health analytics instance."""
        return HealthScoreAnalytics()
    
    def test_compare_periods_improving(self, health_analytics):
        """Test comparison with improving score."""
        current = {
            'overall_score': 80.0,
            'rating': 'Good',
            'components': {
                'savings_rate': {'score': 80.0},
                'goal_progress': {'score': 75.0},
                'spending_diversity': {'score': 85.0},
                'account_utilization': {'score': 80.0},
                'transaction_regularity': {'score': 80.0}
            }
        }
        
        previous = {
            'overall_score': 70.0,
            'rating': 'Fair',
            'components': {
                'savings_rate': {'score': 70.0},
                'goal_progress': {'score': 65.0},
                'spending_diversity': {'score': 75.0},
                'account_utilization': {'score': 70.0},
                'transaction_regularity': {'score': 70.0}
            }
        }
        
        comparison = health_analytics.compare_periods(current, previous)
        
        assert comparison['current_score'] == 80.0
        assert comparison['previous_score'] == 70.0
        assert comparison['score_change'] == 10.0
        assert comparison['overall_trend'] == 'improving'
    
    def test_compare_periods_declining(self, health_analytics):
        """Test comparison with declining score."""
        current = {
            'overall_score': 60.0,
            'rating': 'Fair',
            'components': {
                'savings_rate': {'score': 60.0},
                'goal_progress': {'score': 55.0},
                'spending_diversity': {'score': 65.0},
                'account_utilization': {'score': 60.0},
                'transaction_regularity': {'score': 60.0}
            }
        }
        
        previous = {
            'overall_score': 70.0,
            'rating': 'Good',
            'components': {
                'savings_rate': {'score': 70.0},
                'goal_progress': {'score': 65.0},
                'spending_diversity': {'score': 75.0},
                'account_utilization': {'score': 70.0},
                'transaction_regularity': {'score': 70.0}
            }
        }
        
        comparison = health_analytics.compare_periods(current, previous)
        
        assert comparison['score_change'] == -10.0
        assert comparison['overall_trend'] == 'declining'
    
    def test_compare_periods_stable(self, health_analytics):
        """Test comparison with stable score."""
        data = {
            'overall_score': 75.0,
            'rating': 'Good',
            'components': {
                'savings_rate': {'score': 75.0},
                'goal_progress': {'score': 75.0},
                'spending_diversity': {'score': 75.0},
                'account_utilization': {'score': 75.0},
                'transaction_regularity': {'score': 75.0}
            }
        }
        
        comparison = health_analytics.compare_periods(data, data)
        
        assert comparison['score_change'] == 0.0
        assert comparison['overall_trend'] == 'stable'
    
    def test_compare_periods_component_changes(self, health_analytics):
        """Test component-level changes."""
        current = {
            'overall_score': 75.0,
            'rating': 'Good',
            'components': {
                'savings_rate': {'score': 85.0},
                'goal_progress': {'score': 60.0}
            }
        }
        
        previous = {
            'overall_score': 75.0,
            'rating': 'Good',
            'components': {
                'savings_rate': {'score': 70.0},
                'goal_progress': {'score': 80.0}
            }
        }
        
        comparison = health_analytics.compare_periods(current, previous)
        
        assert 'component_changes' in comparison
        assert comparison['component_changes']['savings_rate']['trend'] == 'improving'
        assert comparison['component_changes']['goal_progress']['trend'] == 'declining'


class TestAnalyzeMethod:
    """Test the main analyze method."""
    
    @pytest.fixture
    def health_analytics(self):
        """Create health analytics instance."""
        return HealthScoreAnalytics()
    
    def test_analyze_with_recommendations(
        self,
        health_analytics
    ):
        """Test analyze method includes recommendations."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        transactions = [
            Transaction(
                transaction_id="txn1",
                user_id="user1",
                institution_id="inst1",
                type="DEPOSIT",
                amount=1000.0,
                transaction_date=base_ts,
                created_at=base_ts,
                description="Income",
                tags=[]
            )
        ]
        
        institutions = [
            Institution(
                institution_id="inst1",
                user_id="user1",
                institution_name="Checking",
                starting_balance=5000.0,
                current_balance=6000.0,
                created_at=base_ts
            )
        ]
        
        goals = []
        
        result = health_analytics.analyze(
            transactions,
            institutions,
            goals,
            include_recommendations=True
        )
        
        assert 'overall_score' in result
        assert 'recommendations' in result
        assert isinstance(result['recommendations'], list)
    
    def test_analyze_without_recommendations(
        self,
        health_analytics
    ):
        """Test analyze method without recommendations."""
        result = health_analytics.analyze(
            [],
            [],
            [],
            include_recommendations=False
        )
        
        assert 'overall_score' in result
        assert 'recommendations' not in result
