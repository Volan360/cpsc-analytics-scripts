"""Lambda function handlers for AWS deployment."""
from src.lambda_handlers.analytics_handler import lambda_handler as analytics_handler
from src.lambda_handlers.report_handler import lambda_handler as report_handler

__all__ = ['analytics_handler', 'report_handler']