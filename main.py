"""
main.py — CLI demo script for PawPal+.

Run:  python main.py
Verifies that Owner, Pet, Task, and Scheduler all work together
before connecting the backend to the Streamlit UI.
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def build_demo() -> tuple[Owner, Scheduler]:
    """Create a sample owner with two pets and several tasks."""

    # ── Owner ──────────────────────────────────────────────────────────
    jordan = Owner(
        name="Jordan",
        available_minutes=90,
        preferences=["medication", "feeding", "walk"],
    )

    # ── Pet 1: Mochi the dog ──────────────────────────────────────────
    mochi = Pet(name="Mochi", species="dog", age_years=3)

    mochi.add_task(Task(
        title="Morning walk",
        category="walk",
        duration_minutes=30,
        priority="high",
        is_recurring=True,
        recurrence_pattern="daily",
        scheduled_time="07:30",
    ))
    mochi.add_task(Task(
        title="Heartworm tablet",
        category="medication",
        duration_minutes=5,
        priority="high",
        is_recurring=True,
        recurrence_pattern="daily",
        scheduled_time="08:00",
        notes="Give with food",
    ))
    mochi.add_task(Task(
        title="Evening play session",
        category="enrichment",
        duration_minutes=20,
        priority="medium",
        is_recurring=True,
        recurrence_pattern="daily",
        scheduled_time="18:00",
    ))
    mochi.add_task(Task(
        title="Brush coat",
        category="grooming",
        duration_minutes=15,
        priority="low",
        is_recurring=True,
        recurrence_pattern="weekly",
    ))

    # ── Pet 2: Luna the cat ───────────────────────────────────────────
    luna = Pet(name="Luna", species="cat", age_years=5, dietary_notes="grain-free kibble only")

    luna.add_task(Task(
        title="Breakfast feeding",
        category="feeding",
        duration_minutes=10,
        priority="high",
        is_recurring=True,
        recurrence_pattern="twice daily",
        scheduled_time="07:45",
    ))
    luna.add_task(Task(
        title="Thyroid medication",
        category="medication",
        duration_minutes=5,
        priority="high",
        is_recurring=True,
        recurrence_pattern="daily",
        scheduled_time="08:00",
        notes="Crush and mix into wet food",
    ))
    luna.add_task(Task(
        title="Litter box clean",
        category="other",
        duration_minutes=10,
        priority="medium",
        is_recurring=True,
        recurrence_pattern="daily",
    ))
    luna.add_task(Task(
        title="Vet check-up",
        category="appointment",
        duration_minutes=60,
        priority="medium",
        scheduled_time="14:00",
        notes="Annual vaccine booster",
    ))

    jordan.add_pet(mochi)
    jordan.add_pet(luna)

    # ── Scheduler ─────────────────────────────────────────────────────
    scheduler = Scheduler(owner=jordan)
    scheduler.load_tasks()

    return jordan, scheduler


def print_section(title: str) -> None:
    """Print a formatted section header."""
    width = 60
    print("\n" + "-" * width)
    print(f"  {title}")
    print("-" * width)


def main() -> None:
    """Run the full CLI demo."""
    print("=" * 60)
    print("  PawPal+  —  CLI Demo")
    print("=" * 60)

    jordan, scheduler = build_demo()

    # ── 1. Owner + pet overview ────────────────────────────────────────
    print_section("Owner & Pets")
    print(jordan)
    for pet in jordan.pets:
        print(f"  {pet}")
        for task in pet.tasks:
            print(f"    {task}")

    # ── 2. Scheduler summary ──────────────────────────────────────────
    print_section("Scheduler Summary")
    print(scheduler.summary())

    # ── 3. Sort by time (timed first, untimed at end) ────────────────
    print_section("Sort by Scheduled Time")
    by_time = scheduler.sort_by_time()
    for t in by_time:
        time_label = t.scheduled_time if t.scheduled_time else "(no time set)"
        print(f"  {time_label:<10}  {t.title}")

    # ── 4. Filter: Mochi's tasks only ────────────────────────────────
    print_section("Filter: Mochi's Tasks")
    mochi_tasks = scheduler.filter_tasks(pet_name="Mochi")
    for t in mochi_tasks:
        print(f"  {t}")

    # ── 5. Conflict detection (human-readable warnings) ───────────────
    print_section("Conflict Warnings")
    warnings = scheduler.conflict_warnings()
    if warnings:
        for w in warnings:
            print(f"  {w}")
    else:
        print("  No scheduling conflicts found.")

    # ── 6. Today's plan ───────────────────────────────────────────────
    print_section("Today's Schedule")
    plan = scheduler.generate_daily_plan()
    print(scheduler.explain_plan(plan))

    # ── 7. Recurring tasks — next occurrence via timedelta ────────────
    print_section("Next Occurrences (recurring tasks)")
    for t in scheduler.get_recurring_tasks():
        next_date = t.next_occurrence()
        print(f"  {t.title:<30}  next: {next_date}  ({t.recurrence_pattern})")

    # ── 8. mark_complete + next occurrence demo ───────────────────────
    print_section("Mark Complete -> Next Occurrence")
    if plan:
        first = plan[0]
        print(f"  Marking '{first.title}' as complete...")
        first.mark_complete()
        print(f"  Status   : {'DONE' if first.completed else 'pending'}")
        if first.is_recurring:
            print(f"  Next due : {first.next_occurrence()}")

    # ── 9. Filter: pending tasks only ─────────────────────────────────
    print_section("Filter: Pending Tasks After Completion")
    pending = scheduler.filter_tasks(completed=False)
    print(f"  {len(pending)} pending task(s) remaining:")
    for t in pending:
        print(f"    {t}")

    print("\n" + "=" * 60)
    print("  Demo complete — all systems nominal!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
