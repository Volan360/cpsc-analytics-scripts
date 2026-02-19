"""Tests for utility calculations module."""

import pytest
from src.utils import calculations


class TestNetFlow:
    """Test net flow calculations."""
    
    def test_positive_net_flow(self):
        """Test calculation with more deposits than withdrawals."""
        deposits = [100, 200, 300]
        withdrawals = [50, 75, 100]
        
        result = calculations.calculate_net_flow(deposits, withdrawals)
        
        assert result == 375  # (600 - 225)
    
    def test_negative_net_flow(self):
        """Test calculation with more withdrawals than deposits."""
        deposits = [100, 200]
        withdrawals = [150, 200, 250]
        
        result = calculations.calculate_net_flow(deposits, withdrawals)
        
        assert result == -300  # (300 - 600)
    
    def test_empty_lists(self):
        """Test calculation with empty lists."""
        result = calculations.calculate_net_flow([], [])
        
        assert result == 0
    
    def test_zero_withdrawals(self):
        """Test calculation with only deposits."""
        deposits = [100, 200, 300]
        withdrawals = []
        
        result = calculations.calculate_net_flow(deposits, withdrawals)
        
        assert result == 600


class TestSavingsRate:
    """Test savings rate calculations."""
    
    def test_positive_savings_rate(self):
        """Test savings rate with positive net flow."""
        deposits = [1000]
        withdrawals = [600]
        
        result = calculations.calculate_savings_rate(deposits, withdrawals)
        
        assert result == 40.0  # 400/1000 * 100
    
    def test_zero_savings_rate(self):
        """Test savings rate when deposits equal withdrawals."""
        deposits = [500]
        withdrawals = [500]
        
        result = calculations.calculate_savings_rate(deposits, withdrawals)
        
        assert result == 0.0
    
    def test_negative_savings_rate(self):
        """Test savings rate when spending exceeds income."""
        deposits = [500]
        withdrawals = [700]
        
        result = calculations.calculate_savings_rate(deposits, withdrawals)
        
        assert result == -40.0  # -200/500 * 100
    
    def test_no_deposits(self):
        """Test savings rate with no deposits."""
        deposits = []
        withdrawals = [100]
        
        result = calculations.calculate_savings_rate(deposits, withdrawals)
        
        assert result == 0.0


class TestGrowthRate:
    """Test growth rate calculations."""
    
    def test_positive_growth(self):
        """Test positive growth calculation."""
        result = calculations.calculate_growth_rate(100, 150)
        
        assert result == 50.0  # 50% growth
    
    def test_negative_growth(self):
        """Test negative growth calculation."""
        result = calculations.calculate_growth_rate(100, 75)
        
        assert result == -25.0  # 25% decline
    
    def test_zero_growth(self):
        """Test no growth."""
        result = calculations.calculate_growth_rate(100, 100)
        
        assert result == 0.0
    
    def test_zero_start_value(self):
        """Test growth from zero."""
        result = calculations.calculate_growth_rate(0, 100)
        
        assert result == 0.0  # Undefined, returns 0


class TestStatistics:
    """Test statistical calculations."""
    
    def test_average(self):
        """Test average calculation."""
        values = [10, 20, 30, 40, 50]
        
        result = calculations.calculate_average(values)
        
        assert result == 30.0
    
    def test_median_odd_count(self):
        """Test median with odd number of values."""
        values = [1, 3, 5, 7, 9]
        
        result = calculations.calculate_median(values)
        
        assert result == 5.0
    
    def test_median_even_count(self):
        """Test median with even number of values."""
        values = [1, 2, 3, 4]
        
        result = calculations.calculate_median(values)
        
        assert result == 2.5
    
    def test_std_dev(self):
        """Test standard deviation calculation."""
        values = [10, 20, 30, 40, 50]
        
        result = calculations.calculate_std_dev(values)
        
        assert round(result, 2) == 15.81  # Approximately
    
    def test_empty_average(self):
        """Test average with empty list."""
        result = calculations.calculate_average([])
        
        assert result == 0.0


class TestBurnRate:
    """Test burn rate calculations."""
    
    def test_daily_burn_rate(self):
        """Test daily burn rate calculation."""
        withdrawals = [100, 200, 300]
        days = 30
        
        result = calculations.calculate_burn_rate(withdrawals, days)
        
        assert result == 20.0  # 600/30
    
    def test_zero_days(self):
        """Test burn rate with zero days."""
        withdrawals = [100, 200]
        days = 0
        
        result = calculations.calculate_burn_rate(withdrawals, days)
        
        assert result == 0.0


class TestRunway:
    """Test runway calculations."""
    
    def test_positive_runway(self):
        """Test runway calculation with positive balance."""
        current_balance = 10000
        burn_rate = 100
        
        result = calculations.calculate_runway(current_balance, burn_rate)
        
        assert result == 100  # 10000/100 days
    
    def test_infinite_runway(self):
        """Test runway with no burn rate."""
        current_balance = 10000
        burn_rate = 0
        
        result = calculations.calculate_runway(current_balance, burn_rate)
        
        assert result == -1  # Infinite
    
    def test_negative_burn_rate(self):
        """Test runway with negative burn rate (gaining money)."""
        current_balance = 10000
        burn_rate = -50
        
        result = calculations.calculate_runway(current_balance, burn_rate)
        
        assert result == -1  # Infinite


class TestOutlierDetection:
    """Test outlier detection."""
    
    def test_detect_outliers(self):
        """Test outlier detection in dataset."""
        values = [10, 12, 11, 13, 10, 12, 100]  # 100 is an outlier
        
        outliers = calculations.detect_outliers(values, threshold=2.0)
        
        assert len(outliers) == 1
        assert outliers[0][1] == 100
    
    def test_no_outliers(self):
        """Test dataset with no outliers."""
        values = [10, 12, 11, 13, 10, 12, 14]
        
        outliers = calculations.detect_outliers(values, threshold=2.0)
        
        assert len(outliers) == 0
    
    def test_insufficient_data(self):
        """Test outlier detection with too few values."""
        values = [10, 20]
        
        outliers = calculations.detect_outliers(values)
        
        assert len(outliers) == 0


class TestVariance:
    """Test variance calculations."""
    
    def test_variance_calculation(self):
        """Test variance with sample data."""
        values = [2, 4, 4, 4, 5, 5, 7, 9]
        
        result = calculations.calculate_variance(values)
        
        assert result == pytest.approx(4.571, rel=0.01)
    
    def test_variance_insufficient_data(self):
        """Test variance with insufficient data."""
        values = [5]
        
        result = calculations.calculate_variance(values)
        
        assert result == 0.0
    
    def test_variance_empty_list(self):
        """Test variance with empty list."""
        result = calculations.calculate_variance([])
        
        assert result == 0.0


class TestCompoundGrowthRate:
    """Test compound annual growth rate calculations."""
    
    def test_positive_cagr(self):
        """Test CAGR with growth."""
        values = [100, 110, 121, 133.1]
        periods = 3
        
        result = calculations.calculate_compound_growth_rate(values, periods)
        
        assert result == pytest.approx(10.0, rel=0.1)
    
    def test_negative_cagr(self):
        """Test CAGR with decline."""
        values = [100, 90, 81]
        periods = 2
        
        result = calculations.calculate_compound_growth_rate(values, periods)
        
        assert result < 0
    
    def test_cagr_zero_start(self):
        """Test CAGR with zero starting value."""
        values = [0, 100, 200]
        periods = 2
        
        result = calculations.calculate_compound_growth_rate(values, periods)
        
        assert result == 0.0
    
    def test_cagr_insufficient_data(self):
        """Test CAGR with insufficient data."""
        values = [100]
        periods = 1
        
        result = calculations.calculate_compound_growth_rate(values, periods)
        
        assert result == 0.0


class TestPercentile:
    """Test percentile calculations."""
    
    def test_percentile_50(self):
        """Test median (50th percentile)."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        result = calculations.calculate_percentile(values, 50)
        
        assert result == 5.5
    
    def test_percentile_90(self):
        """Test 90th percentile."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        result = calculations.calculate_percentile(values, 90)
        
        assert result == 9.1
    
    def test_percentile_empty_list(self):
        """Test percentile with empty list."""
        result = calculations.calculate_percentile([], 50)
        
        assert result == 0.0


class TestWeightedAverage:
    """Test weighted average calculations."""
    
    def test_weighted_average_equal_weights(self):
        """Test weighted average with equal weights."""
        values = [10, 20, 30]
        weights = [1, 1, 1]
        
        result = calculations.calculate_weighted_average(values, weights)
        
        assert result == 20.0
    
    def test_weighted_average_different_weights(self):
        """Test weighted average with different weights."""
        values = [10, 20, 30]
        weights = [1, 2, 3]
        
        result = calculations.calculate_weighted_average(values, weights)
        
        assert result == pytest.approx(23.33, rel=0.01)
    
    def test_weighted_average_empty_lists(self):
        """Test weighted average with empty lists."""
        result = calculations.calculate_weighted_average([], [])
        
        assert result == 0.0
    
    def test_weighted_average_mismatched_lengths(self):
        """Test weighted average with mismatched lengths."""
        values = [10, 20, 30]
        weights = [1, 2]
        
        result = calculations.calculate_weighted_average(values, weights)
        
        assert result == 0.0


class TestMovingAverage:
    """Test moving average calculations."""
    
    def test_moving_average_window_3(self):
        """Test moving average with window size 3."""
        values = [10, 20, 30, 40, 50]
        
        result = calculations.calculate_moving_average(values, 3)
        
        assert result == [10.0, 15.0, 20.0, 30.0, 40.0]
    
    def test_moving_average_window_1(self):
        """Test moving average with window size 1."""
        values = [10, 20, 30]
        
        result = calculations.calculate_moving_average(values, 1)
        
        assert result == values
    
    def test_moving_average_empty_list(self):
        """Test moving average with empty list."""
        result = calculations.calculate_moving_average([], 3)
        
        assert result == []


class TestNormalization:
    """Test value normalization."""
    
    def test_normalize_values(self):
        """Test normalization to 0-1 range."""
        values = [10, 20, 30, 40, 50]
        
        result = calculations.normalize_values(values)
        
        assert result[0] == 0.0
        assert result[-1] == 1.0
        assert result[2] == 0.5
    
    def test_normalize_same_values(self):
        """Test normalization with all same values."""
        values = [5, 5, 5]
        
        result = calculations.normalize_values(values)
        
        assert all(v == 0.5 for v in result)
    
    def test_normalize_empty_list(self):
        """Test normalization with empty list."""
        result = calculations.normalize_values([])
        
        assert result == []


class TestGroupByCategory:
    """Test category grouping."""
    
    def test_group_by_category_basic(self):
        """Test basic category grouping."""
        transactions = [
            {'id': 1, 'tags': ['food'], 'amount': 100},
            {'id': 2, 'tags': ['food'], 'amount': 50},
            {'id': 3, 'tags': ['transport'], 'amount': 30}
        ]
        
        result = calculations.group_by_category(transactions, 'tags')
        
        assert len(result['food']) == 2
        assert len(result['transport']) == 1
    
    def test_group_by_category_uncategorized(self):
        """Test grouping with uncategorized transactions."""
        transactions = [
            {'id': 1, 'tags': [], 'amount': 100},
            {'id': 2, 'tags': ['food'], 'amount': 50}
        ]
        
        result = calculations.group_by_category(transactions, 'tags')
        
        assert 'uncategorized' in result
        assert len(result['uncategorized']) == 1


class TestCategoryTotals:
    """Test category totals calculation."""
    
    def test_calculate_category_totals(self):
        """Test calculating totals per category."""
        grouped = {
            'food': [{'amount': 100}, {'amount': 50}],
            'transport': [{'amount': 30}]
        }
        
        result = calculations.calculate_category_totals(grouped, 'amount')
        
        assert result['food'] == 150
        assert result['transport'] == 30
