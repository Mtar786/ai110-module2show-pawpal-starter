"""
tests/test_pawpal.py — Automated tests for PawPal+ core logic.

Run with:  python -m pytest

Coverage areas
--------------
TestTask          — completion flag, priority rank, time parsing, next_occurrence
TestPet           — add/remove tasks, category/priority filters, totals
TestOwner         — pet roster management, task aggregation
TestScheduler     — load/sort/filter, conflict detection, plan generation
TestSortByTime    — chronological ordering, untimed-tasks-last, ties
TestRecurrence    — next_occurrence() with daily/weekly/twice-daily patterns
TestConflicts     — overlap detection, exact-same-time, adjacent (no overlap)
TestFilterTasks   — pet-name, completion-status, category, combined filters
TestEdgeCases     — empty pets, empty owner, zero-minute budget, no recurring tasks
"""

import pytest
from datetime import date, timedelta
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


# ---------------------------------------------------------------------------
# Sort-by-time tests  (Phase 5)
# ---------------------------------------------------------------------------

def _scheduler_with_timed_tasks() -> Scheduler:
    """Helper: owner with tasks added out of order to verify sort correctness."""
    owner = Owner(name="Sort Test", available_minutes=180)
    pet = Pet(name="Buddy", species="dog")
    # Added deliberately out of chronological order
    pet.add_task(Task(title="Afternoon walk",  scheduled_time="14:00", duration_minutes=20, priority="medium"))
    pet.add_task(Task(title="Morning meds",    scheduled_time="07:00", duration_minutes=5,  priority="high"))
    pet.add_task(Task(title="Lunch feeding",   scheduled_time="12:00", duration_minutes=10, priority="high"))
    pet.add_task(Task(title="No-time grooming",scheduled_time="",      duration_minutes=15, priority="low"))
    pet.add_task(Task(title="Evening play",    scheduled_time="19:30", duration_minutes=25, priority="medium"))
    owner.add_pet(pet)
    s = Scheduler(owner=owner)
    s.load_tasks()
    return s


class TestSortByTime:
    def test_timed_tasks_in_chronological_order(self):
        """sort_by_time() must return timed tasks in ascending HH:MM order."""
        s = _scheduler_with_timed_tasks()
        result = s.sort_by_time()
        timed = [t for t in result if t.scheduled_time]
        times = [t.scheduled_time for t in timed]
        assert times == sorted(times), f"Expected sorted times, got {times}"

    def test_untimed_tasks_appear_last(self):
        """Tasks with no scheduled_time should follow all timed tasks."""
        s = _scheduler_with_timed_tasks()
        result = s.sort_by_time()
        # Find the index of the first untimed task
        untimed_indices = [i for i, t in enumerate(result) if not t.scheduled_time]
        timed_indices   = [i for i, t in enumerate(result) if t.scheduled_time]
        if untimed_indices and timed_indices:
            assert min(untimed_indices) > max(timed_indices), (
                "At least one untimed task appeared before a timed task."
            )

    def test_sort_by_time_does_not_mutate_queue(self):
        """sort_by_time() should return a new list, leaving task_queue unchanged."""
        s = _scheduler_with_timed_tasks()
        original_order = list(s.task_queue)
        s.sort_by_time()
        assert s.task_queue == original_order

    def test_sort_by_time_all_untimed(self):
        """When no task has a scheduled_time, sort_by_time() should still return all tasks."""
        owner = Owner(name="Test", available_minutes=60)
        pet = Pet(name="Cat", species="cat")
        pet.add_task(Task(title="A", duration_minutes=10, priority="low"))
        pet.add_task(Task(title="B", duration_minutes=20, priority="high"))
        owner.add_pet(pet)
        s = Scheduler(owner=owner)
        s.load_tasks()
        result = s.sort_by_time()
        assert len(result) == 2

    def test_sort_by_time_single_task(self):
        """sort_by_time() on a one-task queue should return that one task."""
        owner = Owner(name="Solo", available_minutes=60)
        pet = Pet(name="Dot", species="dog")
        pet.add_task(Task(title="Only task", scheduled_time="09:00", duration_minutes=10))
        owner.add_pet(pet)
        s = Scheduler(owner=owner)
        s.load_tasks()
        result = s.sort_by_time()
        assert len(result) == 1
        assert result[0].title == "Only task"


# ---------------------------------------------------------------------------
# Recurrence / next_occurrence tests  (Phase 5)
# ---------------------------------------------------------------------------

class TestRecurrence:
    def test_daily_next_occurrence_is_tomorrow(self):
        """A 'daily' task's next_occurrence should be today + 1 day."""
        t = Task(title="Daily walk", is_recurring=True, recurrence_pattern="daily")
        today = date.today()
        expected = (today + timedelta(days=1)).isoformat()
        assert t.next_occurrence() == expected

    def test_weekly_next_occurrence_is_seven_days(self):
        """A 'weekly' task's next_occurrence should be today + 7 days."""
        t = Task(title="Weekly groom", is_recurring=True, recurrence_pattern="weekly")
        today = date.today()
        expected = (today + timedelta(weeks=1)).isoformat()
        assert t.next_occurrence() == expected

    def test_twice_daily_next_occurrence_is_same_day(self):
        """A 'twice daily' task's next_occurrence should be today (same day, second slot)."""
        t = Task(title="Twice-daily meds", is_recurring=True, recurrence_pattern="twice daily")
        today = date.today()
        assert t.next_occurrence() == today.isoformat()

    def test_non_recurring_returns_empty_string(self):
        """next_occurrence() should return '' for a non-recurring task."""
        t = Task(title="One-off vet", is_recurring=False)
        assert t.next_occurrence() == ""

    def test_next_occurrence_with_custom_from_date(self):
        """next_occurrence() should accept an explicit from_date for predictable testing."""
        from datetime import date as d
        t = Task(title="Daily walk", is_recurring=True, recurrence_pattern="daily")
        from_date = d(2025, 1, 10)
        assert t.next_occurrence(from_date=from_date) == "2025-01-11"

    def test_weekly_from_specific_date(self):
        """Weekly task from a known date should advance exactly 7 days."""
        from datetime import date as d
        t = Task(title="Weekly groom", is_recurring=True, recurrence_pattern="weekly")
        from_date = d(2025, 1, 10)
        assert t.next_occurrence(from_date=from_date) == "2025-01-17"

    def test_recurring_tasks_all_have_next_occurrence(self, scheduler):
        """Every recurring task in the queue should produce a valid ISO date string."""
        for t in scheduler.get_recurring_tasks():
            result = t.next_occurrence()
            assert len(result) == 10, f"Expected ISO date string, got '{result}'"
            assert result[4] == "-" and result[7] == "-"


# ---------------------------------------------------------------------------
# Conflict-detection tests  (Phase 5 — expanded edge cases)
# ---------------------------------------------------------------------------

def _make_scheduler(tasks: list) -> Scheduler:
    """Helper: build a scheduler with a single pet loaded with the given tasks."""
    owner = Owner(name="Conflict Test", available_minutes=240)
    pet = Pet(name="Pepper", species="dog")
    for t in tasks:
        pet.add_task(t)
    owner.add_pet(pet)
    s = Scheduler(owner=owner)
    s.load_tasks()
    return s


class TestConflicts:
    def test_exact_same_start_time_is_conflict(self):
        """Two tasks starting at exactly the same time should conflict."""
        s = _make_scheduler([
            Task(title="A", scheduled_time="08:00", duration_minutes=15, priority="high"),
            Task(title="B", scheduled_time="08:00", duration_minutes=10, priority="medium"),
        ])
        assert len(s.detect_conflicts()) == 1

    def test_adjacent_tasks_are_not_conflicts(self):
        """A task ending at 08:30 and another starting at 08:30 should NOT conflict."""
        s = _make_scheduler([
            Task(title="A", scheduled_time="08:00", duration_minutes=30, priority="high"),
            Task(title="B", scheduled_time="08:30", duration_minutes=20, priority="medium"),
        ])
        # [08:00, 08:30) ends exactly when [08:30, 08:50) starts — no overlap
        assert s.detect_conflicts() == []

    def test_partial_overlap_is_conflict(self):
        """A task at 08:00+30min overlapping with one at 08:20+30min should conflict."""
        s = _make_scheduler([
            Task(title="A", scheduled_time="08:00", duration_minutes=30, priority="high"),
            Task(title="B", scheduled_time="08:20", duration_minutes=30, priority="medium"),
        ])
        assert len(s.detect_conflicts()) == 1

    def test_fully_contained_task_is_conflict(self):
        """A short task fully inside a long task's window should conflict."""
        s = _make_scheduler([
            Task(title="Long",  scheduled_time="08:00", duration_minutes=60, priority="high"),
            Task(title="Short", scheduled_time="08:15", duration_minutes=10, priority="medium"),
        ])
        assert len(s.detect_conflicts()) == 1

    def test_three_way_overlap_counts_all_pairs(self):
        """Three mutually-overlapping tasks should yield 3 conflict pairs."""
        s = _make_scheduler([
            Task(title="A", scheduled_time="08:00", duration_minutes=60, priority="high"),
            Task(title="B", scheduled_time="08:10", duration_minutes=60, priority="medium"),
            Task(title="C", scheduled_time="08:20", duration_minutes=60, priority="low"),
        ])
        assert len(s.detect_conflicts()) == 3

    def test_conflict_warnings_returns_strings(self):
        """conflict_warnings() should return a list of non-empty strings."""
        s = _make_scheduler([
            Task(title="A", scheduled_time="09:00", duration_minutes=30, priority="high"),
            Task(title="B", scheduled_time="09:15", duration_minutes=30, priority="medium"),
        ])
        warnings = s.conflict_warnings()
        assert len(warnings) == 1
        assert isinstance(warnings[0], str)
        assert len(warnings[0]) > 0

    def test_conflict_warnings_mentions_both_task_titles(self):
        """Each warning string should name both conflicting tasks."""
        s = _make_scheduler([
            Task(title="Morning meds", scheduled_time="08:00", duration_minutes=10, priority="high"),
            Task(title="Breakfast",    scheduled_time="08:05", duration_minutes=15, priority="medium"),
        ])
        warning = s.conflict_warnings()[0]
        assert "Morning meds" in warning
        assert "Breakfast" in warning

    def test_no_conflict_warnings_when_clear(self):
        """conflict_warnings() should return an empty list when no tasks overlap."""
        s = _make_scheduler([
            Task(title="A", scheduled_time="07:00", duration_minutes=20, priority="high"),
            Task(title="B", scheduled_time="08:00", duration_minutes=20, priority="medium"),
        ])
        assert s.conflict_warnings() == []

    def test_untimed_tasks_never_conflict(self):
        """Tasks without a scheduled_time should never appear in conflicts."""
        s = _make_scheduler([
            Task(title="A", scheduled_time="", duration_minutes=30, priority="high"),
            Task(title="B", scheduled_time="", duration_minutes=30, priority="medium"),
        ])
        assert s.detect_conflicts() == []


# ---------------------------------------------------------------------------
# Filter-tasks tests  (Phase 5)
# ---------------------------------------------------------------------------

@pytest.fixture
def two_pet_scheduler():
    """Scheduler with two pets, each having tasks of different categories/statuses."""
    owner = Owner(name="Filter Test", available_minutes=120)

    mochi = Pet(name="Mochi", species="dog")
    mochi.add_task(Task(title="Walk",    category="walk",      priority="high",   duration_minutes=30))
    mochi.add_task(Task(title="Meds",   category="medication", priority="high",   duration_minutes=5))

    luna = Pet(name="Luna", species="cat")
    luna.add_task(Task(title="Feeding", category="feeding",    priority="medium", duration_minutes=10))
    luna.add_task(Task(title="Litter",  category="other",      priority="low",    duration_minutes=10))

    owner.add_pet(mochi)
    owner.add_pet(luna)

    s = Scheduler(owner=owner)
    s.load_tasks()
    return s


class TestFilterTasks:
    def test_filter_by_pet_name(self, two_pet_scheduler):
        """filter_tasks(pet_name='Mochi') should return only Mochi's tasks."""
        result = two_pet_scheduler.filter_tasks(pet_name="Mochi")
        assert len(result) == 2
        titles = {t.title for t in result}
        assert titles == {"Walk", "Meds"}

    def test_filter_by_pet_name_case_insensitive(self, two_pet_scheduler):
        """pet_name filter should be case-insensitive."""
        lower = two_pet_scheduler.filter_tasks(pet_name="mochi")
        upper = two_pet_scheduler.filter_tasks(pet_name="MOCHI")
        assert len(lower) == len(upper) == 2

    def test_filter_by_completion_pending(self, two_pet_scheduler):
        """filter_tasks(completed=False) should return only incomplete tasks."""
        # Mark one task done
        two_pet_scheduler.task_queue[0].mark_complete()
        pending = two_pet_scheduler.filter_tasks(completed=False)
        assert all(not t.completed for t in pending)

    def test_filter_by_completion_done(self, two_pet_scheduler):
        """filter_tasks(completed=True) should return only completed tasks."""
        two_pet_scheduler.task_queue[0].mark_complete()
        done = two_pet_scheduler.filter_tasks(completed=True)
        assert len(done) == 1
        assert done[0].completed is True

    def test_filter_by_category(self, two_pet_scheduler):
        """filter_tasks(category='medication') should return only medication tasks."""
        result = two_pet_scheduler.filter_tasks(category="medication")
        assert len(result) == 1
        assert result[0].title == "Meds"

    def test_filter_combined_pet_and_category(self, two_pet_scheduler):
        """Combining pet_name and category should AND the conditions."""
        result = two_pet_scheduler.filter_tasks(pet_name="Mochi", category="walk")
        assert len(result) == 1
        assert result[0].title == "Walk"

    def test_filter_no_match_returns_empty(self, two_pet_scheduler):
        """filter_tasks with a non-existent pet name should return an empty list."""
        result = two_pet_scheduler.filter_tasks(pet_name="Ghost")
        assert result == []

    def test_filter_does_not_mutate_queue(self, two_pet_scheduler):
        """filter_tasks() must not alter task_queue."""
        original_len = len(two_pet_scheduler.task_queue)
        two_pet_scheduler.filter_tasks(pet_name="Luna", completed=False)
        assert len(two_pet_scheduler.task_queue) == original_len


# ---------------------------------------------------------------------------
# Edge-case tests  (Phase 5)
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_pet_with_no_tasks_has_zero_total_minutes(self):
        """A brand-new pet has zero care minutes."""
        assert Pet(name="Empty", species="cat").total_care_minutes() == 0

    def test_pet_with_no_tasks_pending_is_empty(self):
        """pending_tasks() on a pet with no tasks returns an empty list."""
        assert Pet(name="Empty", species="dog").pending_tasks() == []

    def test_owner_with_no_pets_all_tasks_is_empty(self):
        """all_tasks() returns [] for an owner who has no pets."""
        assert Owner(name="Solo").all_tasks() == []

    def test_owner_with_no_pets_total_tasks_is_zero(self):
        """total_tasks() returns 0 for an owner who has no pets."""
        assert Owner(name="Solo").total_tasks() == 0

    def test_scheduler_empty_queue_plan_is_empty(self):
        """generate_daily_plan() on an empty queue should return []."""
        owner = Owner(name="Empty", available_minutes=60)
        s = Scheduler(owner=owner)
        assert s.generate_daily_plan() == []

    def test_scheduler_zero_budget_only_meds_included(self):
        """With available_minutes=0, only mandatory medication tasks appear."""
        owner = Owner(name="Busy", available_minutes=0)
        pet = Pet(name="Dog", species="dog")
        pet.add_task(Task(title="Walk",  category="walk",       duration_minutes=30, priority="high"))
        pet.add_task(Task(title="Meds",  category="medication", duration_minutes=5,  priority="high"))
        owner.add_pet(pet)
        s = Scheduler(owner=owner)
        s.load_tasks()
        plan = s.generate_daily_plan()
        titles = [t.title for t in plan]
        assert "Meds" in titles
        assert "Walk" not in titles

    def test_scheduler_no_recurring_tasks_returns_empty(self):
        """get_recurring_tasks() returns [] when no tasks are recurring."""
        owner = Owner(name="Test", available_minutes=60)
        pet = Pet(name="Fido", species="dog")
        pet.add_task(Task(title="One-off vet", is_recurring=False, duration_minutes=60))
        owner.add_pet(pet)
        s = Scheduler(owner=owner)
        s.load_tasks()
        assert s.get_recurring_tasks() == []

    def test_single_task_has_no_conflicts(self):
        """A queue with one task can never have a scheduling conflict."""
        owner = Owner(name="Test", available_minutes=60)
        pet = Pet(name="Rex", species="dog")
        pet.add_task(Task(title="Walk", scheduled_time="08:00", duration_minutes=30))
        owner.add_pet(pet)
        s = Scheduler(owner=owner)
        s.load_tasks()
        assert s.detect_conflicts() == []

    def test_generate_plan_single_task_fits_in_budget(self):
        """A single task smaller than the budget should appear in the plan."""
        owner = Owner(name="Test", available_minutes=60)
        pet = Pet(name="Rex", species="dog")
        pet.add_task(Task(title="Short walk", duration_minutes=20, priority="high"))
        owner.add_pet(pet)
        s = Scheduler(owner=owner)
        s.load_tasks()
        plan = s.generate_daily_plan()
        assert len(plan) == 1
        assert plan[0].title == "Short walk"

    def test_generate_plan_single_task_too_long_excluded(self):
        """A single non-medication task longer than the budget should be excluded."""
        owner = Owner(name="Test", available_minutes=10)
        pet = Pet(name="Rex", species="dog")
        pet.add_task(Task(title="Long walk", duration_minutes=60, priority="high"))
        owner.add_pet(pet)
        s = Scheduler(owner=owner)
        s.load_tasks()
        plan = s.generate_daily_plan()
        assert plan == []
