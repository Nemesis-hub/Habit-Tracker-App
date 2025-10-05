from setuptools import setup, find_packages

setup(
    name="habit-tracker",
    version="1.0.0",
    description="A Python backend for habit tracking",
    author="Habit Tracker Team",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "pytest>=7.0.0",
    ],
    entry_points={
        "console_scripts": [
            "habit-tracker=habit_tracker.cli:main",
        ],
    },
)
