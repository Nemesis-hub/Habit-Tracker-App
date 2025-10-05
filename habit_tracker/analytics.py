"""
Analytics functions for habit tracking.
All functions are pure and side-effect free.
"""

from typing import List, Dict, Tuple, Optional
from datetime import datetime, date

from .models import Habit, Periodicity


def list_all_habits(habits: List[Habit]) -> List[Habit]:
    """
    List all habits.
    
    Args:
        habits: List of habit objects
        
    Returns:
        List of all habits (sorted by creation date)
    """
    return sorted(habits, key=lambda h: h.created_at)


def list_habits_by_periodicity(habits: List[Habit], periodicity: Periodicity) -> List[Habit]:
    """
    List habits filtered by periodicity.
    
    Args:
        habits: List of habit objects
        periodicity: The periodicity to filter by
        
    Returns:
        List of habits with the specified periodicity (sorted by creation date)
    """
    return sorted([h for h in habits if h.periodicity == periodicity], 
                  key=lambda h: h.created_at)


def get_longest_streak_overall(habits: List[Habit]) -> Tuple[Optional[Habit], int]:
    """
    Find the habit with the longest streak overall.
    
    Args:
        habits: List of habit objects
        
    Returns:
        Tuple of (habit with longest streak, streak length)
        Returns (None, 0) if no habits exist
    """
    if not habits:
        return None, 0
    
    longest_streak = 0
    habit_with_longest_streak = None
    
    for habit in habits:
        streak = habit.get_longest_streak()
        if streak > longest_streak:
            longest_streak = streak
            habit_with_longest_streak = habit
    
    return habit_with_longest_streak, longest_streak


def get_longest_streak_per_habit(habits: List[Habit]) -> Dict[str, int]:
    """
    Get the longest streak for each habit.
    
    Args:
        habits: List of habit objects
        
    Returns:
        Dictionary mapping habit names to their longest streak lengths
    """
    return {habit.name: habit.get_longest_streak() for habit in habits}


def get_current_streaks(habits: List[Habit]) -> Dict[str, int]:
    """
    Get the current streak for each habit.
    
    Args:
        habits: List of habit objects
        
    Returns:
        Dictionary mapping habit names to their current streak lengths
    """
    return {habit.name: habit.get_current_streak() for habit in habits}


def get_habits_with_streak_above(habits: List[Habit], min_streak: int) -> List[Habit]:
    """
    Get habits with current streak above a minimum threshold.
    
    Args:
        habits: List of habit objects
        min_streak: Minimum streak length
        
    Returns:
        List of habits with current streak >= min_streak
    """
    return [habit for habit in habits if habit.get_current_streak() >= min_streak]


def get_habits_without_recent_activity(habits: List[Habit], days: int = 7) -> List[Habit]:
    """
    Get habits that haven't been checked off in the last N days.
    
    Args:
        habits: List of habit objects
        days: Number of days to look back
        
    Returns:
        List of habits without recent activity
    """
    from datetime import timedelta
    cutoff_date = date.today() - timedelta(days=days)
    inactive_habits = []
    
    for habit in habits:
        if not habit.check_offs:
            inactive_habits.append(habit)
            continue
        
        # Get the most recent check-off
        most_recent = max(habit.check_offs, key=lambda x: x.date())
        
        if most_recent.date() < cutoff_date:
            inactive_habits.append(habit)
    
    return inactive_habits


def get_completion_rate_by_periodicity(habits: List[Habit]) -> Dict[str, float]:
    """
    Calculate completion rate by periodicity.
    
    Args:
        habits: List of habit objects
        
    Returns:
        Dictionary mapping periodicity to completion rate (0.0 to 1.0)
    """
    periodicity_stats = {}
    
    for periodicity in Periodicity:
        period_habits = list_habits_by_periodicity(habits, periodicity)
        if not period_habits:
            periodicity_stats[periodicity.value] = 0.0
            continue
        
        total_expected = 0
        total_completed = 0
        
        for habit in period_habits:
            if periodicity == Periodicity.DAILY:
                # Calculate expected days since creation
                days_since_creation = (date.today() - habit.created_at.date()).days + 1
                total_expected += days_since_creation
            elif periodicity == Periodicity.WEEKLY:
                # Calculate expected weeks since creation
                weeks_since_creation = ((date.today() - habit.created_at.date()).days // 7) + 1
                total_expected += weeks_since_creation
            
            total_completed += len(habit.check_offs)
        
        completion_rate = total_completed / total_expected if total_expected > 0 else 0.0
        # Cap completion rate at 1.0 to avoid values > 100%
        periodicity_stats[periodicity.value] = min(completion_rate, 1.0)
    
    return periodicity_stats


def get_habit_statistics(habits: List[Habit]) -> Dict[str, any]:
    """
    Get comprehensive statistics for all habits.
    
    Args:
        habits: List of habit objects
        
    Returns:
        Dictionary containing various statistics
    """
    if not habits:
        return {
            'total_habits': 0,
            'daily_habits': 0,
            'weekly_habits': 0,
            'total_check_offs': 0,
            'average_check_offs_per_habit': 0.0,
            'longest_streak_overall': 0,
            'habits_with_current_streak': 0
        }
    
    daily_habits = len(list_habits_by_periodicity(habits, Periodicity.DAILY))
    weekly_habits = len(list_habits_by_periodicity(habits, Periodicity.WEEKLY))
    total_check_offs = sum(len(habit.check_offs) for habit in habits)
    
    _, longest_streak = get_longest_streak_overall(habits)
    current_streaks = get_current_streaks(habits)
    habits_with_streak = len([s for s in current_streaks.values() if s > 0])
    
    return {
        'total_habits': len(habits),
        'daily_habits': daily_habits,
        'weekly_habits': weekly_habits,
        'total_check_offs': total_check_offs,
        'average_check_offs_per_habit': total_check_offs / len(habits),
        'longest_streak_overall': longest_streak,
        'habits_with_current_streak': habits_with_streak,
        'completion_rates': get_completion_rate_by_periodicity(habits)
    }


def filter_habits_by_date_range(habits: List[Habit], start_date: date, end_date: date) -> List[Habit]:
    """
    Filter habits that were created within a date range.
    
    Args:
        habits: List of habit objects
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        
    Returns:
        List of habits created within the date range
    """
    return [habit for habit in habits 
            if start_date <= habit.created_at.date() <= end_date]


def get_most_active_habits(habits: List[Habit], limit: int = 5) -> List[Tuple[Habit, int]]:
    """
    Get the most active habits by check-off count.
    
    Args:
        habits: List of habit objects
        limit: Maximum number of habits to return
        
    Returns:
        List of tuples (habit, check_off_count) sorted by activity
    """
    habit_activity = [(habit, len(habit.check_offs)) for habit in habits]
    return sorted(habit_activity, key=lambda x: x[1], reverse=True)[:limit]
