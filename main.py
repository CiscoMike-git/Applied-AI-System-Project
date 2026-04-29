from petwise_system import Owner, Pet, Task, Scheduler

# --- Build pets and tasks ---
# Hard-coded times are omitted — create_schedule() assigns start times from the owner's windows.

buddy = Pet(name="Buddy", species="Dog")
buddy.add_task(Task(name="Morning Walk",   duration=30, priority="high",   frequency="daily",  preferred_slot="morning"))
buddy.add_task(Task(name="Feed Breakfast", duration=10, priority="high",   frequency="daily",  preferred_slot="morning"))
buddy.add_task(Task(name="Brush Fur",      duration=15, priority="medium", frequency="weekly", preferred_slot="morning"))
# Evening Walk can only happen after Brush Fur
buddy.add_task(Task(name="Evening Walk",   duration=30, priority="high",   frequency="daily",  preferred_slot="evening", depends_on="Brush Fur"))

whiskers = Pet(name="Whiskers", species="Cat")
whiskers.add_task(Task(name="Clean Litter Box", duration=10, priority="high",   frequency="daily"))
whiskers.add_task(Task(name="Playtime",         duration=20, priority="medium", preferred_slot="morning"))
whiskers.add_task(Task(name="Trim Nails",       duration=10, priority="low",    frequency="monthly"))
whiskers.add_task(Task(name="Morning Groom",    duration=20, priority="medium", preferred_slot="morning"))

# --- Mark some tasks as already completed ---

buddy.tasks[0].toggle_complete()   # Morning Walk
buddy.tasks[1].toggle_complete()   # Feed Breakfast

# --- Build owner (two non-consecutive windows) ---

owner = Owner(name="Alex", time_available=[("08:00", "08:30"), ("09:00", "09:45")])
owner.add_pet(buddy)
owner.add_pet(whiskers)

# --- Generate and print schedule ---

schedule = Scheduler(owner=owner).create_schedule(current_slot="morning")

print(f"===== Today's Schedule for {owner.name} (Morning) =====")
windows_str = ", ".join(f"{s}–{e}" for s, e in owner.time_available)
print(f"Available time: {int(owner.time_available_minutes)} min ({windows_str})\n")

entries   = schedule["entries"]
completed = schedule["completed"]
skipped   = schedule["skipped"]

all_rows = entries + completed + skipped
task_w = max((len(r["task"]) for r in all_rows), default=10)
pet_w  = max((len(r["pet"])  for r in all_rows), default=10)
dur_w  = max((len(str(int(r["duration"]))) for r in all_rows), default=3)

if completed:
    print("Already Completed:")
    for c in completed:
        tags = "  ".join(filter(None, [
            f"[{c['preferred_slot']}]" if c['preferred_slot'] else "",
            f"({c['frequency']})"      if c['frequency']       else "",
        ]))
        print(
            f"  [ DONE ] {c['task']:<{task_w}} ({c['pet']}){'':<{pet_w - len(c['pet'])}} "
            f"{int(c['duration']):>{dur_w}} min{'  ' + tags if tags else ''}"
        )
    print()

print("Scheduled Tasks:")
for entry in entries:
    time_str = entry["time"] if entry["time"] else "??:??"
    tags = "  ".join(filter(None, [
        f"[{entry['preferred_slot']}]"  if entry['preferred_slot'] else "",
        f"({entry['frequency']})"       if entry['frequency']       else "",
        f"after: {entry['depends_on']}" if entry['depends_on']      else "",
    ]))
    print(
        f"  {time_str}  [{entry['priority'].upper():^6}] {entry['task']:<{task_w}} ({entry['pet']}){'':<{pet_w - len(entry['pet'])}} "
        f"{int(entry['duration']):>{dur_w}} min{'  ' + tags if tags else ''}"
    )
print(f"\n  Total scheduled: {int(schedule['total_time_scheduled'])} / {int(schedule['time_available'])} min")

if skipped:
    print("\nSkipped (not enough time):")
    for s in skipped:
        tags = "  ".join(filter(None, [
            f"[{s['preferred_slot']}]" if s['preferred_slot'] else "",
            f"({s['frequency']})"      if s['frequency']       else "",
        ]))
        print(
            f"  [{s['priority'].upper():^6}] {s['task']:<{task_w}} ({s['pet']}){'':<{pet_w - len(s['pet'])}} "
            f"{int(s['duration']):>{dur_w}} min{'  ' + tags if tags else ''}"
        )

if schedule["conflicts"]:
    print("\nScheduling Conflicts Detected:")
    for warning in schedule["conflicts"]:
        print(f"  {warning}")

print(f"\n{schedule['explanation']}")

# --- Sort by time (reflects scheduler-assigned start times) ---

scheduler = Scheduler(owner=owner)

print("\n===== Tasks Sorted by Scheduled Time =====")
for task in scheduler.sort_by_time():
    time_str = task.time if task.time else "no time"
    status   = "DONE" if task.completed else "    "
    print(f"  {time_str}  [{task.priority.upper():^6}]  {status}  {task.name}")

# --- Filter by completion status ---

print("\n===== Incomplete Tasks (all pets) =====")
for task in scheduler.filter_tasks(completed=False):
    print(f"  {task.name} ({task.priority})")

print("\n===== Completed Tasks (all pets) =====")
for task in scheduler.filter_tasks(completed=True):
    print(f"  {task.name} ({task.priority})")

# --- Filter by pet name ---

print("\n===== All Tasks for Buddy =====")
for task in scheduler.filter_tasks(pet_name="Buddy"):
    status = "DONE" if task.completed else "TODO"
    print(f"  [{status}]  {task.name}")

print("\n===== Incomplete Tasks for Whiskers =====")
for task in scheduler.filter_tasks(completed=False, pet_name="Whiskers"):
    print(f"  {task.name} ({task.priority})")

# --- Conflict detection demo ---
# Two tasks from different pets have manually pre-set times that intentionally overlap.
# detect_conflicts() scans all tasks with an explicit time and reports overlaps without
# crashing, even when the times are invalid or missing.

print("\n===== Conflict Detection Demo =====")
print("Vet Visit (Buddy, 10:00, 60 min) vs Grooming Appt (Whiskers, 10:30, 45 min) — expected overlap\n")

conflict_owner = Owner(name="Alex")
conflict_buddy    = Pet(name="Buddy",    species="Dog")
conflict_whiskers = Pet(name="Whiskers", species="Cat")
conflict_buddy.add_task(Task(   name="Vet Visit",      duration=60, priority="high",   time="10:00"))
conflict_whiskers.add_task(Task(name="Grooming Appt",  duration=45, priority="medium", time="10:30"))
conflict_owner.add_pet(conflict_buddy)
conflict_owner.add_pet(conflict_whiskers)

conflict_scheduler = Scheduler(owner=conflict_owner)
conflicts = conflict_scheduler.detect_conflicts()
if conflicts:
    print("Conflicts detected:")
    for warning in conflicts:
        print(f"  {warning}")
else:
    print("No conflicts detected.")