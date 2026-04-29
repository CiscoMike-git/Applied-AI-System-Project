import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from petwise_system import Task, Pet, Owner, Scheduler
from knowledge_base import retrieve_relevant_chunks
from ai_advisor import (
    _parse_json_response,
    _valid_hhmm,
    _species_for,
    _build_schedule_summary,
    _validate_revised_schedule,
)


# ── Task: properties, validation, lifecycle ───────────────────────────────────

def test_toggle_complete_sets_then_clears():
    task = Task(name="Feed", duration=10, priority="high")
    assert task.completed is False
    task.toggle_complete()
    assert task.completed is True
    task.toggle_complete()
    assert task.completed is False


def test_toggle_complete_back_clears_last_done_for_recurring():
    task = Task(name="Walk", duration=30, priority="high", frequency="daily")
    task.toggle_complete()
    task.last_done = datetime.now()
    task.toggle_complete()  # toggle back
    assert task.completed is False
    assert task.last_done is None


def test_toggle_complete_back_preserves_last_done_for_nonrecurring():
    task = Task(name="Checkup", duration=45, priority="low", frequency=None)
    when = datetime.now()
    task.toggle_complete()
    task.last_done = when
    task.toggle_complete()  # toggle back
    assert task.completed is False
    assert task.last_done == when


def test_set_name_rejects_blank():
    """set_name() raises ValueError for both an empty string and an all-whitespace string."""
    task = Task(name="Feed", duration=10, priority="high")
    for bad in ("", "   "):
        try:
            task.set_name(bad)
            assert False, "Expected ValueError"
        except ValueError:
            pass


def test_set_duration_zero_raises():
    """set_duration(0) is below the valid range [1, 240] and must raise ValueError."""
    task = Task(name="Feed", duration=10, priority="high")
    try:
        task.set_duration(0)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_set_duration_over_max_raises():
    """set_duration(240) is the valid maximum; set_duration(241) must raise ValueError."""
    task = Task(name="Feed", duration=10, priority="high")
    task.set_duration(240)
    assert task.duration == 240
    try:
        task.set_duration(241)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_set_priority_valid_values():
    task = Task(name="Feed", duration=10, priority="high")
    for p in ("low", "medium", "high"):
        task.set_priority(p)
        assert task.priority == p


def test_set_priority_rejects_invalid():
    task = Task(name="Feed", duration=10, priority="high")
    try:
        task.set_priority("urgent")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_set_frequency_valid_values():
    task = Task(name="Walk", duration=30, priority="high")
    for freq in ("daily", "weekly", "monthly"):
        task.set_frequency(freq)
        assert task.frequency == freq


def test_set_frequency_rejects_invalid():
    task = Task(name="Walk", duration=30, priority="high")
    try:
        task.set_frequency("hourly")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_set_frequency_accepts_none():
    task = Task(name="Walk", duration=30, priority="high", frequency="daily")
    task.set_frequency(None)
    assert task.frequency is None


def test_set_preferred_slot_valid_values():
    task = Task(name="Feed", duration=10, priority="high")
    for slot in ("morning", "afternoon", "evening"):
        task.set_preferred_slot(slot)
        assert task.preferred_slot == slot


def test_set_preferred_slot_rejects_invalid():
    task = Task(name="Feed", duration=10, priority="high")
    try:
        task.set_preferred_slot("midnight")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_set_depends_on_stores_value():
    task = Task(name="Play", duration=20, priority="medium")
    task.set_depends_on("Feed")
    assert task.depends_on == "Feed"


def test_set_depends_on_clears_with_none():
    task = Task(name="Play", duration=20, priority="medium", depends_on="Feed")
    task.set_depends_on(None)
    assert task.depends_on is None


def test_set_last_done_stores_value():
    task = Task(name="Walk", duration=30, priority="high")
    when = datetime.now()
    task.set_last_done(when)
    assert task.last_done == when


def test_urgency_multiplier_returns_zero_cases():
    """urgency_multiplier() returns 0.0 when frequency is None and when the task is within its period."""
    no_freq = Task(name="Walk", duration=30, priority="high",
                   frequency=None, last_done=datetime.now() - timedelta(days=10))
    assert no_freq.urgency_multiplier() == 0.0

    on_schedule = Task(name="Walk", duration=30, priority="high",
                       frequency="weekly", last_done=datetime.now() - timedelta(days=3))
    assert on_schedule.urgency_multiplier() == 0.0


def test_urgency_multiplier_overdue_returns_positive():
    """urgency_multiplier() returns a positive value when the task is overdue."""
    task = Task(name="Walk", duration=30, priority="high",
                frequency="daily", last_done=datetime.now() - timedelta(days=5))
    assert task.urgency_multiplier() > 0.0


def test_scheduling_value_slot_bonus_applied():
    """scheduling_value() returns a strictly higher value when the task's preferred_slot is covered."""
    task = Task(name="Feed", duration=10, priority="medium", preferred_slot="morning")
    value_match = task.scheduling_value(covered_slots=frozenset({"morning"}))
    value_no_match = task.scheduling_value(covered_slots=frozenset({"evening"}))
    assert value_match > value_no_match


def test_urgency_multiplier_never_done_returns_one():
    """urgency_multiplier() returns 1.0 when frequency is set but last_done is None (treat as one period overdue)."""
    task = Task(name="Walk", duration=30, priority="high", frequency="daily", last_done=None)
    assert task.urgency_multiplier() == 1.0


def test_urgency_multiplier_last_done_in_future_returns_zero():
    """urgency_multiplier() returns 0.0 when last_done is in the future (task not yet due)."""
    task = Task(name="Walk", duration=30, priority="high",
                frequency="daily", last_done=datetime.now() + timedelta(days=1))
    assert task.urgency_multiplier() == 0.0


def test_scheduling_value_no_preferred_slot_no_bonus():
    """scheduling_value() applies no slot bonus when preferred_slot is None."""
    task = Task(name="Feed", duration=10, priority="medium", preferred_slot=None)
    assert task.scheduling_value(covered_slots=frozenset({"morning"})) == 10.0


# ── Pet: properties and task management ──────────────────────────────────────

def test_pet_set_name_rejects_empty():
    pet = Pet(name="Buddy", species="Dog")
    try:
        pet.set_name("")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_pet_set_species_stores_value():
    pet = Pet(name="Buddy", species="Dog")
    pet.set_species("Cat")
    assert pet.species == "Cat"


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Buddy", species="Dog")
    assert len(pet.tasks) == 0
    pet.add_task(Task(name="Walk", duration=30, priority="medium"))
    assert len(pet.tasks) == 1


def test_add_task_duplicate_name_raises():
    """Adding a second task with the same name and identical priority raises ValueError (Case B does not apply
    when priority is the same). A plain same-name same-priority duplicate is rejected."""
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Walk", duration=30, priority="high"))
    try:
        pet.add_task(Task(name="Walk", duration=15, priority="high"))
        assert False, "Expected ValueError"
    except ValueError:
        pass
    assert len(pet.tasks) == 1


def test_pet_remove_task_valid():
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Walk", duration=30, priority="high"))
    pet.remove_task("Walk")
    assert len(pet.tasks) == 0


def test_pet_remove_task_not_found_raises():
    pet = Pet(name="Buddy", species="Dog")
    try:
        pet.remove_task("Nonexistent")
        assert False, "Expected ValueError"
    except ValueError:
        pass


# ── Owner: name, time windows, pet management ─────────────────────────────────

def test_owner_set_name_rejects_empty():
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    try:
        owner.set_name("")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_owner_add_time_window_valid():
    owner = Owner(name="Alice", time_available=[])
    owner.add_time_window("08:00", "09:00")
    assert ("08:00", "09:00") in owner.time_available


def test_owner_add_time_window_invalid_format_raises():
    owner = Owner(name="Alice", time_available=[])
    try:
        owner.add_time_window("8am", "9am")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_owner_add_time_window_end_before_start_raises():
    owner = Owner(name="Alice", time_available=[])
    try:
        owner.add_time_window("09:00", "08:00")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_owner_validate_window_rejects_hour_over_23():
    """Hours >= 24 are invalid (e.g. '24:00') and must raise ValueError."""
    owner = Owner(name="Alice", time_available=[])
    try:
        owner.add_time_window("24:00", "25:00")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_owner_validate_window_rejects_minute_over_59():
    """Minutes >= 60 are invalid (e.g. '08:60') and must raise ValueError."""
    owner = Owner(name="Alice", time_available=[])
    try:
        owner.add_time_window("08:00", "08:60")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_owner_validate_window_accepts_boundary_23_59():
    """'23:59' is the latest valid time and must not raise."""
    owner = Owner(name="Alice", time_available=[])
    owner.add_time_window("22:00", "23:59")
    assert ("22:00", "23:59") in owner.time_available


def test_add_time_window_merges_overlapping_windows():
    """Adding a window that overlaps an existing one merges them into a single window."""
    owner = Owner(name="Alice", time_available=[])
    owner.add_time_window("08:00", "09:30")
    owner.add_time_window("09:00", "10:30")
    assert owner.time_available == [("08:00", "10:30")]


def test_add_time_window_merges_adjacent_windows():
    """Adding a window that starts exactly where an existing one ends merges them."""
    owner = Owner(name="Alice", time_available=[])
    owner.add_time_window("08:00", "09:00")
    owner.add_time_window("09:00", "10:00")
    assert owner.time_available == [("08:00", "10:00")]


def test_add_time_window_non_overlapping_kept_separate():
    """Windows with a gap between them are kept as two distinct entries."""
    owner = Owner(name="Alice", time_available=[])
    owner.add_time_window("08:00", "09:00")
    owner.add_time_window("10:00", "11:00")
    assert len(owner.time_available) == 2
    assert ("08:00", "09:00") in owner.time_available
    assert ("10:00", "11:00") in owner.time_available


def test_add_time_window_absorbs_multiple_existing():
    """A new window that spans several existing windows merges all of them into one."""
    owner = Owner(name="Alice", time_available=[])
    owner.add_time_window("08:00", "09:00")
    owner.add_time_window("10:00", "11:00")
    owner.add_time_window("07:30", "11:30")  # covers both
    assert owner.time_available == [("07:30", "11:30")]


def test_add_time_window_merges_three_sequential_overlapping_windows():
    """Three windows added in sequence each overlapping the previous merge into a single span."""
    owner = Owner(name="Alice", time_available=[])
    owner.add_time_window("09:00", "11:00")
    owner.add_time_window("10:00", "13:00")
    owner.add_time_window("12:30", "14:00")
    assert owner.time_available == [("09:00", "14:00")]


def test_owner_remove_time_window_valid():
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    owner.remove_time_window("08:00", "09:00")
    assert owner.time_available == []


def test_owner_remove_time_window_not_found_raises():
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    try:
        owner.remove_time_window("10:00", "11:00")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_remove_time_window_trims_start():
    """Removing the first portion of a window leaves only the right remainder."""
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    owner.remove_time_window("08:00", "08:30")
    assert owner.time_available == [("08:30", "09:00")]


def test_remove_time_window_trims_end():
    """Removing the last portion of a window leaves only the left remainder."""
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    owner.remove_time_window("08:30", "09:00")
    assert owner.time_available == [("08:00", "08:30")]


def test_remove_time_window_splits_window():
    """Removing the middle of a window produces two remainder windows."""
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    owner.remove_time_window("08:20", "08:40")
    assert ("08:00", "08:20") in owner.time_available
    assert ("08:40", "09:00") in owner.time_available
    assert len(owner.time_available) == 2


def test_remove_time_window_partial_overlap_left():
    """Removal range starts before the window — trims the start of the window."""
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    owner.remove_time_window("07:30", "08:30")
    assert owner.time_available == [("08:30", "09:00")]


def test_remove_time_window_partial_overlap_right():
    """Removal range ends after the window — trims the end of the window."""
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    owner.remove_time_window("08:30", "09:30")
    assert owner.time_available == [("08:00", "08:30")]


def test_remove_time_window_validates_format():
    """remove_time_window() now validates the HH:MM format and raises ValueError on bad input."""
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    try:
        owner.remove_time_window("8am", "9am")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_owner_time_available_minutes_sum():
    """time_available_minutes sums all window durations correctly."""
    owner = Owner(name="Alice", time_available=[("08:00", "09:00"), ("12:00", "12:30")])
    assert owner.time_available_minutes == 90.0


def test_add_pet_duplicate_name_raises():
    """Adding a second pet with the same name raises ValueError; owner still has only one pet."""
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    owner.add_pet(Pet(name="Buddy", species="Dog"))
    try:
        owner.add_pet(Pet(name="Buddy", species="Cat"))
        assert False, "Expected ValueError"
    except ValueError:
        pass
    assert len(owner.pets) == 1


def test_owner_remove_pet_valid():
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    owner.add_pet(Pet(name="Buddy", species="Dog"))
    owner.remove_pet("Buddy")
    assert len(owner.pets) == 0


def test_owner_remove_pet_not_found_raises():
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    try:
        owner.remove_pet("Ghost")
        assert False, "Expected ValueError"
    except ValueError:
        pass


# ── Scheduler: initialization ─────────────────────────────────────────────────

def test_scheduler_set_owner():
    scheduler = Scheduler()
    assert scheduler.owner is None
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    scheduler.set_owner(owner)
    assert scheduler.owner is owner


# ── Scheduling algorithm: knapsack, selection, metrics ───────────────────────

def test_knapsack_beats_greedy():
    """Greedy (shortest-first within priority) would pick two 5-min medium tasks (value=20)
    and skip the 9-min high task (value=100). Knapsack picks the high task instead."""
    owner = Owner(name="Sam", time_available=[("08:00", "08:09")])
    pet = Pet(name="Rex", species="Dog")
    # Two cheap medium tasks that fit in 10 min total but fill the 9-min budget
    pet.add_task(Task(name="Groom", duration=5, priority="medium"))
    pet.add_task(Task(name="Brush", duration=5, priority="medium"))
    # One high-priority task that fits exactly
    pet.add_task(Task(name="Medication", duration=9, priority="high"))
    owner.add_pet(pet)

    schedule = Scheduler(owner).create_schedule()
    scheduled_names = {e["task"] for e in schedule["entries"]}

    # Knapsack must select Medication (high priority) over the two medium tasks
    assert "Medication" in scheduled_names
    assert "Groom" not in scheduled_names
    assert "Brush" not in scheduled_names


def test_same_pet_tasks_grouped_together():
    """Same-priority tasks for the same pet should appear consecutively."""
    owner = Owner(name="Morgan", time_available=[("08:00", "10:00")])
    dog = Pet(name="Rex", species="Dog")
    cat = Pet(name="Misty", species="Cat")
    dog.add_task(Task(name="Walk", duration=30, priority="medium"))
    cat.add_task(Task(name="Feed Cat", duration=5, priority="medium"))
    dog.add_task(Task(name="Groom Dog", duration=15, priority="medium"))
    owner.add_pet(dog)
    owner.add_pet(cat)

    entries = Scheduler(owner).create_schedule()["entries"]
    pets_in_order = [e["pet"] for e in entries]
    # Rex's tasks should not be split by Misty's task
    rex_indices = [i for i, p in enumerate(pets_in_order) if p == "Rex"]
    assert rex_indices == list(range(min(rex_indices), max(rex_indices) + 1))


def test_slot_matching_task_preferred():
    """A morning-slot task should be preferred when the owner's windows cover morning."""
    owner = Owner(name="Taylor", time_available=[("08:00", "08:15")])
    pet = Pet(name="Cleo", species="Cat")
    pet.add_task(Task(name="Feed", duration=10, priority="medium", preferred_slot="morning"))
    pet.add_task(Task(name="Play", duration=10, priority="medium"))
    owner.add_pet(pet)

    # Owner window is 08:00–08:15 → covered_slots={"morning"}; Feed gets bonus so it wins the slot
    entries = Scheduler(owner).create_schedule()["entries"]
    names = [e["task"] for e in entries]
    assert names[0] == "Feed"


def test_slot_placement_prefers_matching_window():
    """A task with preferred_slot='afternoon' should be placed in the afternoon window
    even when a morning window is also available and comes first chronologically."""
    owner = Owner(name="Sam", time_available=[("08:00", "09:00"), ("13:00", "14:00")])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Walk", duration=30, priority="medium", preferred_slot="afternoon"))
    owner.add_pet(pet)

    entries = Scheduler(owner).create_schedule()["entries"]
    assert len(entries) == 1
    # Walk should start at 13:00, not 08:00
    assert entries[0]["time"] == "13:00"


def test_slot_placement_falls_back_to_any_window():
    """A task with preferred_slot='evening' falls back to a morning window when no evening
    window exists, rather than being dropped."""
    owner = Owner(name="Sam", time_available=[("08:00", "09:00")])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Walk", duration=30, priority="medium", preferred_slot="evening"))
    owner.add_pet(pet)

    entries = Scheduler(owner).create_schedule()["entries"]
    assert len(entries) == 1
    assert entries[0]["time"] == "08:00"


def test_overdue_task_scheduled_over_same_priority_fresh_task():
    """An overdue daily task should outvalue a same-priority task done today."""
    owner = Owner(name="Jordan", time_available=[("08:00", "08:15")])
    pet = Pet(name="Luna", species="Dog")
    # Overdue daily walk — last done 3 days ago (2× overdue)
    overdue_walk = Task(name="Walk", duration=10, priority="medium",
                        frequency="daily", last_done=datetime.now() - timedelta(days=3))
    # Fresh medium task done today
    fresh_task = Task(name="Brush", duration=10, priority="medium",
                      last_done=datetime.now())
    pet.add_task(overdue_walk)
    pet.add_task(fresh_task)
    owner.add_pet(pet)

    # Only 15 min available, each task is 10 min — only one fits, so knapsack must pick the higher-value Walk
    entries = Scheduler(owner).create_schedule()["entries"]
    names_in_order = [e["task"] for e in entries]
    # Walk should appear first since it's more urgent
    assert names_in_order[0] == "Walk"


def test_completion_ratio_all_scheduled():
    owner = Owner(name="Kim", time_available=[("08:00", "09:00")])
    pet = Pet(name="Biscuit", species="Dog")
    pet.add_task(Task(name="Walk", duration=20, priority="high"))
    pet.add_task(Task(name="Feed", duration=10, priority="high"))
    owner.add_pet(pet)

    result = Scheduler(owner).create_schedule()
    assert result["completion_ratio"] == 1.0


def test_completion_ratio_partial():
    owner = Owner(name="Kim", time_available=[("08:00", "08:15")])
    pet = Pet(name="Biscuit", species="Dog")
    pet.add_task(Task(name="Walk", duration=10, priority="high"))
    pet.add_task(Task(name="Feed", duration=10, priority="high"))
    owner.add_pet(pet)

    result = Scheduler(owner).create_schedule()
    assert 0.0 < result["completion_ratio"] < 1.0


def test_completion_ratio_all_already_completed():
    owner = Owner(name="Kim", time_available=[("08:00", "09:00")])
    pet = Pet(name="Biscuit", species="Dog")
    task = Task(name="Walk", duration=20, priority="high")
    task.toggle_complete()
    pet.add_task(task)
    owner.add_pet(pet)

    result = Scheduler(owner).create_schedule()
    assert result["completion_ratio"] == 1.0


def test_create_schedule_no_owner_raises():
    """create_schedule() must raise ValueError when no owner is assigned."""
    try:
        Scheduler().create_schedule()
        assert False, "Expected ValueError"
    except ValueError:
        pass



def test_create_schedule_no_pets_returns_empty():
    """Owner with no pets returns empty entries, no crash, and completion_ratio=1.0."""
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    schedule = Scheduler(owner).create_schedule()
    assert schedule["entries"] == []
    assert schedule["completion_ratio"] == 1.0


def test_create_schedule_no_time_windows_all_skipped():
    """Owner with zero time windows: knapsack capacity is 0, all tasks land in skipped."""
    owner = Owner(name="Alice", time_available=[])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Walk", duration=30, priority="high"))
    pet.add_task(Task(name="Feed", duration=10, priority="medium"))
    owner.add_pet(pet)

    schedule = Scheduler(owner).create_schedule()

    assert schedule["entries"] == []
    assert len(schedule["skipped"]) == 2
    assert schedule["total_time_scheduled"] == 0
    assert schedule["time_available"] == 0.0


def test_create_schedule_task_longer_than_window_is_skipped():
    """BigTask (25 min) fits the total budget (40 min) but exceeds every remaining
    window after SmallTask (15 min) fills the first 20-min window."""
    owner = Owner(name="Alice", time_available=[("08:00", "08:20"), ("09:00", "09:20")])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="SmallTask", duration=15, priority="high"))
    pet.add_task(Task(name="BigTask", duration=25, priority="high"))
    owner.add_pet(pet)

    schedule = Scheduler(owner).create_schedule()
    entry_names = {e["task"] for e in schedule["entries"]}
    skipped_map = {s["task"]: s["reason"] for s in schedule["skipped"]}

    assert "SmallTask" in entry_names
    assert "BigTask" in skipped_map
    assert skipped_map["BigTask"] == "window gap too small to place after earlier tasks"


# ── Dependency resolution ─────────────────────────────────────────────────────

def test_depends_on_ordering_respected():
    """'Play' depends on 'Feed' — Feed must appear before Play regardless of duration sort."""
    owner = Owner(name="Alex", time_available=[("08:00", "09:00")])
    pet = Pet(name="Milo", species="Cat")
    pet.add_task(Task(name="Play", duration=20, priority="high", depends_on="Feed"))
    pet.add_task(Task(name="Feed", duration=5, priority="high"))
    owner.add_pet(pet)

    entries = Scheduler(owner).create_schedule()["entries"]
    names_in_order = [e["task"] for e in entries]
    assert names_in_order.index("Feed") < names_in_order.index("Play")


def test_create_schedule_depends_on_nonexistent_task_no_crash():
    """A dangling depends_on reference (prerequisite task does not exist in the owner's pets) does not crash.
    The scheduler moves the task to skipped because its prerequisite was never schedulable."""
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Walk", duration=30, priority="high", depends_on="Vet Visit"))
    owner.add_pet(pet)

    schedule = Scheduler(owner).create_schedule()

    # No crash; Walk lands in skipped because "Vet Visit" was never in the selected set
    skipped_names = [s["task"] for s in schedule["skipped"]]
    assert "Walk" in skipped_names


def test_create_schedule_dependency_cycle_falls_back_gracefully():
    """Feed depends on Play and Play depends on Feed (cycle). Topo-sort detects it
    and falls back to original order; both tasks must still appear in entries."""
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Feed", duration=10, priority="high", depends_on="Play"))
    pet.add_task(Task(name="Play", duration=10, priority="high", depends_on="Feed"))
    owner.add_pet(pet)

    schedule = Scheduler(owner).create_schedule()

    entry_names = {e["task"] for e in schedule["entries"]}
    assert "Feed" in entry_names
    assert "Play" in entry_names
    assert len(schedule["entries"]) == 2


# ── Task recurrence: complete_task ───────────────────────────────────────────

def test_complete_task_daily_marks_complete_no_new_task():
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Walk", duration=30, priority="high", frequency="daily"))
    owner.add_pet(pet)

    result = Scheduler(owner).complete_task("Buddy", "Walk")

    assert result is None
    assert len(pet.tasks) == 1
    assert pet.tasks[0].completed is True


def test_complete_task_weekly_marks_complete_no_new_task():
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Bath", duration=20, priority="medium", frequency="weekly"))
    owner.add_pet(pet)

    Scheduler(owner).complete_task("Buddy", "Bath")

    assert len(pet.tasks) == 1
    assert pet.tasks[0].completed is True


def test_complete_task_monthly_marks_complete_no_new_task():
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Flea Treatment", duration=15, priority="low", frequency="monthly"))
    owner.add_pet(pet)

    Scheduler(owner).complete_task("Buddy", "Flea Treatment")

    assert len(pet.tasks) == 1
    assert pet.tasks[0].completed is True


def test_complete_task_no_frequency_marks_complete_returns_none():
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="One-off Checkup", duration=45, priority="low", frequency=None))
    owner.add_pet(pet)

    result = Scheduler(owner).complete_task("Buddy", "One-off Checkup")

    assert result is None
    assert pet.tasks[0].completed is True


def test_complete_task_sets_last_done_when_completing():
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Walk", duration=30, priority="high", frequency="daily"))
    owner.add_pet(pet)

    before = datetime.now()
    Scheduler(owner).complete_task("Buddy", "Walk")
    after = datetime.now()

    assert before <= pet.tasks[0].last_done <= after


def test_complete_task_toggle_back_to_incomplete():
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Walk", duration=30, priority="high", frequency="daily"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    scheduler.complete_task("Buddy", "Walk")
    assert pet.tasks[0].completed is True
    scheduler.complete_task("Buddy", "Walk")  # toggle back
    assert pet.tasks[0].completed is False
    assert pet.tasks[0].last_done is None     # cleared because frequency is set


def test_complete_task_toggle_back_nonrecurring_preserves_last_done():
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Checkup", duration=45, priority="low", frequency=None))
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    scheduler.complete_task("Buddy", "Checkup")
    when = pet.tasks[0].last_done
    scheduler.complete_task("Buddy", "Checkup")  # toggle back
    assert pet.tasks[0].completed is False
    assert pet.tasks[0].last_done == when  # last_done preserved for non-recurring


def test_complete_task_toggle_back_bypasses_dependency_check():
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    pet = Pet(name="Buddy", species="Dog")
    feed = Task(name="Feed", duration=10, priority="high")
    walk = Task(name="Walk", duration=20, priority="high", depends_on="Feed")
    feed.toggle_complete()
    walk.toggle_complete()
    walk.last_done = datetime.now()
    pet.add_task(feed)
    pet.add_task(walk)
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    scheduler.complete_task("Buddy", "Feed")   # toggle Feed back to incomplete
    # Walk is completed but its dependency is now incomplete — un-completing should still work
    scheduler.complete_task("Buddy", "Walk")
    assert walk.completed is False


def test_complete_task_raises_for_unknown_pet():
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    try:
        Scheduler(owner).complete_task("Ghost", "Walk")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_complete_task_raises_for_unknown_task():
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Walk", duration=30, priority="high", frequency="daily"))
    owner.add_pet(pet)
    try:
        Scheduler(owner).complete_task("Buddy", "Nonexistent Task")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_complete_task_raises_if_dependency_not_done():
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Feed", duration=10, priority="high"))
    pet.add_task(Task(name="Walk", duration=20, priority="high", depends_on="Feed"))
    owner.add_pet(pet)
    try:
        Scheduler(owner).complete_task("Buddy", "Walk")
        assert False, "Expected ValueError when prerequisite is incomplete"
    except ValueError as e:
        assert "Feed" in str(e)


def test_complete_task_allowed_when_dependency_done():
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    pet = Pet(name="Buddy", species="Dog")
    feed = Task(name="Feed", duration=10, priority="high")
    feed.toggle_complete()
    pet.add_task(feed)
    pet.add_task(Task(name="Walk", duration=20, priority="high", depends_on="Feed"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    scheduler.complete_task("Buddy", "Walk")
    walk = next(t for t in pet.tasks if t.name == "Walk")
    assert walk.completed


def test_complete_task_in_filter_after_toggle():
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Walk", duration=30, priority="high", frequency="daily"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    scheduler.complete_task("Buddy", "Walk")
    scheduler.complete_task("Buddy", "Walk")  # toggle back
    incomplete = scheduler.filter_tasks(completed=False, pet_name="Buddy")

    assert len(incomplete) == 1
    assert incomplete[0].name == "Walk"


# ── Pet.add_task duplicate name validation (Cases A & B) ─────────────────────

def test_add_task_duplicate_name_still_raises_by_default():
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Walk", duration=30, priority="high"))
    try:
        pet.add_task(Task(name="Walk", duration=30, priority="high"))
        assert False, "Expected ValueError for identical duplicate"
    except ValueError:
        pass


def test_add_task_duplicate_name_allowed_case_a_different_slots():
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Walk", duration=30, priority="high", preferred_slot="morning"))
    pet.add_task(Task(name="Walk", duration=30, priority="high", preferred_slot="evening"))
    assert len(pet.tasks) == 2


def test_add_task_duplicate_name_raises_if_one_slot_is_none():
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Walk", duration=30, priority="high", preferred_slot=None))
    try:
        pet.add_task(Task(name="Walk", duration=30, priority="high", preferred_slot="morning"))
        assert False, "Expected ValueError: Case A requires both slots non-None"
    except ValueError:
        pass


def test_add_task_duplicate_name_raises_if_both_slots_none():
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Walk", duration=30, priority="high", preferred_slot=None))
    try:
        pet.add_task(Task(name="Walk", duration=30, priority="high", preferred_slot=None))
        assert False, "Expected ValueError: both slots None"
    except ValueError:
        pass


def test_add_task_duplicate_name_allowed_case_b_different_priority():
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Walk", duration=30, priority="high",
                      frequency="daily", preferred_slot="morning", depends_on=None))
    pet.add_task(Task(name="Walk", duration=30, priority="low",
                      frequency="daily", preferred_slot="morning", depends_on=None))
    assert len(pet.tasks) == 2


def test_add_task_duplicate_name_case_b_different_priority_allowed():
    """Case B: same name, different priority, but identical frequency/slot/depends_on — duration may differ.
    This combination is explicitly permitted by add_task and must NOT raise ValueError."""
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Walk", duration=30, priority="high",
                      frequency="daily", preferred_slot="morning", depends_on=None))
    # Different priority (low vs high), same freq/slot/dep — Case B applies; no error expected
    pet.add_task(Task(name="Walk", duration=20, priority="low",
                      frequency="daily", preferred_slot="morning", depends_on=None))
    assert len(pet.tasks) == 2


# ── Scheduler: reset_due_recurring_tasks ─────────────────────────────────────

def test_reset_due_recurring_tasks_resets_overdue_completed():
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    pet = Pet(name="Buddy", species="Dog")
    task = Task(name="Walk", duration=30, priority="high", frequency="daily",
                completed=True, last_done=datetime.now() - timedelta(days=2))
    pet.add_task(task)
    owner.add_pet(pet)

    count = Scheduler(owner).reset_due_recurring_tasks()

    assert count == 1
    assert task.completed is False
    assert task.last_done is not None  # last_done preserved for urgency scoring


def test_reset_due_recurring_tasks_does_not_reset_not_yet_due():
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    pet = Pet(name="Buddy", species="Dog")
    task = Task(name="Walk", duration=30, priority="high", frequency="weekly",
                completed=True, last_done=datetime.now() - timedelta(days=3))
    pet.add_task(task)
    owner.add_pet(pet)

    count = Scheduler(owner).reset_due_recurring_tasks()

    assert count == 0
    assert task.completed is True


def test_reset_due_recurring_tasks_ignores_non_recurring_completed():
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    pet = Pet(name="Buddy", species="Dog")
    task = Task(name="Checkup", duration=45, priority="low",
                frequency=None, completed=True,
                last_done=datetime.now() - timedelta(days=60))
    pet.add_task(task)
    owner.add_pet(pet)

    count = Scheduler(owner).reset_due_recurring_tasks()

    assert count == 0
    assert task.completed is True


def test_reset_due_recurring_tasks_no_owner_returns_zero():
    assert Scheduler().reset_due_recurring_tasks() == 0


def test_reset_due_recurring_tasks_called_by_create_schedule():
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    pet = Pet(name="Buddy", species="Dog")
    task = Task(name="Walk", duration=30, priority="high", frequency="daily",
                completed=True, last_done=datetime.now() - timedelta(days=2))
    pet.add_task(task)
    owner.add_pet(pet)

    Scheduler(owner).create_schedule()

    assert task.completed is False


# ── Conflict detection ────────────────────────────────────────────────────────

def test_detect_conflicts_same_start_time():
    """Two tasks starting at the same time should conflict."""
    owner = Owner(name="Alice", time_available=[("08:00", "10:00")])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Walk", duration=30, priority="high", time="08:00"))
    pet.add_task(Task(name="Feed", duration=15, priority="medium", time="08:00"))
    owner.add_pet(pet)

    conflicts = Scheduler(owner).detect_conflicts()
    assert len(conflicts) == 1
    assert "Walk" in conflicts[0]
    assert "Feed" in conflicts[0]


def test_detect_conflicts_overlapping_windows():
    """Task B starting before task A finishes should conflict."""
    owner = Owner(name="Alice", time_available=[("08:00", "10:00")])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Walk", duration=60, priority="high", time="08:00"))
    pet.add_task(Task(name="Feed", duration=15, priority="medium", time="08:30"))
    owner.add_pet(pet)

    conflicts = Scheduler(owner).detect_conflicts()
    assert len(conflicts) == 1


def test_detect_conflicts_no_overlap():
    """Non-overlapping tasks should produce no conflicts."""
    owner = Owner(name="Alice", time_available=[("08:00", "10:00")])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Walk", duration=30, priority="high", time="08:00"))
    pet.add_task(Task(name="Feed", duration=15, priority="medium", time="09:00"))
    owner.add_pet(pet)

    conflicts = Scheduler(owner).detect_conflicts()
    assert conflicts == []


def test_detect_conflicts_cross_pet():
    """Tasks on different pets with overlapping times should conflict."""
    owner = Owner(name="Alice", time_available=[("08:00", "10:00")])
    pet1 = Pet(name="Buddy", species="Dog")
    pet1.add_task(Task(name="Walk", duration=30, priority="high", time="08:00"))
    pet2 = Pet(name="Whiskers", species="Cat")
    pet2.add_task(Task(name="Groom", duration=20, priority="low", time="08:10"))
    owner.add_pet(pet1)
    owner.add_pet(pet2)

    conflicts = Scheduler(owner).detect_conflicts()
    assert len(conflicts) == 1
    assert "Buddy" in conflicts[0]
    assert "Whiskers" in conflicts[0]


def test_detect_conflicts_tasks_without_time_ignored():
    """Tasks without a time field should never appear in conflicts."""
    owner = Owner(name="Alice", time_available=[("08:00", "10:00")])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Walk", duration=30, priority="high"))
    pet.add_task(Task(name="Feed", duration=15, priority="medium"))
    owner.add_pet(pet)

    conflicts = Scheduler(owner).detect_conflicts()
    assert conflicts == []


def test_detect_conflicts_in_schedule_dict():
    """create_schedule() should include a 'conflicts' key."""
    owner = Owner(name="Alice", time_available=[("08:00", "10:00")])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Walk", duration=30, priority="high", time="08:00"))
    pet.add_task(Task(name="Feed", duration=15, priority="medium", time="08:00"))
    owner.add_pet(pet)

    schedule = Scheduler(owner).create_schedule()
    assert "conflicts" in schedule


def test_detect_conflicts_strict_adjacency_no_conflict():
    """Task A ends exactly when task B starts (09:30); strictly adjacent tasks must NOT conflict."""
    owner = Owner(name="Alice", time_available=[("08:00", "10:00")])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Walk", duration=30, priority="high", time="09:00"))
    pet.add_task(Task(name="Feed", duration=15, priority="medium", time="09:30"))
    owner.add_pet(pet)

    conflicts = Scheduler(owner).detect_conflicts()
    assert conflicts == []


def test_detect_conflicts_three_way_overlap():
    """Three tasks all starting at the same time produce three pairwise conflict warnings."""
    owner = Owner(name="Alice", time_available=[("08:00", "10:00")])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Walk", duration=30, priority="high", time="08:00"))
    pet.add_task(Task(name="Feed", duration=20, priority="medium", time="08:00"))
    pet.add_task(Task(name="Groom", duration=15, priority="low", time="08:00"))
    owner.add_pet(pet)

    conflicts = Scheduler(owner).detect_conflicts()
    assert len(conflicts) == 3


def test_detect_conflicts_no_owner_returns_empty():
    """detect_conflicts() on a scheduler with no owner must return [] without raising."""
    result = Scheduler().detect_conflicts()
    assert result == []


# ── Filter tasks ──────────────────────────────────────────────────────────────

def _make_filter_scheduler():
    """Shared setup: Alice owns Buddy (Dog) and Whiskers (Cat).
    Buddy has Walk (completed) + Feed (incomplete). Whiskers has Groom (incomplete)."""
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    buddy = Pet(name="Buddy", species="Dog")
    walk = Task(name="Walk", duration=30, priority="high")
    walk.toggle_complete()
    buddy.add_task(walk)
    buddy.add_task(Task(name="Feed", duration=10, priority="medium"))
    whiskers = Pet(name="Whiskers", species="Cat")
    whiskers.add_task(Task(name="Groom", duration=15, priority="low"))
    owner.add_pet(buddy)
    owner.add_pet(whiskers)
    return Scheduler(owner)


def test_filter_tasks_completed_true():
    """filter_tasks(completed=True) returns only completed tasks across all pets."""
    result = _make_filter_scheduler().filter_tasks(completed=True)
    assert len(result) == 1
    assert result[0].name == "Walk"


def test_filter_tasks_no_filters_returns_all():
    """filter_tasks() with no arguments returns every task regardless of status or pet."""
    result = _make_filter_scheduler().filter_tasks()
    assert len(result) == 3


def test_filter_tasks_combined_completed_and_pet_name():
    """filter_tasks(completed=False, pet_name='Buddy') returns only Buddy's incomplete tasks."""
    result = _make_filter_scheduler().filter_tasks(completed=False, pet_name="Buddy")
    result_names = [t.name for t in result]

    assert result_names == ["Feed"]
    assert "Walk" not in result_names
    assert "Groom" not in result_names


def test_filter_tasks_no_owner_raises():
    """filter_tasks() must raise ValueError when no owner is assigned."""
    try:
        Scheduler().filter_tasks()
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_filter_tasks_unknown_pet_raises():
    """filter_tasks(pet_name='Ghost') raises ValueError if no such pet exists."""
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    owner.add_pet(Pet(name="Buddy", species="Dog"))
    try:
        Scheduler(owner).filter_tasks(pet_name="Ghost")
        assert False, "Expected ValueError"
    except ValueError:
        pass


# ── Sort by time ──────────────────────────────────────────────────────────────

def test_sort_by_time_chronological_order():
    """Tasks with time values are returned in ascending chronological order."""
    owner = Owner(name="Alice", time_available=[("07:00", "19:00")])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Evening", duration=10, priority="low", time="18:00"))
    pet.add_task(Task(name="Morning", duration=10, priority="low", time="07:00"))
    pet.add_task(Task(name="Noon", duration=10, priority="low", time="12:00"))
    owner.add_pet(pet)

    result = Scheduler(owner).sort_by_time()
    assert [t.name for t in result] == ["Morning", "Noon", "Evening"]


def test_sort_by_time_untimed_appended_at_end():
    """Timed tasks appear first in chronological order; untimed tasks follow in insertion order."""
    owner = Owner(name="Alice", time_available=[("07:00", "19:00")])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="A", duration=10, priority="low", time=None))
    pet.add_task(Task(name="B", duration=10, priority="low", time="09:00"))
    pet.add_task(Task(name="C", duration=10, priority="low", time=None))
    pet.add_task(Task(name="D", duration=10, priority="low", time="07:30"))
    owner.add_pet(pet)

    result = Scheduler(owner).sort_by_time()
    assert [t.name for t in result] == ["D", "B", "A", "C"]


def test_sort_by_time_all_untimed_preserves_order():
    """When no task has a time value, original insertion order is preserved."""
    owner = Owner(name="Alice", time_available=[("07:00", "19:00")])
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(Task(name="Feed", duration=10, priority="low"))
    pet.add_task(Task(name="Walk", duration=10, priority="low"))
    pet.add_task(Task(name="Play", duration=10, priority="low"))
    owner.add_pet(pet)

    result = Scheduler(owner).sort_by_time()
    assert [t.name for t in result] == ["Feed", "Walk", "Play"]


def test_sort_by_time_cross_pet_ordering():
    """Tasks from different pets with explicit times are merged into a single chronological list."""
    owner = Owner(name="Alice", time_available=[("07:00", "19:00")])
    dog = Pet(name="Rex", species="Dog")
    cat = Pet(name="Misty", species="Cat")
    dog.add_task(Task(name="Walk Rex", duration=30, priority="high", time="09:00"))
    cat.add_task(Task(name="Feed Misty", duration=10, priority="high", time="07:30"))
    dog.add_task(Task(name="Groom Rex", duration=15, priority="low", time="14:00"))
    owner.add_pet(dog)
    owner.add_pet(cat)

    result = Scheduler(owner).sort_by_time()
    assert [t.name for t in result] == ["Feed Misty", "Walk Rex", "Groom Rex"]


def test_sort_by_time_no_owner_raises():
    """sort_by_time() must raise ValueError when no owner is assigned to the scheduler."""
    try:
        Scheduler().sort_by_time()
        assert False, "Expected ValueError"
    except ValueError:
        pass


# ── knowledge_base: retrieval ─────────────────────────────────────────────────

def test_retrieve_dog_exercise_chunk():
    """An exercise-keyword task for a dog returns the dog_exercise chunk."""
    result = retrieve_relevant_chunks(["dog"], ["Walk the dog"])
    keys = [k for k, _ in result]
    assert "dog_exercise" in keys


def test_retrieve_cat_feeding_chunk():
    """A feeding-keyword task for a cat returns the cat_feeding chunk."""
    result = retrieve_relevant_chunks(["cat"], ["Feed cat"])
    keys = [k for k, _ in result]
    assert "cat_feeding" in keys


def test_retrieve_multi_species_includes_general():
    """Two or more species triggers inclusion of general_scheduling regardless of task keywords."""
    result = retrieve_relevant_chunks(["dog", "cat"], ["Walk"])
    keys = [k for k, _ in result]
    assert "general_scheduling" in keys


def test_retrieve_five_tasks_includes_general():
    """Five or more task names triggers inclusion of general_scheduling."""
    result = retrieve_relevant_chunks(["dog"], ["t1", "t2", "t3", "t4", "t5"])
    keys = [k for k, _ in result]
    assert "general_scheduling" in keys


def test_retrieve_fallback_on_unknown_species():
    """An unrecognised species with no keyword matches falls back to the two general chunks."""
    result = retrieve_relevant_chunks(["rabbit"], ["unknown task"])
    keys = [k for k, _ in result]
    assert keys == ["general_scheduling", "task_prioritization"]


def test_retrieve_max_chunks_respected():
    """max_chunks=1 limits the result to at most one tuple regardless of available candidates."""
    result = retrieve_relevant_chunks(["dog", "cat"], ["walk", "feed", "groom", "vet"], max_chunks=1)
    assert len(result) <= 1


def test_retrieve_max_chunks_zero_returns_empty():
    """max_chunks=0 returns an empty list regardless of species or tasks."""
    result = retrieve_relevant_chunks(["dog"], ["feed"], max_chunks=0)
    assert result == []


# ── ai_advisor: helper utilities ──────────────────────────────────────────────

def test_parse_json_response_valid_json():
    assert _parse_json_response('{"key": "val"}') == {"key": "val"}


def test_parse_json_response_embedded_json():
    assert _parse_json_response('some text {"a": 1} more text') == {"a": 1}


def test_parse_json_response_no_json_raises():
    try:
        _parse_json_response("no braces here")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_parse_json_response_invalid_json_in_braces():
    """Braces are present but the content is not valid JSON — must raise ValueError."""
    try:
        _parse_json_response("{ not valid json }")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_valid_hhmm_accepts_valid_times():
    for t in ("08:30", "00:00", "23:59"):
        assert _valid_hhmm(t) is True, f"Expected {t!r} to be valid"


def test_valid_hhmm_rejects_invalid_formats():
    for t in ("25:00", "12:60", "abc", "12:30:00"):
        assert _valid_hhmm(t) is False, f"Expected {t!r} to be invalid"


def test_valid_hhmm_rejects_non_string():
    assert _valid_hhmm(830) is False


def test_valid_hhmm_rejects_none():
    assert _valid_hhmm(None) is False


def test_valid_hhmm_rejects_empty_string():
    assert _valid_hhmm("") is False


def test_valid_hhmm_accepts_single_digit_hour():
    """'1:30' is valid — the function uses int() so zero-padding is not required."""
    assert _valid_hhmm("1:30") is True


def test_valid_hhmm_rejects_hour_exactly_24():
    """'24:00' fails the 0–23 range check even though minutes are valid."""
    assert _valid_hhmm("24:00") is False


def test_species_for_found_pet():
    owner = Owner(name="Alice", time_available=[])
    owner.add_pet(Pet(name="Rex", species="dog"))
    assert _species_for(owner, "Rex") == "dog"


def test_species_for_unknown_pet():
    owner = Owner(name="Alice", time_available=[])
    assert _species_for(owner, "Ghost") == "unknown"


def test_build_schedule_summary_contains_owner_name():
    owner = Owner(name="Alice", time_available=[("08:00", "09:00")])
    summary = _build_schedule_summary(owner, {"entries": [], "skipped": []})
    assert "Alice" in summary


def test_validate_revised_schedule_valid_entries_pass():
    owner = Owner(name="Alice", time_available=[("08:00", "10:00")])
    owner.add_pet(Pet(name="Buddy", species="dog"))
    original = {
        "entries": [
            {"task": "Walk", "pet": "Buddy", "duration": 30, "priority": "high",
             "frequency": None, "preferred_slot": None, "depends_on": None},
        ],
        "skipped": [],
    }
    raw = [{"task": "Walk", "pet": "Buddy", "time": "08:00", "priority": "high"}]
    result = _validate_revised_schedule(owner, original, raw)
    assert result is not None
    assert result["entries"][0]["task"] == "Walk"


def test_validate_revised_schedule_filters_unknown_task():
    """An entry whose task name is not in the original schedule is silently dropped."""
    owner = Owner(name="Alice", time_available=[("08:00", "10:00")])
    owner.add_pet(Pet(name="Buddy", species="dog"))
    original = {
        "entries": [
            {"task": "Walk", "pet": "Buddy", "duration": 30, "priority": "high",
             "frequency": None, "preferred_slot": None, "depends_on": None},
        ],
        "skipped": [],
    }
    raw = [
        {"task": "Ghost Task", "pet": "Buddy", "time": "08:00", "priority": "low"},
        {"task": "Walk", "pet": "Buddy", "time": "08:30", "priority": "high"},
    ]
    result = _validate_revised_schedule(owner, original, raw)
    assert result is not None
    task_names = [e["task"] for e in result["entries"]]
    assert "Walk" in task_names
    assert "Ghost Task" not in task_names


def test_validate_revised_schedule_filters_invalid_time():
    """An entry with an out-of-range time (fails _valid_hhmm) is dropped."""
    owner = Owner(name="Alice", time_available=[("08:00", "10:00")])
    owner.add_pet(Pet(name="Buddy", species="dog"))
    original = {
        "entries": [
            {"task": "Walk", "pet": "Buddy", "duration": 30, "priority": "high",
             "frequency": None, "preferred_slot": None, "depends_on": None},
            {"task": "Feed", "pet": "Buddy", "duration": 10, "priority": "medium",
             "frequency": None, "preferred_slot": None, "depends_on": None},
        ],
        "skipped": [],
    }
    raw = [
        {"task": "Walk", "pet": "Buddy", "time": "25:00", "priority": "high"},
        {"task": "Feed", "pet": "Buddy", "time": "08:00", "priority": "medium"},
    ]
    result = _validate_revised_schedule(owner, original, raw)
    assert result is not None
    task_names = [e["task"] for e in result["entries"]]
    assert "Feed" in task_names
    assert "Walk" not in task_names


def test_validate_revised_schedule_filters_unknown_pet():
    """Entries referencing a pet not in the owner's list are dropped; returns None when nothing survives."""
    owner = Owner(name="Alice", time_available=[("08:00", "10:00")])
    owner.add_pet(Pet(name="Buddy", species="dog"))
    original = {
        "entries": [
            {"task": "Walk", "pet": "Buddy", "duration": 30, "priority": "high",
             "frequency": None, "preferred_slot": None, "depends_on": None},
        ],
        "skipped": [],
    }
    raw = [{"task": "Walk", "pet": "Ghost", "time": "08:00", "priority": "high"}]
    result = _validate_revised_schedule(owner, original, raw)
    assert result is None


def test_validate_revised_schedule_returns_none_when_all_filtered():
    """_validate_revised_schedule returns None when every raw entry fails validation."""
    owner = Owner(name="Alice", time_available=[("08:00", "10:00")])
    owner.add_pet(Pet(name="Buddy", species="dog"))
    original = {
        "entries": [
            {"task": "Walk", "pet": "Buddy", "duration": 30, "priority": "high",
             "frequency": None, "preferred_slot": None, "depends_on": None},
        ],
        "skipped": [],
    }
    raw = [{"task": "Nonexistent", "pet": "Buddy", "time": "08:00", "priority": "high"}]
    result = _validate_revised_schedule(owner, original, raw)
    assert result is None
