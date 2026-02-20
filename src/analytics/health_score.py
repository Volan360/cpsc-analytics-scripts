"""
Financial Health Score Analytics Module

Computes a composite financial health score (0-100) based on multiple dimensions:
- Savings rate (25%)
- Goal progress (25%)
- Spending diversity (20%)
- Account utilization (15%)
- Transaction regularity (15%)

Designed to work with raw data via shared utility calculations.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import statistics

from src.utils.constants import (
    HEALTH_SCORE_EXCELLENT,
    HEALTH_SCORE_GOOD,
    HEALTH_SCORE_FAIR,
    HEALTH_SCORE_POOR,
    HEALTH_WEIGHT_SAVINGS_RATE,
    HEALTH_WEIGHT_GOAL_PROGRESS,
    HEALTH_WEIGHT_SPENDING_DIVERSITY,
    HEALTH_WEIGHT_ACCOUNT_UTILIZATION,
    HEALTH_WEIGHT_TRANSACTION_REGULARITY,
)
from src.utils import calculations
from src.data.data_models import Transaction, Institution, Goal


class HealthScoreAnalytics:
    """
    Analyzes overall financial health by combining multiple metrics.
    Operates on raw data using shared utility calculations.
    """

    def calculate_health_score(
        self,
        transactions: List[Transaction],
        institutions: List[Institution],
        goals: List[Goal],
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate composite financial health score.

        Args:
            transactions: List of transactions
            institutions: List of institutions
            goals: List of goals
            period_days: Analysis period in days

        Returns:
            Dictionary containing health score and breakdown
        """
        savings_score = self._calculate_savings_score(transactions)
        goal_score = self._calculate_goal_score(goals, institutions)
        diversity_score = self._calculate_diversity_score(transactions)
        utilization_score = self._calculate_utilization_score(institutions, transactions)
        regularity_score = self._calculate_regularity_score(transactions, period_days)

        composite_score = (
            savings_score * HEALTH_WEIGHT_SAVINGS_RATE +
            goal_score * HEALTH_WEIGHT_GOAL_PROGRESS +
            diversity_score * HEALTH_WEIGHT_SPENDING_DIVERSITY +
            utilization_score * HEALTH_WEIGHT_ACCOUNT_UTILIZATION +
            regularity_score * HEALTH_WEIGHT_TRANSACTION_REGULARITY
        )

        rating = self._get_health_rating(composite_score)

        return {
            'overall_score': round(composite_score, 2),
            'rating': rating,
            'components': {
                'savings_rate': {
                    'score': round(savings_score, 2),
                    'weight': HEALTH_WEIGHT_SAVINGS_RATE,
                    'contribution': round(savings_score * HEALTH_WEIGHT_SAVINGS_RATE, 2)
                },
                'goal_progress': {
                    'score': round(goal_score, 2),
                    'weight': HEALTH_WEIGHT_GOAL_PROGRESS,
                    'contribution': round(goal_score * HEALTH_WEIGHT_GOAL_PROGRESS, 2)
                },
                'spending_diversity': {
                    'score': round(diversity_score, 2),
                    'weight': HEALTH_WEIGHT_SPENDING_DIVERSITY,
                    'contribution': round(diversity_score * HEALTH_WEIGHT_SPENDING_DIVERSITY, 2)
                },
                'account_utilization': {
                    'score': round(utilization_score, 2),
                    'weight': HEALTH_WEIGHT_ACCOUNT_UTILIZATION,
                    'contribution': round(utilization_score * HEALTH_WEIGHT_ACCOUNT_UTILIZATION, 2)
                },
                'transaction_regularity': {
                    'score': round(regularity_score, 2),
                    'weight': HEALTH_WEIGHT_TRANSACTION_REGULARITY,
                    'contribution': round(regularity_score * HEALTH_WEIGHT_TRANSACTION_REGULARITY, 2)
                }
            },
            'period_days': period_days,
            'computed_at': datetime.now().isoformat()
        }

    def _calculate_savings_score(self, transactions: List[Transaction]) -> float:
        """
        Calculate savings rate score (0-100).
        Score based on net savings rate percentage.
        """
        if not transactions:
            return 50.0  # Neutral score for no data

        deposits = [t.amount for t in transactions if t.type == 'DEPOSIT']
        withdrawals = [t.amount for t in transactions if t.type == 'WITHDRAWAL']

        savings_rate = calculations.calculate_savings_rate(deposits, withdrawals)

        # 0% savings = 0, 20%+ savings = 100
        if savings_rate <= 0:
            return 0.0
        elif savings_rate >= 20.0:
            return 100.0
        else:
            return (savings_rate / 20.0) * 100.0

    def _calculate_goal_score(
        self,
        goals: List[Goal],
        institutions: List[Institution]
    ) -> float:
        """
        Calculate goal progress score (0-100).
        Based on average progress across active goals using institution balances.
        """
        active_goals = [g for g in goals if g.is_active]
        if not active_goals:
            return 50.0  # Neutral score for no active goals

        total_progress = 0.0
        for goal in active_goals:
            if goal.target_amount > 0:
                current = goal.calculate_current_amount(institutions)
                progress_pct = min((current / goal.target_amount) * 100.0, 100.0)
                total_progress += progress_pct

        avg_progress = total_progress / len(active_goals)
        return min(avg_progress, 100.0)

    def _calculate_diversity_score(self, transactions: List[Transaction]) -> float:
        """
        Calculate spending diversity score (0-100).
        Higher score = more diverse spending (lower Gini coefficient).
        """
        withdrawals = [t for t in transactions if t.type == 'WITHDRAWAL']
        if not withdrawals:
            return 50.0

        # Build category totals from primary tag
        category_totals: Dict[str, float] = {}
        for txn in withdrawals:
            primary_tag = txn.tags[0] if txn.tags else 'uncategorized'
            category_totals[primary_tag] = category_totals.get(primary_tag, 0.0) + txn.amount

        if not category_totals:
            return 50.0

        amounts = list(category_totals.values())
        total = sum(amounts)
        if total == 0:
            return 50.0

        # Calculate Gini coefficient
        proportions = sorted([a / total for a in amounts])
        n = len(proportions)
        if n == 1:
            return 0.0  # Single category = max concentration

        cumulative = 0.0
        area_under_lorenz = 0.0
        for p in proportions:
            cumulative += p
            area_under_lorenz += cumulative

        gini = 1 - (2 * area_under_lorenz / n)

        # Convert Gini (0=equality, 1=inequality) to score
        diversity_score = (1.0 - gini) * 100.0
        return max(0.0, min(100.0, diversity_score))

    def _calculate_utilization_score(
        self,
        institutions: List[Institution],
        transactions: List[Transaction]
    ) -> float:
        """
        Calculate account utilization score (0-100).
        Based on percentage of institutions that have transactions.
        """
        if not institutions:
            return 50.0

        institution_ids_with_txns = {t.institution_id for t in transactions}
        active_count = sum(
            1 for inst in institutions
            if inst.institution_id in institution_ids_with_txns
        )
        utilization_pct = (active_count / len(institutions)) * 100.0

        # 80%+ utilization = 100 score
        if utilization_pct >= 80.0:
            return 100.0
        else:
            return (utilization_pct / 80.0) * 100.0

    def _calculate_regularity_score(
        self,
        transactions: List[Transaction],
        period_days: int
    ) -> float:
        """
        Calculate transaction regularity score (0-100).
        Based on consistency of transaction patterns across days.
        """
        if not transactions or period_days <= 0:
            return 50.0

        sorted_txns = sorted(transactions, key=lambda t: t.transaction_date)
        if len(sorted_txns) < 2:
            return 50.0

        # Count transactions per day bucket (UNIX timestamp / seconds per day)
        SECONDS_PER_DAY = 86400
        daily_counts: Dict[int, int] = {}
        for txn in sorted_txns:
            day_key = txn.transaction_date // SECONDS_PER_DAY
            daily_counts[day_key] = daily_counts.get(day_key, 0) + 1

        counts = list(daily_counts.values())
        if len(counts) < 2:
            return 50.0

        mean = statistics.mean(counts)
        if mean == 0:
            return 50.0

        stdev = statistics.stdev(counts)
        cv = stdev / mean  # Coefficient of variation

        # CV 0 (perfectly regular) = 100; CV 2+ (highly irregular) = 0
        if cv >= 2.0:
            return 0.0
        else:
            return max(0.0, (1 - (cv / 2.0)) * 100.0)

    def _get_health_rating(self, score: float) -> str:
        """Get health rating label based on score."""
        if score >= HEALTH_SCORE_EXCELLENT:
            return 'Excellent'
        elif score >= HEALTH_SCORE_GOOD:
            return 'Good'
        elif score >= HEALTH_SCORE_FAIR:
            return 'Fair'
        elif score >= HEALTH_SCORE_POOR:
            return 'Poor'
        else:
            return 'Needs Improvement'

    def get_health_recommendations(
        self,
        health_data: Dict[str, Any]
    ) -> List[str]:
        """
        Generate personalized recommendations based on health score.

        Args:
            health_data: Output from calculate_health_score()

        Returns:
            List of recommendation strings
        """
        recommendations = []
        components = health_data.get('components', {})

        savings = components.get('savings_rate', {}).get('score', 0)
        if savings < 60:
            recommendations.append(
                "💰 Low Savings Rate: Try to increase your savings by reducing discretionary spending. "
                "Aim for at least 20% of deposits to be saved."
            )

        goal_progress = components.get('goal_progress', {}).get('score', 0)
        if goal_progress < 60:
            recommendations.append(
                "🎯 Slow Goal Progress: Review your goals and consider adjusting targets or increasing contributions. "
                "Focus on your highest priority goals first."
            )

        diversity = components.get('spending_diversity', {}).get('score', 0)
        if diversity < 60:
            recommendations.append(
                "🏷️ Low Spending Diversity: Your spending is concentrated in few categories. "
                "Review if you're neglecting important areas or over-spending in specific categories."
            )

        utilization = components.get('account_utilization', {}).get('score', 0)
        if utilization < 60:
            recommendations.append(
                "🏦 Low Account Utilization: You have inactive accounts. "
                "Consider consolidating accounts or ensure all accounts serve a purpose."
            )

        regularity = components.get('transaction_regularity', {}).get('score', 0)
        if regularity < 60:
            recommendations.append(
                "📅 Irregular Transactions: Your transaction patterns are inconsistent. "
                "Consider setting up automatic transfers and bills for more predictable cash flow."
            )

        overall_score = health_data.get('overall_score', 0)
        if overall_score >= HEALTH_SCORE_EXCELLENT:
            recommendations.insert(0, "⭐ Excellent Financial Health! Keep up the great work.")
        elif overall_score >= HEALTH_SCORE_GOOD:
            recommendations.insert(0, "✅ Good Financial Health. Focus on the lower-scoring areas for improvement.")
        elif overall_score < HEALTH_SCORE_POOR:
            recommendations.insert(0, "⚠️ Your financial health needs attention. Start with one improvement area at a time.")

        return recommendations

    def compare_periods(
        self,
        current_data: Dict[str, Any],
        previous_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare health scores between two periods.

        Args:
            current_data: Current period health data
            previous_data: Previous period health data

        Returns:
            Comparison with deltas and trends
        """
        current_score = current_data.get('overall_score', 0)
        previous_score = previous_data.get('overall_score', 0)

        score_change = current_score - previous_score
        score_change_pct = (
            (score_change / previous_score * 100.0) if previous_score > 0 else 0.0
        )

        component_changes = {}
        current_components = current_data.get('components', {})
        previous_components = previous_data.get('components', {})

        for component_name in current_components.keys():
            current_comp_score = current_components.get(component_name, {}).get('score', 0)
            previous_comp_score = previous_components.get(component_name, {}).get('score', 0)

            change = current_comp_score - previous_comp_score
            change_pct = (
                (change / previous_comp_score * 100.0) if previous_comp_score > 0 else 0.0
            )

            component_changes[component_name] = {
                'current_score': current_comp_score,
                'previous_score': previous_comp_score,
                'change': round(change, 2),
                'change_pct': round(change_pct, 2),
                'trend': 'improving' if change > 0 else 'declining' if change < 0 else 'stable'
            }

        return {
            'current_score': round(current_score, 2),
            'previous_score': round(previous_score, 2),
            'score_change': round(score_change, 2),
            'score_change_pct': round(score_change_pct, 2),
            'overall_trend': (
                'improving' if score_change > 0
                else 'declining' if score_change < 0
                else 'stable'
            ),
            'current_rating': current_data.get('rating'),
            'previous_rating': previous_data.get('rating'),
            'component_changes': component_changes
        }

    def analyze(
        self,
        transactions: List[Transaction],
        institutions: List[Institution],
        goals: List[Goal],
        period_days: int = 30,
        include_recommendations: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive health score analysis.

        Args:
            transactions: List of transactions
            institutions: List of institutions
            goals: List of goals
            period_days: Analysis period in days
            include_recommendations: Whether to include recommendations

        Returns:
            Complete health analysis with score, breakdown, and recommendations
        """
        health_data = self.calculate_health_score(
            transactions,
            institutions,
            goals,
            period_days
        )

        if include_recommendations:
            health_data['recommendations'] = self.get_health_recommendations(health_data)

        return health_data
