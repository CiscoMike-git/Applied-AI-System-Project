import logging
import os
import re

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import pandas as pd
from pawpal_system import Task, Pet, Owner, Scheduler
from ai_advisor import get_ai_advice


@st.cache_resource
def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler("petwise.log"),
            logging.StreamHandler(),
        ],
    )


_setup_logging()
logger = logging.getLogger("petwise.app")

st.set_page_config(page_title="Petwise", page_icon="🐾", layout="centered")

st.title("🐾 Petwise")


def _priority_bg(val: str) -> str:
    key = val.strip("[] ").lower()
    return {
        "high":   "background-color: #ff4b4b; color: white",
        "medium": "background-color: #ffd700; color: black",
        "low":    "background-color: #21c55d; color: white",
    }.get(key, "")


def _priority_table(rows: list, priority_col: str = "Priority") -> None:
    df = pd.DataFrame(rows)
    if priority_col in df.columns:
        st.dataframe(
            df.style.map(_priority_bg, subset=[priority_col]),
            hide_index=True,
            width='stretch',
        )
    else:
        st.table(rows)


def _task_table_with_delete(pet: "Pet") -> bool:
    """Render the task list as column rows with per-row completion checkbox and 🗑 delete button.
    Returns True if any state change occurred (caller should st.rerun())."""
    PRIORITY_COLOR = {"high": "#ff4b4b", "medium": "#ffd700", "low": "#21c55d"}
    PRIORITY_TEXT  = {"high": "white",   "medium": "black",   "low": "white"}

    # Scoped to 8-column horizontal blocks — no other section of the app uses 8 columns.
    # (table not formatting correctly, come back if I have time)

    # st.markdown("""
    # <style>
    # /* ── row gap: collapse vertical spacing so border-bottom shows between rows ── */
    # div[data-testid="stVerticalBlockBorderWrapper"]:has(
    #     div[data-testid="column"]:nth-child(8)
    # ) > div[data-testid="stVerticalBlock"] {
    #     gap: 0 !important;
    #     row-gap: 0 !important;
    # }

    # /* ── each row: no column gap, border under every row ── */
    # div[data-testid="stHorizontalBlock"]:has(
    #     > div[data-testid="column"]:nth-child(8)
    # ) {
    #     gap: 0 !important;
    #     border-bottom: 1px solid rgba(49,51,63,0.15);
    # }

    # /* ── each cell: right border + padding + no wrapping ── */
    # div[data-testid="stHorizontalBlock"]:has(
    #     > div[data-testid="column"]:nth-child(8)
    # ) > div[data-testid="column"] {
    #     border-right: 1px solid rgba(49,51,63,0.15);
    #     padding-top:    0.15rem !important;
    #     padding-bottom: 0.15rem !important;
    # }
    # div[data-testid="stHorizontalBlock"]:has(
    #     > div[data-testid="column"]:nth-child(8)
    # ) > div[data-testid="column"] p,
    # div[data-testid="stHorizontalBlock"]:has(
    #     > div[data-testid="column"]:nth-child(8)
    # ) > div[data-testid="column"] span,
    # div[data-testid="stHorizontalBlock"]:has(
    #     > div[data-testid="column"]:nth-child(8)
    # ) > div[data-testid="column"] label {
    #     white-space: nowrap !important;
    #     overflow: visible !important;
    # }

    # /* ── delete column: no right border ── */
    # div[data-testid="stHorizontalBlock"]:has(
    #     > div[data-testid="column"]:nth-child(8)
    # ) > div[data-testid="column"]:nth-child(8) {
    #     border-right: none;
    #     display: flex !important;
    #     align-items: center !important;
    #     justify-content: center !important;
    # }

    # /* ── delete button and all its children: fully centered ── */
    # div[data-testid="stHorizontalBlock"]:has(
    #     > div[data-testid="column"]:nth-child(8)
    # ) > div[data-testid="column"]:nth-child(8) > div {
    #     width: 100% !important;
    # }
    # div[data-testid="stHorizontalBlock"]:has(
    #     > div[data-testid="column"]:nth-child(8)
    # ) > div[data-testid="column"]:nth-child(8) button {
    #     width: 100% !important;
    #     padding: 0 !important;
    #     display: flex !important;
    #     justify-content: center !important;
    #     align-items: center !important;
    # }
    # div[data-testid="stHorizontalBlock"]:has(
    #     > div[data-testid="column"]:nth-child(8)
    # ) > div[data-testid="column"]:nth-child(8) button > div,
    # div[data-testid="stHorizontalBlock"]:has(
    #     > div[data-testid="column"]:nth-child(8)
    # ) > div[data-testid="column"]:nth-child(8) button p {
    #     width: 100% !important;
    #     text-align: center !important;
    #     margin: 0 !important;
    #     padding: 0 !important;
    #     display: flex !important;
    #     justify-content: center !important;
    #     align-items: center !important;
    # }

    # /* ── header row: distinct background ── */
    # div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"]:nth-child(1):has(
    #     > div[data-testid="column"]:nth-child(8)
    # ) {
    #     background-color: rgba(49,51,63,0.08) !important;
    #     border-radius: 4px 4px 0 0;
    # }
    # </style>
    # """, unsafe_allow_html=True)

    deleted = False
    changed = False
    with st.container(border=True):
        headers = ["Done", "Task", "Duration", "Priority", "Frequency", "Slot", "Depends On", ""]
        col_widths = [0.65, 1.4, 1.0, 1.1, 1.3, 1.3, 1.4, 0.6]
        cols = st.columns(col_widths)
        for col, header in zip(cols[:7], headers[:7]):
            col.markdown(f"**{header}**")
        for task in list(pet.tasks):
            cols = st.columns(col_widths)
            checked = cols[0].checkbox(
                "",
                value=task.completed,
                key=f"chk_{pet.name}_{task.name}",
                label_visibility="collapsed",
            )
            if checked != task.completed:
                try:
                    Scheduler(owner=st.session_state.owner).complete_task(pet.name, task.name)
                    st.session_state.pop("last_schedule", None)
                    st.session_state.pop("last_advice", None)
                    changed = True
                except ValueError as e:
                    st.error(str(e))
                    changed = True
            cols[1].write(task.name)
            cols[2].write(f"{task.duration} min")
            color = PRIORITY_COLOR.get(task.priority, "")
            text  = PRIORITY_TEXT.get(task.priority, "black")
            cols[3].markdown(
                f"<span style='background:{color};padding:2px 6px;border-radius:4px;"
                f"color:{text}'>{task.priority.title()}</span>",
                unsafe_allow_html=True,
            )
            cols[4].write(task.frequency.title() if task.frequency else "—")
            cols[5].write(task.preferred_slot.title() if task.preferred_slot else "—")
            cols[6].write(task.depends_on or "—")
            if cols[7].button("🗑 ", key=f"del_{pet.name}_{task.name}"):
                pet.remove_task(task.name)
                st.session_state.pop("last_schedule", None)
                st.session_state.pop("last_advice", None)
                deleted = True
    return deleted or changed


def _make_tags(row: dict) -> str:
    parts = []
    if row.get("preferred_slot"):
        parts.append(f"[{row['preferred_slot'].title()}]")
    if row.get("frequency"):
        parts.append(f"({row['frequency'].title()})")
    if row.get("depends_on"):
        parts.append(f"after: {row['depends_on']}")
    return "  ".join(parts)


def _render_schedule(schedule: dict, owner: Owner) -> None:
    entries   = schedule["entries"]
    completed = schedule["completed"]
    skipped   = schedule["skipped"]
    upcoming  = schedule.get("upcoming", [])

    windows_str = ", ".join(f"{s}–{e}" for s, e in owner.time_available)
    st.subheader(f"Today's Schedule for {owner.name}")
    st.caption(f"Available: {int(owner.time_available_minutes)} min ({windows_str})")

    if completed:
        st.markdown("**Already Completed**")
        st.table([
            {
                "Status":   "[ DONE ]",
                "Task":     r["task"],
                "Pet":      r["pet"],
                "Duration": f"{int(r['duration'])} min",
                "Tags":     _make_tags(r),
            }
            for r in completed
        ])

    st.markdown("**Scheduled Tasks**")
    if entries:
        _priority_table([
            {
                "Time":     r["time"] if r["time"] else "??:??",
                "Priority": r["priority"].title(),
                "Task":     r["task"],
                "Pet":      r["pet"],
                "Duration": f"{int(r['duration'])} min",
                "Tags":     _make_tags(r),
            }
            for r in entries
        ])
    else:
        st.info("No tasks could be scheduled.")
    st.caption(
        f"Total scheduled: {int(schedule['total_time_scheduled'])} / "
        f"{int(schedule['time_available'])} min"
    )

    if skipped:
        st.markdown("**Skipped (not enough time)**")
        _priority_table([
            {
                "Priority": r["priority"].title(),
                "Task":     r["task"],
                "Pet":      r["pet"],
                "Duration": f"{int(r['duration'])} min",
                "Tags":     _make_tags(r),
            }
            for r in skipped
        ])

    if upcoming:
        st.markdown("**Coming Up (already done today — next occurrence scheduled)**")
        st.table([
            {
                "Next Due": r["next_due"],
                "Task":     r["task"],
                "Pet":      r["pet"],
                "Duration": f"{int(r['duration'])} min",
                "Tags":     _make_tags(r),
            }
            for r in upcoming
        ])

    for warning in schedule["conflicts"]:
        st.warning(warning)

    st.info(schedule["explanation"])


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

st.subheader("Owner")

owner_name = st.text_input("Owner Name", value="Jordan").title()

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name)
else:
    if st.session_state.owner.name != owner_name:
        st.session_state.owner.name = owner_name
        st.session_state.pop("last_schedule", None)
        st.session_state.pop("last_advice", None)
    else:
        st.session_state.owner.name = owner_name

if st.session_state.owner.time_available:
    st.markdown("**Available Time Windows**")
    for s, e in st.session_state.owner.time_available:
        st.write(f"- {s} – {e}")
    st.caption(f"Total: {int(st.session_state.owner.time_available_minutes)} min")
else:
    st.info("No availability windows added yet.")

def _normalize_time_input(t: str) -> str:
    t = t.strip()
    period = None
    m = re.match(r'^(.*?)\s*(am|pm)$', t, re.IGNORECASE)
    if m:
        t = m.group(1).strip()
        period = m.group(2).lower()
    if ":" not in t and t.isdigit():
        if len(t) == 4:
            t = t[:2] + ":" + t[2:]
        elif len(t) == 3:
            t = t[0] + ":" + t[1:]
        elif period and len(t) in (1, 2):
            t = t + ":00"
    if period and ":" in t:
        try:
            h, mn = map(int, t.split(":"))
            if period == "am":
                h = 0 if h == 12 else h
            else:
                h = h if h == 12 else h + 12
            t = f"{h:02d}:{mn:02d}"
        except ValueError:
            pass
    if ":" in t:
        try:
            h, mn = map(int, t.split(":"))
            if h >= 24 or mn >= 60:
                t = f"{h % 24:02d}:{mn % 60:02d}"
        except ValueError:
            pass
    return t

def _on_win_change(key: str):
    st.session_state[key] = _normalize_time_input(st.session_state[key])

if "win_start" not in st.session_state:
    st.session_state["win_start"] = "08:00"
if "win_end" not in st.session_state:
    st.session_state["win_end"] = "09:00"

col_ws, col_we = st.columns(2)
with col_ws:
    win_start = st.text_input("Window Start (HH:MM)", key="win_start", on_change=_on_win_change, args=("win_start",))
with col_we:
    win_end = st.text_input("Window End (HH:MM)", key="win_end", on_change=_on_win_change, args=("win_end",))

col_add_w, col_rem_w = st.columns(2)
with col_add_w:
    if st.button("Add Window"):
        try:
            st.session_state.owner.add_time_window(win_start, win_end)
            st.session_state.pop("last_schedule", None)
            st.session_state.pop("last_advice", None)
            st.rerun()
        except ValueError as e:
            st.error(str(e))
with col_rem_w:
    if st.button("Remove Window"):
        try:
            st.session_state.owner.remove_time_window(win_start, win_end)
            st.session_state.pop("last_schedule", None)
            st.session_state.pop("last_advice", None)
            st.rerun()
        except ValueError as e:
            st.error(str(e))


# ---------------------------------------------------------------------------
# Pets
# ---------------------------------------------------------------------------

st.subheader("Pets")

if st.session_state.owner.pets:
    for pet in st.session_state.owner.pets:
        st.write(f"- {pet.name} ({pet.species.title()})")
else:
    st.info("No pets added yet.")

pet_name = st.text_input("Pet Name", value="Mochi").title()
species = st.selectbox("Species", ["Dog", "Cat", "Rabbit", "Bird", "Guinea Pig", "Hamster", "Reptile", "Fish", "Other"])

col_add, col_rem = st.columns(2)
with col_add:
    if st.button("Add Pet"):
        try:
            st.session_state.owner.add_pet(Pet(name=pet_name, species=species.lower()))
            st.session_state.pop("last_schedule", None)
            st.session_state.pop("last_advice", None)
            st.rerun()
        except ValueError as e:
            st.error(str(e))
with col_rem:
    if st.button("Remove Pet"):
        try:
            st.session_state.owner.remove_pet(pet_name)
            st.session_state.pop("last_schedule", None)
            st.session_state.pop("last_advice", None)
            st.rerun()
        except ValueError as e:
            st.error(str(e))


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

st.subheader("Tasks")

pet_names = [p.name for p in st.session_state.owner.pets]
Scheduler(owner=st.session_state.owner).reset_due_recurring_tasks()

if pet_names:
    selected_pet_name = st.selectbox("Select Pet", pet_names)

    selected_pet = next(p for p in st.session_state.owner.pets if p.name == selected_pet_name)
    if selected_pet.tasks:
        st.write("Current Tasks:")
        if _task_table_with_delete(selected_pet):
            st.rerun()
    else:
        st.info("No tasks yet for this pet. Add one below.")

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task Title", value="Morning walk").title()
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["Low", "Medium", "High"], index=2)

    col4, col5, col6 = st.columns(3)
    with col4:
        frequency_opts = ["None", "Daily", "Weekly", "Monthly"]
        frequency = st.selectbox("Frequency", frequency_opts)
        frequency = None if frequency == "None" else frequency.lower()
    with col5:
        slot_opts = ["None", "Morning", "Afternoon", "Evening"]
        preferred_slot = st.selectbox("Preferred Slot", slot_opts)
        preferred_slot = None if preferred_slot == "None" else preferred_slot.lower()
    with col6:
        depends_on_opts = ["None"] + [t.name for t in selected_pet.tasks]
        depends_on_select = st.selectbox("Depends On", depends_on_opts)
        depends_on = None if depends_on_select == "None" else depends_on_select

    if st.button("Add Task"):
        try:
            selected_pet.add_task(Task(
                name=task_title,
                duration=duration,
                priority=priority.lower(),
                frequency=frequency,
                preferred_slot=preferred_slot,
                depends_on=depends_on,
            ))
            st.session_state.pop("last_schedule", None)
            st.session_state.pop("last_advice", None)
            st.rerun()
        except ValueError as e:
            st.error(str(e))

else:
    st.info("Add a pet first to manage tasks.")


# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------

st.divider()

st.subheader("Build Schedule")

if st.button("Generate Schedule"):
    if not st.session_state.owner.pets:
        st.warning("Add at least one pet before generating a schedule.")
    elif not any(p.tasks for p in st.session_state.owner.pets):
        st.warning("Add at least one task before generating a schedule.")
    elif not st.session_state.owner.time_available:
        st.warning("Add at least one availability window before generating a schedule.")
    else:
        logger.info(
            "Generate schedule clicked: owner='%s'",
            st.session_state.owner.name,
        )
        schedule = Scheduler(owner=st.session_state.owner).create_schedule()
        st.session_state["last_schedule"] = schedule
        st.session_state.pop("last_advice", None)

if "last_schedule" in st.session_state:
    _render_schedule(st.session_state["last_schedule"], st.session_state.owner)


# ---------------------------------------------------------------------------
# AI Advisor
# ---------------------------------------------------------------------------

st.divider()
st.subheader("AI Advisor")

if "last_schedule" not in st.session_state:
    st.info("Generate a schedule above to unlock AI advice.")
else:
    st.caption(
        "Petwise AI Advisor uses Gemini to review your schedule and provide "
        "personalized pet care recommendations based on retrieved veterinary knowledge."
    )

    if not os.environ.get("GOOGLE_API_KEY"):
        st.error(
            "GOOGLE_API_KEY environment variable is not set. "
            "Set it before running the app to enable AI advice — see the README for setup instructions."
        )
    else:
        if st.button("Get AI Advice"):
            logger.info(
                "AI Advice requested: owner='%s', pets=%s",
                st.session_state.owner.name,
                [p.name for p in st.session_state.owner.pets],
            )
            with st.status("AI advisor is thinking...", expanded=True) as ai_status:
                advice = get_ai_advice(
                    owner=st.session_state.owner,
                    schedule=st.session_state["last_schedule"],
                    status_callback=st.write,
                )
                if advice.get("error"):
                    ai_status.update(label="AI advisor encountered an error.", state="error")
                else:
                    ai_status.update(label="AI advisor finished!", state="complete")
            st.session_state["last_advice"] = advice

    if "last_advice" in st.session_state:
        advice = st.session_state["last_advice"]

        if advice.get("error"):
            st.error(f"AI Advisor error: {advice['error']}")
        else:
            conf = advice["confidence"]
            conf_color = "green" if conf >= 75 else ("orange" if conf >= 50 else "red")
            st.markdown(f"**Confidence Score:** :{conf_color}[{conf}/100]")

            if advice.get("sources_used"):
                st.caption("Knowledge sources consulted: " + ", ".join(advice["sources_used"]))

            st.markdown("**Recommendations**")
            st.info(advice.get("recommendation") or "No recommendation available.")

            if advice.get("concerns"):
                st.markdown("**Potential Concerns**")
                for concern in advice["concerns"]:
                    st.warning(str(concern))

            with st.expander("AI Self-Critique (how the AI checked its own work)"):
                st.write(advice.get("self_critique") or "No critique available.")

            st.markdown("**Final Recommendation (after self-review)**")
            st.success(advice.get("final_recommendation") or "No final recommendation available.")

            revised = advice.get("revised_schedule")
            if revised:
                st.divider()
                st.subheader("AI-Revised Schedule")
                st.caption(
                    "The AI advisor produced this alternative schedule based on its recommendations. "
                    "Compare it against the deterministic schedule above."
                )
                _render_schedule(revised, st.session_state.owner)
            elif advice.get("final_recommendation"):
                st.caption("The AI advisor did not produce a valid revised schedule for this run.")
