"""Lambda function handlers for AWS deployment."""
from src.lambda_handlers.analytics_handler import handler as analytics_handler
from src.lambda_handlers.report_handler import handler as report_handler

__all__ = ['analytics_handler', 'report_handler']