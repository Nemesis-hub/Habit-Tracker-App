"""
Command-line interface for the habit tracker application.
"""

import click
from datetime import datetime, date
from typing import Optional, List
import sys

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm, IntPrompt
import inquirer
from rich.text import Text
from rich.columns import Columns
from rich.align import Align
from rich import box
from rich.syntax import Syntax

from .models import Habit, Periodicity
from .persistence import get_repository
from .analytics import (
    list_all_habits,
    list_habits_by_periodicity,
    get_longest_streak_overall,
    get_longest_streak_per_habit,
    get_current_streaks,
    get_habit_statistics
)

# Initialize Rich console
console = Console()


class HabitTrackerCLI:
    """Main CLI class for the habit tracker."""
    
    def __init__(self, backend: str = "sqlite", db_path: Optional[str] = None):
        """
        Initialize the CLI.
        
        Args:
            backend: Storage backend ("sqlite" or "json")
            db_path: Path to the database file (optional)
        """
        kwargs = {}
        if db_path:
            if backend == "sqlite":
                kwargs["db_path"] = db_path
            elif backend == "json":
                kwargs["json_path"] = db_path
        
        self.repository = get_repository(backend, **kwargs)
    
    def _show_success(self, message: str) -> None:
        """Show a success message with consistent formatting."""
        console.print(f"✅ [bold green]{message}[/bold green]")
    
    def _show_error(self, message: str) -> None:
        """Show an error message with consistent formatting."""
        console.print(f"❌ [bold red]{message}[/bold red]")
    
    def _show_warning(self, message: str) -> None:
        """Show a warning message with consistent formatting."""
        console.print(f"⚠️ [bold yellow]{message}[/bold yellow]")
    
    def _show_info(self, message: str) -> None:
        """Show an info message with consistent formatting."""
        console.print(f"ℹ️ [bold blue]{message}[/bold blue]")
    
    def create_habit(self, name: str, periodicity: str) -> bool:
        """
        Create a new habit.
        
        Args:
            name: Name of the habit
            periodicity: "daily" or "weekly"
            
        Returns:
            True if created successfully, False otherwise
        """
        try:
            periodicity_enum = Periodicity(periodicity.lower())
            habit = Habit(name=name, periodicity=periodicity_enum)
            
            with console.status(f"[bold green]Creating habit '{name}'..."):
                self.repository.create_habit(habit)
            
            # Show success with a nice panel
            success_panel = Panel(
                f"[bold green]Habit Created Successfully![/bold green]\n\n"
                f"Name: [bold]{name}[/bold]\n"
                f"Periodicity: [bold]{periodicity.title()}[/bold]\n"
                f"ID: [dim]{habit.id}[/dim]",
                title="🎉 Success",
                border_style="green",
                padding=(1, 2)
            )
            console.print(success_panel)
            return True
        except ValueError:
            self._show_error(f"Invalid periodicity: '{periodicity}'. Must be 'daily' or 'weekly'")
            console.print("\n[bold]Valid options:[/bold]")
            console.print("• [cyan]daily[/cyan] - Habit to be completed every day")
            console.print("• [cyan]weekly[/cyan] - Habit to be completed once per week")
            return False
        except Exception as e:
            self._show_error(f"Error creating habit: {e}")
            return False
    
    def delete_habit(self, habit_id: str, force: bool = False) -> bool:
        """
        Delete a habit.
        
        Args:
            habit_id: ID of the habit to delete
            force: Skip confirmation dialog
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # First, get the habit to show details
            habit = self.repository.get_habit(habit_id)
            if not habit:
                self._show_error(f"Habit with ID '{habit_id}' not found")
                return False
            
            # Show confirmation unless forced
            if not force:
                warning_panel = Panel(
                    f"[bold red]⚠️ WARNING: This action cannot be undone![/bold red]\n\n"
                    f"You are about to delete:\n"
                    f"• [bold]Name:[/bold] {habit.name}\n"
                    f"• [bold]Periodicity:[/bold] {habit.periodicity.value.title()}\n"
                    f"• [bold]Current Streak:[/bold] {habit.get_current_streak()}\n"
                    f"• [bold]Total Check-offs:[/bold] {len(habit.check_offs)}\n\n"
                    f"[bold red]All check-off data will be permanently lost![/bold red]",
                    title="🗑️ Delete Habit",
                    border_style="red",
                    padding=(1, 2)
                )
                console.print(warning_panel)
                
                if not Confirm.ask("Are you sure you want to delete this habit?", default=False):
                    console.print("❌ [yellow]Deletion cancelled.[/yellow]")
                    return False
            
            with console.status(f"[bold red]Deleting habit '{habit.name}'..."):
                if self.repository.delete_habit(habit_id):
                    self._show_success(f"Successfully deleted habit '{habit.name}'")
                    return True
                else:
                    self._show_error(f"Failed to delete habit with ID '{habit_id}'")
                    return False
        except Exception as e:
            self._show_error(f"Error deleting habit: {e}")
            return False
    
    def check_off_habit(self, habit_id: str, check_off_time: Optional[datetime] = None) -> bool:
        """
        Check off a habit.
        
        Args:
            habit_id: ID of the habit to check off
            check_off_time: When the habit was completed (defaults to now)
            
        Returns:
            True if checked off successfully, False otherwise
        """
        try:
            if check_off_time is None:
                check_off_time = datetime.now()
            
            # Get habit details first
            habit = self.repository.get_habit(habit_id)
            if not habit:
                self._show_error(f"Habit with ID '{habit_id}' not found")
                return False
            
            with console.status(f"[bold green]Checking off '{habit.name}'..."):
                if self.repository.add_check_off(habit_id, check_off_time):
                    # Refresh habit data to get updated streak
                    habit = self.repository.get_habit(habit_id)
                    
                    # Show success with streak information
                    streak_emoji = "🔥" if habit.get_current_streak() > 5 else "⭐" if habit.get_current_streak() > 0 else "🎯"
                    
                    success_panel = Panel(
                        f"[bold green]Habit Checked Off![/bold green]\n\n"
                        f"✅ [bold]{habit.name}[/bold]\n"
                        f"{streak_emoji} [bold]Current Streak:[/bold] {habit.get_current_streak()}\n"
                        f"📅 [bold]Completed:[/bold] {check_off_time.strftime('%Y-%m-%d %H:%M')}\n"
                        f"📊 [bold]Total Completions:[/bold] {len(habit.check_offs)}",
                        title="🎉 Great Job!",
                        border_style="green",
                        padding=(1, 2)
                    )
                    console.print(success_panel)
                    
                    # Show streak motivation
                    if habit.get_current_streak() > 0:
                        if habit.get_current_streak() == 1:
                            console.print("🌟 [bold yellow]You're off to a great start! Keep it up![/bold yellow]")
                        elif habit.get_current_streak() < 7:
                            console.print(f"🔥 [bold bright_red]Amazing! {habit.get_current_streak()} days in a row![/bold bright_red]")
                        elif habit.get_current_streak() < 30:
                            console.print(f"🚀 [bold purple]Incredible! {habit.get_current_streak()} days streak![/bold purple]")
                        else:
                            console.print(f"🏆 [bold bright_yellow]LEGENDARY! {habit.get_current_streak()} days streak![/bold bright_yellow]")
                    
                    return True
                else:
                    self._show_error("Could not check off habit. It may already be checked off for this period.")
                    console.print("\n[bold]Possible reasons:[/bold]")
                    console.print("• The habit was already completed for this period")
                    console.print("• The habit doesn't exist")
                    console.print("• There was a database error")
                    return False
        except Exception as e:
            self._show_error(f"Error checking off habit: {e}")
            return False
    
    def list_habits(self, periodicity: Optional[str] = None) -> None:
        """
        List all habits or filter by periodicity.
        
        Args:
            periodicity: Optional filter by "daily" or "weekly"
        """
        try:
            habits = self.repository.get_all_habits()
            
            if periodicity:
                try:
                    periodicity_enum = Periodicity(periodicity.lower())
                    habits = list_habits_by_periodicity(habits, periodicity_enum)
                    title = f"📋 {periodicity.title()} Habits"
                except ValueError:
                    self._show_error(f"Invalid periodicity: '{periodicity}'. Must be 'daily' or 'weekly'")
                    return
            else:
                title = "📋 All Habits"
            
            if not habits:
                empty_panel = Panel(
                    "[bold yellow]No habits found.[/bold yellow]\n\n"
                    "Create your first habit to get started!",
                    title="📝 Empty",
                    border_style="yellow",
                    padding=(1, 2)
                )
                console.print(empty_panel)
                return
            
            # Create a beautiful table
            table = Table(
                title=title,
                show_header=True,
                header_style="bold magenta",
                box=box.ROUNDED,
                border_style="blue"
            )
            
            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Type", style="green", justify="center")
            table.add_column("Current Streak", style="yellow", justify="center")
            table.add_column("Best Streak", style="blue", justify="center")
            table.add_column("Completions", style="purple", justify="center")
            table.add_column("ID", style="dim", no_wrap=True)
            
            for habit in habits:
                current_streak = habit.get_current_streak()
                longest_streak = habit.get_longest_streak()
                
                # Add streak emoji
                streak_emoji = ""
                if current_streak > 0:
                    if current_streak >= 30:
                        streak_emoji = "🏆 "
                    elif current_streak >= 7:
                        streak_emoji = "🔥 "
                    else:
                        streak_emoji = "⭐ "
                
                # Add periodicity emoji
                period_emoji = "📅" if habit.periodicity == Periodicity.DAILY else "📆"
                
                table.add_row(
                    habit.name,
                    f"{period_emoji} {habit.periodicity.value.title()}",
                    f"{streak_emoji}{current_streak}",
                    str(longest_streak),
                    str(len(habit.check_offs)),
                    habit.id[:8] + "..." if len(habit.id) > 8 else habit.id
                )
            
            console.print(table)
            
            # Show summary
            total_habits = len(habits)
            total_completions = sum(len(habit.check_offs) for habit in habits)
            active_streaks = sum(1 for habit in habits if habit.get_current_streak() > 0)
            
            summary_panel = Panel(
                f"[bold]Summary:[/bold]\n"
                f"• Total habits: [bold cyan]{total_habits}[/bold cyan]\n"
                f"• Active streaks: [bold green]{active_streaks}[/bold green]\n"
                f"• Total completions: [bold blue]{total_completions}[/bold blue]",
                title="📊 Quick Stats",
                border_style="green",
                padding=(0, 1)
            )
            console.print(summary_panel)
            
        except Exception as e:
            self._show_error(f"Error listing habits: {e}")
    
    def show_analytics(self) -> None:
        """Show comprehensive analytics."""
        try:
            habits = self.repository.get_all_habits()
            
            if not habits:
                empty_panel = Panel(
                    "[bold yellow]No habits found.[/bold yellow]\n\n"
                    "Create some habits first to see analytics!",
                    title="📊 Analytics Dashboard",
                    border_style="yellow",
                    padding=(1, 2)
                )
                console.print(empty_panel)
                return
            
            # Main analytics panel
            console.print(Panel(
                "[bold blue]📊 Habit Analytics Dashboard[/bold blue]",
                border_style="blue",
                padding=(0, 1)
            ))
            
            # Basic statistics
            stats = get_habit_statistics(habits)
            
            # Create overview table
            overview_table = Table(
                title="📈 Overview",
                show_header=True,
                header_style="bold cyan",
                box=box.ROUNDED,
                border_style="cyan"
            )
            
            overview_table.add_column("Metric", style="bold")
            overview_table.add_column("Value", style="green", justify="center")
            
            overview_table.add_row("Total Habits", str(stats['total_habits']))
            overview_table.add_row("Daily Habits", str(stats['daily_habits']))
            overview_table.add_row("Weekly Habits", str(stats['weekly_habits']))
            overview_table.add_row("Total Completions", str(stats['total_check_offs']))
            overview_table.add_row("Avg Completions/Habit", f"{stats['average_check_offs_per_habit']:.1f}")
            
            console.print(overview_table)
            
            # Longest streak overall
            habit, streak = get_longest_streak_overall(habits)
            if habit and streak > 0:
                champion_panel = Panel(
                    f"[bold bright_yellow]🏆 CHAMPION HABIT[/bold bright_yellow]\n\n"
                    f"[bold]{habit.name}[/bold]\n"
                    f"[bold bright_yellow]{streak} days streak![/bold bright_yellow]\n"
                    f"Periodicity: {habit.periodicity.value.title()}",
                    title="👑 Record Holder",
                    border_style="bright_yellow",
                    padding=(1, 2)
                )
                console.print(champion_panel)
            else:
                console.print("🏆 [dim]No streaks yet - start building them![/dim]")
            
            # Current streaks
            current_streaks = get_current_streaks(habits)
            active_streaks = {name: streak for name, streak in current_streaks.items() if streak > 0}
            
            if active_streaks:
                streaks_table = Table(
                    title="🔥 Active Streaks",
                    show_header=True,
                    header_style="bold bright_red",
                    box=box.ROUNDED,
                    border_style="bright_red"
                )
                
                streaks_table.add_column("Habit", style="cyan")
                streaks_table.add_column("Current Streak", style="bold bright_red", justify="center")
                streaks_table.add_column("Status", justify="center")
                
                for name, streak in sorted(active_streaks.items(), key=lambda x: x[1], reverse=True):
                    if streak >= 30:
                        status = "🏆 LEGENDARY"
                        status_style = "bold bright_yellow"
                    elif streak >= 7:
                        status = "🔥 ON FIRE"
                        status_style = "bold red"
                    else:
                        status = "⭐ BUILDING"
                        status_style = "bold yellow"
                    
                    streaks_table.add_row(
                        name,
                        str(streak),
                        f"[{status_style}]{status}[/{status_style}]"
                    )
                
                console.print(streaks_table)
            else:
                console.print("🔥 [dim]No active streaks - time to start![/dim]")
            
            # Longest streaks per habit
            longest_streaks = get_longest_streak_per_habit(habits)
            if longest_streaks:
                best_table = Table(
                    title="📈 Best Streaks (All Time)",
                    show_header=True,
                    header_style="bold purple",
                    box=box.ROUNDED,
                    border_style="purple"
                )
                
                best_table.add_column("Habit", style="cyan")
                best_table.add_column("Best Streak", style="bold purple", justify="center")
                best_table.add_column("Achievement", justify="center")
                
                for name, streak in sorted(longest_streaks.items(), key=lambda x: x[1], reverse=True):
                    if streak >= 30:
                        achievement = "🏆 MASTER"
                        achievement_style = "bold bright_yellow"
                    elif streak >= 7:
                        achievement = "🔥 EXPERT"
                        achievement_style = "bold red"
                    elif streak > 0:
                        achievement = "⭐ ROOKIE"
                        achievement_style = "bold yellow"
                    else:
                        achievement = "🎯 STARTING"
                        achievement_style = "dim"
                    
                    best_table.add_row(
                        name,
                        str(streak),
                        f"[{achievement_style}]{achievement}[/{achievement_style}]"
                    )
                
                console.print(best_table)
            
            # Completion rates
            completion_rates = stats['completion_rates']
            if completion_rates:
                rates_table = Table(
                    title="📊 Completion Rates",
                    show_header=True,
                    header_style="bold green",
                    box=box.ROUNDED,
                    border_style="green"
                )
                
                rates_table.add_column("Period", style="cyan")
                rates_table.add_column("Rate", style="bold green", justify="center")
                rates_table.add_column("Progress", justify="center")
                
                for period, rate in completion_rates.items():
                    # Create a simple progress bar
                    filled = int(rate * 10)
                    progress_bar = "█" * filled + "░" * (10 - filled)
                    
                    rates_table.add_row(
                        period.title(),
                        f"{rate:.1%}",
                        f"[green]{progress_bar}[/green]"
                    )
                
                console.print(rates_table)
            
        except Exception as e:
            self._show_error(f"Error showing analytics: {e}")


# Global CLI instance
cli_instance = None


def get_cli() -> HabitTrackerCLI:
    """Get the global CLI instance."""
    global cli_instance
    if cli_instance is None:
        cli_instance = HabitTrackerCLI()
    return cli_instance


@click.group()
@click.option('--backend', default='sqlite', type=click.Choice(['sqlite', 'json']),
              help='Storage backend to use (sqlite or json)')
@click.option('--db-path', help='Path to database file (for sqlite) or JSON file (for json)')
@click.version_option(version='1.0.0', prog_name='Habit Tracker')
@click.pass_context
def main(ctx, backend, db_path):
    """
    🏃‍♂️ Habit Tracker - Beautiful CLI for tracking daily and weekly habits.
    
    Track your habits, build streaks, and achieve your goals with comprehensive analytics.
    
    Examples:
        habit-tracker menu                    # Start interactive menu
        habit-tracker create "Exercise" daily # Create a daily habit
        habit-tracker list                    # List all habits
        habit-tracker analytics               # View detailed analytics
    """
    global cli_instance
    cli_instance = HabitTrackerCLI(backend, db_path)
    ctx.ensure_object(dict)
    ctx.obj['cli'] = cli_instance


@main.command()
@click.argument('name')
@click.argument('periodicity', type=click.Choice(['daily', 'weekly']))
@click.pass_context
def create(ctx, name, periodicity):
    """Create a new habit with the specified name and periodicity."""
    cli = ctx.obj['cli']
    cli.create_habit(name, periodicity)


@main.command()
@click.argument('habit_id')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation dialog')
@click.pass_context
def delete(ctx, habit_id, force):
    """Delete a habit by ID."""
    cli = ctx.obj['cli']
    cli.delete_habit(habit_id, force)


@main.command()
@click.argument('habit_id')
@click.option('--time', help='Check-off time (YYYY-MM-DD HH:MM:SS)')
@click.pass_context
def checkoff(ctx, habit_id, time):
    """Check off a habit."""
    cli = ctx.obj['cli']
    
    check_off_time = None
    if time:
        try:
            check_off_time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            click.echo("❌ Invalid time format. Use YYYY-MM-DD HH:MM:SS")
            return
    
    cli.check_off_habit(habit_id, check_off_time)


@main.command()
@click.option('--periodicity', type=click.Choice(['daily', 'weekly']),
              help='Filter by periodicity')
@click.pass_context
def list(ctx, periodicity):
    """List all habits or filter by periodicity."""
    cli = ctx.obj['cli']
    cli.list_habits(periodicity)


@main.command()
@click.pass_context
def analytics(ctx):
    """Show comprehensive analytics dashboard with streaks, completion rates, and achievements."""
    cli = ctx.obj['cli']
    cli.show_analytics()


@main.command()
@click.pass_context
def status(ctx):
    """Show a quick status overview of all habits."""
    cli = ctx.obj['cli']
    habits = cli.repository.get_all_habits()
    
    if not habits:
        console.print(Panel(
            "[bold yellow]No habits found.[/bold yellow]\n\n"
            "Create your first habit to get started!",
            title="📝 No Habits",
            border_style="yellow",
            padding=(1, 2)
        ))
        return
    
    # Quick status table
    status_table = Table(
        title="📊 Quick Status",
        show_header=True,
        header_style="bold cyan",
        box=box.ROUNDED,
        border_style="cyan"
    )
    
    status_table.add_column("Habit", style="cyan", no_wrap=True)
    status_table.add_column("Type", style="green", justify="center")
    status_table.add_column("Streak", style="yellow", justify="center")
    status_table.add_column("Status", justify="center")
    
    for habit in habits:
        current_streak = habit.get_current_streak()
        period_emoji = "📅" if habit.periodicity == Periodicity.DAILY else "📆"
        
        if current_streak > 0:
            if current_streak >= 7:
                status_text = "🔥 ON FIRE"
                status_style = "bold red"
            else:
                status_text = "⭐ ACTIVE"
                status_style = "bold yellow"
        else:
            status_text = "🎯 READY"
            status_style = "dim"
        
        status_table.add_row(
            habit.name,
            f"{period_emoji} {habit.periodicity.value.title()}",
            str(current_streak),
            f"[{status_style}]{status_text}[/{status_style}]"
        )
    
    console.print(status_table)


@main.command()
@click.pass_context
def sample(ctx):
    """Populate the database with sample data for testing."""
    cli = ctx.obj['cli']
    
    # Check if habits already exist
    existing_habits = cli.repository.get_all_habits()
    if existing_habits:
        if not Confirm.ask("Habits already exist. This will add sample data. Continue?", default=False):
            console.print("❌ [yellow]Sample data import cancelled.[/yellow]")
            return
    
    try:
        from .sample_data import populate_sample_data
        
        with console.status("[bold green]Importing sample data..."):
            populate_sample_data(cli.repository)
        
        console.print(Panel(
            "[bold green]Sample data imported successfully![/bold green]\n\n"
            "Added 5 sample habits with 4 weeks of realistic data:\n"
            "• 3 daily habits (Brush teeth, Exercise, Read)\n"
            "• 2 weekly habits (Grocery shop, Clean house)\n\n"
            "Use 'list' command to see all habits or 'analytics' for insights!",
            title="🎉 Sample Data Imported",
            border_style="green",
            padding=(1, 2)
        ))
    except ImportError:
        cli._show_error("Sample data module not available")
    except Exception as e:
        cli._show_error(f"Error importing sample data: {e}")


@main.command()
@click.pass_context
def menu(ctx):
    """Interactive menu for habit tracking."""
    cli = ctx.obj['cli']
    
    # Welcome message
    welcome_panel = Panel(
        "[bold blue]Welcome to Habit Tracker![/bold blue]\n\n"
        "Track your daily and weekly habits with beautiful analytics.\n"
        "Build streaks, stay motivated, and achieve your goals! 🎯",
        title="🏃‍♂️ Habit Tracker",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(welcome_panel)
    
    while True:
        # Main menu with arrow navigation
        try:
            questions = [
                inquirer.List(
                    'choice',
                    message="🎯 What would you like to do?",
                    choices=[
                        "📝 Create a new habit",
                        "📋 List all habits", 
                        "✅ Check off a habit",
                        "🗑️ Delete a habit",
                        "📊 View analytics",
                        "❓ Show help",
                        "👋 Exit"
                    ],
                    carousel=True
                )
            ]
            answers = inquirer.prompt(questions)
            if answers is None:  # User pressed Ctrl+C
                console.print("\n👋 [bold yellow]Goodbye![/bold yellow]")
                break
            choice = answers['choice']
        except KeyboardInterrupt:
            console.print("\n👋 [bold yellow]Goodbye![/bold yellow]")
            break
        
        if choice == "📝 Create a new habit":
            # Create habit
            console.print("\n[bold green]📝 Creating New Habit[/bold green]")
            name = Prompt.ask("Enter habit name")
            periodicity = Prompt.ask(
                "Enter periodicity", 
                choices=["daily", "weekly"],
                default="daily"
            )
            cli.create_habit(name, periodicity)
        
        elif choice == "📋 List all habits":
            # List habits
            console.print("\n[bold blue]📋 Listing Habits[/bold blue]")
            filter_choice = Confirm.ask("Filter by periodicity?", default=False)
            if filter_choice:
                periodicity = Prompt.ask(
                    "Enter periodicity", 
                    choices=["daily", "weekly"]
                )
                cli.list_habits(periodicity)
            else:
                cli.list_habits()
        
        elif choice == "✅ Check off a habit":
            # Check off habit
            console.print("\n[bold green]✅ Check Off Habit[/bold green]")
            habits = cli.repository.get_all_habits()
            if not habits:
                cli._show_error("No habits found. Create some habits first!")
                continue
            
            # Create habit selection table
            selection_table = Table(
                title="Available Habits",
                show_header=True,
                header_style="bold green",
                box=box.ROUNDED,
                border_style="green"
            )
            
            selection_table.add_column("#", style="cyan", justify="center")
            selection_table.add_column("Name", style="bold")
            selection_table.add_column("Type", style="green", justify="center")
            selection_table.add_column("Current Streak", style="yellow", justify="center")
            
            for i, habit in enumerate(habits, 1):
                current_streak = habit.get_current_streak()
                streak_emoji = "🔥" if current_streak > 5 else "⭐" if current_streak > 0 else "🎯"
                period_emoji = "📅" if habit.periodicity == Periodicity.DAILY else "📆"
                
                selection_table.add_row(
                    str(i),
                    habit.name,
                    f"{period_emoji} {habit.periodicity.value.title()}",
                    f"{streak_emoji} {current_streak}"
                )
            
            console.print(selection_table)
            
            try:
                habit_choices = [f"{habit.name} ({habit.periodicity.value})" for habit in habits]
                questions = [
                    inquirer.List(
                        'habit',
                        message="Choose a habit to check off:",
                        choices=habit_choices,
                        carousel=True
                    )
                ]
                answers = inquirer.prompt(questions)
                if answers is None:  # User pressed Ctrl+C
                    console.print("❌ [yellow]Cancelled.[/yellow]")
                    continue
                selected_choice = answers['habit']
                # Find the selected habit
                selected_habit = None
                for habit in habits:
                    if f"{habit.name} ({habit.periodicity.value})" == selected_choice:
                        selected_habit = habit
                        break
                cli.check_off_habit(selected_habit.id)
            except KeyboardInterrupt:
                console.print("❌ [yellow]Cancelled.[/yellow]")
                continue
        
        elif choice == "🗑️ Delete a habit":
            # Delete habit
            console.print("\n[bold red]🗑️ Delete Habit[/bold red]")
            habits = cli.repository.get_all_habits()
            if not habits:
                cli._show_error("No habits found.")
                continue
            
            # Create habit selection table
            selection_table = Table(
                title="Habits to Delete",
                show_header=True,
                header_style="bold red",
                box=box.ROUNDED,
                border_style="red"
            )
            
            selection_table.add_column("#", style="cyan", justify="center")
            selection_table.add_column("Name", style="bold")
            selection_table.add_column("Type", style="green", justify="center")
            selection_table.add_column("Completions", style="purple", justify="center")
            
            for i, habit in enumerate(habits, 1):
                period_emoji = "📅" if habit.periodicity == Periodicity.DAILY else "📆"
                
                selection_table.add_row(
                    str(i),
                    habit.name,
                    f"{period_emoji} {habit.periodicity.value.title()}",
                    str(len(habit.check_offs))
                )
            
            console.print(selection_table)
            
            try:
                habit_choices = [f"{habit.name} ({habit.periodicity.value})" for habit in habits]
                questions = [
                    inquirer.List(
                        'habit',
                        message="Choose a habit to delete:",
                        choices=habit_choices,
                        carousel=True
                    )
                ]
                answers = inquirer.prompt(questions)
                if answers is None:  # User pressed Ctrl+C
                    console.print("❌ [yellow]Cancelled.[/yellow]")
                    continue
                selected_choice = answers['habit']
                # Find the selected habit
                selected_habit = None
                for habit in habits:
                    if f"{habit.name} ({habit.periodicity.value})" == selected_choice:
                        selected_habit = habit
                        break
                cli.delete_habit(selected_habit.id)
            except KeyboardInterrupt:
                console.print("❌ [yellow]Cancelled.[/yellow]")
                continue
        
        elif choice == "📊 View analytics":
            # Show analytics
            console.print("\n[bold blue]📊 Analytics Dashboard[/bold blue]")
            cli.show_analytics()
        
        elif choice == "❓ Show help":
            # Show help
            help_panel = Panel(
                "[bold cyan]Habit Tracker Help[/bold cyan]\n\n"
                "[bold]Creating Habits:[/bold]\n"
                "• Choose a clear, specific name\n"
                "• Select daily or weekly periodicity\n"
                "• Start with 1-3 habits maximum\n\n"
                "[bold]Building Streaks:[/bold]\n"
                "• Check off habits consistently\n"
                "• Don't break the chain!\n"
                "• Focus on progress, not perfection\n\n"
                "[bold]Analytics:[/bold]\n"
                "• View your progress over time\n"
                "• Track completion rates\n"
                "• Celebrate your achievements!\n\n"
                "[bold]Tips:[/bold]\n"
                "• Start small and build momentum\n"
                "• Use the interactive menu for easy access\n"
                "• Review analytics regularly for motivation",
                title="❓ Help & Tips",
                border_style="cyan",
                padding=(1, 2)
            )
            console.print(help_panel)
        
        elif choice == "👋 Exit":
            # Exit
            goodbye_panel = Panel(
                "[bold green]Thank you for using Habit Tracker![/bold green]\n\n"
                "Keep building those habits and achieving your goals! 🎯\n"
                "Remember: Consistency is key! 💪",
                title="👋 Goodbye",
                border_style="green",
                padding=(1, 2)
            )
            console.print(goodbye_panel)
            break
        
        else:
            cli._show_error("Invalid choice. Please try again.")
        
        # Pause before showing menu again
        if choice != 7:
            console.print("\n[dim]Press Enter to continue...[/dim]")
            try:
                input()
            except KeyboardInterrupt:
                console.print("\n👋 [bold yellow]Goodbye![/bold yellow]")
                break


if __name__ == '__main__':
    main()
