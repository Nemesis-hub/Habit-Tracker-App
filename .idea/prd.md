Product Requirements Document (PRD) for Habit Tracking App Backend

**1. Overview**  
Purpose: Build Python backend for habit tracking using OOP and functional programming. No GUI required; focus on core functionality for daily/weekly habits, check-offs, streaks, persistence, and analytics.

**2. Target Users**  
Individuals tracking personal habits (e.g., exercise, reading). Assumes basic tech familiarity for CLI interaction.

**3. Key Features**  
- Habit Class (OOP): Define task, periodicity (daily/weekly), creation date, check-off timestamps.  
- Persistence: Use SQLite DB or JSON files for storing habits and check-offs.  
- Predefined Habits: 5 examples (3 daily: "Brush teeth", "Exercise", "Read"; 2 weekly: "Grocery shop", "Clean house") with 4 weeks of sample data.  
- Analytics (Functional Programming): Functions to list all habits, list by periodicity, longest streak overall, longest streak per habit.  
- Interface: CLI with menu for create/delete/check-off/analyze habits (using click library).  
- Testing: Unit tests with pytest for habit logic and analytics.

**4. Technical Requirements**  
- Python 3.7+.  
- Libraries: sqlite3/json, click, pytest.  
- Data Flow: User inputs via CLI → Habit objects → DB storage → Functional queries for analysis.  

**5. Non-Functional Requirements**  
- Documentation: README.md with install/run instructions, docstrings in code.  
- Security: Basic (no auth needed).  
- Performance: Handle 100+ habits efficiently.

**6. Assumptions & Risks**  
- Single-user app.  
- Risk: Date handling errors; mitigate with unit tests.  

Implement in phases: Concept → Development → Finalization.