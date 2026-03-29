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
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None
if "last_plan" not in st.session_state:
    st.session_state.last_plan = []

# ---------------------------------------------------------------------------
# Sidebar — filters and sort controls (only shown once a plan exists)
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Schedule Controls")

    sort_mode = st.radio(
        "Sort plan by",
        options=["Priority (high first)", "Scheduled time"],
        index=0,
    )

    st.markdown("---")
    st.subheader("Filter tasks")

    owner_obj: Owner | None = st.session_state.owner
    pet_names = [p.name for p in owner_obj.pets] if owner_obj else []

    filter_pet = st.selectbox(
        "Show tasks for pet",
        options=["All pets"] + pet_names,
    )
    filter_status = st.selectbox(
        "Completion status",
        options=["All", "Pending only", "Done only"],
    )
    filter_category = st.selectbox(
        "Category",
        options=["All", "walk", "feeding", "medication", "appointment",
                 "enrichment", "grooming", "other"],
    )

    if st.button("Apply filters", use_container_width=True):
        sched: Scheduler | None = st.session_state.scheduler
        if sched:
            kwargs = {}
            if filter_pet != "All pets":
                kwargs["pet_name"] = filter_pet
            if filter_status == "Pending only":
                kwargs["completed"] = False
            elif filter_status == "Done only":
                kwargs["completed"] = True
            if filter_category != "All":
                kwargs["category"] = filter_category

            filtered = sched.filter_tasks(**kwargs)
            if filtered:
                st.success(f"{len(filtered)} task(s) match your filters:")
                for t in filtered:
                    time_str = t.scheduled_time or "flexible"
                    status_icon = "✓" if t.completed else "○"
                    st.markdown(f"- **{status_icon} {t.title}** ({time_str}, {t.duration_minutes} min)")
            else:
                st.info("No tasks match the selected filters.")
        else:
            st.info("Generate a schedule first.")

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("PawPal+")
st.caption("Smart pet care scheduling — sorting, conflict detection, and recurring task tracking.")
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
    if st.session_state.owner is None:
        st.session_state.owner = Owner(
            name=owner_name,
            available_minutes=int(available_minutes),
        )
    else:
        st.session_state.owner.name = owner_name
        st.session_state.owner.available_minutes = int(available_minutes)
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
                owner.add_pet(new_pet)
                st.session_state.last_plan = []
                st.success(f"Added {new_pet}")

    if owner.pets:
        for pet in owner.pets:
            with st.expander(
                f"{pet.name} ({pet.species}, {pet.age_years}yr) — {len(pet.tasks)} task(s)"
            ):
                if pet.dietary_notes:
                    st.caption(f"Dietary notes: {pet.dietary_notes}")

                if pet.tasks:
                    task_data = [
                        {
                            "Title": t.title,
                            "Category": t.category,
                            "Duration (min)": t.duration_minutes,
                            "Priority": t.priority,
                            "Time": t.scheduled_time or "flexible",
                            "Recurring": t.recurrence_pattern if t.is_recurring else "—",
                            "Next occurrence": t.next_occurrence() if t.is_recurring else "—",
                            "Done": "yes" if t.completed else "no",
                        }
                        for t in pet.tasks
                    ]
                    st.table(task_data)
                else:
                    st.info("No tasks yet — add one below.")

                if st.button(f"Remove {pet.name}", key=f"remove_{pet.name}"):
                    owner.remove_pet(pet.name)
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
                ["walk", "feeding", "medication", "appointment",
                 "enrichment", "grooming", "other"],
            )
        with col2:
            duration = st.number_input(
                "Duration (minutes)", min_value=1, max_value=240, value=20
            )
            priority = st.selectbox("Priority", ["high", "medium", "low"], index=1)
            scheduled_time = st.text_input("Preferred time (HH:MM, optional)", value="")

        col3, col4 = st.columns(2)
        with col3:
            is_recurring = st.checkbox("Recurring task")
        with col4:
            recurrence_pattern = st.text_input(
                "Recurrence (e.g. daily, weekly)",
                value="daily",
                disabled=not is_recurring,
            )
        notes = st.text_input("Notes (optional)", value="")
        submitted_task = st.form_submit_button("Add task")

    if submitted_task:
        pet = owner.get_pet(target_pet)
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
        pet.add_task(new_task)
        st.session_state.last_plan = []
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

    col_gen, col_clear = st.columns([1, 1])
    with col_gen:
        generate = st.button("Generate schedule", type="primary", use_container_width=True)
    with col_clear:
        if st.button("Clear schedule", use_container_width=True):
            st.session_state.last_plan = []
            st.session_state.scheduler = None
            st.rerun()

    if generate:
        sched = Scheduler(owner=owner)
        sched.load_tasks()
        st.session_state.scheduler = sched
        st.session_state.last_plan = sched.generate_daily_plan()

    plan = st.session_state.last_plan

    if plan:
        sched = st.session_state.scheduler

        # ── Conflict warnings (prominent banner) ──────────────────────
        warnings = sched.conflict_warnings()
        if warnings:
            st.error(
                f"**{len(warnings)} scheduling conflict(s) detected** — "
                "two or more tasks overlap in time. Consider adjusting their start times."
            )
            with st.expander("View conflict details"):
                for w in warnings:
                    st.warning(w)
        else:
            st.success("No scheduling conflicts — your plan looks clean!")

        # ── Sort plan according to sidebar control ─────────────────────
        if sort_mode == "Scheduled time":
            display_plan = sched.sort_by_time()
            # Only show tasks that are actually in the plan
            plan_set = set(id(t) for t in plan)
            display_plan = [t for t in display_plan if id(t) in plan_set]
            sort_label = "sorted by scheduled time"
        else:
            display_plan = plan  # already sorted by priority from generate_daily_plan
            sort_label = "sorted by priority"

        # ── Budget summary metrics ─────────────────────────────────────
        total_min = sum(t.duration_minutes for t in plan)
        remaining = owner.available_minutes - total_min
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Time budget", f"{owner.available_minutes} min")
        col_b.metric("Planned", f"{total_min} min")
        col_c.metric("Remaining", f"{remaining} min", delta=remaining)

        # ── Plan table ────────────────────────────────────────────────
        st.subheader(f"Scheduled tasks ({sort_label})")

        plan_data = []
        for i, t in enumerate(display_plan, start=1):
            pet_name_str = next(
                (p.name for p in owner.pets if t in p.tasks), "—"
            )
            mandatory_tag = " (mandatory)" if t.category == "medication" else ""
            recur_tag = t.recurrence_pattern if t.is_recurring else "—"
            next_due = t.next_occurrence() if t.is_recurring else "—"
            plan_data.append({
                "#": i,
                "Task": t.title,
                "Pet": pet_name_str,
                "Category": t.category + mandatory_tag,
                "Time": t.scheduled_time or "flexible",
                "Duration": f"{t.duration_minutes} min",
                "Priority": t.priority,
                "Recurring": recur_tag,
                "Next due": next_due,
                "Done": "yes" if t.completed else "no",
            })
        st.table(plan_data)

        # ── Plain-English explanation ──────────────────────────────────
        with st.expander("Why were these tasks chosen?"):
            st.text(sched.explain_plan(plan))

        # ── Mark tasks complete with next-occurrence feedback ──────────
        st.subheader("Mark tasks done")
        st.caption(
            "Checking a recurring task shows when it's next due "
            "so you can plan ahead."
        )

        for task in display_plan:
            col_check, col_info = st.columns([3, 2])
            with col_check:
                done = st.checkbox(
                    f"{task.title} ({task.duration_minutes} min) — {task.priority} priority",
                    value=task.completed,
                    key=f"done_{task.title}_{id(task)}",
                )
            with col_info:
                if done:
                    task.mark_complete()
                    if task.is_recurring:
                        st.success(f"Next due: {task.next_occurrence()}")
                    else:
                        st.success("Done!")
                else:
                    task.mark_incomplete()
                    if task.scheduled_time:
                        st.caption(f"Scheduled @ {task.scheduled_time}")

        # ── Recurring task preview ─────────────────────────────────────
        recurring_in_plan = [t for t in plan if t.is_recurring]
        if recurring_in_plan:
            with st.expander(f"Recurring task overview ({len(recurring_in_plan)} task(s))"):
                st.caption(
                    "These tasks repeat automatically. "
                    "The 'Next due' date updates when you mark them complete."
                )
                rec_data = [
                    {
                        "Task": t.title,
                        "Pattern": t.recurrence_pattern,
                        "Next due": t.next_occurrence(),
                    }
                    for t in recurring_in_plan
                ]
                st.table(rec_data)

    elif st.session_state.scheduler is not None:
        st.info("No tasks fit within the current time budget.")
