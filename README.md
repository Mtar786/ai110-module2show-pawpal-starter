# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

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

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
