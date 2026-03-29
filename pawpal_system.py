"""
pawpal_system.py — PawPal+ backend logic layer.

Classes: Task, Pet, Owner, Scheduler
All scheduling, conflict-detection, and plan-generation logic lives here.
The Streamlit UI (app.py) imports from this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet-care action (walk, feeding, medication, appointment, etc.).

    Attributes:
        title:              Short human-readable name, e.g. "Morning walk".
        category:           One of: 'walk', 'feeding', 'medication',
                            'appointment', 'enrichment', 'grooming', 'other'.
        duration_minutes:   How long the task takes.
        priority:           'low', 'medium', or 'high'.
        is_recurring:       True if the task repeats on a schedule.
        recurrence_pattern: Human-readable repeat cadence, e.g. 'daily',
                            'twice daily', 'weekly'.  Ignored when
                            is_recurring is False.
        scheduled_time:     Optional preferred wall-clock time, e.g. '08:00'.
        notes:              Free-text extra information.
    """

    title: str
    category: str = "other"
    duration_minutes: int = 15
    priority: str = "medium"  # 'low' | 'medium' | 'high'
    is_recurring: bool = False
    recurrence_pattern: str = ""
    scheduled_time: str = ""   # HH:MM format, empty = flexible
    notes: str = ""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def priority_rank(self) -> int:
        """Return a numeric rank for sorting (higher = more urgent)."""
        return {"high": 3, "medium": 2, "low": 1}.get(self.priority, 0)

    def __str__(self) -> str:
        time_tag = f" @ {self.scheduled_time}" if self.scheduled_time else ""
        return (
            f"[{self.priority.upper()}] {self.title}"
            f" ({self.duration_minutes} min){time_tag}"
        )


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Represents a single pet owned by an Owner.

    Attributes:
        name:           Pet's name.
        species:        'dog', 'cat', or 'other'.
        age_years:      Age in years (0 for < 1 year old).
        dietary_notes:  Free-text dietary restrictions or preferences.
        tasks:          Tasks associated with this pet.
    """

    name: str
    species: str = "dog"
    age_years: int = 1
    dietary_notes: str = ""
    tasks: List[Task] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Task management
    # ------------------------------------------------------------------

    def add_task(self, task: Task) -> None:
        """Attach a Task to this pet."""
        pass  # TODO: implement

    def remove_task(self, title: str) -> bool:
        """Remove the first task whose title matches.  Return True if found."""
        pass  # TODO: implement

    def get_tasks_by_category(self, category: str) -> List[Task]:
        """Return all tasks belonging to the given category."""
        pass  # TODO: implement

    def get_tasks_by_priority(self, priority: str) -> List[Task]:
        """Return all tasks with the given priority level."""
        pass  # TODO: implement

    def total_care_minutes(self) -> int:
        """Sum of duration_minutes across all tasks."""
        pass  # TODO: implement

    def __str__(self) -> str:
        return f"{self.name} ({self.species}, {self.age_years}yr)"


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    """Represents a pet owner who has one or more pets.

    Attributes:
        name:               Owner's name.
        available_minutes:  Total daily minutes available for pet care.
        preferences:        Ordered list of preferred task categories,
                            e.g. ['walk', 'feeding', 'medication'].
        pets:               Pets belonging to this owner.
    """

    name: str
    available_minutes: int = 120
    preferences: List[str] = field(default_factory=list)
    pets: List[Pet] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Pet management
    # ------------------------------------------------------------------

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's roster."""
        pass  # TODO: implement

    def remove_pet(self, pet_name: str) -> bool:
        """Remove the pet with the given name.  Return True if found."""
        pass  # TODO: implement

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Look up a pet by name (case-insensitive)."""
        pass  # TODO: implement

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def all_tasks(self) -> List[Task]:
        """Collect every task across all pets owned by this owner."""
        pass  # TODO: implement

    def total_tasks(self) -> int:
        """Count of all tasks across all pets."""
        pass  # TODO: implement

    def __str__(self) -> str:
        pet_names = ", ".join(p.name for p in self.pets) or "no pets"
        return f"Owner: {self.name} | Pets: {pet_names}"


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """Builds and explains a daily care plan for an Owner.

    The scheduler pulls tasks from all of the owner's pets, applies
    prioritisation rules, checks for conflicts, and produces an ordered
    list of tasks that fits within the owner's available time.

    Attributes:
        owner:      The Owner whose pets' tasks will be scheduled.
        task_queue: Flat list of tasks collected from all pets.
    """

    def __init__(self, owner: Owner) -> None:
        self.owner: Owner = owner
        self.task_queue: List[Task] = []

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_tasks(self) -> None:
        """Populate task_queue from all pets belonging to self.owner."""
        pass  # TODO: implement

    def add_task(self, task: Task) -> None:
        """Manually push a single task into the queue."""
        pass  # TODO: implement

    # ------------------------------------------------------------------
    # Sorting and conflict detection
    # ------------------------------------------------------------------

    def sort_by_priority(self) -> List[Task]:
        """Return tasks sorted highest → lowest priority.
        Tasks with the same priority are sub-sorted by duration (shorter first).
        """
        pass  # TODO: implement

    def detect_conflicts(self) -> List[tuple[Task, Task]]:
        """Find pairs of tasks whose scheduled_time windows overlap.
        Returns a list of (task_a, task_b) conflict pairs.
        """
        pass  # TODO: implement

    # ------------------------------------------------------------------
    # Plan generation
    # ------------------------------------------------------------------

    def generate_daily_plan(
        self,
        available_minutes: Optional[int] = None,
    ) -> List[Task]:
        """Build an ordered plan that respects the time budget.

        Strategy:
        1. Sort tasks by priority (high → low).
        2. Greedily include tasks until available_minutes is exhausted.
        3. Always include 'medication' tasks regardless of time budget.

        Args:
            available_minutes: Override the owner's default if provided.

        Returns:
            Ordered list of tasks included in today's plan.
        """
        pass  # TODO: implement

    def explain_plan(self, plan: Optional[List[Task]] = None) -> str:
        """Return a human-readable explanation of the daily plan.

        For each task in the plan, describe:
        - Why it was selected (priority / category / mandatory).
        - When it is scheduled (if scheduled_time is set).

        Args:
            plan: The plan to explain.  If None, generate_daily_plan() is
                  called first.

        Returns:
            A multi-line string suitable for display in the UI.
        """
        pass  # TODO: implement

    # ------------------------------------------------------------------
    # Recurring tasks
    # ------------------------------------------------------------------

    def get_recurring_tasks(self) -> List[Task]:
        """Filter task_queue to only recurring tasks."""
        pass  # TODO: implement

    def apply_recurring_tasks(self, days: int = 7) -> List[List[Task]]:
        """Project recurring tasks over the next *days* days.

        Returns a list of daily plans (each plan is a list of Tasks).
        """
        pass  # TODO: implement

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def summary(self) -> str:
        """One-line summary: owner name, pet count, total task minutes."""
        pass  # TODO: implement

    def __repr__(self) -> str:
        return f"Scheduler(owner={self.owner.name!r}, tasks={len(self.task_queue)})"
