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
        completed:          Whether the task has been marked done today.
    """

    title: str
    category: str = "other"
    duration_minutes: int = 15
    priority: str = "medium"  # 'low' | 'medium' | 'high'
    is_recurring: bool = False
    recurrence_pattern: str = ""
    scheduled_time: str = ""   # HH:MM format, empty = flexible
    notes: str = ""
    completed: bool = False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def priority_rank(self) -> int:
        """Return a numeric rank for sorting (higher = more urgent)."""
        return {"high": 3, "medium": 2, "low": 1}.get(self.priority, 0)

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Reset this task to incomplete."""
        self.completed = False

    def scheduled_start_minutes(self) -> Optional[int]:
        """Parse scheduled_time ('HH:MM') into minutes-since-midnight, or None."""
        if not self.scheduled_time:
            return None
        try:
            h, m = self.scheduled_time.split(":")
            return int(h) * 60 + int(m)
        except (ValueError, AttributeError):
            return None

    def __str__(self) -> str:
        """Return a human-readable one-line summary of the task."""
        status = "[DONE]" if self.completed else f"[{self.priority.upper()}]"
        time_tag = f" @ {self.scheduled_time}" if self.scheduled_time else ""
        recur_tag = f" ({self.recurrence_pattern})" if self.is_recurring else ""
        return (
            f"{status} {self.title}"
            f" - {self.duration_minutes} min{time_tag}{recur_tag}"
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
        self.tasks.append(task)

    def remove_task(self, title: str) -> bool:
        """Remove the first task whose title matches (case-insensitive). Return True if found."""
        for i, t in enumerate(self.tasks):
            if t.title.lower() == title.lower():
                del self.tasks[i]
                return True
        return False

    def get_tasks_by_category(self, category: str) -> List[Task]:
        """Return all tasks belonging to the given category."""
        return [t for t in self.tasks if t.category.lower() == category.lower()]

    def get_tasks_by_priority(self, priority: str) -> List[Task]:
        """Return all tasks with the given priority level."""
        return [t for t in self.tasks if t.priority.lower() == priority.lower()]

    def total_care_minutes(self) -> int:
        """Sum of duration_minutes across all tasks."""
        return sum(t.duration_minutes for t in self.tasks)

    def pending_tasks(self) -> List[Task]:
        """Return only tasks that have not been marked complete."""
        return [t for t in self.tasks if not t.completed]

    def __str__(self) -> str:
        """Return a one-line description of this pet."""
        return f"{self.name} ({self.species}, {self.age_years}yr) - {len(self.tasks)} task(s)"


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
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> bool:
        """Remove the pet with the given name (case-insensitive). Return True if found."""
        for i, p in enumerate(self.pets):
            if p.name.lower() == pet_name.lower():
                del self.pets[i]
                return True
        return False

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Look up a pet by name (case-insensitive). Return None if not found."""
        for p in self.pets:
            if p.name.lower() == pet_name.lower():
                return p
        return None

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def all_tasks(self) -> List[Task]:
        """Collect every task across all pets owned by this owner."""
        tasks: List[Task] = []
        for pet in self.pets:
            tasks.extend(pet.tasks)
        return tasks

    def total_tasks(self) -> int:
        """Count of all tasks across all pets."""
        return sum(len(p.tasks) for p in self.pets)

    def __str__(self) -> str:
        """Return a readable summary of this owner and their pets."""
        pet_names = ", ".join(p.name for p in self.pets) or "no pets"
        return (
            f"Owner: {self.name} | Pets: {pet_names} | "
            f"Daily budget: {self.available_minutes} min"
        )


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

# Priority order used when no explicit scheduled_time is set
_PRIORITY_RANK = {"high": 3, "medium": 2, "low": 1}

# Categories that are always included regardless of the time budget
_MANDATORY_CATEGORIES = {"medication"}


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
        """Initialise the scheduler for the given owner."""
        self.owner: Owner = owner
        self.task_queue: List[Task] = []

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_tasks(self) -> None:
        """Populate task_queue from all pets belonging to self.owner."""
        self.task_queue = list(self.owner.all_tasks())

    def add_task(self, task: Task) -> None:
        """Manually push a single task into the queue."""
        self.task_queue.append(task)

    # ------------------------------------------------------------------
    # Sorting and conflict detection
    # ------------------------------------------------------------------

    def sort_by_priority(self) -> List[Task]:
        """Return tasks sorted highest to lowest priority; ties broken by duration (shortest first)."""
        return sorted(
            self.task_queue,
            key=lambda t: (-t.priority_rank(), t.duration_minutes),
        )

    def detect_conflicts(self) -> List[tuple]:
        """Find pairs of tasks whose scheduled_time windows overlap.

        Two tasks conflict when both have a scheduled_time and their
        [start, start + duration) intervals intersect.

        Returns:
            List of (task_a, task_b) tuples for each conflicting pair.
        """
        timed = [t for t in self.task_queue if t.scheduled_start_minutes() is not None]
        conflicts: List[tuple] = []
        for i in range(len(timed)):
            for j in range(i + 1, len(timed)):
                a, b = timed[i], timed[j]
                a_start = a.scheduled_start_minutes()
                b_start = b.scheduled_start_minutes()
                a_end = a_start + a.duration_minutes
                b_end = b_start + b.duration_minutes
                # Overlap when intervals are not disjoint
                if a_start < b_end and b_start < a_end:
                    conflicts.append((a, b))
        return conflicts

    # ------------------------------------------------------------------
    # Plan generation
    # ------------------------------------------------------------------

    def generate_daily_plan(
        self,
        available_minutes: Optional[int] = None,
    ) -> List[Task]:
        """Build an ordered plan that fits within the owner's time budget.

        Strategy:
          1. Always include mandatory tasks (category == 'medication') first.
          2. Sort remaining tasks by priority (high → low), then duration (short first).
          3. Greedily add tasks until the budget is exhausted.
          4. Return the final list sorted by scheduled_time where available,
             then by priority for the rest.

        Args:
            available_minutes: Override the owner's default if provided.

        Returns:
            Ordered list of Task objects included in today's plan.
        """
        budget = available_minutes if available_minutes is not None else self.owner.available_minutes
        sorted_tasks = self.sort_by_priority()

        plan: List[Task] = []
        used_minutes = 0

        # Pass 1: mandatory tasks (always included)
        for task in sorted_tasks:
            if task.category.lower() in _MANDATORY_CATEGORIES:
                plan.append(task)
                used_minutes += task.duration_minutes

        # Pass 2: remaining tasks — greedy by priority
        for task in sorted_tasks:
            if task in plan:
                continue
            if used_minutes + task.duration_minutes <= budget:
                plan.append(task)
                used_minutes += task.duration_minutes

        # Final sort: timed tasks first (by wall-clock), then untimed by priority
        timed = sorted(
            [t for t in plan if t.scheduled_start_minutes() is not None],
            key=lambda t: t.scheduled_start_minutes(),
        )
        untimed = sorted(
            [t for t in plan if t.scheduled_start_minutes() is None],
            key=lambda t: -t.priority_rank(),
        )
        return timed + untimed

    def explain_plan(self, plan: Optional[List[Task]] = None) -> str:
        """Return a human-readable explanation of the daily plan.

        For each task, describes why it was selected and when it is scheduled.

        Args:
            plan: The plan to explain. If None, generate_daily_plan() is called.

        Returns:
            A multi-line string suitable for terminal or UI display.
        """
        if plan is None:
            plan = self.generate_daily_plan()

        if not plan:
            return "No tasks fit within today's time budget."

        total = sum(t.duration_minutes for t in plan)
        lines = [
            f"=== Today's PawPal+ Schedule for {self.owner.name} ===",
            f"    Time budget : {self.owner.available_minutes} min",
            f"    Planned time: {total} min across {len(plan)} task(s)",
            "",
        ]

        for i, task in enumerate(plan, start=1):
            time_str = f"@ {task.scheduled_time}" if task.scheduled_time else "(flexible)"

            # Reason string
            if task.category.lower() in _MANDATORY_CATEGORIES:
                reason = "mandatory - medication always included"
            elif task.priority == "high":
                reason = "high priority"
            elif task.priority == "medium":
                reason = "medium priority, fits in budget"
            else:
                reason = "low priority, fits in budget"

            recur = f" | repeats: {task.recurrence_pattern}" if task.is_recurring else ""
            lines.append(
                f"  {i:>2}. {task.title:<30} {time_str:<12}"
                f"  {task.duration_minutes:>3} min  [{reason}{recur}]"
            )
            if task.notes:
                lines.append(f"       Note: {task.notes}")

        lines.append("")
        lines.append(f"    Remaining budget: {self.owner.available_minutes - total} min")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Recurring tasks
    # ------------------------------------------------------------------

    def get_recurring_tasks(self) -> List[Task]:
        """Filter task_queue to only recurring tasks."""
        return [t for t in self.task_queue if t.is_recurring]

    def apply_recurring_tasks(self, days: int = 7) -> List[List[Task]]:
        """Project recurring tasks over the next *days* days.

        Each day receives a fresh copy of all recurring tasks.

        Returns:
            A list of length *days*, where each element is the list of
            recurring tasks for that day.
        """
        recurring = self.get_recurring_tasks()
        return [list(recurring) for _ in range(days)]

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def summary(self) -> str:
        """Return a one-line summary: owner name, pet count, and total task minutes."""
        total_min = sum(t.duration_minutes for t in self.task_queue)
        return (
            f"Scheduler | owner: {self.owner.name} | "
            f"pets: {len(self.owner.pets)} | "
            f"tasks: {len(self.task_queue)} ({total_min} min total)"
        )

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return f"Scheduler(owner={self.owner.name!r}, tasks={len(self.task_queue)})"
