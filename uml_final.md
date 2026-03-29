# PawPal+ — Final UML Class Diagram

This diagram reflects the **final implementation** in `pawpal_system.py` after all six project phases.
Paste the Mermaid code block into the [Mermaid Live Editor](https://mermaid.live) to render the diagram, or preview it in VS Code with the Mermaid Preview extension.

---

```mermaid
classDiagram
    direction TB

    class Task {
        +str title
        +str category
        +int duration_minutes
        +str priority
        +bool is_recurring
        +str recurrence_pattern
        +str scheduled_time
        +str notes
        +bool completed
        +str due_date
        +priority_rank() int
        +mark_complete() None
        +mark_incomplete() None
        +scheduled_start_minutes() int
        +next_occurrence(from_date) str
    }

    class Pet {
        +str name
        +str species
        +int age_years
        +str dietary_notes
        +List~Task~ tasks
        +add_task(task) None
        +remove_task(title) bool
        +get_tasks_by_category(category) List~Task~
        +get_tasks_by_priority(priority) List~Task~
        +total_care_minutes() int
        +pending_tasks() List~Task~
    }

    class Owner {
        +str name
        +int available_minutes
        +List~str~ preferences
        +List~Pet~ pets
        +add_pet(pet) None
        +remove_pet(pet_name) bool
        +get_pet(pet_name) Pet
        +all_tasks() List~Task~
        +total_tasks() int
    }

    class Scheduler {
        +Owner owner
        +List~Task~ task_queue
        +load_tasks() None
        +add_task(task) None
        +sort_by_priority() List~Task~
        +sort_by_time() List~Task~
        +filter_tasks(pet_name, completed, category) List~Task~
        +detect_conflicts() List~tuple~
        +conflict_warnings() List~str~
        +generate_daily_plan(available_minutes) List~Task~
        +explain_plan(plan) str
        +get_recurring_tasks() List~Task~
        +apply_recurring_tasks(days) List~List~
        +summary() str
    }

    Owner "1" *-- "1..*" Pet : owns
    Pet "1" *-- "*" Task : has
    Scheduler "1" --> "1" Owner : manages
    Scheduler ..> Task : schedules / filters / sorts
```

---

## Key changes from Phase 1 UML

| Change | Reason |
|---|---|
| Added `Task.completed: bool` | Required for `mark_complete/incomplete` and `filter_tasks(completed=...)` |
| Added `Task.due_date: str` | Stores computed next-occurrence date from `next_occurrence()` |
| Added `Task.next_occurrence(from_date)` | Recurring task date arithmetic using `timedelta`; placed on Task so it owns its own scheduling math |
| Added `Scheduler.sort_by_time()` | Sort by HH:MM wall-clock, untimed tasks last |
| Added `Scheduler.filter_tasks(pet_name, completed, category)` | AND-filtered view of the task queue without mutation |
| Added `Scheduler.conflict_warnings()` | Human-readable strings wrapping `detect_conflicts()` for UI display |
| Added `Pet.pending_tasks()` | Convenience helper filtering out completed tasks |
