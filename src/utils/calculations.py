"""Financial calculation utilities."""

from typing import List, Dict, Tuple
import statistics
from collections import defaultdict


def calculate_net_flow(deposits: List[float], withdrawals: List[float]) -> float:
    """
    Calculate net cash flow.
    
    Args:
        deposits: List of deposit amounts
        withdrawals: List of withdrawal amounts
        
    Returns:
        Net flow (deposits - withdrawals)
    """
    total_deposits = sum(deposits) if deposits else 0
    total_withdrawals = sum(withdrawals) if withdrawals else 0
    return total_deposits - total_withdrawals


def calculate_average(values: List[float]) -> float:
    """
    Calculate average of values.
    
    Args:
        values: List of numeric values
        
    Returns:
        Average value or 0 if empty
    """
    return statistics.mean(values) if values else 0.0


def calculate_median(values: List[float]) -> float:
    """
    Calculate median of values.
    
    Args:
        values: List of numeric values
        
    Returns:
        Median value or 0 if empty
    """
    return statistics.median(values) if values else 0.0


def calculate_std_dev(values: List[float]) -> float:
    """
    Calculate standard deviation of values.
    
    Args:
        values: List of numeric values
        
    Returns:
        Standard deviation or 0 if insufficient data
    """
    if len(values) < 2:
        return 0.0
    return statistics.stdev(values)


def calculate_variance(values: List[float]) -> float:
    """
    Calculate variance of values.
    
    Args:
        values: List of numeric values
        
    Returns:
        Variance or 0 if insufficient data
    """
    if len(values) < 2:
        return 0.0
    return statistics.variance(values)


def calculate_savings_rate(deposits: List[float], withdrawals: List[float]) -> float:
    """
    Calculate savings rate as percentage.
    
    Args:
        deposits: List of deposit amounts
        withdrawals: List of withdrawal amounts
        
    Returns:
        Savings rate percentage (0-100)
    """
    total_deposits = sum(deposits) if deposits else 0
    if total_deposits == 0:
        return 0.0
    
    net_savings = calculate_net_flow(deposits, withdrawals)
    return (net_savings / total_deposits) * 100


def calculate_growth_rate(start_value: float, end_value: float) -> float:
    """
    Calculate percentage growth rate.
    
    Args:
        start_value: Starting value
        end_value: Ending value
        
    Returns:
        Growth rate percentage
    """
    if start_value == 0:
        return 0.0
    return ((end_value - start_value) / start_value) * 100


def calculate_compound_growth_rate(values: List[float], periods: int) -> float:
    """
    Calculate compound annual growth rate (CAGR).
    
    Args:
        values: List of values over time
        periods: Number of periods (years)
        
    Returns:
        CAGR percentage
    """
    if not values or len(values) < 2 or periods <= 0:
        return 0.0
    
    start_value = values[0]
    end_value = values[-1]
    
    if start_value <= 0:
        return 0.0
    
    return (((end_value / start_value) ** (1 / periods)) - 1) * 100


def calculate_burn_rate(withdrawals: List[float], days: int) -> float:
    """
    Calculate daily burn rate (average spending per day).
    
    Args:
        withdrawals: List of withdrawal amounts
        days: Number of days in period
        
    Returns:
        Average daily spending
    """
    if days <= 0:
        return 0.0
    
    total_withdrawals = sum(withdrawals) if withdrawals else 0
    return total_withdrawals / days


def calculate_percentile(values: List[float], percentile: float) -> float:
    """
    Calculate percentile of values.
    
    Args:
        values: List of numeric values
        percentile: Percentile to calculate (0-100)
        
    Returns:
        Value at given percentile
    """
    if not values:
        return 0.0
    
    sorted_values = sorted(values)
    k = (len(sorted_values) - 1) * (percentile / 100)
    f = int(k)
    c = k - f
    
    if f + 1 < len(sorted_values):
        return sorted_values[f] + (c * (sorted_values[f + 1] - sorted_values[f]))
    return sorted_values[f]


def calculate_weighted_average(values: List[float], weights: List[float]) -> float:
    """
    Calculate weighted average.
    
    Args:
        values: List of values
        weights: List of weights (same length as values)
        
    Returns:
        Weighted average
    """
    if not values or not weights or len(values) != len(weights):
        return 0.0
    
    total_weight = sum(weights)
    if total_weight == 0:
        return 0.0
    
    weighted_sum = sum(v * w for v, w in zip(values, weights))
    return weighted_sum / total_weight


def group_by_category(transactions: List[Dict], category_key: str = 'tags') -> Dict[str, List]:
    """
    Group transactions by category/tag.
    
    Args:
        transactions: List of transaction dictionaries
        category_key: Key to use for categorization
        
    Returns:
        Dictionary mapping categories to transaction lists
    """
    grouped = defaultdict(list)
    
    for txn in transactions:
        categories = txn.get(category_key, [])
        if not categories:
            grouped['uncategorized'].append(txn)
        else:
            for category in categories:
                grouped[category].append(txn)
    
    return dict(grouped)


def calculate_category_totals(grouped_transactions: Dict[str, List], amount_key: str = 'amount') -> Dict[str, float]:
    """
    Calculate total amounts per category.
    
    Args:
        grouped_transactions: Dictionary of categories to transaction lists
        amount_key: Key to extract amount from transactions
        
    Returns:
        Dictionary mapping categories to total amounts
    """
    totals = {}
    for category, transactions in grouped_transactions.items():
        total = sum(txn.get(amount_key, 0) for txn in transactions)
        totals[category] = total
    
    return totals


def calculate_moving_average(values: List[float], window_size: int) -> List[float]:
    """
    Calculate moving average.
    
    Args:
        values: List of values
        window_size: Size of moving window
        
    Returns:
        List of moving averages
    """
    if not values or window_size <= 0:
        return []
    
    moving_avgs = []
    for i in range(len(values)):
        start_idx = max(0, i - window_size + 1)
        window = values[start_idx:i + 1]
        moving_avgs.append(statistics.mean(window))
    
    return moving_avgs


def normalize_values(values: List[float]) -> List[float]:
    """
    Normalize values to 0-1 range.
    
    Args:
        values: List of values
        
    Returns:
        List of normalized values
    """
    if not values:
        return []
    
    min_val = min(values)
    max_val = max(values)
    
    if min_val == max_val:
        return [0.5] * len(values)
    
    return [(v - min_val) / (max_val - min_val) for v in values]


def detect_outliers(values: List[float], threshold: float = 2.0) -> List[Tuple[int, float]]:
    """
    Detect outliers using standard deviation method.
    
    Args:
        values: List of values
        threshold: Number of standard deviations to consider as outlier
        
    Returns:
        List of tuples (index, value) for outliers
    """
    if len(values) < 3:
        return []
    
    mean = statistics.mean(values)
    std_dev = statistics.stdev(values)
    
    outliers = []
    for i, value in enumerate(values):
        z_score = abs((value - mean) / std_dev) if std_dev > 0 else 0
        if z_score > threshold:
            outliers.append((i, value))
    
    return outliers


def calculate_runway(current_balance: float, burn_rate: float) -> int:
    """
    Calculate runway (days until balance reaches zero).
    
    Args:
        current_balance: Current balance amount
        burn_rate: Daily burn rate (positive value for spending)
        
    Returns:
        Number of days until balance is exhausted.
        Returns -1 for infinite runway (no spending or gaining money).
        Returns 0 if current balance is zero or negative.
    """
    if current_balance <= 0:
        return 0  # No balance, no runway
    
    if burn_rate <= 0:
        return -1  # Infinite runway (no spending or gaining money)
    
    return int(current_balance / burn_rate)
