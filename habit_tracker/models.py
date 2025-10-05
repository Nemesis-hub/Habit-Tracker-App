"""
Habit model classes for the habit tracker application.
"""

from datetime import datetime, date, timedelta
from typing import List, Optional
from enum import Enum


class Periodicity(Enum):
    """Enumeration for habit periodicity."""
    DAILY = "daily"
    WEEKLY = "weekly"


class Habit:
    """
    A habit represents a task that can be tracked with check-offs.
    
    Attributes:
        id: Unique identifier for the habit
        name: Name of the habit
        periodicity: How often the habit should be performed (daily/weekly)
        created_at: When the habit was created
        check_offs: List of timestamps when the habit was completed
    """
    
    def __init__(self, name: str, periodicity: Periodicity, habit_id: Optional[str] = None):
        """
        Initialize a new habit.
        
        Args:
            name: Name of the habit
            periodicity: How often the habit should be performed
            habit_id: Optional unique identifier (generated if not provided)
        """
        self.id = habit_id or self._generate_id()
        self.name = name
        self.periodicity = periodicity
        self.created_at = datetime.now()
        self.check_offs: List[datetime] = []
    
    def _generate_id(self) -> str:
        """Generate a unique ID for the habit."""
        import time
        import random
        timestamp = int(time.time() * 1000000)  # microseconds for better uniqueness
        random_part = random.randint(1000, 9999)
        return f"habit_{timestamp}_{random_part}"
    
    def add_check_off(self, check_off_time: Optional[datetime] = None) -> None:
        """
        Add a check-off for this habit.
        
        Args:
            check_off_time: When the habit was completed (defaults to now)
        """
        if check_off_time is None:
            check_off_time = datetime.now()
        
        # Avoid duplicate check-offs for the same day/week
        if not self._is_duplicate_check_off(check_off_time):
            self.check_offs.append(check_off_time)
            self.check_offs.sort()  # Keep check-offs sorted by time
    
    def _is_duplicate_check_off(self, check_off_time: datetime) -> bool:
        """
        Check if a check-off already exists for the same period.
        
        Args:
            check_off_time: The time to check for duplicates
            
        Returns:
            True if a duplicate check-off exists, False otherwise
        """
        check_off_date = check_off_time.date()
        
        for existing_check_off in self.check_offs:
            existing_date = existing_check_off.date()
            
            if self.periodicity == Periodicity.DAILY:
                if check_off_date == existing_date:
                    return True
            elif self.periodicity == Periodicity.WEEKLY:
                # Check if both dates are in the same week
                if self._same_week(check_off_date, existing_date):
                    return True
        
        return False
    
    def _same_week(self, date1: date, date2: date) -> bool:
        """
        Check if two dates are in the same week.
        
        Args:
            date1: First date
            date2: Second date
            
        Returns:
            True if both dates are in the same week, False otherwise
        """
        # Get the Monday of the week for each date
        monday1 = date1 - timedelta(days=date1.weekday())
        monday2 = date2 - timedelta(days=date2.weekday())
        return monday1 == monday2
    
    def get_current_streak(self) -> int:
        """
        Calculate the current streak for this habit.
        
        Returns:
            The current streak count
        """
        if not self.check_offs:
            return 0
        
        # Sort check-offs in descending order (most recent first)
        sorted_check_offs = sorted(self.check_offs, reverse=True)
        current_streak = 0
        current_date = date.today()
        
        for check_off in sorted_check_offs:
            check_off_date = check_off.date()
            
            if self.periodicity == Periodicity.DAILY:
                if check_off_date == current_date:
                    current_streak += 1
                    current_date = current_date - timedelta(days=1)
                elif check_off_date < current_date:
                    break
            elif self.periodicity == Periodicity.WEEKLY:
                if self._same_week(check_off_date, current_date):
                    current_streak += 1
                    # Move to previous week
                    current_date = current_date - timedelta(weeks=1)
                elif check_off_date < current_date:
                    break
        
        return current_streak
    
    def get_longest_streak(self) -> int:
        """
        Calculate the longest streak for this habit.
        
        Returns:
            The longest streak count
        """
        if not self.check_offs:
            return 0
        
        sorted_check_offs = sorted(self.check_offs)
        longest_streak = 0
        current_streak = 0
        previous_date = None
        
        for check_off in sorted_check_offs:
            check_off_date = check_off.date()
            
            if previous_date is None:
                current_streak = 1
            else:
                if self.periodicity == Periodicity.DAILY:
                    # Check if this is the next consecutive day
                    if (check_off_date - previous_date).days == 1:
                        current_streak += 1
                    else:
                        longest_streak = max(longest_streak, current_streak)
                        current_streak = 1
                elif self.periodicity == Periodicity.WEEKLY:
                    # Check if this is the next consecutive week
                    if self._is_next_week(previous_date, check_off_date):
                        current_streak += 1
                    else:
                        longest_streak = max(longest_streak, current_streak)
                        current_streak = 1
            
            previous_date = check_off_date
        
        return max(longest_streak, current_streak)
    
    def _is_next_week(self, date1: date, date2: date) -> bool:
        """
        Check if date2 is in the week immediately following date1.
        
        Args:
            date1: First date
            date2: Second date
            
        Returns:
            True if date2 is in the next week, False otherwise
        """
        monday1 = date1 - timedelta(days=date1.weekday())
        monday2 = date2 - timedelta(days=date2.weekday())
        return (monday2 - monday1).days == 7
    
    def to_dict(self) -> dict:
        """
        Convert the habit to a dictionary for serialization.
        
        Returns:
            Dictionary representation of the habit
        """
        return {
            'id': self.id,
            'name': self.name,
            'periodicity': self.periodicity.value,
            'created_at': self.created_at.isoformat(),
            'check_offs': [check_off.isoformat() for check_off in self.check_offs]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Habit':
        """
        Create a habit from a dictionary.
        
        Args:
            data: Dictionary containing habit data
            
        Returns:
            Habit instance
        """
        habit = cls(
            name=data['name'],
            periodicity=Periodicity(data['periodicity']),
            habit_id=data['id']
        )
        habit.created_at = datetime.fromisoformat(data['created_at'])
        habit.check_offs = [datetime.fromisoformat(check_off) for check_off in data['check_offs']]
        return habit
    
    def __str__(self) -> str:
        """String representation of the habit."""
        return f"Habit(id={self.id}, name='{self.name}', periodicity={self.periodicity.value})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the habit."""
        return (f"Habit(id={self.id}, name='{self.name}', periodicity={self.periodicity.value}, "
                f"created_at={self.created_at}, check_offs_count={len(self.check_offs)})")
