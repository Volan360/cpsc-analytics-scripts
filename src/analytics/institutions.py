"""Institution Analytics Module.

Analyzes performance and utilization of financial institutions,
comparing balances, growth rates, and transaction activity.
"""

import logging
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

from ..data.dynamodb_client import DynamoDBClient
from ..data.data_models import Institution, Transaction, Goal
from ..utils import date_utils, calculations, constants


logger = logging.getLogger(__name__)


class InstitutionAnalytics:
    """Financial institution performance and comparison analysis."""
    
    def __init__(self, db_client: DynamoDBClient):
        """
        Initialize institution analytics.
        
        Args:
            db_client: DynamoDB client instance
        """
        self.db_client = db_client
    
    def analyze(
        self,
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        Perform comprehensive institution analysis.
        
        Args:
            user_id: User ID from Cognito
            start_date: Start date for transaction analysis (optional)
            end_date: End date for transaction analysis (optional)
            
        Returns:
            Dictionary containing institution metrics and comparisons
        """
        logger.info(f"Analyzing institutions for user {user_id}")
        
        # Fetch institutions
        institutions = self.db_client.get_institutions(user_id)
        
        if not institutions:
            logger.warning(f"No institutions found for user {user_id}")
            return self._generate_empty_response()
        
        # Fetch goals for allocation analysis
        goals = self.db_client.get_goals(user_id)
        
        # Convert dates if provided
        start_ts = date_utils.iso_to_timestamp(start_date) if start_date else None
        end_ts = date_utils.iso_to_timestamp(end_date) if end_date else None
        
        # Analyze each institution
        institution_details = []
        total_balance = 0
        total_starting_balance = 0
        
        for inst in institutions:
            details = self._analyze_single_institution(
                inst, 
                goals, 
                start_ts, 
                end_ts
            )
            institution_details.append(details)
            total_balance += inst.current_balance
            total_starting_balance += inst.starting_balance
        
        # Calculate rankings
        rankings = self._calculate_rankings(institution_details)
        
        # Identify underutilized institutions
        underutilized = self._identify_underutilized(institution_details)
        
        # Calculate portfolio metrics
        portfolio = self._calculate_portfolio_metrics(institutions, institution_details)
        
        result = {
            'user_id': user_id,
            'analysis_period': {
                'start': start_date,
                'end': end_date
            } if start_date and end_date else None,
            'summary': {
                'total_institutions': len(institutions),
                'total_balance': round(total_balance, 2),
                'total_starting_balance': round(total_starting_balance, 2),
                'total_growth': round(total_balance - total_starting_balance, 2),
                'average_balance': round(total_balance / len(institutions), 2)
            },
            'institutions': institution_details,
            'rankings': rankings,
            'underutilized': underutilized,
            'portfolio': portfolio
        }
        
        logger.info(f"Institution analysis complete: {len(institutions)} institutions analyzed")
        return result
    
    def _analyze_single_institution(
        self,
        institution: Institution,
        goals: List[Goal],
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None
    ) -> Dict:
        """
        Analyze a single institution in detail.
        
        Args:
            institution: Institution object
            goals: List of all goals
            start_ts: Start timestamp for transactions (optional)
            end_ts: End timestamp for transactions (optional)
            
        Returns:
            Dictionary with institution analysis
        """
        # Fetch transactions for this institution
        transactions = self.db_client.get_transactions(
            institution_id=institution.institution_id,
            start_date=start_ts,
            end_date=end_ts
        )
        
        # Calculate transaction metrics
        deposits = [t for t in transactions if t.is_deposit]
        withdrawals = [t for t in transactions if t.is_withdrawal]
        
        total_deposits = sum(t.amount for t in deposits)
        total_withdrawals = sum(t.amount for t in withdrawals)
        net_flow = total_deposits - total_withdrawals
        
        # Calculate transaction frequency
        if transactions:
            first_txn_date = min(t.transaction_date for t in transactions)
            last_txn_date = max(t.transaction_date for t in transactions)
            days_span = date_utils.get_days_between(first_txn_date, last_txn_date)
            avg_transactions_per_month = (len(transactions) / max(days_span, 1)) * 30 if days_span > 0 else 0
        else:
            avg_transactions_per_month = 0
            first_txn_date = None
            last_txn_date = None
        
        # Calculate growth metrics
        balance_change = institution.balance_change
        growth_rate = institution.growth_rate
        
        # Calculate goal allocation
        linked_goals = [g for g in goals if institution.institution_id in g.linked_institutions]
        total_allocated_to_goals = sum(
            g.linked_institutions.get(institution.institution_id, 0)
            for g in linked_goals
        )
        
        # Calculate utilization score (0-100)
        utilization_score = self._calculate_utilization_score(
            institution,
            len(transactions),
            total_allocated_to_goals,
            len(linked_goals)
        )
        
        return {
            'institution_id': institution.institution_id,
            'institution_name': institution.institution_name,
            'balances': {
                'starting': round(institution.starting_balance, 2),
                'current': round(institution.current_balance, 2),
                'change': round(balance_change, 2),
                'growth_rate': round(growth_rate, 2)
            },
            'transactions': {
                'total_count': len(transactions),
                'deposit_count': len(deposits),
                'withdrawal_count': len(withdrawals),
                'total_deposits': round(total_deposits, 2),
                'total_withdrawals': round(total_withdrawals, 2),
                'net_flow': round(net_flow, 2),
                'avg_per_month': round(avg_transactions_per_month, 2),
                'first_transaction_date': date_utils.timestamp_to_iso(first_txn_date) if first_txn_date else None,
                'last_transaction_date': date_utils.timestamp_to_iso(last_txn_date) if last_txn_date else None
            },
            'goals': {
                'linked_count': len(linked_goals),
                'total_allocated_percent': total_allocated_to_goals,
                'linked_goal_names': [g.name for g in linked_goals]
            },
            'metrics': {
                'utilization_score': utilization_score,
                'activity_level': self._categorize_activity_level(avg_transactions_per_month)
            },
            'created_at': date_utils.timestamp_to_iso(institution.created_at)
        }
    
    def _calculate_utilization_score(
        self,
        institution: Institution,
        transaction_count: int,
        allocated_percent: int,
        goal_count: int
    ) -> float:
        """
        Calculate how well an institution is being utilized.
        
        Args:
            institution: Institution object
            transaction_count: Number of transactions
            allocated_percent: Percentage allocated to goals
            goal_count: Number of linked goals
            
        Returns:
            Utilization score (0-100)
        """
        score = 0.0
        
        # Balance factor (max 30 points)
        if institution.current_balance > 0:
            score += 30
        
        # Transaction activity (max 30 points)
        if transaction_count > 0:
            score += min(transaction_count / 10 * 30, 30)
        
        # Goal allocation (max 40 points)
        if allocated_percent > 0:
            score += min(allocated_percent / 100 * 40, 40)
        
        return min(score, 100.0)
    
    def _categorize_activity_level(self, avg_transactions_per_month: float) -> str:
        """Categorize transaction activity level."""
        if avg_transactions_per_month >= 10:
            return 'Very Active'
        elif avg_transactions_per_month >= 5:
            return 'Active'
        elif avg_transactions_per_month >= 1:
            return 'Moderate'
        elif avg_transactions_per_month > 0:
            return 'Low'
        else:
            return 'Inactive'
    
    def _calculate_rankings(self, institution_details: List[Dict]) -> Dict:
        """
        Rank institutions by various metrics.
        
        Args:
            institution_details: List of institution detail dictionaries
            
        Returns:
            Dictionary with ranked lists
        """
        # Sort by balance
        by_balance = sorted(
            institution_details,
            key=lambda x: x['balances']['current'],
            reverse=True
        )
        
        # Sort by growth rate
        by_growth = sorted(
            institution_details,
            key=lambda x: x['balances']['growth_rate'],
            reverse=True
        )
        
        # Sort by transaction volume
        by_activity = sorted(
            institution_details,
            key=lambda x: x['transactions']['total_count'],
            reverse=True
        )
        
        # Sort by utilization
        by_utilization = sorted(
            institution_details,
            key=lambda x: x['metrics']['utilization_score'],
            reverse=True
        )
        
        return {
            'by_balance': [
                {
                    'rank': i + 1,
                    'institution_name': inst['institution_name'],
                    'value': inst['balances']['current']
                }
                for i, inst in enumerate(by_balance)
            ],
            'by_growth_rate': [
                {
                    'rank': i + 1,
                    'institution_name': inst['institution_name'],
                    'value': inst['balances']['growth_rate']
                }
                for i, inst in enumerate(by_growth)
            ],
            'by_activity': [
                {
                    'rank': i + 1,
                    'institution_name': inst['institution_name'],
                    'value': inst['transactions']['total_count']
                }
                for i, inst in enumerate(by_activity)
            ],
            'by_utilization': [
                {
                    'rank': i + 1,
                    'institution_name': inst['institution_name'],
                    'value': inst['metrics']['utilization_score']
                }
                for i, inst in enumerate(by_utilization)
            ]
        }
    
    def _identify_underutilized(self, institution_details: List[Dict]) -> List[Dict]:
        """
        Identify institutions that are underutilized.
        
        Args:
            institution_details: List of institution detail dictionaries
            
        Returns:
            List of underutilized institution summaries
        """
        underutilized = []
        
        for inst in institution_details:
            utilization = inst['metrics']['utilization_score']
            
            if utilization < 50:
                reasons = []
                recommendations = []
                
                # Check for issues
                if inst['transactions']['total_count'] == 0:
                    reasons.append('No transactions')
                    recommendations.append('Start using this account for transactions')
                
                if inst['goals']['total_allocated_percent'] == 0:
                    reasons.append('Not linked to any goals')
                    recommendations.append('Link to one or more financial goals')
                
                if inst['balances']['current'] == 0:
                    reasons.append('Zero balance')
                    recommendations.append('Add funds to this account')
                
                underutilized.append({
                    'institution_id': inst['institution_id'],
                    'institution_name': inst['institution_name'],
                    'utilization_score': utilization,
                    'reasons': reasons,
                    'recommendations': recommendations
                })
        
        # Sort by utilization score (lowest first)
        underutilized.sort(key=lambda x: x['utilization_score'])
        
        return underutilized
    
    def _calculate_portfolio_metrics(
        self,
        institutions: List[Institution],
        institution_details: List[Dict]
    ) -> Dict:
        """
        Calculate portfolio-level metrics.
        
        Args:
            institutions: List of Institution objects
            institution_details: List of institution detail dictionaries
            
        Returns:
            Dictionary with portfolio metrics
        """
        total_balance = sum(inst.current_balance for inst in institutions)
        
        # Calculate balance distribution
        distribution = []
        for inst, details in zip(institutions, institution_details):
            percent = (inst.current_balance / total_balance * 100) if total_balance > 0 else 0
            distribution.append({
                'institution_name': inst.institution_name,
                'balance': round(inst.current_balance, 2),
                'percent': round(percent, 2)
            })
        
        # Calculate concentration (HHI)
        if total_balance > 0:
            proportions = [inst.current_balance / total_balance for inst in institutions]
            hhi = sum(p ** 2 for p in proportions)
            
            # Categorize concentration
            if hhi < 0.15:
                concentration_level = 'Highly diversified'
            elif hhi < 0.25:
                concentration_level = 'Moderately diversified'
            elif hhi < 0.50:
                concentration_level = 'Somewhat concentrated'
            else:
                concentration_level = 'Highly concentrated'
        else:
            hhi = 0
            concentration_level = 'No balance'
        
        # Calculate average growth rate
        growth_rates = [details['balances']['growth_rate'] for details in institution_details]
        avg_growth_rate = calculations.calculate_average(growth_rates)
        
        return {
            'distribution': distribution,
            'concentration': {
                'hhi': round(hhi, 4),
                'level': concentration_level,
                'recommendation': 'Consider diversifying' if hhi > 0.5 else 'Well diversified'
            },
            'performance': {
                'average_growth_rate': round(avg_growth_rate, 2),
                'best_performer': max(institution_details, key=lambda x: x['balances']['growth_rate'])['institution_name'] if institution_details else None,
                'worst_performer': min(institution_details, key=lambda x: x['balances']['growth_rate'])['institution_name'] if institution_details else None
            }
        }
    
    def compare_institutions(
        self,
        user_id: str,
        institution_id1: str,
        institution_id2: str
    ) -> Dict:
        """
        Compare two institutions side by side.
        
        Args:
            user_id: User ID from Cognito
            institution_id1: First institution ID
            institution_id2: Second institution ID
            
        Returns:
            Dictionary containing comparison metrics
        """
        logger.info(f"Comparing institutions {institution_id1} and {institution_id2}")
        
        # Fetch institutions
        inst1 = self.db_client.get_institution(user_id, institution_id1)
        inst2 = self.db_client.get_institution(user_id, institution_id2)
        
        if not inst1 or not inst2:
            raise ValueError("One or both institutions not found")
        
        # Get goals
        goals = self.db_client.get_goals(user_id)
        
        # Analyze both institutions
        inst1_details = self._analyze_single_institution(inst1, goals)
        inst2_details = self._analyze_single_institution(inst2, goals)
        
        return {
            'institution1': inst1_details,
            'institution2': inst2_details,
            'comparison': {
                'balance_difference': round(
                    inst1_details['balances']['current'] - inst2_details['balances']['current'],
                    2
                ),
                'growth_rate_difference': round(
                    inst1_details['balances']['growth_rate'] - inst2_details['balances']['growth_rate'],
                    2
                ),
                'transaction_count_difference': (
                    inst1_details['transactions']['total_count'] - 
                    inst2_details['transactions']['total_count']
                ),
                'more_active': inst1_details['institution_name']
                    if inst1_details['transactions']['total_count'] > inst2_details['transactions']['total_count']
                    else inst2_details['institution_name'],
                'higher_utilization': inst1_details['institution_name']
                    if inst1_details['metrics']['utilization_score'] > inst2_details['metrics']['utilization_score']
                    else inst2_details['institution_name']
            }
        }
    
    def _generate_empty_response(self) -> Dict:
        """Generate empty response when no institutions exist."""
        return {
            'summary': {
                'total_institutions': 0,
                'total_balance': 0
            },
            'institutions': [],
            'rankings': {},
            'underutilized': [],
            'portfolio': {},
            'message': 'No institutions found'
        }
