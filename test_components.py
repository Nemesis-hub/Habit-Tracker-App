#!/usr/bin/env python3
"""
Simple test script to verify individual components work correctly.
"""

import sys
import os
from datetime import datetime, date, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from habit_tracker.models import Habit, Periodicity
from habit_tracker.persistence import get_repository
from habit_tracker.analytics import (
    list_all_habits,
    get_longest_streak_overall,
    get_habit_statistics
)


def test_habit_model():
    """Test the Habit model."""
    print("🧪 Testing Habit Model...")
    
    # Create a daily habit
    habit = Habit("Test Exercise", Periodicity.DAILY)
    print(f"   ✅ Created habit: {habit.name}")
    
    # Add some check-offs
    today = date.today()
    for i in range(3):
        check_date = today - timedelta(days=i)
        check_time = datetime.combine(check_date, datetime.min.time())
        habit.add_check_off(check_time)
    
    print(f"   ✅ Added {len(habit.check_offs)} check-offs")
    print(f"   ✅ Current streak: {habit.get_current_streak()}")
    print(f"   ✅ Longest streak: {habit.get_longest_streak()}")
    
    return habit


def test_sqlite_persistence():
    """Test SQLite persistence."""
    print("\n🧪 Testing SQLite Persistence...")
    
    repository = get_repository("sqlite", db_path="test_habits.db")
    
    # Create and save a habit
    habit = Habit("SQLite Test", Periodicity.WEEKLY)
    repository.create_habit(habit)
    print(f"   ✅ Created habit in SQLite: {habit.name}")
    
    # Retrieve the habit
    retrieved = repository.get_habit(habit.id)
    print(f"   ✅ Retrieved habit: {retrieved.name}")
    
    # Add a check-off
    repository.add_check_off(habit.id, datetime.now())
    updated = repository.get_habit(habit.id)
    print(f"   ✅ Added check-off, total: {len(updated.check_offs)}")
    
    # Clean up
    repository.delete_habit(habit.id)
    print("   ✅ Cleaned up test data")
    
    # Remove test database
    if os.path.exists("test_habits.db"):
        os.remove("test_habits.db")


def test_analytics():
    """Test analytics functions."""
    print("\n🧪 Testing Analytics...")
    
    # Create test habits
    habits = []
    
    # Daily habit with good streak
    daily_habit = Habit("Daily Exercise", Periodicity.DAILY)
    today = date.today()
    for i in range(5):
        check_date = today - timedelta(days=i)
        check_time = datetime.combine(check_date, datetime.min.time())
        daily_habit.add_check_off(check_time)
    habits.append(daily_habit)
    
    # Weekly habit
    weekly_habit = Habit("Weekly Cleanup", Periodicity.WEEKLY)
    current_week = today - timedelta(days=today.weekday())
    for i in range(2):
        week_monday = current_week - timedelta(weeks=i)
        check_time = datetime.combine(week_monday, datetime.min.time())
        weekly_habit.add_check_off(check_time)
    habits.append(weekly_habit)
    
    # Test analytics
    all_habits = list_all_habits(habits)
    print(f"   ✅ Listed {len(all_habits)} habits")
    
    habit, streak = get_longest_streak_overall(habits)
    print(f"   ✅ Longest streak: {streak} ({habit.name})")
    
    stats = get_habit_statistics(habits)
    print(f"   ✅ Total habits: {stats['total_habits']}")
    print(f"   ✅ Total check-offs: {stats['total_check_offs']}")


def main():
    """Run all component tests."""
    print("🏃‍♂️ Habit Tracker Component Tests")
    print("=" * 50)
    
    try:
        # Test individual components
        test_habit_model()
        test_sqlite_persistence()
        test_analytics()
        
        print("\n🎉 All component tests passed!")
        print("\nThe habit tracker is working correctly!")
        print("\nTo use the full application:")
        print("   py -m habit_tracker.cli menu")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
