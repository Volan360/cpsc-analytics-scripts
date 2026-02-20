"""DynamoDB client for fetching financial data."""

import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Key, Attr

from .data_models import Institution, Transaction, Goal


logger = logging.getLogger(__name__)


class DynamoDBClient:
    """Client for accessing DynamoDB tables."""
    
    def __init__(self, environment: str = "devl", profile: str = "cpsc-devops", region: str = "us-east-1"):
        """
        Initialize DynamoDB client.
        
        Args:
            environment: Environment name (devl, acpt, prod)
            profile: AWS profile name
            region: AWS region
        """
        self.environment = environment
        self.region = region
        
        # Initialize boto3 session with profile
        session = boto3.Session(profile_name=profile, region_name=region)
        self.dynamodb = session.resource('dynamodb')
        
        # Table names
        self.institutions_table_name = f"Institutions-{environment}"
        self.transactions_table_name = f"Transactions-{environment}"
        self.goals_table_name = f"Goals-{environment}"
        
        # Get table references
        self.institutions_table = self.dynamodb.Table(self.institutions_table_name)
        self.transactions_table = self.dynamodb.Table(self.transactions_table_name)
        self.goals_table = self.dynamodb.Table(self.goals_table_name)
        
        logger.info(f"DynamoDBClient initialized for environment: {environment}")
    
    def get_institutions(self, user_id: str) -> List[Institution]:
        """
        Get all institutions for a user.
        
        Args:
            user_id: User ID from Cognito
            
        Returns:
            List of Institution objects
        """
        try:
            response = self.institutions_table.query(
                KeyConditionExpression=Key('userId').eq(user_id)
            )
            
            institutions = []
            for item in response.get('Items', []):
                institution = Institution(
                    user_id=item['userId'],
                    institution_id=item['institutionId'],
                    institution_name=item['institutionName'],
                    starting_balance=float(item.get('startingBalance', 0)),
                    current_balance=float(item.get('currentBalance', 0)),
                    created_at=int(item.get('createdAt', 0)),
                    allocated_percent=item.get('allocatedPercent'),
                    linked_goals=item.get('linkedGoals', [])
                )
                institutions.append(institution)
            
            logger.info(f"Retrieved {len(institutions)} institutions for user {user_id}")
            return institutions
            
        except Exception as e:
            logger.error(f"Error fetching institutions for user {user_id}: {str(e)}")
            raise
    
    def get_institution(self, user_id: str, institution_id: str) -> Optional[Institution]:
        """
        Get a specific institution.
        
        Args:
            user_id: User ID from Cognito
            institution_id: Institution ID
            
        Returns:
            Institution object or None if not found
        """
        try:
            response = self.institutions_table.get_item(
                Key={
                    'userId': user_id,
                    'institutionId': institution_id
                }
            )
            
            item = response.get('Item')
            if not item:
                return None
            
            return Institution(
                user_id=item['userId'],
                institution_id=item['institutionId'],
                institution_name=item['institutionName'],
                starting_balance=float(item.get('startingBalance', 0)),
                current_balance=float(item.get('currentBalance', 0)),
                created_at=int(item.get('createdAt', 0)),
                allocated_percent=item.get('allocatedPercent'),
                linked_goals=item.get('linkedGoals', [])
            )
            
        except Exception as e:
            logger.error(f"Error fetching institution {institution_id}: {str(e)}")
            raise
    
    def get_transactions(
        self,
        institution_id: str,
        user_id: Optional[str] = None,
        start_date: Optional[int] = None,
        end_date: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Transaction]:
        """
        Get transactions for an institution with optional filters.
        
        Args:
            institution_id: Institution ID (partition key)
            user_id: Filter by user ID
            start_date: Start timestamp (inclusive)
            end_date: End timestamp (inclusive)
            limit: Maximum number of results
            
        Returns:
            List of Transaction objects
        """
        try:
            # Build key condition
            key_condition = Key('institutionId').eq(institution_id)
            
            # Add date range to key condition if provided
            if start_date and end_date:
                key_condition &= Key('createdAt').between(start_date, end_date)
            elif start_date:
                key_condition &= Key('createdAt').gte(start_date)
            elif end_date:
                key_condition &= Key('createdAt').lte(end_date)
            
            # Build query parameters
            query_params = {
                'KeyConditionExpression': key_condition,
                'ScanIndexForward': False  # Sort descending (newest first)
            }
            
            # Add filter expression for user_id if provided
            if user_id:
                query_params['FilterExpression'] = Attr('userId').eq(user_id)
            
            # Add limit if provided
            if limit:
                query_params['Limit'] = limit
            
            response = self.transactions_table.query(**query_params)
            
            transactions = []
            for item in response.get('Items', []):
                transaction = Transaction(
                    institution_id=item['institutionId'],
                    created_at=int(item['createdAt']),
                    transaction_id=item['transactionId'],
                    user_id=item['userId'],
                    type=item['type'],
                    amount=float(item['amount']),
                    transaction_date=int(item.get('transactionDate', item['createdAt'])),
                    tags=item.get('tags', []),
                    description=item.get('description')
                )
                transactions.append(transaction)
            
            logger.info(f"Retrieved {len(transactions)} transactions for institution {institution_id}")
            return transactions
            
        except Exception as e:
            logger.error(f"Error fetching transactions for institution {institution_id}: {str(e)}")
            raise
    
    def get_all_user_transactions(
        self,
        user_id: str,
        start_date: Optional[int] = None,
        end_date: Optional[int] = None
    ) -> List[Transaction]:
        """
        Get all transactions for a user across all institutions.
        
        Args:
            user_id: User ID from Cognito
            start_date: Start timestamp (inclusive)
            end_date: End timestamp (inclusive)
            
        Returns:
            List of Transaction objects
        """
        # First get all institutions for the user
        institutions = self.get_institutions(user_id)
        
        # Then fetch transactions for each institution
        all_transactions = []
        for institution in institutions:
            transactions = self.get_transactions(
                institution_id=institution.institution_id,
                user_id=user_id,
                start_date=start_date,
                end_date=end_date
            )
            all_transactions.extend(transactions)
        
        # Sort by transaction_date descending
        all_transactions.sort(key=lambda t: t.transaction_date, reverse=True)
        
        logger.info(f"Retrieved {len(all_transactions)} total transactions for user {user_id}")
        return all_transactions
    
    def get_goals(self, user_id: str) -> List[Goal]:
        """
        Get all goals for a user.
        
        Args:
            user_id: User ID from Cognito
            
        Returns:
            List of Goal objects
        """
        try:
            response = self.goals_table.query(
                KeyConditionExpression=Key('userId').eq(user_id)
            )
            
            goals = []
            for item in response.get('Items', []):
                raw_linked = item.get('linkedInstitutions', {})
                completed_at_raw = item.get('completedAt')
                goal = Goal(
                    user_id=item['userId'],
                    goal_id=item['goalId'],
                    name=item['name'],
                    target_amount=float(item.get('targetAmount', 0)),
                    created_at=int(item.get('createdAt', 0)),
                    is_completed=item.get('isCompleted', False),
                    is_active=item.get('isActive', True),
                    description=item.get('description'),
                    linked_institutions={k: float(v) for k, v in raw_linked.items()},
                    linked_transactions=item.get('linkedTransactions', []),
                    completed_at=int(completed_at_raw) if completed_at_raw is not None else None
                )
                goals.append(goal)
            
            logger.info(f"Retrieved {len(goals)} goals for user {user_id}")
            return goals
            
        except Exception as e:
            logger.error(f"Error fetching goals for user {user_id}: {str(e)}")
            raise
    
    def get_goal(self, user_id: str, goal_id: str) -> Optional[Goal]:
        """
        Get a specific goal.
        
        Args:
            user_id: User ID from Cognito
            goal_id: Goal ID
            
        Returns:
            Goal object or None if not found
        """
        try:
            response = self.goals_table.get_item(
                Key={
                    'userId': user_id,
                    'goalId': goal_id
                }
            )
            
            item = response.get('Item')
            if not item:
                return None
            
            raw_linked = item.get('linkedInstitutions', {})
            completed_at_raw = item.get('completedAt')
            return Goal(
                user_id=item['userId'],
                goal_id=item['goalId'],
                name=item['name'],
                target_amount=float(item.get('targetAmount', 0)),
                created_at=int(item.get('createdAt', 0)),
                is_completed=item.get('isCompleted', False),
                is_active=item.get('isActive', True),
                description=item.get('description'),
                linked_institutions={k: float(v) for k, v in raw_linked.items()},
                linked_transactions=item.get('linkedTransactions', []),
                completed_at=int(completed_at_raw) if completed_at_raw is not None else None
            )
            
        except Exception as e:
            logger.error(f"Error fetching goal {goal_id}: {str(e)}")
            raise
