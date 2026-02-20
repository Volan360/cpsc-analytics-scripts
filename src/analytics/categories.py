"""Category Analytics Module.

Analyzes spending patterns by transaction tags/categories, identifying
top spending areas, trends, and budget allocation insights.
"""

import logging
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

from ..data.dynamodb_client import DynamoDBClient
from ..data.data_models import Transaction
from ..utils import date_utils, calculations, constants


logger = logging.getLogger(__name__)


class CategoryAnalytics:
    """Spending category analysis and insights."""
    
    def __init__(self, db_client: DynamoDBClient):
        """
        Initialize category analytics.
        
        Args:
            db_client: DynamoDB client instance
        """
        self.db_client = db_client
    
    def analyze(
        self,
        user_id: str,
        start_date: str,
        end_date: str,
        transaction_type: Optional[str] = None
    ) -> Dict:
        """
        Perform comprehensive category analysis.
        
        Args:
            user_id: User ID from Cognito
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            transaction_type: Filter by type ('DEPOSIT', 'WITHDRAWAL', or None for both)
            
        Returns:
            Dictionary containing category metrics and breakdowns
        """
        logger.info(f"Analyzing categories for user {user_id} from {start_date} to {end_date}")
        
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
        
        # Filter by transaction type if specified
        if transaction_type:
            transactions = [t for t in transactions if t.type == transaction_type]
        
        if len(transactions) < constants.MIN_TRANSACTIONS_FOR_ANALYSIS:
            logger.warning(f"Insufficient transactions for analysis: {len(transactions)}")
            return self._generate_empty_response(start_date, end_date)
        
        # Group transactions by category
        category_groups = self._group_by_categories(transactions)
        
        # Calculate category metrics
        category_totals = self._calculate_category_totals(category_groups)
        category_counts = self._calculate_category_counts(category_groups)
        category_averages = self._calculate_category_averages(category_groups)
        
        # Find top categories
        top_categories = self._get_top_categories(category_totals, limit=constants.MAX_CATEGORIES_DISPLAY)
        
        # Calculate category trends over time
        trends = self._calculate_category_trends(transactions)
        
        # Calculate diversity metrics
        diversity = self._calculate_spending_diversity(category_totals)
        
        # Identify co-occurring categories
        co_occurrences = self._find_category_co_occurrences(transactions)
        
        # Get total spending (from transactions to avoid double-counting multi-tagged transactions)
        total_amount = sum(t.amount for t in transactions)
        
        result = {
            'user_id': user_id,
            'date_range': {
                'start': start_date,
                'end': end_date
            },
            'summary': {
                'total_amount': round(total_amount, 2),
                'transaction_count': len(transactions),
                'unique_categories': len(category_totals),
                'transaction_type': transaction_type or 'ALL'
            },
            'categories': {
                'totals': {k: round(v, 2) for k, v in category_totals.items()},
                'counts': category_counts,
                'averages': {k: round(v, 2) for k, v in category_averages.items()},
                'percentages': {
                    k: round((v / total_amount * 100), 2) if total_amount > 0 else 0
                    for k, v in category_totals.items()
                }
            },
            'top_categories': top_categories,
            'trends': trends,
            'diversity': diversity,
            'co_occurrences': co_occurrences[:10]  # Top 10 pairs
        }
        
        logger.info(f"Category analysis complete: {len(category_totals)} unique categories found")
        return result
    
    def _group_by_categories(self, transactions: List[Transaction]) -> Dict[str, List[Transaction]]:
        """
        Group transactions by their tags/categories.
        
        Args:
            transactions: List of transactions
            
        Returns:
            Dictionary mapping category names to transaction lists
        """
        grouped = defaultdict(list)
        
        for txn in transactions:
            if not txn.tags or len(txn.tags) == 0:
                grouped['uncategorized'].append(txn)
            else:
                for tag in txn.tags:
                    grouped[tag].append(txn)
        
        return dict(grouped)
    
    def _calculate_category_totals(self, category_groups: Dict[str, List[Transaction]]) -> Dict[str, float]:
        """Calculate total amount per category."""
        totals = {}
        for category, transactions in category_groups.items():
            totals[category] = sum(t.amount for t in transactions)
        return totals
    
    def _calculate_category_counts(self, category_groups: Dict[str, List[Transaction]]) -> Dict[str, int]:
        """Calculate transaction count per category."""
        return {category: len(transactions) for category, transactions in category_groups.items()}
    
    def _calculate_category_averages(self, category_groups: Dict[str, List[Transaction]]) -> Dict[str, float]:
        """Calculate average transaction amount per category."""
        averages = {}
        for category, transactions in category_groups.items():
            if transactions:
                amounts = [t.amount for t in transactions]
                averages[category] = calculations.calculate_average(amounts)
        return averages
    
    def _get_top_categories(self, category_totals: Dict[str, float], limit: int = 10) -> List[Dict]:
        """
        Get top categories by total amount.
        
        Args:
            category_totals: Dictionary of category totals
            limit: Maximum number of categories to return
            
        Returns:
            List of category dictionaries sorted by amount
        """
        sorted_categories = sorted(
            category_totals.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        total_amount = sum(category_totals.values())

        return [
            {
                'name': category,
                'amount': round(amount, 2),
                'rank': i + 1,
                'percentage': round((amount / total_amount * 100), 2) if total_amount > 0 else 0.0
            }
            for i, (category, amount) in enumerate(sorted_categories)
        ]
    
    def _calculate_category_trends(self, transactions: List[Transaction]) -> Dict:
        """
        Calculate spending trends per category over time.
        
        Args:
            transactions: List of transactions
            
        Returns:
            Dictionary containing trend data
        """
        # Group by month and category
        monthly_data = defaultdict(lambda: defaultdict(float))
        
        for txn in transactions:
            month_key = date_utils.format_date(txn.transaction_date, '%Y-%m')
            
            if not txn.tags:
                monthly_data[month_key]['uncategorized'] += txn.amount
            else:
                for tag in txn.tags:
                    monthly_data[month_key][tag] += txn.amount
        
        # Convert to sorted list format
        trends = {}
        for category in self._get_all_categories(transactions):
            category_trend = []
            for month in sorted(monthly_data.keys()):
                category_trend.append({
                    'month': month,
                    'amount': round(monthly_data[month].get(category, 0), 2)
                })
            trends[category] = category_trend
        
        return trends
    
    def _get_all_categories(self, transactions: List[Transaction]) -> set:
        """Extract all unique categories from transactions."""
        categories = set()
        for txn in transactions:
            if not txn.tags:
                categories.add('uncategorized')
            else:
                categories.update(txn.tags)
        return categories
    
    def _calculate_spending_diversity(self, category_totals: Dict[str, float]) -> Dict:
        """
        Calculate spending diversity metrics.
        
        Args:
            category_totals: Dictionary of category totals
            
        Returns:
            Dictionary with diversity metrics
        """
        if not category_totals:
            return {
                'score': 0,
                'description': 'No data'
            }
        
        total_amount = sum(category_totals.values())
        if total_amount == 0:
            return {
                'score': 0,
                'description': 'No spending'
            }
        
        # Calculate Herfindahl-Hirschman Index (HHI) for diversity
        # Lower HHI = more diverse spending
        proportions = [amount / total_amount for amount in category_totals.values()]
        hhi = sum(p ** 2 for p in proportions)
        
        # Convert to 0-100 scale (inverted, so higher = more diverse)
        diversity_score = (1 - hhi) * 100
        
        # Categorize diversity
        if diversity_score >= 75:
            description = 'Highly diverse - spending spread across many categories'
        elif diversity_score >= 50:
            description = 'Moderately diverse - balanced spending'
        elif diversity_score >= 25:
            description = 'Concentrated - spending focused on few categories'
        else:
            description = 'Highly concentrated - dominated by 1-2 categories'
        
        return {
            'score': round(diversity_score, 2),
            'hhi': round(hhi, 4),
            'description': description,
            'num_categories': len(category_totals)
        }
    
    def _find_category_co_occurrences(self, transactions: List[Transaction]) -> List[Dict]:
        """
        Find categories that frequently occur together in transactions.
        
        Args:
            transactions: List of transactions
            
        Returns:
            List of category pair dictionaries with co-occurrence counts
        """
        co_occurrence_counts = defaultdict(int)
        
        for txn in transactions:
            if txn.tags and len(txn.tags) > 1:
                # Sort tags to ensure consistent pairing
                sorted_tags = sorted(txn.tags)
                for i in range(len(sorted_tags)):
                    for j in range(i + 1, len(sorted_tags)):
                        pair = (sorted_tags[i], sorted_tags[j])
                        co_occurrence_counts[pair] += 1
        
        # Sort by count
        sorted_pairs = sorted(
            co_occurrence_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {
                'category_1': pair[0],
                'category_2': pair[1],
                'count': count
            }
            for pair, count in sorted_pairs
        ]
    
    def compare_periods(
        self,
        user_id: str,
        period1_start: str,
        period1_end: str,
        period2_start: str,
        period2_end: str
    ) -> Dict:
        """
        Compare category spending between two time periods.
        
        Args:
            user_id: User ID from Cognito
            period1_start: Start date of first period
            period1_end: End date of first period
            period2_start: Start date of second period
            period2_end: End date of second period
            
        Returns:
            Dictionary containing comparison metrics
        """
        logger.info(f"Comparing spending periods for user {user_id}")
        
        # Analyze both periods
        period1_data = self.analyze(user_id, period1_start, period1_end)
        period2_data = self.analyze(user_id, period2_start, period2_end)
        
        # Extract category totals
        period1_totals = period1_data['categories']['totals']
        period2_totals = period2_data['categories']['totals']
        
        # Calculate changes
        all_categories = set(period1_totals.keys()) | set(period2_totals.keys())
        
        changes = []
        for category in all_categories:
            amount1 = period1_totals.get(category, 0)
            amount2 = period2_totals.get(category, 0)
            change = amount2 - amount1
            
            if amount1 > 0:
                percent_change = (change / amount1) * 100
            elif amount2 > 0:
                percent_change = 100  # New category
            else:
                percent_change = 0
            
            changes.append({
                'category': category,
                'period1_amount': round(amount1, 2),
                'period2_amount': round(amount2, 2),
                'change': round(change, 2),
                'percent_change': round(percent_change, 2)
            })
        
        # Sort by absolute change
        changes.sort(key=lambda x: abs(x['change']), reverse=True)
        
        return {
            'period1': {
                'start': period1_start,
                'end': period1_end,
                'total': period1_data['summary']['total_amount']
            },
            'period2': {
                'start': period2_start,
                'end': period2_end,
                'total': period2_data['summary']['total_amount']
            },
            'total_change': round(
                period2_data['summary']['total_amount'] - period1_data['summary']['total_amount'],
                2
            ),
            'category_changes': changes
        }
    
    def _generate_empty_response(self, start_date: str, end_date: str) -> Dict:
        """Generate empty response when insufficient data."""
        return {
            'date_range': {
                'start': start_date,
                'end': end_date
            },
            'summary': {
                'total_amount': 0,
                'transaction_count': 0,
                'unique_categories': 0
            },
            'categories': {},
            'top_categories': [],
            'trends': {},
            'message': constants.ERROR_INSUFFICIENT_DATA
        }
