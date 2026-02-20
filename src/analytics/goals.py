"""Goal Analytics Module.

Tracks progress toward financial goals, calculates completion estimates,
and provides insights on goal achievement strategies.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from ..data.dynamodb_client import DynamoDBClient
from ..data.data_models import Goal, Institution, Transaction
from ..utils import date_utils, calculations, constants


logger = logging.getLogger(__name__)


class GoalAnalytics:
    """Financial goal tracking and progress analysis."""
    
    def __init__(self, db_client: DynamoDBClient):
        """
        Initialize goal analytics.
        
        Args:
            db_client: DynamoDB client instance
        """
        self.db_client = db_client
    
    def analyze(self, user_id: str) -> Dict:
        """
        Perform comprehensive goal analysis.
        
        Args:
            user_id: User ID from Cognito
            
        Returns:
            Dictionary containing goal metrics and projections
        """
        logger.info(f"Analyzing goals for user {user_id}")
        
        # Fetch goals and institutions
        goals = self.db_client.get_goals(user_id)
        institutions = self.db_client.get_institutions(user_id)
        
        if not goals:
            logger.warning(f"No goals found for user {user_id}")
            return self._generate_empty_response()
        
        # Calculate metrics for each goal
        goal_details = []
        total_target = 0
        total_current = 0
        completed_count = 0
        active_count = 0
        
        for goal in goals:
            details = self._analyze_single_goal(goal, institutions)
            goal_details.append(details)
            
            total_target += goal.target_amount
            total_current += details['current_amount']
            
            if goal.is_completed:
                completed_count += 1
            if goal.is_active:
                active_count += 1
        
        # Calculate overall progress
        overall_progress = (total_current / total_target * 100) if total_target > 0 else 0
        
        # Identify goals at risk
        at_risk_goals = self._identify_at_risk_goals(goal_details)
        
        # Identify goals near completion
        near_completion = [g for g in goal_details if g['progress_percent'] >= 90 and not g['is_completed']]
        
        # Calculate priority recommendations
        priorities = self._calculate_goal_priorities(goal_details)
        
        result = {
            'user_id': user_id,
            'summary': {
                'total_goals': len(goals),
                'active_goals': active_count,
                'completed_goals': completed_count,
                'total_target_amount': round(total_target, 2),
                'total_current_amount': round(total_current, 2),
                'overall_progress': round(overall_progress, 2)
            },
            'goals': goal_details,
            'insights': {
                'at_risk': at_risk_goals,
                'near_completion': near_completion,
                'priorities': priorities
            }
        }
        
        logger.info(f"Goal analysis complete: {len(goals)} goals analyzed")
        return result
    
    def _analyze_single_goal(self, goal: Goal, institutions: List[Institution]) -> Dict:
        """
        Analyze a single goal in detail.
        
        Args:
            goal: Goal object
            institutions: List of user's institutions
            
        Returns:
            Dictionary with goal analysis
        """
        # Inactive goals are treated as 100% complete regardless of actual balance.
        # They have been closed/deactivated so should not show as 0% on charts.
        if not goal.is_active:
            current_amount = goal.target_amount
            progress_percent = 100.0
            remaining_amount = 0.0
        else:
            current_amount = goal.calculate_current_amount(institutions)
            progress_percent = goal.calculate_progress_percent(institutions)
            remaining_amount = goal.calculate_remaining_amount(institutions)
        
        # Calculate time metrics
        current_ts = date_utils.get_current_timestamp()
        days_since_creation = date_utils.get_days_between(goal.created_at, current_ts)
        
        # Estimate completion time
        if goal.is_completed:
            days_to_completion = date_utils.get_days_between(goal.created_at, goal.completed_at)
            estimated_completion_date = None
        else:
            days_to_completion = None
            if days_since_creation > 0 and current_amount > 0:
                # Calculate growth rate and project completion
                daily_growth_rate = current_amount / days_since_creation
                if daily_growth_rate > 0:
                    days_remaining = remaining_amount / daily_growth_rate
                    estimated_completion_ts = date_utils.add_days(current_ts, int(days_remaining))
                    estimated_completion_date = date_utils.format_date(estimated_completion_ts)
                else:
                    estimated_completion_date = None
            else:
                estimated_completion_date = None
        
        # Calculate required monthly contribution
        if not goal.is_completed and remaining_amount > 0:
            # Calculate based on current progress rate, default to 6 months if no progress
            if days_since_creation > 0 and current_amount > 0:
                daily_growth_rate = current_amount / days_since_creation
                if daily_growth_rate > 0:
                    days_to_completion = remaining_amount / daily_growth_rate
                    months_to_target = max(days_to_completion / 30, 1)  # At least 1 month
                else:
                    months_to_target = 6  # Default to 6 months if no growth
            else:
                months_to_target = 6  # Default to 6 months for new goals
            required_monthly = remaining_amount / months_to_target
        else:
            required_monthly = 0
        
        # Get allocation details
        allocations = []
        for inst_id, percent in goal.linked_institutions.items():
            institution = next((i for i in institutions if i.institution_id == inst_id), None)
            if institution:
                allocated_amount = (institution.current_balance * percent) / 100
                allocations.append({
                    'institution_name': institution.institution_name,
                    'institution_id': inst_id,
                    'allocation_percent': percent,
                    'allocated_amount': round(allocated_amount, 2)
                })
        
        return {
            'goal_id': goal.goal_id,
            'name': goal.name,
            'description': goal.description,
            'target_amount': round(goal.target_amount, 2),
            'current_amount': round(current_amount, 2),
            'remaining_amount': round(remaining_amount, 2),
            'progress_percent': round(progress_percent, 2),
            'is_completed': goal.is_completed,
            'is_active': goal.is_active,
            'created_at': date_utils.timestamp_to_iso(goal.created_at),
            'completed_at': date_utils.timestamp_to_iso(goal.completed_at) if goal.completed_at else None,
            'days_since_creation': days_since_creation,
            'days_to_completion': days_to_completion,
            'estimated_completion_date': estimated_completion_date,
            'required_monthly_contribution': round(required_monthly, 2),
            'allocations': allocations,
            'total_allocation_percent': goal.total_allocated_percent
        }
    
    def _identify_at_risk_goals(self, goal_details: List[Dict]) -> List[Dict]:
        """
        Identify goals that are at risk of not being completed.
        
        Args:
            goal_details: List of goal detail dictionaries
            
        Returns:
            List of at-risk goal summaries
        """
        at_risk = []
        
        for goal in goal_details:
            if goal['is_completed'] or not goal['is_active']:
                continue
            
            # Risk factors:
            # 1. Low progress after significant time (< 25% after 30+ days)
            # 2. No estimated completion date (no growth)
            # 3. Under-allocated (< 50% of target allocated)
            
            risk_score = 0
            risk_reasons = []
            
            if goal['days_since_creation'] > 30 and goal['progress_percent'] < 25:
                risk_score += 3
                risk_reasons.append('Slow progress')
            
            if goal['estimated_completion_date'] is None:
                risk_score += 2
                risk_reasons.append('No growth detected')
            
            if goal['total_allocation_percent'] < 50:
                risk_score += 1
                risk_reasons.append('Under-allocated')
            
            if risk_score >= 2:
                at_risk.append({
                    'goal_id': goal['goal_id'],
                    'name': goal['name'],
                    'progress_percent': goal['progress_percent'],
                    'risk_score': risk_score,
                    'risk_reasons': risk_reasons,
                    'recommendation': self._generate_risk_recommendation(risk_reasons)
                })
        
        # Sort by risk score
        at_risk.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return at_risk
    
    def _generate_risk_recommendation(self, risk_reasons: List[str]) -> str:
        """Generate recommendation based on risk factors."""
        if 'No growth detected' in risk_reasons:
            return 'Increase allocation percentages to this goal'
        elif 'Under-allocated' in risk_reasons:
            return 'Link more institutions or increase allocation percentages'
        elif 'Slow progress' in risk_reasons:
            return 'Consider increasing monthly contributions'
        else:
            return 'Review goal target and timeline'
    
    def _calculate_goal_priorities(self, goal_details: List[Dict]) -> List[Dict]:
        """
        Calculate priority ranking for goals.
        
        Args:
            goal_details: List of goal detail dictionaries
            
        Returns:
            List of goals ranked by priority
        """
        priorities = []
        
        for goal in goal_details:
            if goal['is_completed'] or not goal['is_active']:
                continue
            
            # Priority factors:
            # 1. Proximity to completion (80-95% = highest priority)
            # 2. Required monthly contribution (lower = easier to complete)
            # 3. Days since creation (older = higher priority)
            
            priority_score = 0
            
            # Near completion bonus
            if 80 <= goal['progress_percent'] < 95:
                priority_score += 10
            elif 60 <= goal['progress_percent'] < 80:
                priority_score += 7
            elif 40 <= goal['progress_percent'] < 60:
                priority_score += 5
            
            # Age factor (1 point per 30 days, max 5 points)
            age_score = min(goal['days_since_creation'] // 30, 5)
            priority_score += age_score
            
            # Feasibility (inverse of required monthly contribution)
            if goal['required_monthly_contribution'] > 0:
                # Lower contribution = higher priority
                if goal['required_monthly_contribution'] < 100:
                    priority_score += 3
                elif goal['required_monthly_contribution'] < 500:
                    priority_score += 2
                elif goal['required_monthly_contribution'] < 1000:
                    priority_score += 1
            
            priorities.append({
                'goal_id': goal['goal_id'],
                'name': goal['name'],
                'priority_score': priority_score,
                'progress_percent': goal['progress_percent'],
                'remaining_amount': goal['remaining_amount'],
                'estimated_completion_date': goal['estimated_completion_date']
            })
        
        # Sort by priority score
        priorities.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return priorities
    
    def compare_goals(self, user_id: str, goal_id1: str, goal_id2: str) -> Dict:
        """
        Compare two goals side by side.
        
        Args:
            user_id: User ID from Cognito
            goal_id1: First goal ID
            goal_id2: Second goal ID
            
        Returns:
            Dictionary containing comparison metrics
        """
        logger.info(f"Comparing goals {goal_id1} and {goal_id2} for user {user_id}")
        
        # Fetch goals
        goal1 = self.db_client.get_goal(user_id, goal_id1)
        goal2 = self.db_client.get_goal(user_id, goal_id2)
        
        if not goal1 or not goal2:
            raise ValueError("One or both goals not found")
        
        # Get institutions
        institutions = self.db_client.get_institutions(user_id)
        
        # Analyze both goals
        goal1_details = self._analyze_single_goal(goal1, institutions)
        goal2_details = self._analyze_single_goal(goal2, institutions)
        
        return {
            'goal1': goal1_details,
            'goal2': goal2_details,
            'comparison': {
                'progress_difference': round(
                    goal1_details['progress_percent'] - goal2_details['progress_percent'],
                    2
                ),
                'target_difference': round(
                    goal1_details['target_amount'] - goal2_details['target_amount'],
                    2
                ),
                'faster_completion': goal1_details['name'] 
                    if goal1_details.get('estimated_completion_date') and 
                       (not goal2_details.get('estimated_completion_date') or
                        goal1_details['estimated_completion_date'] < goal2_details['estimated_completion_date'])
                    else goal2_details['name']
            }
        }
    
    def calculate_reallocation_strategy(self, user_id: str, goal_id: str) -> Dict:
        """
        Suggest optimal allocation strategy for a goal.
        
        Args:
            user_id: User ID from Cognito
            goal_id: Goal ID to optimize
            
        Returns:
            Dictionary with reallocation recommendations
        """
        logger.info(f"Calculating reallocation strategy for goal {goal_id}")
        
        # Fetch goal and institutions
        goal = self.db_client.get_goal(user_id, goal_id)
        if not goal:
            raise ValueError("Goal not found")
        
        institutions = self.db_client.get_institutions(user_id)
        
        # Current allocation
        current_details = self._analyze_single_goal(goal, institutions)
        
        # Calculate optimal allocation (proportional to balance)
        total_balance = sum(inst.current_balance for inst in institutions)
        
        recommended_allocations = []
        for inst in institutions:
            if total_balance > 0:
                optimal_percent = int((inst.current_balance / total_balance) * 100)
                current_percent = goal.linked_institutions.get(inst.institution_id, 0)
                
                recommended_allocations.append({
                    'institution_id': inst.institution_id,
                    'institution_name': inst.institution_name,
                    'current_balance': round(inst.current_balance, 2),
                    'current_allocation': current_percent,
                    'recommended_allocation': optimal_percent,
                    'change': optimal_percent - current_percent
                })
        
        return {
            'goal_id': goal_id,
            'goal_name': goal.name,
            'current_progress': current_details['progress_percent'],
            'current_total_allocation': goal.total_allocated_percent,
            'recommendations': recommended_allocations
        }
    
    def _generate_empty_response(self) -> Dict:
        """Generate empty response when no goals exist."""
        return {
            'summary': {
                'total_goals': 0,
                'active_goals': 0,
                'completed_goals': 0
            },
            'goals': [],
            'insights': {
                'at_risk': [],
                'near_completion': [],
                'priorities': []
            },
            'message': 'No goals found'
        }
