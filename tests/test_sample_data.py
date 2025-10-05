"""
Tests for sample data functionality.
"""

import pytest
from datetime import datetime, date, timedelta

from habit_tracker.models import Habit, Periodicity
from habit_tracker.sample_data import (
    create_sample_habits,
    populate_sample_data,
    get_sample_habit_summary,
    SAMPLE_HABIT_DATA
)
from habit_tracker.persistence import SQLiteHabitRepository, JSONHabitRepository


class TestSampleData:
    """Test cases for sample data functionality."""
    
    def test_create_sample_habits(self):
        """Test creating sample habits."""
        habits = create_sample_habits()
        
        assert len(habits) == 5
        
        # Check that we have the expected habits
        habit_names = [h.name for h in habits]
        expected_names = ["Brush teeth", "Exercise", "Read", "Grocery shop", "Clean house"]
        
        for expected_name in expected_names:
            assert expected_name in habit_names
        
        # Check periodicity distribution
        daily_habits = [h for h in habits if h.periodicity == Periodicity.DAILY]
        weekly_habits = [h for h in habits if h.periodicity == Periodicity.WEEKLY]
        
        assert len(daily_habits) == 3
        assert len(weekly_habits) == 2
    
    def test_sample_habits_have_check_offs(self):
        """Test that sample habits have check-off data."""
        habits = create_sample_habits()
        
        for habit in habits:
            assert len(habit.check_offs) > 0
            
            # Check that check-offs are sorted
            check_off_dates = [co.date() for co in habit.check_offs]
            assert check_off_dates == sorted(check_off_dates)
    
    def test_daily_habits_have_reasonable_check_offs(self):
        """Test that daily habits have reasonable number of check-offs."""
        habits = create_sample_habits()
        daily_habits = [h for h in habits if h.periodicity == Periodicity.DAILY]
        
        for habit in daily_habits:
            # Should have check-offs for roughly 4 weeks (28 days)
            # But not every day due to realistic patterns
            assert 15 <= len(habit.check_offs) <= 28
    
    def test_weekly_habits_have_reasonable_check_offs(self):
        """Test that weekly habits have reasonable number of check-offs."""
        habits = create_sample_habits()
        weekly_habits = [h for h in habits if h.periodicity == Periodicity.WEEKLY]
        
        for habit in weekly_habits:
            # Should have check-offs for roughly 4 weeks
            # But not every week due to realistic patterns
            assert 2 <= len(habit.check_offs) <= 4
    
    def test_no_duplicate_check_offs(self):
        """Test that sample habits don't have duplicate check-offs."""
        habits = create_sample_habits()
        
        for habit in habits:
            check_off_dates = [co.date() for co in habit.check_offs]
            
            if habit.periodicity == Periodicity.DAILY:
                # For daily habits, no duplicate dates
                assert len(check_off_dates) == len(set(check_off_dates))
            elif habit.periodicity == Periodicity.WEEKLY:
                # For weekly habits, no duplicate weeks
                week_numbers = [d.isocalendar()[1] for d in check_off_dates]
                assert len(week_numbers) == len(set(week_numbers))
    
    def test_populate_sample_data_sqlite(self):
        """Test populating sample data in SQLite repository."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            repository = SQLiteHabitRepository(db_path)
            populate_sample_data(repository)
            
            # Verify data was populated
            habits = repository.get_all_habits()
            assert len(habits) == 5
            
            # Check that habits have check-offs
            for habit in habits:
                assert len(habit.check_offs) > 0
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_populate_sample_data_json(self):
        """Test populating sample data in JSON repository."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            json_path = f.name
        
        try:
            repository = JSONHabitRepository(json_path)
            populate_sample_data(repository)
            
            # Verify data was populated
            habits = repository.get_all_habits()
            assert len(habits) == 5
            
            # Check that habits have check-offs
            for habit in habits:
                assert len(habit.check_offs) > 0
        finally:
            if os.path.exists(json_path):
                os.unlink(json_path)
    
    def test_populate_sample_data_existing_data(self):
        """Test that populate_sample_data skips if data already exists."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            repository = SQLiteHabitRepository(db_path)
            
            # Add one existing habit
            existing_habit = Habit("Existing Habit", Periodicity.DAILY)
            repository.create_habit(existing_habit)
            
            # Try to populate sample data
            populate_sample_data(repository)
            
            # Should still only have the original habit
            habits = repository.get_all_habits()
            assert len(habits) == 1
            assert habits[0].name == "Existing Habit"
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_get_sample_habit_summary(self):
        """Test getting sample habit summary."""
        summary = get_sample_habit_summary()
        
        assert isinstance(summary, str)
        assert "Sample Habits Summary:" in summary
        assert "Brush teeth" in summary
        assert "Exercise" in summary
        assert "Read" in summary
        assert "Grocery shop" in summary
        assert "Clean house" in summary
        
        # Check that summary contains streak information
        assert "Current streak:" in summary
        assert "Longest streak:" in summary
    
    def test_sample_habit_data_constants(self):
        """Test that SAMPLE_HABIT_DATA constant is properly defined."""
        assert len(SAMPLE_HABIT_DATA) == 5
        
        for habit_data in SAMPLE_HABIT_DATA:
            assert "name" in habit_data
            assert "periodicity" in habit_data
            assert "expected_check_offs" in habit_data
            assert "description" in habit_data
            
            assert habit_data["periodicity"] in ["daily", "weekly"]
            assert isinstance(habit_data["expected_check_offs"], int)
            assert habit_data["expected_check_offs"] > 0
    
    def test_sample_habits_have_realistic_streaks(self):
        """Test that sample habits have realistic streak patterns."""
        habits = create_sample_habits()
        
        for habit in habits:
            current_streak = habit.get_current_streak()
            longest_streak = habit.get_longest_streak()
            
            # Current streak should be reasonable
            assert 0 <= current_streak <= 30  # Max 30 days/weeks
            
            # Longest streak should be at least as long as current streak
            assert longest_streak >= current_streak
            
            # Longest streak should be reasonable
            assert 0 <= longest_streak <= 30
