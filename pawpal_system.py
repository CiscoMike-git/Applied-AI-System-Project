import logging
from dataclasses import dataclass, field
from datetime import datetime
from heapq import heapify, heappop, heappush
from typing import List, Optional, Tuple

logger = logging.getLogger("petwise.system")


PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
PRIORITY_VALUE = {"high": 100, "medium": 10, "low": 1}
FREQUENCY_DAYS = {"daily": 1, "weekly": 7, "monthly": 30}
VALID_SLOTS = ("morning", "afternoon", "evening")
VALID_FREQUENCIES = ("daily", "weekly", "monthly")


@dataclass
class Task:
    name: str = ""
    duration: int = 1
    priority: str = "low"
    completed: bool = False
    depends_on: Optional[str] = None
    frequency: Optional[str] = None
    last_done: Optional[datetime] = None
    preferred_slot: Optional[str] = None
    time: Optional[str] = None  # "HH:MM" format

    def toggle_complete(self) -> None:
        """Toggle task completion. Completing sets completed=True; un-completing sets it False
        and clears last_done for recurring tasks so they become immediately due again."""
        if self.completed:
            self.completed = False
            if self.frequency is not None:
                self.last_done = None
        else:
            self.completed = True

    def set_name(self, name: str) -> None:
        """Set the task name, raising ValueError if empty or whitespace."""
        if not name.strip():
            raise ValueError("Task name must not be empty or whitespace.")
        self.name = name

    def set_duration(self, length: int) -> None:
        """Set the task duration in minutes, raising ValueError if not between 1 and 240."""
        if not (1 <= length <= 240):
            raise ValueError(f"Duration must be between 1 and 240 minutes, got {length}.")
        self.duration = length

    def set_priority(self, priority: str) -> None:
        """Set the task priority to 'low', 'medium', or 'high'."""
        if priority not in ("low", "medium", "high"):
            raise ValueError(f"Priority must be 'low', 'medium', or 'high', got '{priority}'.")
        self.priority = priority

    def set_depends_on(self, task_name: Optional[str]) -> None:
        """Set the name of a task this task must come after in the schedule, or None to clear."""
        self.depends_on = task_name

    def set_frequency(self, frequency: Optional[str]) -> None:
        """Set recurrence frequency: 'daily', 'weekly', 'monthly', or None."""
        if frequency is not None and frequency not in VALID_FREQUENCIES:
            raise ValueError(
                f"Frequency must be one of {VALID_FREQUENCIES} or None, got '{frequency}'."
            )
        self.frequency = frequency

    def set_last_done(self, when: Optional[datetime]) -> None:
        """Record when this task was last completed to enable urgency scoring."""
        self.last_done = when

    def set_preferred_slot(self, slot: Optional[str]) -> None:
        """Set a preferred time-of-day slot: 'morning', 'afternoon', 'evening', or None."""
        if slot is not None and slot not in VALID_SLOTS:
            raise ValueError(
                f"Slot must be one of {VALID_SLOTS} or None, got '{slot}'."
            )
        self.preferred_slot = slot

    def urgency_multiplier(self) -> float:
        """Return how overdue a recurring task is as a multiplier (0.0 if no frequency)."""
        if self.frequency is None:
            return 0.0
        if self.last_done is None:
            return 1.0  # never-done recurring task: treat as one period overdue
        days_since = (datetime.now() - self.last_done).days
        period = FREQUENCY_DAYS[self.frequency]
        return max(0.0, days_since / period - 1.0)

    def scheduling_value(self, covered_slots: frozenset = frozenset()) -> float:
        """Compute a scheduling value based on priority, urgency, and slot match."""
        base = PRIORITY_VALUE[self.priority]
        slot_bonus = 0.5 if (self.preferred_slot and self.preferred_slot in covered_slots) else 0.0
        return base * (1.0 + self.urgency_multiplier()) + slot_bonus


@dataclass
class Pet:
    name: str = ""
    species: str = ""
    tasks: List[Task] = field(default_factory=list)

    def set_name(self, name: str) -> None:
        """Set the pet's name, raising ValueError if empty or whitespace."""
        if not name.strip():
            raise ValueError("Pet name must not be empty or whitespace.")
        self.name = name

    def set_species(self, species: str) -> None:
        """Set the pet's species."""
        self.species = species

    def add_task(self, task: Task) -> None:
        """Add a task to this pet.

        Raises ValueError if a task with the same name already exists, UNLESS:
        - Case A: both tasks have different non-None preferred_slot values, OR
        - Case B: the tasks have different priority values and frequency, preferred_slot,
          and depends_on are identical (duration may differ).
        """
        for existing in self.tasks:
            if existing.name != task.name:
                continue
            # Case A: different non-None slots
            if (
                task.preferred_slot is not None
                and existing.preferred_slot is not None
                and task.preferred_slot != existing.preferred_slot
            ):
                continue
            # Case B: different priority, frequency/slot/depends_on identical (duration may differ)
            if (
                task.priority != existing.priority
                and task.frequency == existing.frequency
                and task.preferred_slot == existing.preferred_slot
                and task.depends_on == existing.depends_on
            ):
                continue
            raise ValueError(
                f"Task '{task.name}' already exists for this pet. "
                "Same-named tasks are only allowed when they have different non-None time slots "
                "(e.g. 'morning' vs 'evening'), or when they share the same frequency, "
                "slot, and dependencies but differ in priority."
            )
        self.tasks.append(task)

    def remove_task(self, name: str) -> None:
        """Remove a task by name, raising ValueError if it does not exist."""
        if not any(t.name == name for t in self.tasks):
            raise ValueError(f"Task '{name}' not found for this pet.")
        self.tasks = [t for t in self.tasks if t.name != name]

    def remove_task_by_index(self, index: int) -> None:
        """Remove a task by its list index, raising ValueError if out of range."""
        if index < 0 or index >= len(self.tasks):
            raise ValueError(f"Task index {index} is out of range.")
        del self.tasks[index]


@dataclass
class Owner:
    name: str = ""
    time_available: List[Tuple[str, str]] = field(default_factory=list)  # list of (start "HH:MM", end "HH:MM") windows
    pets: List[Pet] = field(default_factory=list)

    @property
    def time_available_minutes(self) -> float:
        """Return the total available time across all windows in minutes."""
        def _to_min(t: str) -> int:
            h, m = map(int, t.split(":"))
            return h * 60 + m
        return float(sum(max(0, _to_min(end) - _to_min(start)) for start, end in self.time_available))

    @property
    def covered_slots(self) -> frozenset:
        """Return the set of time-of-day slots that have any available minutes.

        Slot boundaries: morning 00:00–11:59, afternoon 12:00–16:59, evening 17:00–23:59.
        """
        if not self.time_available:
            return frozenset()
        _BOUNDARIES = [("morning", 0, 720), ("afternoon", 720, 1020), ("evening", 1020, 1440)]

        def _to_min(t: str) -> int:
            h, m = map(int, t.split(":"))
            return h * 60 + m

        result = set()
        for start, end in self.time_available:
            s, e = _to_min(start), _to_min(end)
            for slot, lo, hi in _BOUNDARIES:
                if min(e, hi) - max(s, lo) > 0:
                    result.add(slot)
        return frozenset(result)

    def set_name(self, name: str) -> None:
        """Set the owner's name, raising ValueError if empty or whitespace."""
        if not name.strip():
            raise ValueError("Owner name must not be empty or whitespace.")
        self.name = name

    @staticmethod
    def _validate_window(start: str, end: str) -> None:
        for label, t in (("start", start), ("end", end)):
            parts = t.split(":")
            if len(parts) != 2 or not all(p.isdigit() for p in parts):
                raise ValueError(f"{label} time must be in HH:MM format, got '{t}'.")
            h, m = int(parts[0]), int(parts[1])
            if m >= 60 or (h == 24 and m > 0) or h >= 24:
                raise ValueError(f"{label} time '{t}' is out of range (must be 00:00–23:59).")
        if start >= end:
            raise ValueError(f"Start time '{start}' must be before end time '{end}'.")

    @staticmethod
    def _min_to_hhmm(minutes: int) -> str:
        return f"{minutes // 60:02d}:{minutes % 60:02d}"

    @staticmethod
    def _hhmm_to_min(t: str) -> int:
        h, m = map(int, t.split(":"))
        return h * 60 + m

    def add_time_window(self, start: str, end: str) -> None:
        """Add a (start, end) availability window, merging any overlapping existing windows."""
        self._validate_window(start, end)
        new_s = self._hhmm_to_min(start)
        new_e = self._hhmm_to_min(end)
        merged = []
        for ws, we in [(self._hhmm_to_min(s), self._hhmm_to_min(e)) for s, e in self.time_available]:
            if ws <= new_e and we >= new_s:  # overlapping or adjacent — absorb
                new_s = min(new_s, ws)
                new_e = max(new_e, we)
            else:
                merged.append((ws, we))
        merged.append((new_s, new_e))
        merged.sort()
        self.time_available = [(self._min_to_hhmm(s), self._min_to_hhmm(e)) for s, e in merged]

    def remove_time_window(self, start: str, end: str) -> None:
        """Remove a (start, end) interval from availability, trimming or splitting existing windows."""
        self._validate_window(start, end)
        rm_s = self._hhmm_to_min(start)
        rm_e = self._hhmm_to_min(end)
        result = []
        changed = False
        for ws, we in [(self._hhmm_to_min(s), self._hhmm_to_min(e)) for s, e in self.time_available]:
            if rm_e <= ws or rm_s >= we:  # no overlap — keep as-is
                result.append((ws, we))
            else:
                changed = True
                if ws < rm_s:  # left remainder
                    result.append((ws, rm_s))
                if we > rm_e:  # right remainder
                    result.append((rm_e, we))
        if not changed:
            raise ValueError(f"No availability window overlaps '{start}'–'{end}'.")
        self.time_available = [(self._min_to_hhmm(s), self._min_to_hhmm(e)) for s, e in result]

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner, raising ValueError if a pet with the same name already exists."""
        if any(p.name == pet.name for p in self.pets):
            raise ValueError(f"Pet '{pet.name}' already exists for this owner.")
        self.pets.append(pet)

    def remove_pet(self, name: str) -> None:
        """Remove a pet by name, raising ValueError if it does not exist."""
        if not any(p.name == name for p in self.pets):
            raise ValueError(f"Pet '{name}' not found for this owner.")
        self.pets = [p for p in self.pets if p.name != name]


class Scheduler:
    def __init__(self, owner: "Owner | None" = None):
        """Initialise the scheduler, optionally binding it to an owner."""
        self.owner = owner

    @staticmethod
    def _is_due(task: "Task") -> bool:
        """Return True if a task is due today (overdue, never done, or one-time)."""
        if task.frequency is None or task.last_done is None:
            return True
        days_since = (datetime.now() - task.last_done).days
        return days_since >= FREQUENCY_DAYS[task.frequency]

    @staticmethod
    def _knapsack_select(pairs: list, capacity: float, covered_slots: frozenset = frozenset()) -> list:
        """Return the subset of (pet, task) pairs that maximises total value within capacity."""
        n = len(pairs)
        if n == 0 or capacity <= 0:
            return []
        cap = int(capacity)
        weights = [max(1, p[1].duration) for p in pairs]
        values = [p[1].scheduling_value(covered_slots) for p in pairs]

        # Standard 0/1 knapsack DP — O(n * cap) time and space
        dp = [[0.0] * (cap + 1) for _ in range(n + 1)]
        for i in range(1, n + 1):
            w, v = weights[i - 1], values[i - 1]
            for j in range(cap + 1):
                dp[i][j] = dp[i - 1][j]
                if j >= w and dp[i - 1][j - w] + v > dp[i][j]:
                    dp[i][j] = dp[i - 1][j - w] + v

        selected, j = [], cap
        for i in range(n, 0, -1):
            if dp[i][j] != dp[i - 1][j]:
                selected.append(pairs[i - 1])
                j -= weights[i - 1]
        return selected

    @staticmethod
    def _topo_sort(ordered_pairs: list) -> list:
        """Stable topological sort: reorder pairs to satisfy Task.depends_on constraints."""
        name_to_indices: dict[str, list[int]] = {}
        for i, (_, task) in enumerate(ordered_pairs):
            name_to_indices.setdefault(task.name, []).append(i)

        n = len(ordered_pairs)
        in_degree = [0] * n
        edges = [[] for _ in range(n)]

        for i, (_, task) in enumerate(ordered_pairs):
            if task.depends_on and task.depends_on in name_to_indices:
                for parent in name_to_indices[task.depends_on]:
                    edges[parent].append(i)
                    in_degree[i] += 1

        available = [i for i in range(n) if in_degree[i] == 0]
        heapify(available)
        result = []
        while available:
            i = heappop(available)
            result.append(ordered_pairs[i])
            for j in edges[i]:
                in_degree[j] -= 1
                if in_degree[j] == 0:
                    heappush(available, j)

        # Fall back to original order if a dependency cycle is detected
        return result if len(result) == n else ordered_pairs

    @staticmethod
    def _assign_start_times(selected: list, time_available: List[Tuple[str, str]]) -> None:
        """Pack selected tasks into the owner's time windows, writing task.time for each.

        Each task is placed in the earliest window whose slot matches the task's preferred_slot
        and that has enough remaining capacity. If no preferred-slot window can fit the task,
        it falls back to the earliest window of any slot that can fit it. A window's slot is
        determined by its start time: morning 00:00–11:59, afternoon 12:00–16:59, evening 17:00+.
        Tasks that cannot fit in any window are assigned time = None.
        """
        _SLOT_BOUNDS = [("morning", 0, 720), ("afternoon", 720, 1020), ("evening", 1020, 1440)]

        def to_min(t: str) -> int:
            h, m = map(int, t.split(":"))
            return h * 60 + m

        def to_hhmm(minutes: int) -> str:
            return f"{minutes // 60:02d}:{minutes % 60:02d}"

        def window_slot(win_start: int) -> str:
            for slot, lo, hi in _SLOT_BOUNDS:
                if lo <= win_start < hi:
                    return slot
            return "evening"

        windows = sorted((to_min(s), to_min(e)) for s, e in time_available)
        if not windows:
            for _, task in selected:
                task.time = None
            return

        # Each entry is [win_start, win_end, cursor] where cursor tracks the next free minute.
        win_state = [[ws, we, ws] for ws, we in windows]

        def try_place(candidates: list, duration: int) -> bool:
            for w in candidates:
                if w[2] + duration <= w[1]:
                    task.time = to_hhmm(w[2])
                    w[2] += duration
                    return True
            return False

        for _, task in selected:
            duration = max(1, task.duration)
            placed = False
            if task.preferred_slot:
                preferred = [w for w in win_state if window_slot(w[0]) == task.preferred_slot]
                placed = try_place(preferred, duration)
            if not placed:
                placed = try_place(win_state, duration)
            if not placed:
                task.time = None

    @staticmethod
    def _build_explanation(
        owner: "Owner",
        entries: list,
        skipped: list,
        time_used: float,
        completion_ratio: float,
        covered_slots: frozenset,
        selected: list,
    ) -> str:
        """Build a human-readable explanation of the scheduling result."""
        total_min = owner.time_available_minutes
        windows_str = ", ".join(f"{s}–{e}" for s, e in owner.time_available) or "none"
        lines = [f"{owner.name} has {total_min:.0f} minutes available today ({windows_str})."]
        if not entries:
            lines.append("No tasks could be scheduled.")
            if total_min == 0:
                lines.append(
                    "The time budget is 0 minutes — add availability windows to schedule tasks."
                )
            elif skipped:
                s = min(skipped, key=lambda x: x["duration"])
                lines.append(
                    f"Even the shortest task ('{s['task']}' for {s['pet']}, {s['duration']} min) "
                    "exceeds the available time."
                )
        else:
            word = "task" if len(entries) == 1 else "tasks"
            lines.append(
                f"{len(entries)} {word} scheduled ({completion_ratio:.0%} of incomplete tasks), "
                f"using {time_used:.0f} of {total_min:.0f} minutes."
            )
            lines.append(
                "Tasks were selected to maximise priority-weighted value within the time budget. "
                "Within the same priority, tasks are grouped by pet to reduce context-switching."
            )
            if any(t.depends_on for _, t in selected):
                lines.append(
                    "Dependency ordering was applied where tasks specify a 'depends_on' constraint."
                )
            if covered_slots:
                lines.append("Tasks whose preferred time slot matched your availability windows were prioritized.")

        if skipped:
            word = "task was" if len(skipped) == 1 else "tasks were"
            names = ", ".join(
                "'{task}' ({pet}, {duration} min, {priority} priority)".format(**s)
                for s in skipped
            )
            lines.append(
                f"{len(skipped)} {word} excluded because the time budget was reached: {names}."
            )
        return " ".join(lines)

    def set_owner(self, owner: Owner) -> None:
        """Assign an owner to this scheduler."""
        self.owner = owner

    def filter_tasks(
        self,
        completed: Optional[bool] = None,
        pet_name: Optional[str] = None,
    ) -> List[Task]:
        """Return tasks filtered by completion status and/or pet name.

        Args:
            completed: If True, return only completed tasks. If False, return only
                       incomplete tasks. If None, completion status is not filtered.
            pet_name:  If provided, return only tasks belonging to the named pet.
                       Raises ValueError if no pet with that name exists.
        """
        if self.owner is None:
            raise ValueError("Cannot filter tasks: no owner assigned.")
        if pet_name is not None and not any(p.name == pet_name for p in self.owner.pets):
            raise ValueError(f"Pet '{pet_name}' not found.")

        tasks = [
            task
            for pet in self.owner.pets
            for task in pet.tasks
            if (pet_name is None or pet.name == pet_name)
            and (completed is None or task.completed == completed)
        ]
        return tasks

    def sort_by_time(self) -> List[Task]:
        """Return all tasks across all pets sorted by their time attribute.

        Tasks with a time value come first in chronological order.
        Tasks with no time set are appended at the end in their original order.
        """
        if self.owner is None:
            raise ValueError("Cannot sort tasks: no owner assigned.")
        all_tasks = [task for pet in self.owner.pets for task in pet.tasks]
        timed = sorted((t for t in all_tasks if t.time is not None), key=lambda t: t.time)
        untimed = [t for t in all_tasks if t.time is None]
        return timed + untimed

    def detect_conflicts(self) -> List[str]:
        """Return warning strings for any tasks whose time windows overlap.

        Only tasks with an explicit ``time`` value ("HH:MM") are considered.
        Tasks without a time are ignored. Never raises; always returns a list
        (empty when there are no conflicts).
        """
        timed: List[tuple] = []
        if self.owner:
            for pet in self.owner.pets:
                for task in pet.tasks:
                    if task.time and not task.completed:
                        timed.append((pet.name, task))

        warnings: List[str] = []
        for i in range(len(timed)):
            for j in range(i + 1, len(timed)):
                pet_a, task_a = timed[i]
                pet_b, task_b = timed[j]
                try:
                    h_a, m_a = map(int, task_a.time.split(":"))
                    h_b, m_b = map(int, task_b.time.split(":"))
                except (ValueError, AttributeError):
                    continue
                start_a = h_a * 60 + m_a
                start_b = h_b * 60 + m_b
                end_a = start_a + task_a.duration
                end_b = start_b + task_b.duration
                if start_a < end_b and start_b < end_a:
                    warnings.append(
                        f"Conflict: '{task_a.name}' ({pet_a}) at {task_a.time} "
                        f"overlaps with '{task_b.name}' ({pet_b}) at {task_b.time}."
                    )
        return warnings

    def complete_task_by_index(self, pet_name: str, task_index: int) -> None:
        """Toggle completion for a task identified by its position in the pet's task list.

        Raises ValueError if the pet is not found or the index is out of range.
        """
        if self.owner is None:
            raise ValueError("Cannot complete task: no owner assigned.")

        pet = next((p for p in self.owner.pets if p.name == pet_name), None)
        if pet is None:
            raise ValueError(f"Pet '{pet_name}' not found.")

        if task_index < 0 or task_index >= len(pet.tasks):
            raise ValueError(f"Task index {task_index} is out of range for pet '{pet_name}'.")

        task = pet.tasks[task_index]

        if not task.completed:
            if task.depends_on:
                prereq = next((t for t in pet.tasks if t.name == task.depends_on), None)
                if prereq is not None and not prereq.completed:
                    raise ValueError(
                        f"Cannot complete '{task.name}': '{task.depends_on}' must be completed first."
                    )
            task.toggle_complete()
            task.last_done = datetime.now()
            logger.info("Task completed: pet='%s', task='%s'", pet_name, task.name)
        else:
            task.toggle_complete()
            logger.info("Task un-completed: pet='%s', task='%s'", pet_name, task.name)

    def complete_task(self, pet_name: str, task_name: str) -> None:
        """Toggle a task's completion state.

        Completing (incomplete → complete):
          - Enforces depends_on: raises ValueError if the prerequisite is not done.
          - Sets task.completed = True and task.last_done = datetime.now().
          - Does NOT create a new task instance for recurring tasks.

        Un-completing (complete → incomplete):
          - No dependency check.
          - Sets task.completed = False; clears last_done for recurring tasks.

        Raises ValueError if the pet or task is not found.
        """
        if self.owner is None:
            raise ValueError("Cannot complete task: no owner assigned.")

        pet = next((p for p in self.owner.pets if p.name == pet_name), None)
        if pet is None:
            raise ValueError(f"Pet '{pet_name}' not found.")

        task = next((t for t in pet.tasks if t.name == task_name), None)
        if task is None:
            raise ValueError(f"Task '{task_name}' not found for pet '{pet_name}'.")

        if not task.completed:
            if task.depends_on:
                prereq = next((t for t in pet.tasks if t.name == task.depends_on), None)
                if prereq is not None and not prereq.completed:
                    raise ValueError(
                        f"Cannot complete '{task_name}': '{task.depends_on}' must be completed first."
                    )
            task.toggle_complete()
            task.last_done = datetime.now()
            logger.info("Task completed: pet='%s', task='%s'", pet_name, task_name)
        else:
            task.toggle_complete()
            logger.info("Task un-completed: pet='%s', task='%s'", pet_name, task_name)
        return None

    def reset_due_recurring_tasks(self) -> int:
        """Reset completed recurring tasks whose next due date has arrived.

        For each recurring task where completed=True and days since last_done >= frequency period,
        sets completed=False. last_done is preserved so urgency scoring remains accurate.
        Returns the count of tasks reset.
        """
        if self.owner is None:
            return 0
        count = 0
        for pet in self.owner.pets:
            for task in pet.tasks:
                if (
                    task.frequency is not None
                    and task.completed
                    and task.last_done is not None
                    and (datetime.now() - task.last_done).days >= FREQUENCY_DAYS[task.frequency]
                ):
                    task.completed = False
                    count += 1
                    logger.info(
                        "Recurring task reset to incomplete (due): pet='%s', task='%s'",
                        pet.name, task.name,
                    )
        return count

    def create_schedule(self) -> dict:
        """Build and return a prioritised schedule of pet tasks within the owner's available time.

        Uses a 0/1 knapsack algorithm to select the highest-value tasks that fit within the
        time budget. Value is derived from priority, urgency (how overdue a recurring task is),
        and whether the task's preferred_slot falls within the owner's availability windows.
        Selected tasks are then grouped by pet (to minimise owner context-switching) and
        reordered to satisfy any depends_on constraints.
        """
        if self.owner is None:
            raise ValueError("Cannot create schedule: no owner assigned.")

        owner = self.owner
        self.reset_due_recurring_tasks()
        covered_slots = owner.covered_slots

        if not owner.pets:
            return {
                "entries": [], "skipped": [], "completed": [], "upcoming": [],
                "total_time_scheduled": 0.0, "time_available": owner.time_available_minutes,
                "completion_ratio": 1.0, "conflicts": [],
                "explanation": f"{owner.name} has no pets registered. Add a pet and its tasks first.",
            }

        incomplete_pairs = [(pet, task) for pet in owner.pets for task in pet.tasks if not task.completed]
        all_pairs = [(pet, task) for pet, task in incomplete_pairs if self._is_due(task)]
        # "Coming Up": completed recurring tasks whose next occurrence is not yet due
        upcoming_pairs = [
            (pet, task)
            for pet in owner.pets
            for task in pet.tasks
            if task.completed and task.frequency is not None and not self._is_due(task)
        ]
        upcoming_ids = {id(task) for _, task in upcoming_pairs}
        # "Already Completed": one-time completed tasks, or recurring ones already due again
        completed_pairs = [
            (pet, task)
            for pet in owner.pets
            for task in pet.tasks
            if task.completed and id(task) not in upcoming_ids
        ]

        def _upcoming_row(pet, task):
            from datetime import timedelta
            period = FREQUENCY_DAYS.get(task.frequency, 1)
            next_due = (task.last_done + timedelta(days=period)).strftime("%Y-%m-%d") if task.last_done else "unknown"
            return {
                "pet": pet.name, "task": task.name,
                "duration": task.duration, "priority": task.priority,
                "preferred_slot": task.preferred_slot,
                "frequency": task.frequency, "next_due": next_due,
            }

        if not all_pairs and not completed_pairs and not upcoming_pairs:
            pet_names = ", ".join(p.name for p in owner.pets)
            return {
                "entries": [], "skipped": [], "completed": [], "upcoming": [],
                "total_time_scheduled": 0.0, "time_available": owner.time_available_minutes,
                "completion_ratio": 1.0, "conflicts": [],
                "explanation": f"{owner.name} has pets ({pet_names}) but none have tasks. Add tasks first.",
            }

        if not all_pairs:
            return {
                "entries": [], "skipped": [],
                "completed": [
                    {
                        "pet": pet.name, "task": task.name,
                        "duration": task.duration, "priority": task.priority,
                        "time": task.time, "preferred_slot": task.preferred_slot,
                        "frequency": task.frequency, "depends_on": task.depends_on,
                    }
                    for pet, task in completed_pairs
                ],
                "upcoming": [_upcoming_row(pet, task) for pet, task in upcoming_pairs],
                "total_time_scheduled": 0.0, "time_available": owner.time_available_minutes,
                "completion_ratio": 1.0, "conflicts": [],
                "explanation": f"All tasks for {owner.name}'s pets are already completed.",
            }

        # Knapsack selects the best-value subset that fits within the time budget
        selected = self._knapsack_select(all_pairs, owner.time_available_minutes, covered_slots)
        selected_ids = {id(task) for _, task in selected}
        skipped = [
            {
                "pet": pet.name, "task": task.name,
                "duration": task.duration, "priority": task.priority,
                "time": task.time, "preferred_slot": task.preferred_slot,
                "frequency": task.frequency, "depends_on": task.depends_on,
                "reason": "time budget exhausted",
            }
            for pet, task in all_pairs if id(task) not in selected_ids
        ]

        # Drop any selected task whose prerequisite was not also selected (iterative for chains).
        # Upcoming tasks (completed recurring, not yet due again) and completed one-time tasks
        # satisfy dependencies. reset_due_recurring_tasks() guarantees completed_pairs never
        # contains overdue recurring tasks, so all of completed_pairs is safe to include.
        already_done_names = (
            {task.name for _, task in upcoming_pairs} |
            {task.name for _, task in completed_pairs}
        )
        changed = True
        while changed:
            changed = False
            selected_task_names = {task.name for _, task in selected}
            satisfied_names = selected_task_names | already_done_names
            violations = [(pet, task) for pet, task in selected
                          if task.depends_on and task.depends_on not in satisfied_names]
            if violations:
                violation_ids = {id(task) for _, task in violations}
                skipped.extend(
                    {
                        "pet": pet.name, "task": task.name,
                        "duration": task.duration, "priority": task.priority,
                        "time": task.time, "preferred_slot": task.preferred_slot,
                        "frequency": task.frequency, "depends_on": task.depends_on,
                        "reason": f"prerequisite '{task.depends_on}' was not scheduled",
                    }
                    for pet, task in violations
                )
                selected = [(pet, task) for pet, task in selected if id(task) not in violation_ids]
                changed = True

        # Sort selected tasks: priority → pet grouping (reduces context-switching) → duration
        selected.sort(key=lambda p: (PRIORITY_RANK[p[1].priority], p[0].name, p[1].duration))

        # Reorder to satisfy depends_on constraints while preserving the priority/pet sort
        selected = self._topo_sort(selected)

        # Reset stale times so detect_conflicts() only sees freshly-assigned values.
        for _, task in all_pairs:
            task.time = None

        # Assign a concrete start time to each task by packing them into the owner's windows.
        # Any task that could not be placed within a window gets task.time = None.
        self._assign_start_times(selected, owner.time_available)

        # The knapsack used total minutes as capacity, unaware of window-boundary dead space.
        # Demote any task that _assign_start_times could not place to skipped so that entries
        # only contains tasks with a confirmed start time.
        unplaceable = [(pet, task) for pet, task in selected if task.time is None]
        if unplaceable:
            unplaceable_ids = {id(task) for _, task in unplaceable}
            selected = [(pet, task) for pet, task in selected if id(task) not in unplaceable_ids]
            skipped.extend(
                {
                    "pet": pet.name, "task": task.name,
                    "duration": task.duration, "priority": task.priority,
                    "time": None, "preferred_slot": task.preferred_slot,
                    "frequency": task.frequency, "depends_on": task.depends_on,
                    "reason": "window gap too small to place after earlier tasks",
                }
                for pet, task in unplaceable
            )

        entries = sorted(
            [
                {
                    "order": i, "pet": pet.name, "task": task.name,
                    "duration": task.duration, "priority": task.priority,
                    "time": task.time, "preferred_slot": task.preferred_slot,
                    "frequency": task.frequency, "depends_on": task.depends_on,
                }
                for i, (pet, task) in enumerate(selected, 1)
            ],
            key=lambda e: e["time"] or "99:99",
        )
        time_used = sum(task.duration for _, task in selected)

        total_incomplete = len(all_pairs)
        completion_ratio = len(entries) / total_incomplete if total_incomplete > 0 else 1.0

        logger.info(
            "Schedule created: owner='%s', covered_slots=%s, scheduled=%d, skipped=%d",
            owner.name, sorted(covered_slots), len(entries), len(skipped),
        )
        return {
            "entries": entries,
            "skipped": skipped,
            "completed": [
                {
                    "pet": pet.name, "task": task.name,
                    "duration": task.duration, "priority": task.priority,
                    "time": task.time, "preferred_slot": task.preferred_slot,
                    "frequency": task.frequency, "depends_on": task.depends_on,
                }
                for pet, task in completed_pairs
            ],
            "upcoming": [_upcoming_row(pet, task) for pet, task in upcoming_pairs],
            "total_time_scheduled": time_used,
            "time_available": owner.time_available_minutes,
            "completion_ratio": completion_ratio,
            "explanation": self._build_explanation(
                owner, entries, skipped, time_used, completion_ratio, covered_slots, selected
            ),
            "conflicts": self.detect_conflicts(),
        }
