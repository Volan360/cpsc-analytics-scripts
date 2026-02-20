"""Analytics modules for financial data analysis."""

from src.analytics.cash_flow import CashFlowAnalytics
from src.analytics.categories import CategoryAnalytics
from src.analytics.goals import GoalAnalytics
from src.analytics.institutions import InstitutionAnalytics
from src.analytics.network import NetworkAnalytics
from src.analytics.health_score import HealthScoreAnalytics

__all__ = [
    'CashFlowAnalytics',
    'CategoryAnalytics',
    'GoalAnalytics',
    'InstitutionAnalytics',
    'NetworkAnalytics',
    'HealthScoreAnalytics',
]
