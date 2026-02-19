"""Data models for analytics entities."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class Institution:
    """Financial institution data model."""
    
    user_id: str
    institution_id: str
    institution_name: str
    starting_balance: float
    current_balance: float
    created_at: int  # UNIX timestamp
    allocated_percent: Optional[int] = None
    linked_goals: List[str] = field(default_factory=list)
    
    @property
    def balance_change(self) -> float:
        """Calculate change from starting balance."""
        return self.current_balance - self.starting_balance
    
    @property
    def growth_rate(self) -> float:
        """Calculate percentage growth rate."""
        if self.starting_balance == 0:
            return 0.0
        return (self.balance_change / self.starting_balance) * 100


@dataclass
class Transaction:
    """Transaction data model."""
    
    institution_id: str
    created_at: int  # UNIX timestamp (sort key)
    transaction_id: str
    user_id: str
    type: str  # DEPOSIT or WITHDRAWAL
    amount: float
    transaction_date: int  # UNIX timestamp (when it occurred)
    tags: List[str] = field(default_factory=list)
    description: Optional[str] = None
    
    @property
    def is_deposit(self) -> bool:
        """Check if transaction is a deposit."""
        return self.type == "DEPOSIT"
    
    @property
    def is_withdrawal(self) -> bool:
        """Check if transaction is a withdrawal."""
        return self.type == "WITHDRAWAL"
    
    @property
    def signed_amount(self) -> float:
        """Return amount with sign (+/-)."""
        return self.amount if self.is_deposit else -self.amount


@dataclass
class Goal:
    """Financial goal data model."""
    
    user_id: str
    goal_id: str
    name: str
    target_amount: float
    created_at: int  # UNIX timestamp
    is_completed: bool = False
    is_active: bool = True
    description: Optional[str] = None
    linked_institutions: Dict[str, int] = field(default_factory=dict)  # {institution_id: percent}
    linked_transactions: List[str] = field(default_factory=list)
    completed_at: Optional[int] = None
    
    @property
    def total_allocated_percent(self) -> int:
        """Calculate total allocation percentage."""
        return sum(self.linked_institutions.values())
    
    def calculate_current_amount(self, institutions: List[Institution]) -> float:
        """Calculate current amount toward goal based on linked institutions."""
        total = 0.0
        inst_dict = {inst.institution_id: inst for inst in institutions}
        
        for inst_id, percent in self.linked_institutions.items():
            if inst_id in inst_dict:
                institution = inst_dict[inst_id]
                allocated_amount = (institution.current_balance * percent) / 100
                total += allocated_amount
        
        return total
    
    def calculate_progress_percent(self, institutions: List[Institution]) -> float:
        """Calculate progress percentage toward goal."""
        if self.target_amount == 0:
            return 0.0
        current = self.calculate_current_amount(institutions)
        return min((current / self.target_amount) * 100, 100.0)
    
    def calculate_remaining_amount(self, institutions: List[Institution]) -> float:
        """Calculate remaining amount needed to reach goal."""
        current = self.calculate_current_amount(institutions)
        return max(self.target_amount - current, 0.0)


@dataclass
class AnalyticsRequest:
    """Request model for analytics generation."""
    
    user_id: str
    analytics_type: str
    start_date: str  # ISO format: YYYY-MM-DD
    end_date: str    # ISO format: YYYY-MM-DD
    include_visualizations: bool = True
    output_format: str = "json"  # json, html, pdf
    
    def get_start_timestamp(self) -> int:
        """Convert start_date to UNIX timestamp."""
        dt = datetime.fromisoformat(self.start_date)
        return int(dt.timestamp())
    
    def get_end_timestamp(self) -> int:
        """Convert end_date to UNIX timestamp."""
        dt = datetime.fromisoformat(self.end_date)
        return int(dt.timestamp())


@dataclass
class AnalyticsResponse:
    """Response model for analytics results."""
    
    analytics_type: str
    user_id: str
    generated_at: str  # ISO format timestamp
    data: Dict
    visualizations: List[Dict] = field(default_factory=list)
    error: Optional[str] = None
    
    def add_visualization(self, viz_type: str, title: str, url: str):
        """Add a visualization to the response."""
        self.visualizations.append({
            "type": viz_type,
            "title": title,
            "url": url
        })
