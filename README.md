# PawPal+ (Module 2 Project)

**PawPal+** is a smart pet care scheduling assistant built with Python and Streamlit. It helps busy pet owners plan daily care tasks for their pets by intelligently sorting, filtering, and prioritising activities within a configurable time budget.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

## Features

### Core scheduling
- **Priority-based daily plan** — greedily builds a schedule from high to low priority, always including medication tasks regardless of budget
- **Mandatory task guarantee** — medication tasks are included even when the time budget is exhausted
- **Plain-English plan explanation** — each task in the plan comes with a reason (why it was chosen and when)

### Smart algorithms
- **Sort by time** — reorder the plan chronologically by `HH:MM`; tasks without a fixed time appear at the end
- **Sort by priority** — reorder from high to low priority, ties broken by duration (shortest first)
- **Filter by pet / status / category** — narrow the task view without mutating the underlying queue
- **Conflict detection** — finds all pairs of tasks whose time windows overlap; reports as human-readable warnings
- **Recurring task next-occurrence** — for `daily`, `weekly`, or `twice daily` tasks, computes the next due date using Python's `timedelta`

### UI features
- Sidebar sort/filter controls with live Apply button
- Conflict banner — red error if conflicts exist, green success when the plan is clean
- Budget metrics (total budget / planned minutes / remaining)
- "Mark done" checkboxes that reveal next-occurrence dates for recurring tasks
- Recurring task preview table showing upcoming due dates

## Project structure

```
pawpal_system.py   — backend logic (Task, Pet, Owner, Scheduler classes)
app.py             — Streamlit UI, wired to backend via st.session_state
main.py            — CLI demo script to verify logic without the UI
tests/
  test_pawpal.py   — 72 automated tests (pytest)
uml_final.md       — final Mermaid.js UML diagram with change log
reflection.md      — design decisions, tradeoffs, and AI collaboration notes
```

## 📸 Demo

<!-- Replace the path below with your screenshot once you capture it -->
<a href="/course_images/ai110/pawpal_screenshot.png" target="_blank">
  <img src='/course_images/ai110/pawpal_screenshot.png' title='PawPal App' width='' alt='PawPal App' class='center-block' />
</a>

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the CLI demo

```bash
python main.py
```

### Run tests

```bash
python -m pytest
```

### Launch the Streamlit UI

```bash
streamlit run app.py
```

---

## Smarter Scheduling

PawPal+ goes beyond a simple task list. The `Scheduler` class in `pawpal_system.py` implements four algorithms that make the daily plan intelligent:

### 1. Sort by time (`sort_by_time`)
Tasks are ordered by their `scheduled_time` (HH:MM) so the plan reads chronologically. Tasks with no fixed time appear at the end. Uses Python's `sorted()` with a tuple key — `(0, "HH:MM")` for timed tasks, `(1, "")` for untimed — so lexicographic comparison on zero-padded 24-hour strings gives the correct order.

### 2. Filter by pet or status (`filter_tasks`)
The task queue can be filtered by any combination of:
- **pet name** — see only tasks belonging to a specific pet
- **completion status** — see only pending or only done tasks
- **category** — see only walks, medications, etc.

Filtering never mutates the queue; it returns a new list, so the original plan is preserved.

### 3. Recurring task next-occurrence (`Task.next_occurrence`)
When a recurring task is marked complete, `next_occurrence()` uses Python's `timedelta` to compute the next due date:
- `"daily"` → +1 day
- `"weekly"` → +7 days
- `"twice daily"` → same day (second slot)

This gives owners a concrete date to plan around rather than a vague label.

### 4. Conflict detection with warnings (`detect_conflicts` / `conflict_warnings`)
The scheduler finds pairs of tasks whose time windows `[start, start + duration)` overlap and returns human-readable warning strings instead of raising exceptions. This is a safe O(n²) strategy suited to a small daily task list (typically < 20 items).

---

## Testing PawPal+

### Run the test suite

```bash
python -m pytest
```

Add `-v` for verbose output showing every individual test name:

```bash
python -m pytest -v
```

### What the tests cover

The suite lives in `tests/test_pawpal.py` and contains **72 tests** across 8 test classes:

| Class | What is verified |
|---|---|
| `TestTask` | `mark_complete/incomplete`, `priority_rank`, `scheduled_start_minutes`, `__str__` |
| `TestPet` | `add/remove_task`, `get_tasks_by_category/priority`, `total_care_minutes`, `pending_tasks` |
| `TestOwner` | `add/remove/get_pet` (including case-insensitivity), `all_tasks`, `total_tasks` |
| `TestScheduler` | `load_tasks`, `sort_by_priority`, `generate_daily_plan` (budget + mandatory meds), `detect_conflicts`, `explain_plan`, `apply_recurring_tasks` |
| `TestSortByTime` | Chronological order, untimed-tasks-last, non-mutation of queue, single-task and all-untimed edge cases |
| `TestRecurrence` | `next_occurrence()` for daily (+1d), weekly (+7d), twice-daily (same day); non-recurring returns `''`; fixed-date determinism |
| `TestConflicts` | Exact same time, adjacent (no overlap), partial overlap, fully-contained, 3-way overlap, `conflict_warnings` string content, untimed tasks never conflict |
| `TestFilterTasks` | Filter by pet name, completion status, category, combined AND conditions, no-match → empty list, non-mutation |
| `TestEdgeCases` | Pet/owner with no tasks, empty scheduler plan, zero-minute budget (meds still included), single task fits/excluded, no-recurring returns `[]` |

### Confidence level

**4 / 5 stars**

The happy paths (sorting, filtering, plan generation, conflict detection) and the most important edge cases (empty pets, zero budget, mandatory meds, adjacent-but-not-overlapping times) are all covered and passing. The remaining gap is integration-level testing — e.g., verifying that changes made via the Streamlit UI are correctly reflected in `st.session_state` across re-renders. Those tests would require Streamlit's testing utilities and are the logical next step.

---

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
