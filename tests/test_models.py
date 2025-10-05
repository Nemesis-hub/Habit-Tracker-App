"""
Tests for the Habit model.
"""

import pytest
from datetime import datetime, date, timedelta

from habit_tracker.models import Habit, Periodicity


class TestHabit:
    """Test cases for the Habit class."""
    
    def test_habit_creation(self):
        """Test basic habit creation."""
        habit = Habit("Test Habit", Periodicity.DAILY)
        
        assert habit.name == "Test Habit"
        assert habit.periodicity == Periodicity.DAILY
        assert habit.id is not None
        assert isinstance(habit.created_at, datetime)
        assert len(habit.check_offs) == 0
    
    def test_habit_with_custom_id(self):
        """Test habit creation with custom ID."""
        custom_id = "custom_habit_123"
        habit = Habit("Test Habit", Periodicity.WEEKLY, habit_id=custom_id)
        
        assert habit.id == custom_id
    
    def test_add_check_off(self):
        """Test adding check-offs to a habit."""
        habit = Habit("Test Habit", Periodicity.DAILY)
        
        # Add first check-off
        check_off_time = datetime(2023, 1, 1, 8, 0, 0)
        habit.add_check_off(check_off_time)
        
        assert len(habit.check_offs) == 1
        assert habit.check_offs[0] == check_off_time
    
    def test_add_check_off_default_time(self):
        """Test adding check-off with default time (now)."""
        habit = Habit("Test Habit", Periodicity.DAILY)
        
        before = datetime.now()
        habit.add_check_off()
        after = datetime.now()
        
        assert len(habit.check_offs) == 1
        assert before <= habit.check_offs[0] <= after
    
    def test_duplicate_daily_check_off(self):
        """Test that duplicate daily check-offs are prevented."""
        habit = Habit("Test Habit", Periodicity.DAILY)
        
        # Add check-off for today
        today = datetime.now()
        habit.add_check_off(today)
        
        # Try to add another check-off for the same day
        later_today = today.replace(hour=20)
        habit.add_check_off(later_today)
        
        # Should still only have one check-off
        assert len(habit.check_offs) == 1
    
    def test_duplicate_weekly_check_off(self):
        """Test that duplicate weekly check-offs are prevented."""
        habit = Habit("Test Habit", Periodicity.WEEKLY)
        
        # Add check-off for Monday
        monday = datetime(2023, 1, 2, 10, 0, 0)  # Monday
        habit.add_check_off(monday)
        
        # Try to add another check-off for the same week (Wednesday)
        wednesday = datetime(2023, 1, 4, 10, 0, 0)  # Wednesday of same week
        habit.add_check_off(wednesday)
        
        # Should still only have one check-off
        assert len(habit.check_offs) == 1
    
    def test_different_weeks_check_off(self):
        """Test that check-offs in different weeks are allowed."""
        habit = Habit("Test Habit", Periodicity.WEEKLY)
        
        # Add check-off for first week
        week1 = datetime(2023, 1, 2, 10, 0, 0)  # Monday
        habit.add_check_off(week1)
        
        # Add check-off for next week
        week2 = datetime(2023, 1, 9, 10, 0, 0)  # Monday of next week
        habit.add_check_off(week2)
        
        # Should have two check-offs
        assert len(habit.check_offs) == 2
    
    def test_current_streak_daily(self):
        """Test current streak calculation for daily habits."""
        habit = Habit("Test Habit", Periodicity.DAILY)
        
        # Add check-offs for consecutive days
        today = date.today()
        for i in range(3):
            check_date = today - timedelta(days=i)
            check_time = datetime.combine(check_date, datetime.min.time())
            habit.add_check_off(check_time)
        
        assert habit.get_current_streak() == 3
    
    def test_current_streak_weekly(self):
        """Test current streak calculation for weekly habits."""
        habit = Habit("Test Habit", Periodicity.WEEKLY)
        
        # Add check-offs for consecutive weeks
        today = date.today()
        current_week_monday = today - timedelta(days=today.weekday())
        
        for i in range(3):
            week_monday = current_week_monday - timedelta(weeks=i)
            check_time = datetime.combine(week_monday, datetime.min.time())
            habit.add_check_off(check_time)
        
        assert habit.get_current_streak() == 3
    
    def test_longest_streak_daily(self):
        """Test longest streak calculation for daily habits."""
        habit = Habit("Test Habit", Periodicity.DAILY)
        
        # Add check-offs with a gap
        base_date = date(2023, 1, 1)
        
        # First streak: 3 consecutive days
        for i in range(3):
            check_date = base_date + timedelta(days=i)
            check_time = datetime.combine(check_date, datetime.min.time())
            habit.add_check_off(check_time)
        
        # Gap of 2 days
        
        # Second streak: 5 consecutive days
        for i in range(5):
            check_date = base_date + timedelta(days=i + 5)
            check_time = datetime.combine(check_date, datetime.min.time())
            habit.add_check_off(check_time)
        
        assert habit.get_longest_streak() == 5
    
    def test_longest_streak_weekly(self):
        """Test longest streak calculation for weekly habits."""
        habit = Habit("Test Habit", Periodicity.WEEKLY)
        
        # Add check-offs with a gap
        base_date = date(2023, 1, 2)  # Monday
        
        # First streak: 2 consecutive weeks
        for i in range(2):
            week_monday = base_date + timedelta(weeks=i)
            check_time = datetime.combine(week_monday, datetime.min.time())
            habit.add_check_off(check_time)
        
        # Gap of 1 week
        
        # Second streak: 4 consecutive weeks
        for i in range(4):
            week_monday = base_date + timedelta(weeks=i + 3)
            check_time = datetime.combine(week_monday, datetime.min.time())
            habit.add_check_off(check_time)
        
        assert habit.get_longest_streak() == 4
    
    def test_to_dict(self):
        """Test habit serialization to dictionary."""
        habit = Habit("Test Habit", Periodicity.DAILY)
        habit.add_check_off(datetime(2023, 1, 1, 8, 0, 0))
        
        data = habit.to_dict()
        
        assert data['name'] == "Test Habit"
        assert data['periodicity'] == "daily"
        assert data['id'] == habit.id
        assert 'created_at' in data
        assert len(data['check_offs']) == 1
        assert data['check_offs'][0] == "2023-01-01T08:00:00"
    
    def test_from_dict(self):
        """Test habit deserialization from dictionary."""
        data = {
            'id': 'test_id',
            'name': 'Test Habit',
            'periodicity': 'weekly',
            'created_at': '2023-01-01T00:00:00',
            'check_offs': ['2023-01-02T10:00:00', '2023-01-09T10:00:00']
        }
        
        habit = Habit.from_dict(data)
        
        assert habit.id == 'test_id'
        assert habit.name == 'Test Habit'
        assert habit.periodicity == Periodicity.WEEKLY
        assert habit.created_at == datetime(2023, 1, 1, 0, 0, 0)
        assert len(habit.check_offs) == 2
        assert habit.check_offs[0] == datetime(2023, 1, 2, 10, 0, 0)
        assert habit.check_offs[1] == datetime(2023, 1, 9, 10, 0, 0)
    
    def test_str_representation(self):
        """Test string representation of habit."""
        habit = Habit("Test Habit", Periodicity.DAILY)
        habit_str = str(habit)
        
        assert "Test Habit" in habit_str
        assert "daily" in habit_str
        assert habit.id in habit_str
    
    def test_repr_representation(self):
        """Test detailed string representation of habit."""
        habit = Habit("Test Habit", Periodicity.DAILY)
        habit_repr = repr(habit)
        
        assert "Test Habit" in habit_repr
        assert "daily" in habit_repr
        assert habit.id in habit_repr
        assert "check_offs_count=0" in habit_repr
