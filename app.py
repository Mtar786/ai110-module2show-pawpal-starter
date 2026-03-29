"""
app.py — PawPal+ Streamlit UI.

Imports backend logic from pawpal_system.py and wires UI actions to class methods.
All application state (owner, pets, tasks) is persisted in st.session_state so
it survives re-renders caused by button clicks.
"""

import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(page_title="PawPal+", page_icon="", layout="wide")

# ---------------------------------------------------------------------------
# Session-state initialisation
# Streamlit re-runs this file top-to-bottom on every interaction.
# We check for existing objects in the "vault" before creating new ones,
# so data persists for the entire browser session.
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None          # Owner | None
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None      # Scheduler | None
if "last_plan" not in st.session_state:
    st.session_state.last_plan = []        # List[Task]

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("PawPal+")
st.caption("Smart pet care scheduling for busy owners.")
st.divider()

# ---------------------------------------------------------------------------
# Section 1 — Owner setup
# ---------------------------------------------------------------------------

st.header("1. Owner Profile")

with st.form("owner_form"):
    col1, col2 = st.columns(2)
    with col1:
        owner_name = st.text_input("Your name", value="Jordan")
    with col2:
        available_minutes = st.number_input(
            "Daily time budget (minutes)", min_value=10, max_value=480, value=120, step=10
        )
    submitted_owner = st.form_submit_button("Save owner profile")

if submitted_owner:
    # Create a fresh Owner (or update the existing one's budget while keeping pets)
    if st.session_state.owner is None:
        st.session_state.owner = Owner(
            name=owner_name,
            available_minutes=int(available_minutes),
        )
    else:
        st.session_state.owner.name = owner_name
        st.session_state.owner.available_minutes = int(available_minutes)
    # Rebuild scheduler whenever the owner changes
    st.session_state.scheduler = Scheduler(owner=st.session_state.owner)
    st.session_state.last_plan = []
    st.success(f"Owner profile saved: {st.session_state.owner}")

if st.session_state.owner:
    st.info(str(st.session_state.owner))

st.divider()

# ---------------------------------------------------------------------------
# Section 2 — Pet management
# ---------------------------------------------------------------------------

st.header("2. Pets")

if st.session_state.owner is None:
    st.warning("Save an owner profile above before adding pets.")
else:
    owner: Owner = st.session_state.owner

    # -- Add pet form --
    with st.expander("Add a new pet", expanded=len(owner.pets) == 0):
        with st.form("pet_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                pet_name = st.text_input("Pet name", value="Mochi")
            with col2:
                species = st.selectbox("Species", ["dog", "cat", "other"])
            with col3:
                age_years = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
            dietary_notes = st.text_input("Dietary notes (optional)", value="")
            submitted_pet = st.form_submit_button("Add pet")

        if submitted_pet:
            if owner.get_pet(pet_name):
                st.error(f"A pet named '{pet_name}' already exists.")
            else:
                new_pet = Pet(
                    name=pet_name,
                    species=species,
                    age_years=int(age_years),
                    dietary_notes=dietary_notes,
                )
                owner.add_pet(new_pet)           # Owner.add_pet() — Phase 2 method
                st.session_state.last_plan = []  # invalidate old plan
                st.success(f"Added {new_pet}")

    # -- Pet list --
    if owner.pets:
        for pet in owner.pets:
            with st.expander(f"{pet.name} ({pet.species}, {pet.age_years}yr) — {len(pet.tasks)} task(s)"):
                if pet.dietary_notes:
                    st.caption(f"Dietary notes: {pet.dietary_notes}")

                # Show existing tasks
                if pet.tasks:
                    task_data = [
                        {
                            "Title": t.title,
                            "Category": t.category,
                            "Duration (min)": t.duration_minutes,
                            "Priority": t.priority,
                            "Time": t.scheduled_time or "flexible",
                            "Recurring": t.recurrence_pattern if t.is_recurring else "no",
                            "Done": "yes" if t.completed else "no",
                        }
                        for t in pet.tasks
                    ]
                    st.table(task_data)
                else:
                    st.info("No tasks yet — add one below.")

                # Remove pet button
                if st.button(f"Remove {pet.name}", key=f"remove_{pet.name}"):
                    owner.remove_pet(pet.name)   # Owner.remove_pet() — Phase 2 method
                    st.session_state.last_plan = []
                    st.rerun()
    else:
        st.info("No pets yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Section 3 — Task management
# ---------------------------------------------------------------------------

st.header("3. Tasks")

if st.session_state.owner is None or not st.session_state.owner.pets:
    st.warning("Add at least one pet before scheduling tasks.")
else:
    owner = st.session_state.owner

    with st.form("task_form"):
        col1, col2 = st.columns(2)
        with col1:
            target_pet = st.selectbox("Assign to pet", [p.name for p in owner.pets])
            task_title = st.text_input("Task title", value="Morning walk")
            category = st.selectbox(
                "Category",
                ["walk", "feeding", "medication", "appointment", "enrichment", "grooming", "other"],
            )
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
            priority = st.selectbox("Priority", ["high", "medium", "low"], index=1)
            scheduled_time = st.text_input("Preferred time (HH:MM, optional)", value="")

        col3, col4 = st.columns(2)
        with col3:
            is_recurring = st.checkbox("Recurring task")
        with col4:
            recurrence_pattern = st.text_input(
                "Recurrence pattern (e.g. daily, weekly)", value="daily", disabled=not is_recurring
            )
        notes = st.text_input("Notes (optional)", value="")
        submitted_task = st.form_submit_button("Add task")

    if submitted_task:
        pet = owner.get_pet(target_pet)          # Owner.get_pet() — Phase 2 method
        new_task = Task(
            title=task_title,
            category=category,
            duration_minutes=int(duration),
            priority=priority,
            scheduled_time=scheduled_time.strip(),
            is_recurring=is_recurring,
            recurrence_pattern=recurrence_pattern if is_recurring else "",
            notes=notes,
        )
        pet.add_task(new_task)                   # Pet.add_task() — Phase 2 method
        st.session_state.last_plan = []          # invalidate plan so it regenerates
        st.success(f"Added task '{task_title}' to {pet.name}.")

st.divider()

# ---------------------------------------------------------------------------
# Section 4 — Schedule generation
# ---------------------------------------------------------------------------

st.header("4. Today's Schedule")

if st.session_state.owner is None:
    st.warning("Complete your owner profile first.")
elif not st.session_state.owner.pets:
    st.warning("Add at least one pet to generate a schedule.")
elif st.session_state.owner.total_tasks() == 0:
    st.warning("Add at least one task to generate a schedule.")
else:
    owner = st.session_state.owner

    col_gen, col_info = st.columns([1, 3])
    with col_gen:
        generate = st.button("Generate schedule", type="primary")

    if generate:
        sched = Scheduler(owner=owner)
        sched.load_tasks()                       # Scheduler.load_tasks() — Phase 2 method
        st.session_state.scheduler = sched
        st.session_state.last_plan = sched.generate_daily_plan()  # Phase 2 method

    plan = st.session_state.last_plan

    if plan:
        sched = st.session_state.scheduler

        # -- Conflict warnings --
        conflicts = sched.detect_conflicts()     # Scheduler.detect_conflicts() — Phase 2 method
        if conflicts:
            for a, b in conflicts:
                st.warning(f"[Conflict] '{a.title}' and '{b.title}' overlap in time.")

        # -- Plan table --
        st.subheader("Scheduled tasks")
        total_min = sum(t.duration_minutes for t in plan)
        remaining = owner.available_minutes - total_min
        st.caption(
            f"Budget: {owner.available_minutes} min | Planned: {total_min} min | Remaining: {remaining} min"
        )

        plan_data = []
        for i, t in enumerate(plan, start=1):
            plan_data.append({
                "#": i,
                "Task": t.title,
                "Pet": next((p.name for p in owner.pets if t in p.tasks), "—"),
                "Category": t.category,
                "Time": t.scheduled_time or "flexible",
                "Duration": f"{t.duration_minutes} min",
                "Priority": t.priority,
            })
        st.table(plan_data)

        # -- Plain-English explanation --
        with st.expander("Why were these tasks chosen?"):
            st.text(sched.explain_plan(plan))    # Scheduler.explain_plan() — Phase 2 method

        # -- Mark tasks complete --
        st.subheader("Mark tasks done")
        for task in plan:
            done = st.checkbox(
                f"{task.title} ({task.duration_minutes} min)",
                value=task.completed,
                key=f"done_{task.title}_{id(task)}",
            )
            if done:
                task.mark_complete()             # Task.mark_complete() — Phase 2 method
            else:
                task.mark_incomplete()

    elif st.session_state.scheduler is not None:
        st.info("No tasks fit within the current time budget.")
