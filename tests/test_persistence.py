"""
Tests for the persistence layer.
"""

import pytest
import tempfile
import os
from datetime import datetime

from habit_tracker.models import Habit, Periodicity
from habit_tracker.persistence import (
    SQLiteHabitRepository,
    JSONHabitRepository,
    get_repository
)


class TestSQLiteHabitRepository:
    """Test cases for SQLite repository."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        yield db_path
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def repository(self, temp_db):
        """Create a repository instance."""
        return SQLiteHabitRepository(temp_db)
    
    def test_create_habit(self, repository):
        """Test creating a habit."""
        habit = Habit("Test Habit", Periodicity.DAILY)
        repository.create_habit(habit)
        
        retrieved_habit = repository.get_habit(habit.id)
        assert retrieved_habit is not None
        assert retrieved_habit.name == "Test Habit"
        assert retrieved_habit.periodicity == Periodicity.DAILY
    
    def test_get_habit_not_found(self, repository):
        """Test getting a non-existent habit."""
        habit = repository.get_habit("non_existent_id")
        assert habit is None
    
    def test_get_all_habits(self, repository):
        """Test getting all habits."""
        # Create multiple habits
        habit1 = Habit("Habit 1", Periodicity.DAILY)
        habit2 = Habit("Habit 2", Periodicity.WEEKLY)
        
        repository.create_habit(habit1)
        repository.create_habit(habit2)
        
        all_habits = repository.get_all_habits()
        assert len(all_habits) == 2
        
        habit_names = [h.name for h in all_habits]
        assert "Habit 1" in habit_names
        assert "Habit 2" in habit_names
    
    def test_update_habit(self, repository):
        """Test updating a habit."""
        habit = Habit("Original Name", Periodicity.DAILY)
        repository.create_habit(habit)
        
        # Modify habit
        habit.name = "Updated Name"
        habit.add_check_off(datetime(2023, 1, 1, 8, 0, 0))
        
        repository.update_habit(habit)
        
        # Verify update
        updated_habit = repository.get_habit(habit.id)
        assert updated_habit.name == "Updated Name"
        assert len(updated_habit.check_offs) == 1
    
    def test_delete_habit(self, repository):
        """Test deleting a habit."""
        habit = Habit("Test Habit", Periodicity.DAILY)
        repository.create_habit(habit)
        
        # Delete habit
        result = repository.delete_habit(habit.id)
        assert result is True
        
        # Verify deletion
        deleted_habit = repository.get_habit(habit.id)
        assert deleted_habit is None
    
    def test_delete_habit_not_found(self, repository):
        """Test deleting a non-existent habit."""
        result = repository.delete_habit("non_existent_id")
        assert result is False
    
    def test_add_check_off(self, repository):
        """Test adding a check-off."""
        habit = Habit("Test Habit", Periodicity.DAILY)
        repository.create_habit(habit)
        
        check_off_time = datetime(2023, 1, 1, 8, 0, 0)
        result = repository.add_check_off(habit.id, check_off_time)
        
        assert result is True
        
        # Verify check-off was added
        updated_habit = repository.get_habit(habit.id)
        assert len(updated_habit.check_offs) == 1
        assert updated_habit.check_offs[0] == check_off_time
    
    def test_add_duplicate_check_off(self, repository):
        """Test adding a duplicate check-off."""
        habit = Habit("Test Habit", Periodicity.DAILY)
        repository.create_habit(habit)
        
        check_off_time = datetime(2023, 1, 1, 8, 0, 0)
        
        # Add first check-off
        result1 = repository.add_check_off(habit.id, check_off_time)
        assert result1 is True
        
        # Try to add duplicate
        result2 = repository.add_check_off(habit.id, check_off_time)
        assert result2 is False
        
        # Verify only one check-off exists
        updated_habit = repository.get_habit(habit.id)
        assert len(updated_habit.check_offs) == 1


class TestJSONHabitRepository:
    """Test cases for JSON repository."""
    
    @pytest.fixture
    def temp_json(self):
        """Create a temporary JSON file for testing."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            json_path = f.name
        
        yield json_path
        
        # Cleanup
        if os.path.exists(json_path):
            os.unlink(json_path)
    
    @pytest.fixture
    def repository(self, temp_json):
        """Create a repository instance."""
        return JSONHabitRepository(temp_json)
    
    def test_create_habit(self, repository):
        """Test creating a habit."""
        habit = Habit("Test Habit", Periodicity.DAILY)
        repository.create_habit(habit)
        
        retrieved_habit = repository.get_habit(habit.id)
        assert retrieved_habit is not None
        assert retrieved_habit.name == "Test Habit"
        assert retrieved_habit.periodicity == Periodicity.DAILY
    
    def test_get_habit_not_found(self, repository):
        """Test getting a non-existent habit."""
        habit = repository.get_habit("non_existent_id")
        assert habit is None
    
    def test_get_all_habits(self, repository):
        """Test getting all habits."""
        # Create multiple habits
        habit1 = Habit("Habit 1", Periodicity.DAILY)
        habit2 = Habit("Habit 2", Periodicity.WEEKLY)
        
        repository.create_habit(habit1)
        repository.create_habit(habit2)
        
        all_habits = repository.get_all_habits()
        assert len(all_habits) == 2
        
        habit_names = [h.name for h in all_habits]
        assert "Habit 1" in habit_names
        assert "Habit 2" in habit_names
    
    def test_update_habit(self, repository):
        """Test updating a habit."""
        habit = Habit("Original Name", Periodicity.DAILY)
        repository.create_habit(habit)
        
        # Modify habit
        habit.name = "Updated Name"
        habit.add_check_off(datetime(2023, 1, 1, 8, 0, 0))
        
        repository.update_habit(habit)
        
        # Verify update
        updated_habit = repository.get_habit(habit.id)
        assert updated_habit.name == "Updated Name"
        assert len(updated_habit.check_offs) == 1
    
    def test_delete_habit(self, repository):
        """Test deleting a habit."""
        habit = Habit("Test Habit", Periodicity.DAILY)
        repository.create_habit(habit)
        
        # Delete habit
        result = repository.delete_habit(habit.id)
        assert result is True
        
        # Verify deletion
        deleted_habit = repository.get_habit(habit.id)
        assert deleted_habit is None
    
    def test_delete_habit_not_found(self, repository):
        """Test deleting a non-existent habit."""
        result = repository.delete_habit("non_existent_id")
        assert result is False
    
    def test_add_check_off(self, repository):
        """Test adding a check-off."""
        habit = Habit("Test Habit", Periodicity.DAILY)
        repository.create_habit(habit)
        
        check_off_time = datetime(2023, 1, 1, 8, 0, 0)
        result = repository.add_check_off(habit.id, check_off_time)
        
        assert result is True
        
        # Verify check-off was added
        updated_habit = repository.get_habit(habit.id)
        assert len(updated_habit.check_offs) == 1
        assert updated_habit.check_offs[0] == check_off_time
    
    def test_add_duplicate_check_off(self, repository):
        """Test adding a duplicate check-off."""
        habit = Habit("Test Habit", Periodicity.DAILY)
        repository.create_habit(habit)
        
        check_off_time = datetime(2023, 1, 1, 8, 0, 0)
        
        # Add first check-off
        result1 = repository.add_check_off(habit.id, check_off_time)
        assert result1 is True
        
        # Try to add duplicate
        result2 = repository.add_check_off(habit.id, check_off_time)
        assert result2 is False
        
        # Verify only one check-off exists
        updated_habit = repository.get_habit(habit.id)
        assert len(updated_habit.check_offs) == 1


class TestRepositoryFactory:
    """Test cases for repository factory function."""
    
    def test_get_sqlite_repository(self):
        """Test getting SQLite repository."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            repo = get_repository("sqlite", db_path=db_path)
            assert isinstance(repo, SQLiteHabitRepository)
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_get_json_repository(self):
        """Test getting JSON repository."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            json_path = f.name
        
        try:
            repo = get_repository("json", json_path=json_path)
            assert isinstance(repo, JSONHabitRepository)
        finally:
            if os.path.exists(json_path):
                os.unlink(json_path)
    
    def test_invalid_backend(self):
        """Test invalid backend raises error."""
        with pytest.raises(ValueError):
            get_repository("invalid_backend")
