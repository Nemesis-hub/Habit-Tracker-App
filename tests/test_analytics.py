"""
Tests for the analytics functions.
"""

import pytest
from datetime import datetime, date, timedelta

from habit_tracker.models import Habit, Periodicity
from habit_tracker.analytics import (
    list_all_habits,
    list_habits_by_periodicity,
    get_longest_streak_overall,
    get_longest_streak_per_habit,
    get_current_streaks,
    get_habit_statistics,
    get_habits_with_streak_above,
    get_habits_without_recent_activity,
    get_completion_rate_by_periodicity,
    filter_habits_by_date_range,
    get_most_active_habits
)


class TestAnalytics:
    """Test cases for analytics functions."""
    
    @pytest.fixture
    def sample_habits(self):
        """Create sample habits for testing."""
        habits = []
        
        # Daily habit with good streak
        daily_habit = Habit("Exercise", Periodicity.DAILY)
        today = date.today()
        for i in range(5):  # 5-day streak
            check_date = today - timedelta(days=i)
            check_time = datetime.combine(check_date, datetime.min.time())
            daily_habit.add_check_off(check_time)
        habits.append(daily_habit)
        
        # Weekly habit with moderate streak
        weekly_habit = Habit("Grocery shop", Periodicity.WEEKLY)
        current_week = today - timedelta(days=today.weekday())
        for i in range(3):  # 3-week streak
            week_monday = current_week - timedelta(weeks=i)
            check_time = datetime.combine(week_monday, datetime.min.time())
            weekly_habit.add_check_off(check_time)
        habits.append(weekly_habit)
        
        # Daily habit with no recent activity
        inactive_habit = Habit("Read", Periodicity.DAILY)
        old_date = today - timedelta(days=10)
        check_time = datetime.combine(old_date, datetime.min.time())
        inactive_habit.add_check_off(check_time)
        habits.append(inactive_habit)
        
        return habits
    
    def test_list_all_habits(self, sample_habits):
        """Test listing all habits."""
        result = list_all_habits(sample_habits)
        
        assert len(result) == 3
        # Should be sorted by creation date
        assert result[0].name == "Exercise"
        assert result[1].name == "Grocery shop"
        assert result[2].name == "Read"
    
    def test_list_habits_by_periodicity(self, sample_habits):
        """Test filtering habits by periodicity."""
        daily_habits = list_habits_by_periodicity(sample_habits, Periodicity.DAILY)
        weekly_habits = list_habits_by_periodicity(sample_habits, Periodicity.WEEKLY)
        
        assert len(daily_habits) == 2
        assert len(weekly_habits) == 1
        
        assert all(h.periodicity == Periodicity.DAILY for h in daily_habits)
        assert all(h.periodicity == Periodicity.WEEKLY for h in weekly_habits)
    
    def test_get_longest_streak_overall(self, sample_habits):
        """Test finding the habit with longest streak overall."""
        habit, streak = get_longest_streak_overall(sample_habits)
        
        assert habit.name == "Exercise"
        assert streak == 5
    
    def test_get_longest_streak_overall_empty(self):
        """Test longest streak with no habits."""
        habit, streak = get_longest_streak_overall([])
        
        assert habit is None
        assert streak == 0
    
    def test_get_longest_streak_per_habit(self, sample_habits):
        """Test getting longest streak for each habit."""
        streaks = get_longest_streak_per_habit(sample_habits)
        
        assert streaks["Exercise"] == 5
        assert streaks["Grocery shop"] == 3
        assert streaks["Read"] == 1
    
    def test_get_current_streaks(self, sample_habits):
        """Test getting current streaks for each habit."""
        streaks = get_current_streaks(sample_habits)
        
        assert streaks["Exercise"] == 5
        assert streaks["Grocery shop"] == 3
        assert streaks["Read"] == 0  # No recent activity
    
    def test_get_habits_with_streak_above(self, sample_habits):
        """Test filtering habits by minimum streak."""
        high_streak_habits = get_habits_with_streak_above(sample_habits, 4)
        moderate_streak_habits = get_habits_with_streak_above(sample_habits, 2)
        
        assert len(high_streak_habits) == 1
        assert high_streak_habits[0].name == "Exercise"
        
        assert len(moderate_streak_habits) == 2
        assert any(h.name == "Exercise" for h in moderate_streak_habits)
        assert any(h.name == "Grocery shop" for h in moderate_streak_habits)
    
    def test_get_habits_without_recent_activity(self, sample_habits):
        """Test finding habits without recent activity."""
        inactive_habits = get_habits_without_recent_activity(sample_habits, days=7)
        
        assert len(inactive_habits) == 1
        assert inactive_habits[0].name == "Read"
    
    def test_get_completion_rate_by_periodicity(self, sample_habits):
        """Test calculating completion rates by periodicity."""
        rates = get_completion_rate_by_periodicity(sample_habits)
        
        assert "daily" in rates
        assert "weekly" in rates
        assert 0.0 <= rates["daily"] <= 1.0
        assert 0.0 <= rates["weekly"] <= 1.0
    
    def test_get_habit_statistics(self, sample_habits):
        """Test comprehensive habit statistics."""
        stats = get_habit_statistics(sample_habits)
        
        assert stats['total_habits'] == 3
        assert stats['daily_habits'] == 2
        assert stats['weekly_habits'] == 1
        assert stats['total_check_offs'] == 9  # 5 + 3 + 1
        assert stats['average_check_offs_per_habit'] == 3.0
        assert stats['longest_streak_overall'] == 5
        assert stats['habits_with_current_streak'] == 2
        assert 'completion_rates' in stats
    
    def test_get_habit_statistics_empty(self):
        """Test statistics with no habits."""
        stats = get_habit_statistics([])
        
        assert stats['total_habits'] == 0
        assert stats['daily_habits'] == 0
        assert stats['weekly_habits'] == 0
        assert stats['total_check_offs'] == 0
        assert stats['average_check_offs_per_habit'] == 0.0
        assert stats['longest_streak_overall'] == 0
        assert stats['habits_with_current_streak'] == 0
    
    def test_filter_habits_by_date_range(self, sample_habits):
        """Test filtering habits by creation date range."""
        # Modify creation dates for testing
        today = date.today()
        sample_habits[0].created_at = datetime.combine(today - timedelta(days=5), datetime.min.time())
        sample_habits[1].created_at = datetime.combine(today - timedelta(days=10), datetime.min.time())
        sample_habits[2].created_at = datetime.combine(today - timedelta(days=15), datetime.min.time())
        
        start_date = today - timedelta(days=7)
        end_date = today - timedelta(days=3)
        
        filtered_habits = filter_habits_by_date_range(sample_habits, start_date, end_date)
        
        assert len(filtered_habits) == 1
        assert filtered_habits[0].name == "Exercise"
    
    def test_get_most_active_habits(self, sample_habits):
        """Test getting most active habits by check-off count."""
        active_habits = get_most_active_habits(sample_habits, limit=2)
        
        assert len(active_habits) == 2
        assert active_habits[0][0].name == "Exercise"  # 5 check-offs
        assert active_habits[0][1] == 5
        assert active_habits[1][0].name == "Grocery shop"  # 3 check-offs
        assert active_habits[1][1] == 3
    
    def test_pure_functions(self, sample_habits):
        """Test that analytics functions are pure (no side effects)."""
        original_habits = sample_habits.copy()
        
        # Call various analytics functions
        list_all_habits(sample_habits)
        get_longest_streak_overall(sample_habits)
        get_habit_statistics(sample_habits)
        
        # Verify original habits are unchanged
        assert len(sample_habits) == len(original_habits)
        for i, habit in enumerate(sample_habits):
            assert habit.name == original_habits[i].name
            assert len(habit.check_offs) == len(original_habits[i].check_offs)
