"""Cash Flow Analytics Module.

Analyzes income vs expenses over time, calculating key metrics like
net cash flow, burn rate, savings rate, and trend analysis.
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from collections import defaultdict

from ..data.dynamodb_client import DynamoDBClient
from ..data.data_models import Transaction, Institution
from ..utils import date_utils, calculations, constants


logger = logging.getLogger(__name__)


class CashFlowAnalytics:
    """Cash flow analysis and metrics calculation."""
    
    def __init__(self, db_client: DynamoDBClient):
        """
        Initialize cash flow analytics.
        
        Args:
            db_client: DynamoDB client instance
        """
        self.db_client = db_client
    
    def analyze(
        self,
        user_id: str,
        start_date: str,
        end_date: str,
        group_by: str = 'month'
    ) -> Dict:
        """
        Perform comprehensive cash flow analysis.
        
        Args:
            user_id: User ID from Cognito
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            group_by: Grouping period ('day', 'week', 'month')
            
        Returns:
            Dictionary containing cash flow metrics and trends
        """
        logger.info(f"Analyzing cash flow for user {user_id} from {start_date} to {end_date}")
        
        # Convert dates to timestamps
        start_ts, end_ts = date_utils.get_date_range(start_date, end_date)
        
        # Validate date range
        if start_ts >= end_ts:
            raise ValueError(constants.ERROR_INVALID_DATE_RANGE)
        
        # Fetch transactions
        transactions = self.db_client.get_all_user_transactions(
            user_id=user_id,
            start_date=start_ts,
            end_date=end_ts
        )
        
        if len(transactions) < constants.MIN_TRANSACTIONS_FOR_ANALYSIS:
            logger.warning(f"Insufficient transactions for analysis: {len(transactions)}")
            return self._generate_empty_response(start_date, end_date)
        
        # Calculate metrics
        deposits = [t.amount for t in transactions if t.is_deposit]
        withdrawals = [t.amount for t in transactions if t.is_withdrawal]
        
        # Overall metrics
        net_flow = calculations.calculate_net_flow(deposits, withdrawals)
        total_deposits = sum(deposits)
        total_withdrawals = sum(withdrawals)
        savings_rate = calculations.calculate_savings_rate(deposits, withdrawals)
        
        # Time-based metrics
        days = date_utils.get_days_between(start_ts, end_ts)
        burn_rate = calculations.calculate_burn_rate(withdrawals, days) if days > 0 else 0
        
        # Group transactions by period
        grouped_data = self._group_transactions_by_period(transactions, group_by)
        
        # Calculate trends
        trend_data = self._calculate_trends(grouped_data)
        
        # Identify anomalies
        anomalies = self._detect_anomalies(transactions)
        
        # Get current balances
        institutions = self.db_client.get_institutions(user_id)
        total_balance = sum(inst.current_balance for inst in institutions)
        runway = calculations.calculate_runway(total_balance, burn_rate)
        
        result = {
            'user_id': user_id,
            'date_range': {
                'start': start_date,
                'end': end_date,
                'days': days
            },
            'summary': {
                'total_deposits': round(total_deposits, 2),
                'total_withdrawals': round(total_withdrawals, 2),
                'net_cash_flow': round(net_flow, 2),
                'transaction_count': len(transactions),
                'deposit_count': len(deposits),
                'withdrawal_count': len(withdrawals)
            },
            'metrics': {
                'savings_rate': round(savings_rate, 2),
                'daily_burn_rate': round(burn_rate, 2),
                'average_deposit': round(calculations.calculate_average(deposits), 2),
                'average_withdrawal': round(calculations.calculate_average(withdrawals), 2),
                'median_deposit': round(calculations.calculate_median(deposits), 2),
                'median_withdrawal': round(calculations.calculate_median(withdrawals), 2),
                'deposit_volatility': round(calculations.calculate_std_dev(deposits), 2),
                'withdrawal_volatility': round(calculations.calculate_std_dev(withdrawals), 2)
            },
            'balance': {
                'current_total': round(total_balance, 2),
                'runway_days': runway if runway >= 0 else None
            },
            'trends': trend_data,
            'anomalies': anomalies
        }
        
        logger.info(f"Cash flow analysis complete: net flow = ${net_flow:.2f}")
        return result
    
    def _group_transactions_by_period(
        self,
        transactions: List[Transaction],
        period: str
    ) -> Dict[str, Dict]:
        """
        Group transactions by time period.
        
        Args:
            transactions: List of transactions
            period: Grouping period ('day', 'week', 'month')
            
        Returns:
            Dictionary mapping period keys to transaction data
        """
        grouped = defaultdict(lambda: {'deposits': [], 'withdrawals': []})
        
        for txn in transactions:
            # Determine period key
            if period == 'day':
                key = date_utils.format_date(txn.transaction_date, '%Y-%m-%d')
            elif period == 'week':
                key = date_utils.format_date(txn.transaction_date, '%Y-W%U')
            else:  # month
                key = date_utils.format_date(txn.transaction_date, '%Y-%m')
            
            # Add to appropriate list
            if txn.is_deposit:
                grouped[key]['deposits'].append(txn.amount)
            else:
                grouped[key]['withdrawals'].append(txn.amount)
        
        # Calculate totals for each period
        result = {}
        for period_key, data in sorted(grouped.items()):
            deposits = data['deposits']
            withdrawals = data['withdrawals']
            
            result[period_key] = {
                'total_deposits': sum(deposits),
                'total_withdrawals': sum(withdrawals),
                'net_flow': calculations.calculate_net_flow(deposits, withdrawals),
                'transaction_count': len(deposits) + len(withdrawals),
                'deposit_count': len(deposits),
                'withdrawal_count': len(withdrawals)
            }
        
        return result
    
    def _calculate_trends(self, grouped_data: Dict[str, Dict]) -> Dict:
        """
        Calculate trend metrics from grouped data.
        
        Args:
            grouped_data: Dictionary of period-grouped transaction data
            
        Returns:
            Dictionary containing trend analysis
        """
        if not grouped_data:
            return {}
        
        periods = sorted(grouped_data.keys())
        net_flows = [grouped_data[p]['net_flow'] for p in periods]
        deposits = [grouped_data[p]['total_deposits'] for p in periods]
        withdrawals = [grouped_data[p]['total_withdrawals'] for p in periods]
        
        # Calculate moving averages (3-period)
        moving_avg_net = calculations.calculate_moving_average(net_flows, 3)
        
        # Determine trend direction
        if len(net_flows) >= 2:
            recent_trend = 'improving' if net_flows[-1] > net_flows[-2] else 'declining'
        else:
            recent_trend = 'stable'
        
        return {
            'periods': periods,
            'net_flows': [round(nf, 2) for nf in net_flows],
            'deposits': [round(d, 2) for d in deposits],
            'withdrawals': [round(w, 2) for w in withdrawals],
            'moving_average': [round(ma, 2) for ma in moving_avg_net],
            'trend_direction': recent_trend,
            'best_period': max(grouped_data.items(), key=lambda x: x[1]['net_flow'])[0],
            'worst_period': min(grouped_data.items(), key=lambda x: x[1]['net_flow'])[0]
        }
    
    def _detect_anomalies(self, transactions: List[Transaction]) -> List[Dict]:
        """
        Detect unusual transactions (outliers).
        
        Args:
            transactions: List of transactions
            
        Returns:
            List of anomaly dictionaries
        """
        if len(transactions) < 10:
            return []
        
        # Separate deposits and withdrawals
        deposits = [(i, t) for i, t in enumerate(transactions) if t.is_deposit]
        withdrawals = [(i, t) for i, t in enumerate(transactions) if t.is_withdrawal]
        
        anomalies = []
        
        # Detect deposit anomalies
        if len(deposits) >= 3:
            deposit_amounts = [t.amount for _, t in deposits]
            outliers = calculations.detect_outliers(deposit_amounts, threshold=2.0)
            for idx, amount in outliers:
                txn = deposits[idx][1]
                anomalies.append({
                    'type': 'large_deposit',
                    'transaction_id': txn.transaction_id,
                    'amount': round(amount, 2),
                    'date': date_utils.timestamp_to_iso(txn.transaction_date),
                    'description': txn.description or 'No description'
                })
        
        # Detect withdrawal anomalies
        if len(withdrawals) >= 3:
            withdrawal_amounts = [t.amount for _, t in withdrawals]
            outliers = calculations.detect_outliers(withdrawal_amounts, threshold=2.0)
            for idx, amount in outliers:
                txn = withdrawals[idx][1]
                anomalies.append({
                    'type': 'large_withdrawal',
                    'transaction_id': txn.transaction_id,
                    'amount': round(amount, 2),
                    'date': date_utils.timestamp_to_iso(txn.transaction_date),
                    'description': txn.description or 'No description'
                })
        
        return anomalies
    
    def _generate_empty_response(self, start_date: str, end_date: str) -> Dict:
        """
        Generate empty response when insufficient data.
        
        Args:
            start_date: Start date string
            end_date: End date string
            
        Returns:
            Dictionary with empty/zero values
        """
        return {
            'date_range': {
                'start': start_date,
                'end': end_date
            },
            'summary': {
                'total_deposits': 0,
                'total_withdrawals': 0,
                'net_cash_flow': 0,
                'transaction_count': 0
            },
            'metrics': {},
            'trends': {},
            'anomalies': [],
            'message': constants.ERROR_INSUFFICIENT_DATA
        }
    
    def calculate_projection(
        self,
        user_id: str,
        months_ahead: int = 3
    ) -> Dict:
        """
        Project future cash flow based on historical trends.
        
        Args:
            user_id: User ID from Cognito
            months_ahead: Number of months to project
            
        Returns:
            Dictionary containing projection data
        """
        logger.info(f"Calculating {months_ahead}-month cash flow projection for user {user_id}")
        
        # Get last 6 months of data for projection
        end_ts = date_utils.get_current_timestamp()
        start_ts = date_utils.add_months(end_ts, -6)
        
        transactions = self.db_client.get_all_user_transactions(
            user_id=user_id,
            start_date=start_ts,
            end_date=end_ts
        )
        
        if not transactions:
            return {'error': constants.ERROR_INSUFFICIENT_DATA}
        
        # Calculate historical averages
        deposits = [t.amount for t in transactions if t.is_deposit]
        withdrawals = [t.amount for t in transactions if t.is_withdrawal]
        
        # Calculate total deposits/withdrawals over 6 months, then average per month
        total_deposits = sum(deposits)
        total_withdrawals = sum(withdrawals)
        avg_monthly_deposits = total_deposits / 6
        avg_monthly_withdrawals = total_withdrawals / 6
        
        # Get current balance
        institutions = self.db_client.get_institutions(user_id)
        current_balance = sum(inst.current_balance for inst in institutions)
        
        # Project future months
        projections = []
        balance = current_balance
        
        for month in range(1, months_ahead + 1):
            month_deposits = avg_monthly_deposits
            month_withdrawals = avg_monthly_withdrawals
            net_flow = month_deposits - month_withdrawals
            balance += net_flow
            
            future_date = date_utils.add_months(end_ts, month)
            
            projections.append({
                'month': date_utils.format_date(future_date, '%Y-%m'),
                'projected_deposits': round(month_deposits, 2),
                'projected_withdrawals': round(month_withdrawals, 2),
                'projected_net_flow': round(net_flow, 2),
                'projected_balance': round(balance, 2)
            })
        
        return {
            'current_balance': round(current_balance, 2),
            'historical_monthly_average': {
                'deposits': round(avg_monthly_deposits, 2),
                'withdrawals': round(avg_monthly_withdrawals, 2),
                'net_flow': round(avg_monthly_deposits - avg_monthly_withdrawals, 2)
            },
            'projections': projections
        }
