"""
Sample data for the habit tracker application.
Contains predefined habits with 4 weeks of sample check-off data.
"""

from datetime import datetime, date, timedelta
from typing import List

from .models import Habit, Periodicity
from .persistence import HabitRepository


def create_sample_habits() -> List[Habit]:
    """
    Create the 5 predefined habits with sample data.
    
    Returns:
        List of habits with 4 weeks of sample check-off data
    """
    # Create the 5 predefined habits
    habits = [
        Habit("Brush teeth", Periodicity.DAILY),
        Habit("Exercise", Periodicity.DAILY),
        Habit("Read", Periodicity.DAILY),
        Habit("Grocery shop", Periodicity.WEEKLY),
        Habit("Clean house", Periodicity.WEEKLY)
    ]
    
    # Generate 4 weeks of sample data (starting from 4 weeks ago)
    start_date = date.today() - timedelta(weeks=4)
    
    # Add sample check-offs for daily habits
    for habit in habits[:3]:  # First 3 are daily habits
        current_date = start_date
        while current_date <= date.today():
            # Simulate realistic check-off patterns (not every day)
            if _should_check_off_daily(current_date):
                check_off_time = datetime.combine(current_date, datetime.min.time().replace(hour=8))
                habit.add_check_off(check_off_time)
            current_date += timedelta(days=1)
    
    # Add sample check-offs for weekly habits
    for habit in habits[3:]:  # Last 2 are weekly habits
        current_date = start_date
        while current_date <= date.today():
            # Check if this is a week boundary (Monday)
            if current_date.weekday() == 0:  # Monday
                if _should_check_off_weekly(current_date):
                    check_off_time = datetime.combine(current_date, datetime.min.time().replace(hour=10))
                    habit.add_check_off(check_off_time)
            current_date += timedelta(days=1)
    
    return habits


def _should_check_off_daily(check_date: date) -> bool:
    """
    Determine if a daily habit should be checked off on a given date.
    Simulates realistic patterns (weekends less likely, some random misses).
    
    Args:
        check_date: The date to check
        
    Returns:
        True if the habit should be checked off, False otherwise
    """
    # Weekend check-off rate is lower
    if check_date.weekday() >= 5:  # Saturday or Sunday
        return check_date.day % 3 != 0  # 66% chance on weekends
    
    # Weekday check-off rate is higher
    return check_date.day % 5 != 0  # 80% chance on weekdays


def _should_check_off_weekly(check_date: date) -> bool:
    """
    Determine if a weekly habit should be checked off on a given week.
    Simulates realistic patterns (some weeks might be missed).
    
    Args:
        check_date: The date to check (should be a Monday)
        
    Returns:
        True if the habit should be checked off, False otherwise
    """
    # 85% chance of checking off weekly habits
    return check_date.day % 7 != 0


def populate_sample_data(repository: HabitRepository) -> None:
    """
    Populate the repository with sample data.
    
    Args:
        repository: The repository to populate
    """
    # Check if data already exists
    existing_habits = repository.get_all_habits()
    if existing_habits:
        print("⚠️  Repository already contains habits. Skipping sample data population.")
        return
    
    # Create and save sample habits
    sample_habits = create_sample_habits()
    
    for habit in sample_habits:
        repository.create_habit(habit)
    
    print(f"✅ Populated repository with {len(sample_habits)} sample habits:")
    for habit in sample_habits:
        print(f"   • {habit.name} ({habit.periodicity.value}) - {len(habit.check_offs)} check-offs")


def get_sample_habit_summary() -> str:
    """
    Get a summary of the sample habits and their data.
    
    Returns:
        String summary of sample habits
    """
    habits = create_sample_habits()
    
    summary = "Sample Habits Summary:\n"
    summary += "=" * 50 + "\n"
    
    for habit in habits:
        current_streak = habit.get_current_streak()
        longest_streak = habit.get_longest_streak()
        summary += f"{habit.name} ({habit.periodicity.value}):\n"
        summary += f"  • Check-offs: {len(habit.check_offs)}\n"
        summary += f"  • Current streak: {current_streak}\n"
        summary += f"  • Longest streak: {longest_streak}\n"
        summary += f"  • Created: {habit.created_at.strftime('%Y-%m-%d')}\n"
        summary += "\n"
    
    return summary


# Sample data for testing
SAMPLE_HABIT_DATA = [
    {
        "name": "Brush teeth",
        "periodicity": "daily",
        "expected_check_offs": 20,  # Approximate for 4 weeks
        "description": "Daily dental hygiene habit"
    },
    {
        "name": "Exercise",
        "periodicity": "daily", 
        "expected_check_offs": 18,  # Slightly less consistent
        "description": "Daily physical activity"
    },
    {
        "name": "Read",
        "periodicity": "daily",
        "expected_check_offs": 22,  # Most consistent
        "description": "Daily reading habit"
    },
    {
        "name": "Grocery shop",
        "periodicity": "weekly",
        "expected_check_offs": 3,  # 3-4 weeks
        "description": "Weekly grocery shopping"
    },
    {
        "name": "Clean house",
        "periodicity": "weekly",
        "expected_check_offs": 3,  # 3-4 weeks
        "description": "Weekly house cleaning"
    }
]
