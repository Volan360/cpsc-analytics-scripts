"""Date and time utility functions."""

from datetime import datetime, timedelta, timezone
from typing import Tuple, List
import calendar


def timestamp_to_datetime(timestamp: int) -> datetime:
    """
    Convert UNIX timestamp to datetime object (UTC).
    
    Args:
        timestamp: UNIX timestamp (seconds since epoch)
        
    Returns:
        datetime object in UTC
    """
    return datetime.fromtimestamp(float(timestamp), tz=timezone.utc)


def datetime_to_timestamp(dt: datetime) -> int:
    """
    Convert datetime object to UNIX timestamp.
    
    Args:
        dt: datetime object
        
    Returns:
        UNIX timestamp (seconds since epoch)
    """
    return int(dt.timestamp())


def iso_to_timestamp(iso_string: str) -> int:
    """
    Convert ISO format date string to UNIX timestamp.
    
    Args:
        iso_string: Date string in ISO format (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
        
    Returns:
        UNIX timestamp
    """
    dt = datetime.fromisoformat(iso_string)
    return int(dt.timestamp())


def timestamp_to_iso(timestamp: int) -> str:
    """
    Convert UNIX timestamp to ISO format string (UTC).
    
    Args:
        timestamp: UNIX timestamp
        
    Returns:
        ISO format date string
    """
    dt = datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
    return dt.isoformat()


def get_date_range(start_date: str, end_date: str) -> Tuple[int, int]:
    """
    Convert date range strings to timestamps.
    
    Args:
        start_date: Start date in ISO format
        end_date: End date in ISO format
        
    Returns:
        Tuple of (start_timestamp, end_timestamp)
    """
    start_ts = iso_to_timestamp(start_date)
    end_ts = iso_to_timestamp(end_date)
    return start_ts, end_ts


def get_month_boundaries(timestamp: int) -> Tuple[int, int]:
    """
    Get start and end timestamps for the month containing the given timestamp.
    
    Args:
        timestamp: UNIX timestamp
        
    Returns:
        Tuple of (month_start_timestamp, month_end_timestamp)
    """
    dt = datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
    
    # First day of month
    month_start = datetime(dt.year, dt.month, 1, tzinfo=timezone.utc)
    
    # Last day of month
    last_day = calendar.monthrange(dt.year, dt.month)[1]
    month_end = datetime(dt.year, dt.month, last_day, 23, 59, 59, tzinfo=timezone.utc)
    
    return int(month_start.timestamp()), int(month_end.timestamp())


def group_by_month(timestamps: List[int]) -> dict:
    """
    Group timestamps by month.
    
    Args:
        timestamps: List of UNIX timestamps
        
    Returns:
        Dictionary mapping month keys (YYYY-MM) to list of timestamps
    """
    grouped = {}
    for ts in timestamps:
        dt = datetime.fromtimestamp(float(ts), tz=timezone.utc)
        month_key = dt.strftime('%Y-%m')
        if month_key not in grouped:
            grouped[month_key] = []
        grouped[month_key].append(ts)
    
    return grouped


def group_by_week(timestamps: List[int]) -> dict:
    """
    Group timestamps by week.
    
    Args:
        timestamps: List of UNIX timestamps
        
    Returns:
        Dictionary mapping week keys (YYYY-Wxx) to list of timestamps
    """
    grouped = {}
    for ts in timestamps:
        dt = datetime.fromtimestamp(float(ts), tz=timezone.utc)
        week_key = dt.strftime('%Y-W%U')
        if week_key not in grouped:
            grouped[week_key] = []
        grouped[week_key].append(ts)
    
    return grouped


def group_by_day(timestamps: List[int]) -> dict:
    """
    Group timestamps by day.
    
    Args:
        timestamps: List of UNIX timestamps
        
    Returns:
        Dictionary mapping day keys (YYYY-MM-DD) to list of timestamps
    """
    grouped = {}
    for ts in timestamps:
        dt = datetime.fromtimestamp(float(ts), tz=timezone.utc)
        day_key = dt.strftime('%Y-%m-%d')
        if day_key not in grouped:
            grouped[day_key] = []
        grouped[day_key].append(ts)
    
    return grouped


def get_days_between(start_timestamp: int, end_timestamp: int) -> int:
    """
    Calculate number of days between two timestamps.
    
    Args:
        start_timestamp: Start UNIX timestamp
        end_timestamp: End UNIX timestamp
        
    Returns:
        Number of days (rounded down)
    """
    diff_seconds = end_timestamp - start_timestamp
    return diff_seconds // (24 * 3600)


def get_months_between(start_timestamp: int, end_timestamp: int) -> int:
    """
    Calculate approximate number of months between two timestamps.
    
    Args:
        start_timestamp: Start UNIX timestamp
        end_timestamp: End UNIX timestamp
        
    Returns:
        Number of months (approximate)
    """
    start_dt = datetime.fromtimestamp(float(start_timestamp), tz=timezone.utc)
    end_dt = datetime.fromtimestamp(float(end_timestamp), tz=timezone.utc)
    
    return (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)


def format_date(timestamp: int, format_string: str = '%Y-%m-%d') -> str:
    """
    Format timestamp as string (UTC).
    
    Args:
        timestamp: UNIX timestamp
        format_string: strftime format string
        
    Returns:
        Formatted date string
    """
    dt = datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
    return dt.strftime(format_string)


def get_current_timestamp() -> int:
    """
    Get current UNIX timestamp.
    
    Returns:
        Current UNIX timestamp
    """
    return int(datetime.now().timestamp())


def add_days(timestamp: int, days: int) -> int:
    """
    Add days to a timestamp.
    
    Args:
        timestamp: UNIX timestamp
        days: Number of days to add (can be negative)
        
    Returns:
        New UNIX timestamp
    """
    dt = datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
    new_dt = dt + timedelta(days=days)
    return int(new_dt.timestamp())


def add_months(timestamp: int, months: int) -> int:
    """
    Add months to a timestamp (approximate).
    
    Args:
        timestamp: UNIX timestamp
        months: Number of months to add (can be negative)
        
    Returns:
        New UNIX timestamp
    """
    dt = datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
    
    # Calculate new month and year
    new_month = dt.month + months
    new_year = dt.year
    
    while new_month > 12:
        new_month -= 12
        new_year += 1
    
    while new_month < 1:
        new_month += 12
        new_year -= 1
    
    # Handle day overflow (e.g., Jan 31 + 1 month = Feb 28/29)
    max_day = calendar.monthrange(new_year, new_month)[1]
    new_day = min(dt.day, max_day)
    
    new_dt = datetime(new_year, new_month, new_day, dt.hour, dt.minute, dt.second, tzinfo=timezone.utc)
    return int(new_dt.timestamp())
