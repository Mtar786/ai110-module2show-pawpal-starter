"""
tests/test_pawpal.py — Automated tests for PawPal+ core logic.

Run with:  python -m pytest
"""

import pytest
from pawpal_system import Owner, Pet, Task, Scheduler


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_task():
    """A basic medium-priority task for reuse across tests."""
    return Task(title="Morning walk", category="walk", duration_minutes=30, priority="medium")


@pytest.fixture
def med_task():
    """A mandatory medication task."""
    return Task(title="Heartworm tablet", category="medication", duration_minutes=5, priority="high")


@pytest.fixture
def pet_with_tasks():
    """A Pet pre-loaded with two tasks."""
    pet = Pet(name="Mochi", species="dog", age_years=3)
    pet.add_task(Task(title="Walk", category="walk", duration_minutes=30, priority="high"))
    pet.add_task(Task(title="Feeding", category="feeding", duration_minutes=10, priority="medium"))
    return pet


@pytest.fixture
def owner_with_pets(pet_with_tasks):
    """An Owner with one pet already attached."""
    owner = Owner(name="Jordan", available_minutes=90)
    owner.add_pet(pet_with_tasks)
    return owner


@pytest.fixture
def scheduler(owner_with_pets):
    """A Scheduler loaded from owner_with_pets."""
    s = Scheduler(owner=owner_with_pets)
    s.load_tasks()
    return s


# ---------------------------------------------------------------------------
# Task tests
# ---------------------------------------------------------------------------

class TestTask:
    def test_mark_complete_sets_flag(self, sample_task):
        """mark_complete() should set completed to True."""
        assert sample_task.completed is False
        sample_task.mark_complete()
        assert sample_task.completed is True

    def test_mark_incomplete_resets_flag(self, sample_task):
        """mark_incomplete() should reset completed to False after it was True."""
        sample_task.mark_complete()
        sample_task.mark_incomplete()
        assert sample_task.completed is False

    def test_priority_rank_values(self):
        """priority_rank() should return 3/2/1 for high/medium/low."""
        assert Task(title="x", priority="high").priority_rank() == 3
        assert Task(title="x", priority="medium").priority_rank() == 2
        assert Task(title="x", priority="low").priority_rank() == 1

    def test_priority_rank_unknown_defaults_zero(self):
        """An unknown priority string should return 0."""
        assert Task(title="x", priority="urgent").priority_rank() == 0

    def test_scheduled_start_minutes_valid(self):
        """scheduled_start_minutes() should correctly parse HH:MM."""
        t = Task(title="x", scheduled_time="08:30")
        assert t.scheduled_start_minutes() == 8 * 60 + 30

    def test_scheduled_start_minutes_empty(self, sample_task):
        """scheduled_start_minutes() should return None when no time is set."""
        assert sample_task.scheduled_start_minutes() is None

    def test_str_includes_title_and_duration(self, sample_task):
        """__str__ should include the task title and duration."""
        result = str(sample_task)
        assert "Morning walk" in result
        assert "30" in result


# ---------------------------------------------------------------------------
# Pet tests
# ---------------------------------------------------------------------------

class TestPet:
    def test_add_task_increases_count(self, sample_task):
        """Adding a task to a Pet should increase its task list by 1."""
        pet = Pet(name="Luna", species="cat")
        initial_count = len(pet.tasks)
        pet.add_task(sample_task)
        assert len(pet.tasks) == initial_count + 1

    def test_remove_task_decreases_count(self, pet_with_tasks):
        """remove_task() should reduce the task list when the title matches."""
        count_before = len(pet_with_tasks.tasks)
        removed = pet_with_tasks.remove_task("Walk")
        assert removed is True
        assert len(pet_with_tasks.tasks) == count_before - 1

    def test_remove_task_returns_false_when_missing(self, pet_with_tasks):
        """remove_task() should return False if no task matches the title."""
        assert pet_with_tasks.remove_task("NonExistentTask") is False

    def test_get_tasks_by_category(self, pet_with_tasks):
        """get_tasks_by_category() should filter correctly."""
        walks = pet_with_tasks.get_tasks_by_category("walk")
        assert len(walks) == 1
        assert walks[0].title == "Walk"

    def test_get_tasks_by_priority(self, pet_with_tasks):
        """get_tasks_by_priority() should return only matching priority tasks."""
        high = pet_with_tasks.get_tasks_by_priority("high")
        assert all(t.priority == "high" for t in high)

    def test_total_care_minutes(self, pet_with_tasks):
        """total_care_minutes() should sum all task durations."""
        expected = sum(t.duration_minutes for t in pet_with_tasks.tasks)
        assert pet_with_tasks.total_care_minutes() == expected

    def test_pending_tasks_excludes_completed(self, pet_with_tasks):
        """pending_tasks() should not include tasks marked complete."""
        pet_with_tasks.tasks[0].mark_complete()
        pending = pet_with_tasks.pending_tasks()
        assert all(not t.completed for t in pending)
        assert len(pending) == len(pet_with_tasks.tasks) - 1


# ---------------------------------------------------------------------------
# Owner tests
# ---------------------------------------------------------------------------

class TestOwner:
    def test_add_pet_increases_count(self):
        """add_pet() should append to the pets list."""
        owner = Owner(name="Alex", available_minutes=60)
        owner.add_pet(Pet(name="Rex", species="dog"))
        assert len(owner.pets) == 1

    def test_remove_pet_success(self, owner_with_pets):
        """remove_pet() should return True and shrink the list."""
        count_before = len(owner_with_pets.pets)
        result = owner_with_pets.remove_pet("Mochi")
        assert result is True
        assert len(owner_with_pets.pets) == count_before - 1

    def test_remove_pet_missing_returns_false(self, owner_with_pets):
        """remove_pet() should return False for an unknown pet name."""
        assert owner_with_pets.remove_pet("Phantom") is False

    def test_get_pet_finds_by_name(self, owner_with_pets):
        """get_pet() should return the correct Pet object."""
        pet = owner_with_pets.get_pet("Mochi")
        assert pet is not None
        assert pet.name == "Mochi"

    def test_get_pet_case_insensitive(self, owner_with_pets):
        """get_pet() should work regardless of case."""
        assert owner_with_pets.get_pet("mochi") is not None
        assert owner_with_pets.get_pet("MOCHI") is not None

    def test_get_pet_returns_none_for_unknown(self, owner_with_pets):
        """get_pet() should return None when the pet doesn't exist."""
        assert owner_with_pets.get_pet("Unknown") is None

    def test_all_tasks_aggregates_across_pets(self, owner_with_pets):
        """all_tasks() should return every task from every pet."""
        total = sum(len(p.tasks) for p in owner_with_pets.pets)
        assert len(owner_with_pets.all_tasks()) == total

    def test_total_tasks_count(self, owner_with_pets):
        """total_tasks() should equal the sum of tasks across pets."""
        assert owner_with_pets.total_tasks() == len(owner_with_pets.all_tasks())


# ---------------------------------------------------------------------------
# Scheduler tests
# ---------------------------------------------------------------------------

class TestScheduler:
    def test_load_tasks_fills_queue(self, scheduler, owner_with_pets):
        """load_tasks() should populate task_queue from all pets."""
        expected = owner_with_pets.total_tasks()
        assert len(scheduler.task_queue) == expected

    def test_sort_by_priority_order(self, scheduler):
        """sort_by_priority() should place high-priority tasks before low ones."""
        sorted_tasks = scheduler.sort_by_priority()
        ranks = [t.priority_rank() for t in sorted_tasks]
        assert ranks == sorted(ranks, reverse=True)

    def test_generate_daily_plan_respects_budget(self, scheduler):
        """generate_daily_plan() should not exceed the owner's available_minutes."""
        plan = scheduler.generate_daily_plan()
        total = sum(t.duration_minutes for t in plan)
        assert total <= scheduler.owner.available_minutes

    def test_generate_daily_plan_always_includes_medication(self, owner_with_pets, med_task):
        """Medication tasks should always appear in the plan even if they push over budget."""
        # Set a very tight budget that wouldn't normally fit the med task
        owner_with_pets.available_minutes = 1
        owner_with_pets.pets[0].add_task(med_task)
        s = Scheduler(owner=owner_with_pets)
        s.load_tasks()
        plan = s.generate_daily_plan()
        categories = [t.category for t in plan]
        assert "medication" in categories

    def test_detect_conflicts_finds_overlapping_times(self):
        """detect_conflicts() should flag tasks with overlapping time windows."""
        owner = Owner(name="Test", available_minutes=60)
        pet = Pet(name="Buddy", species="dog")
        # Both start at 08:00 and last 30 min — clear overlap
        pet.add_task(Task(title="A", scheduled_time="08:00", duration_minutes=30, priority="high"))
        pet.add_task(Task(title="B", scheduled_time="08:15", duration_minutes=30, priority="medium"))
        owner.add_pet(pet)
        s = Scheduler(owner=owner)
        s.load_tasks()
        conflicts = s.detect_conflicts()
        assert len(conflicts) == 1

    def test_detect_conflicts_no_overlap(self):
        """detect_conflicts() should return empty list when tasks don't overlap."""
        owner = Owner(name="Test", available_minutes=60)
        pet = Pet(name="Buddy", species="dog")
        pet.add_task(Task(title="A", scheduled_time="08:00", duration_minutes=30, priority="high"))
        pet.add_task(Task(title="B", scheduled_time="09:00", duration_minutes=30, priority="medium"))
        owner.add_pet(pet)
        s = Scheduler(owner=owner)
        s.load_tasks()
        assert s.detect_conflicts() == []

    def test_get_recurring_tasks(self, scheduler):
        """get_recurring_tasks() should return only tasks with is_recurring=True."""
        recurring = scheduler.get_recurring_tasks()
        assert all(t.is_recurring for t in recurring)

    def test_explain_plan_returns_string(self, scheduler):
        """explain_plan() should return a non-empty string."""
        result = scheduler.explain_plan()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_explain_plan_empty_queue(self):
        """explain_plan() with no tasks should return the 'no tasks' message."""
        owner = Owner(name="Empty", available_minutes=60)
        s = Scheduler(owner=owner)
        result = s.explain_plan(plan=[])
        assert "No tasks" in result

    def test_add_task_grows_queue(self, scheduler, sample_task):
        """add_task() should append a task to the queue."""
        count_before = len(scheduler.task_queue)
        scheduler.add_task(sample_task)
        assert len(scheduler.task_queue) == count_before + 1

    def test_apply_recurring_tasks_length(self, scheduler):
        """apply_recurring_tasks(n) should return exactly n day-lists."""
        result = scheduler.apply_recurring_tasks(days=5)
        assert len(result) == 5
