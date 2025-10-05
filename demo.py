#!/usr/bin/env python3
"""
Demo script for the Habit Tracker application.
This script demonstrates the core functionality without requiring CLI interaction.
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
from habit_tracker.sample_data import populate_sample_data


def main():
    """Run the demo."""
    print("🏃‍♂️ Habit Tracker Demo")
    print("=" * 50)
    
    # Create a temporary JSON repository for demo
    repository = get_repository("json", json_path="demo_habits.json")
    
    print("\n1. Creating sample habits with data...")
    populate_sample_data(repository)
    
    print("\n2. Listing all habits:")
    habits = repository.get_all_habits()
    for habit in habits:
        current_streak = habit.get_current_streak()
        longest_streak = habit.get_longest_streak()
        print(f"   • {habit.name} ({habit.periodicity.value})")
        print(f"     Current streak: {current_streak}")
        print(f"     Longest streak: {longest_streak}")
        print(f"     Check-offs: {len(habit.check_offs)}")
        print()
    
    print("3. Analytics Summary:")
    stats = get_habit_statistics(habits)
    print(f"   Total habits: {stats['total_habits']}")
    print(f"   Daily habits: {stats['daily_habits']}")
    print(f"   Weekly habits: {stats['weekly_habits']}")
    print(f"   Total check-offs: {stats['total_check_offs']}")
    print(f"   Average check-offs per habit: {stats['average_check_offs_per_habit']:.1f}")
    
    habit, streak = get_longest_streak_overall(habits)
    if habit:
        print(f"   Longest streak overall: {streak} ({habit.name})")
    
    print("\n4. Creating a new habit and checking it off...")
    new_habit = Habit("Demo Habit", Periodicity.DAILY)
    repository.create_habit(new_habit)
    
    # Add a few check-offs
    today = date.today()
    for i in range(3):
        check_date = today - timedelta(days=i)
        check_time = datetime.combine(check_date, datetime.min.time())
        repository.add_check_off(new_habit.id, check_time)
    
    updated_habit = repository.get_habit(new_habit.id)
    print(f"   Created: {updated_habit.name}")
    print(f"   Current streak: {updated_habit.get_current_streak()}")
    print(f"   Check-offs: {len(updated_habit.check_offs)}")
    
    print("\n5. Demo completed successfully! 🎉")
    print("\nTo use the full CLI interface, run:")
    print("   python -m habit_tracker.cli menu")
    print("\nOr install the package and use:")
    print("   habit-tracker menu")
    
    # Clean up demo file
    if os.path.exists("demo_habits.json"):
        os.remove("demo_habits.json")


if __name__ == "__main__":
    main()
