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

    # ── 3. Conflict detection ─────────────────────────────────────────
    print_section("Conflict Check")
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        print(f"  {len(conflicts)} conflict(s) detected:")
        for a, b in conflicts:
            print(f"    [!] '{a.title}' overlaps with '{b.title}'")
    else:
        print("  No scheduling conflicts found.")

    # ── 4. Today's plan ───────────────────────────────────────────────
    print_section("Today's Schedule")
    plan = scheduler.generate_daily_plan()
    print(scheduler.explain_plan(plan))

    # ── 5. Recurring tasks (next 3 days preview) ──────────────────────
    print_section("Recurring Tasks (next 3 days)")
    weekly = scheduler.apply_recurring_tasks(days=3)
    for day_num, day_tasks in enumerate(weekly, start=1):
        titles = ", ".join(t.title for t in day_tasks) or "none"
        print(f"  Day {day_num}: {titles}")

    # ── 6. mark_complete demo ─────────────────────────────────────────
    print_section("Mark a Task Complete")
    if plan:
        first = plan[0]
        print(f"  Marking '{first.title}' as complete...")
        first.mark_complete()
        print(f"  Status: {'DONE' if first.completed else 'pending'}")

    print("\n" + "=" * 60)
    print("  Demo complete — all systems nominal!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
