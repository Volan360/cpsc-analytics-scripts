"""Tests for date utilities module."""

import pytest
from datetime import datetime
from src.utils import date_utils


class TestTimestampConversion:
    """Test timestamp conversion functions."""
    
    def test_timestamp_to_datetime(self):
        """Test converting timestamp to datetime."""
        timestamp = 1735689600  # 2025-01-01 00:00:00 UTC
        
        result = date_utils.timestamp_to_datetime(timestamp)
        
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 1
    
    def test_datetime_to_timestamp(self):
        """Test converting datetime to timestamp."""
        dt = datetime(2025, 1, 1, 0, 0, 0)
        
        result = date_utils.datetime_to_timestamp(dt)
        
        assert isinstance(result, int)
        assert result > 0
    
    def test_round_trip_conversion(self):
        """Test converting back and forth maintains value."""
        original_ts = 1735689600
        
        dt = date_utils.timestamp_to_datetime(original_ts)
        result_ts = date_utils.datetime_to_timestamp(dt)
        
        assert result_ts == original_ts


class TestISOConversion:
    """Test ISO format conversion."""
    
    def test_iso_to_timestamp(self):
        """Test converting ISO string to timestamp."""
        iso_string = "2025-01-01"
        
        result = date_utils.iso_to_timestamp(iso_string)
        
        assert isinstance(result, int)
        assert result > 0
    
    def test_timestamp_to_iso(self):
        """Test converting timestamp to ISO string."""
        timestamp = 1735689600
        
        result = date_utils.timestamp_to_iso(timestamp)
        
        assert isinstance(result, str)
        assert "2025" in result


class TestDateRange:
    """Test date range functions."""
    
    def test_get_date_range(self):
        """Test getting timestamp range from date strings."""
        start_date = "2025-01-01"
        end_date = "2025-12-31"
        
        start_ts, end_ts = date_utils.get_date_range(start_date, end_date)
        
        assert isinstance(start_ts, int)
        assert isinstance(end_ts, int)
        assert end_ts > start_ts
    
    def test_days_between(self):
        """Test calculating days between timestamps."""
        start_ts = 1735689600  # 2025-01-01
        end_ts = 1738368000    # 2025-02-01
        
        result = date_utils.get_days_between(start_ts, end_ts)
        
        assert result == 31
    
    def test_months_between(self):
        """Test calculating months between timestamps."""
        start_ts = 1735689600  # 2025-01-01
        end_ts = 1767225600    # 2026-01-01
        
        result = date_utils.get_months_between(start_ts, end_ts)
        
        assert result == 12


class TestGrouping:
    """Test timestamp grouping functions."""
    
    def test_group_by_month(self):
        """Test grouping timestamps by month."""
        timestamps = [
            1735689600,  # 2025-01-01
            1736294400,  # 2025-01-08
            1738368000,  # 2025-02-01
        ]
        
        result = date_utils.group_by_month(timestamps)
        
        assert len(result) == 2
        assert "2025-01" in result
        assert "2025-02" in result
        assert len(result["2025-01"]) == 2
        assert len(result["2025-02"]) == 1
    
    def test_group_by_day(self):
        """Test grouping timestamps by day."""
        timestamps = [
            1735689600,  # 2025-01-01 00:00
            1735693200,  # 2025-01-01 01:00
            1735776000,  # 2025-01-02 00:00
        ]
        
        result = date_utils.group_by_day(timestamps)
        
        assert len(result) >= 2  # At least 2 different days


class TestDateArithmetic:
    """Test date arithmetic functions."""
    
    def test_add_days_positive(self):
        """Test adding days to timestamp."""
        timestamp = 1735689600  # 2025-01-01
        
        result = date_utils.add_days(timestamp, 7)
        
        days_diff = date_utils.get_days_between(timestamp, result)
        assert days_diff == 7
    
    def test_add_days_negative(self):
        """Test subtracting days from timestamp."""
        timestamp = 1735689600  # 2025-01-01
        
        result = date_utils.add_days(timestamp, -7)
        
        assert result < timestamp
    
    def test_add_months(self):
        """Test adding months to timestamp."""
        timestamp = 1735689600  # 2025-01-01
        
        result = date_utils.add_months(timestamp, 1)
        
        # Should be approximately February 1
        dt = date_utils.timestamp_to_datetime(result)
        assert dt.month == 2


class TestFormatting:
    """Test date formatting functions."""
    
    def test_format_date_default(self):
        """Test default date formatting."""
        timestamp = 1735689600  # 2025-01-01
        
        result = date_utils.format_date(timestamp)
        
        assert result == "2025-01-01"
    
    def test_format_date_custom(self):
        """Test custom date formatting."""
        timestamp = 1735689600  # 2025-01-01
        
        result = date_utils.format_date(timestamp, '%m/%d/%Y')
        
        assert "01" in result
        assert "2025" in result
    
    def test_get_current_timestamp(self):
        """Test getting current timestamp."""
        result = date_utils.get_current_timestamp()
        
        assert isinstance(result, int)
        assert result > 1700000000  # After 2023


class TestGroupingEdgeCases:
    """Test edge cases in grouping functions."""
    
    def test_group_by_week(self):
        """Test grouping timestamps by week."""
        timestamps = [
            1735689600,  # 2025-01-01 (Wed)
            1735776000,  # 2025-01-02 (Thu)
            1736208000,  # 2025-01-07 (Tue - next week)
        ]
        
        result = date_utils.group_by_week(timestamps)
        
        # Should have at least 2 different weeks
        assert len(result) >= 2
    
    def test_group_by_month_edge_month_boundaries(self):
        """Test grouping at month boundaries."""
        # Use actual month boundary dates
        timestamps = [
            1738367999,  # 2025-01-31 23:59:59 UTC
            1738454400,  # 2025-02-01 00:00:00 UTC
        ]
        
        result = date_utils.group_by_month(timestamps)
        
        # Should be in different months
        assert len(result) == 2
        assert "2025-01" in result
        assert "2025-02" in result
    
    def test_group_by_day_empty_list(self):
        """Test grouping with empty list."""
        result = date_utils.group_by_day([])
        
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_group_by_month_single_timestamp(self):
        """Test grouping with single timestamp."""
        timestamps = [1735689600]
        
        result = date_utils.group_by_month(timestamps)
        
        assert len(result) == 1


class TestDateArithmeticEdgeCases:
    """Test edge cases in date arithmetic."""
    
    def test_add_months_year_boundary(self):
        """Test adding months across year boundary."""
        timestamp = 1735689600  # 2025-01-01
        
        result = date_utils.add_months(timestamp, 12)
        
        dt = date_utils.timestamp_to_datetime(result)
        assert dt.year == 2026
        assert dt.month == 1
    
    def test_add_months_negative(self):
        """Test subtracting months."""
        timestamp = 1738368000  # 2025-02-01
        
        result = date_utils.add_months(timestamp, -1)
        
        dt = date_utils.timestamp_to_datetime(result)
        assert dt.month == 1
    
    def test_add_days_zero(self):
        """Test adding zero days."""
        timestamp = 1735689600
        
        result = date_utils.add_days(timestamp, 0)
        
        assert result == timestamp
    
    def test_add_months_zero(self):
        """Test adding zero months."""
        timestamp = 1735689600
        
        result = date_utils.add_months(timestamp, 0)
        
        assert result == timestamp


class TestDateRangeEdgeCases:
    """Test edge cases in date range calculations."""
    
    def test_days_between_same_day(self):
        """Test days between same timestamp."""
        timestamp = 1735689600
        
        result = date_utils.get_days_between(timestamp, timestamp)
        
        assert result == 0
    
    def test_months_between_same_month(self):
        """Test months between same timestamp."""
        timestamp = 1735689600
        
        result = date_utils.get_months_between(timestamp, timestamp)
        
        assert result == 0
    
    def test_months_between_mid_month(self):
        """Test months between mid-month dates."""
        start_ts = 1735948800  # 2025-01-15
        end_ts = 1738627200    # 2025-02-15
        
        result = date_utils.get_months_between(start_ts, end_ts)
        
        assert result == 1


class TestFormattingEdgeCases:
    """Test edge cases in date formatting."""
    
    def test_format_date_with_time(self):
        """Test formatting with time component."""
        timestamp = 1735689600
        
        result = date_utils.format_date(timestamp, '%Y-%m-%d %H:%M:%S')
        
        assert "2025" in result
        assert ":" in result
    
    def test_format_date_year_only(self):
        """Test formatting year only."""
        timestamp = 1735689600
        
        result = date_utils.format_date(timestamp, '%Y')
        
        assert result == "2025"
    
    def test_timestamp_to_iso_none(self):
        """Test converting None/null timestamp returns None."""
        # This is expected to raise an error since timestamp_to_iso
        # expects an integer. This test validates the type requirement.
        with pytest.raises(TypeError):
            date_utils.timestamp_to_iso(None)
