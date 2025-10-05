"""
Persistence layer for the habit tracker application.
Supports both SQLite and JSON storage backends.
"""

import sqlite3
import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import contextmanager

from .models import Habit, Periodicity


class HabitRepository:
    """Abstract base class for habit persistence."""
    
    def create_habit(self, habit: Habit) -> None:
        """Create a new habit."""
        raise NotImplementedError
    
    def get_habit(self, habit_id: str) -> Optional[Habit]:
        """Get a habit by ID."""
        raise NotImplementedError
    
    def get_all_habits(self) -> List[Habit]:
        """Get all habits."""
        raise NotImplementedError
    
    def update_habit(self, habit: Habit) -> None:
        """Update an existing habit."""
        raise NotImplementedError
    
    def delete_habit(self, habit_id: str) -> bool:
        """Delete a habit by ID. Returns True if deleted, False if not found."""
        raise NotImplementedError
    
    def add_check_off(self, habit_id: str, check_off_time: datetime) -> bool:
        """Add a check-off to a habit. Returns True if added, False if duplicate."""
        raise NotImplementedError


class SQLiteHabitRepository(HabitRepository):
    """SQLite implementation of habit persistence."""
    
    def __init__(self, db_path: str = "habits.db"):
        """
        Initialize the SQLite repository.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize the database schema."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS habits (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    periodicity TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS check_offs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    habit_id TEXT NOT NULL,
                    check_off_time TEXT NOT NULL,
                    FOREIGN KEY (habit_id) REFERENCES habits (id)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_check_offs_habit_id 
                ON check_offs (habit_id)
            """)
    
    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper transaction handling."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def create_habit(self, habit: Habit) -> None:
        """Create a new habit."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO habits (id, name, periodicity, created_at)
                VALUES (?, ?, ?, ?)
            """, (habit.id, habit.name, habit.periodicity.value, habit.created_at.isoformat()))
            
            # Insert check-offs if they exist
            for check_off in habit.check_offs:
                conn.execute("""
                    INSERT INTO check_offs (habit_id, check_off_time)
                    VALUES (?, ?)
                """, (habit.id, check_off.isoformat()))
    
    def get_habit(self, habit_id: str) -> Optional[Habit]:
        """Get a habit by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, name, periodicity, created_at
                FROM habits WHERE id = ?
            """, (habit_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            habit = Habit(
                name=row['name'],
                periodicity=Periodicity(row['periodicity']),
                habit_id=row['id']
            )
            habit.created_at = datetime.fromisoformat(row['created_at'])
            
            # Load check-offs
            cursor = conn.execute("""
                SELECT check_off_time FROM check_offs
                WHERE habit_id = ? ORDER BY check_off_time
            """, (habit_id,))
            
            habit.check_offs = [datetime.fromisoformat(row['check_off_time']) 
                              for row in cursor.fetchall()]
            
            return habit
    
    def get_all_habits(self) -> List[Habit]:
        """Get all habits."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, name, periodicity, created_at
                FROM habits ORDER BY created_at
            """)
            
            habits = []
            for row in cursor.fetchall():
                habit = Habit(
                    name=row['name'],
                    periodicity=Periodicity(row['periodicity']),
                    habit_id=row['id']
                )
                habit.created_at = datetime.fromisoformat(row['created_at'])
                
                # Load check-offs
                check_off_cursor = conn.execute("""
                    SELECT check_off_time FROM check_offs
                    WHERE habit_id = ? ORDER BY check_off_time
                """, (habit.id,))
                
                habit.check_offs = [datetime.fromisoformat(row['check_off_time']) 
                                  for row in check_off_cursor.fetchall()]
                
                habits.append(habit)
            
            return habits
    
    def update_habit(self, habit: Habit) -> None:
        """Update an existing habit."""
        with self._get_connection() as conn:
            # Update habit basic info
            conn.execute("""
                UPDATE habits 
                SET name = ?, periodicity = ?
                WHERE id = ?
            """, (habit.name, habit.periodicity.value, habit.id))
            
            # Clear existing check-offs
            conn.execute("DELETE FROM check_offs WHERE habit_id = ?", (habit.id,))
            
            # Insert new check-offs
            for check_off in habit.check_offs:
                conn.execute("""
                    INSERT INTO check_offs (habit_id, check_off_time)
                    VALUES (?, ?)
                """, (habit.id, check_off.isoformat()))
    
    def delete_habit(self, habit_id: str) -> bool:
        """Delete a habit by ID."""
        with self._get_connection() as conn:
            # Delete check-offs first (foreign key constraint)
            conn.execute("DELETE FROM check_offs WHERE habit_id = ?", (habit_id,))
            
            # Delete habit
            cursor = conn.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
            return cursor.rowcount > 0
    
    def add_check_off(self, habit_id: str, check_off_time: datetime) -> bool:
        """Add a check-off to a habit."""
        habit = self.get_habit(habit_id)
        if not habit:
            return False
        
        # Check for duplicates
        if habit._is_duplicate_check_off(check_off_time):
            return False
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO check_offs (habit_id, check_off_time)
                VALUES (?, ?)
            """, (habit_id, check_off_time.isoformat()))
        
        return True


class JSONHabitRepository(HabitRepository):
    """JSON file implementation of habit persistence."""
    
    def __init__(self, json_path: str = "habits.json"):
        """
        Initialize the JSON repository.
        
        Args:
            json_path: Path to the JSON file
        """
        self.json_path = json_path
        self._ensure_file_exists()
    
    def _ensure_file_exists(self) -> None:
        """Ensure the JSON file exists with proper structure."""
        if not os.path.exists(self.json_path):
            with open(self.json_path, 'w') as f:
                json.dump({"habits": []}, f, indent=2)
    
    def _load_data(self) -> Dict[str, Any]:
        """Load data from JSON file."""
        try:
            with open(self.json_path, 'r') as f:
                content = f.read().strip()
                if not content:
                    return {"habits": []}
                return json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"habits": []}
    
    def _save_data(self, data: Dict[str, Any]) -> None:
        """Save data to JSON file."""
        with open(self.json_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_habit(self, habit: Habit) -> None:
        """Create a new habit."""
        data = self._load_data()
        data["habits"].append(habit.to_dict())
        self._save_data(data)
    
    def get_habit(self, habit_id: str) -> Optional[Habit]:
        """Get a habit by ID."""
        data = self._load_data()
        for habit_data in data["habits"]:
            if habit_data["id"] == habit_id:
                return Habit.from_dict(habit_data)
        return None
    
    def get_all_habits(self) -> List[Habit]:
        """Get all habits."""
        data = self._load_data()
        return [Habit.from_dict(habit_data) for habit_data in data["habits"]]
    
    def update_habit(self, habit: Habit) -> None:
        """Update an existing habit."""
        data = self._load_data()
        for i, habit_data in enumerate(data["habits"]):
            if habit_data["id"] == habit.id:
                data["habits"][i] = habit.to_dict()
                break
        self._save_data(data)
    
    def delete_habit(self, habit_id: str) -> bool:
        """Delete a habit by ID."""
        data = self._load_data()
        for i, habit_data in enumerate(data["habits"]):
            if habit_data["id"] == habit_id:
                del data["habits"][i]
                self._save_data(data)
                return True
        return False
    
    def add_check_off(self, habit_id: str, check_off_time: datetime) -> bool:
        """Add a check-off to a habit."""
        habit = self.get_habit(habit_id)
        if not habit:
            return False
        
        # Check for duplicates
        if habit._is_duplicate_check_off(check_off_time):
            return False
        
        habit.add_check_off(check_off_time)
        self.update_habit(habit)
        return True


def get_repository(backend: str = "sqlite", **kwargs) -> HabitRepository:
    """
    Factory function to get the appropriate repository.
    
    Args:
        backend: Storage backend ("sqlite" or "json")
        **kwargs: Additional arguments for the repository
        
    Returns:
        HabitRepository instance
    """
    if backend.lower() == "sqlite":
        return SQLiteHabitRepository(**kwargs)
    elif backend.lower() == "json":
        return JSONHabitRepository(**kwargs)
    else:
        raise ValueError(f"Unsupported backend: {backend}")
