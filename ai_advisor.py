import json
import logging
import os
import time

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from google.api_core import retry as google_retry

def _is_retryable_quota_error(exc):
    if not isinstance(exc, google_exceptions.ResourceExhausted):
        return False
    # Only retry per-minute limits (reset in ~60s) — all other quota dimensions won't resolve within the session
    exc_str = str(exc)
    return "PerMinute" in exc_str or "per_minute" in exc_str

_gemini_retry = google_retry.Retry(
    predicate=_is_retryable_quota_error,
    initial=65.0,
    maximum=120.0,
    multiplier=1.5,
    deadline=300.0,
)

from knowledge_base import retrieve_relevant_chunks

logger = logging.getLogger("petwise.ai_advisor")

MODEL = "gemini-2.5-flash-lite"
MAX_INPUT_CHARS = 4000
MAX_KNOWLEDGE_CHARS = 4000
MAX_TOKENS_ADVICE = 1200   # calls 1 & 2: raised from 600 — verbose JSON responses need the headroom
MAX_TOKENS_SCHEDULE = 1500  # call 3: JSON array of all scheduled tasks

_EMPTY_RESULT: dict = {
    "recommendation": "",
    "concerns": [],
    "confidence": 0,
    "self_critique": "",
    "final_recommendation": "",
    "revised_schedule": None,
    "sources_used": [],
    "error": None,
}


def _retrying_send(chat, message: str, generation_config=None):
    """Send a chat message with retry, restoring history before each attempt.

    Prevents the chat history from accumulating duplicate user turns when the
    SDK appends the outgoing message to _history before the API call returns.
    generation_config overrides the model-level config for this call only.
    """
    snapshot = list(chat.history)

    def _attempt():
        chat._history = list(snapshot)  # private attr; stable across current SDK versions
        return chat.send_message(message, generation_config=generation_config)

    return _gemini_retry(_attempt)()


def _parse_json_response(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found in response")
    return json.loads(text[start:end])


def _build_schedule_summary(owner, schedule: dict) -> str:
    windows_str = ", ".join(f"{s}-{e}" for s, e in owner.time_available)
    pets_str = ", ".join(f"{p.name} ({p.species})" for p in owner.pets)
    lines = [
        f"Owner: {owner.name} | Available: {int(owner.time_available_minutes)} min ({windows_str})",
        f"Pets: {pets_str}",
    ]

    entries = schedule.get("entries", [])
    lines.append(f"Scheduled tasks ({len(entries)}):")
    for e in entries:
        time_str = e.get("time") or "??"
        slot_str = f", slot: {e['preferred_slot']}" if e.get("preferred_slot") else ""
        dep_str = f", requires: {e['depends_on']}" if e.get("depends_on") else ""
        lines.append(
            f"  - {time_str} {e['task']} ({e['pet']}/{_species_for(owner, e['pet'])}, "
            f"{int(e['duration'])} min, {e['priority']}, {e.get('frequency') or 'one-time'}"
            f"{slot_str}{dep_str})"
        )

    skipped = schedule.get("skipped", [])
    lines.append(f"Skipped tasks ({len(skipped)}):")
    for s in skipped:
        slot_str = f", slot: {s['preferred_slot']}" if s.get("preferred_slot") else ""
        dep_str = f", requires: {s['depends_on']}" if s.get("depends_on") else ""
        freq_str = s.get("frequency") or "one-time"
        reason_str = s.get("reason") or "not enough time"
        lines.append(
            f"  - {s['task']} ({s['pet']}, {int(s['duration'])} min, {s['priority']}, "
            f"{freq_str}{slot_str}{dep_str}) — {reason_str}"
        )

    completed = schedule.get("completed", [])
    if completed:
        lines.append(f"Already completed ({len(completed)}):")
        for c in completed:
            dep_str = f", requires: {c['depends_on']}" if c.get("depends_on") else ""
            lines.append(
                f"  - {c['task']} ({c['pet']}, {int(c['duration'])} min, {c['priority']}{dep_str})"
            )

    upcoming = schedule.get("upcoming", [])
    if upcoming:
        lines.append(f"Coming up — done this cycle, next occurrence not yet due ({len(upcoming)}):")
        for u in upcoming:
            slot_str = f", slot: {u['preferred_slot']}" if u.get("preferred_slot") else ""
            lines.append(
                f"  - {u['task']} ({u['pet']}, {u.get('frequency')}, next due: {u.get('next_due', 'unknown')}{slot_str})"
            )

    return "\n".join(lines)


def _species_for(owner, pet_name: str) -> str:
    for pet in owner.pets:
        if pet.name == pet_name:
            return pet.species
    return "unknown"


def _valid_hhmm(t) -> bool:
    if not isinstance(t, str):
        return False
    parts = t.split(":")
    if len(parts) != 2:
        return False
    try:
        h, m = int(parts[0]), int(parts[1])
        return 0 <= h <= 23 and 0 <= m <= 59
    except ValueError:
        return False


def _validate_revised_schedule(owner, original_schedule: dict, raw_entries: list) -> "dict | None":
    """Validate AI-generated schedule entries against the original task pool.

    Returns a schedule dict compatible with _render_schedule, or None if no valid
    entries survive validation.
    """
    all_original = original_schedule.get("entries", []) + original_schedule.get("skipped", [])

    # Build a multi-valued pool: (task, pet) → list of originals.
    # Same-named tasks for the same pet are stored as separate entries so each
    # can be matched and consumed independently.
    task_pool: dict[tuple, list] = {}
    for e in all_original:
        task_pool.setdefault((e["task"], e["pet"]), []).append(e)

    # Track which original objects have been consumed to prevent double-matching.
    used_orig_ids: set[int] = set()

    valid_pets = {p.name for p in owner.pets}
    valid_priorities = {"low", "medium", "high"}
    validated: list[dict] = []

    for raw in raw_entries:
        if not isinstance(raw, dict):
            continue
        task_name = raw.get("task", "")
        pet_name = raw.get("pet", "")
        ai_priority = raw.get("priority", "")
        key = (task_name, pet_name)

        # Prefer an unused original whose priority matches the AI's report so that
        # same-named tasks with different priorities bind to the correct instance.
        # Fall back to any unused original when no priority match exists.
        candidates = task_pool.get(key, [])
        original = None
        for candidate in candidates:
            if id(candidate) not in used_orig_ids and candidate.get("priority") == ai_priority:
                original = candidate
                break
        if original is None:
            for candidate in candidates:
                if id(candidate) not in used_orig_ids:
                    original = candidate
                    break

        if original is None:
            logger.warning("AI revised schedule: unknown task '%s' for pet '%s' — dropped", task_name, pet_name)
            continue
        if pet_name not in valid_pets:
            logger.warning("AI revised schedule: unknown pet '%s' for task '%s' — dropped", pet_name, task_name)
            continue
        if not _valid_hhmm(raw.get("time")):
            logger.warning("AI revised schedule: invalid time '%s' for task '%s' — dropped", raw.get("time"), task_name)
            continue

        # Consume this original instance only after all checks pass.
        used_orig_ids.add(id(original))

        priority = ai_priority if ai_priority in valid_priorities else original["priority"]

        # Store a back-reference (_orig) for identity-based removal below; stripped before return.
        validated.append({
            "order": len(validated) + 1,
            "time": raw["time"],
            "task": task_name,
            "pet": pet_name,
            "duration": original["duration"],  # always use original; never trust AI duration
            "priority": priority,
            "frequency": original.get("frequency"),
            "preferred_slot": original.get("preferred_slot"),
            "depends_on": original.get("depends_on"),
            "_orig": original,
        })

    # Drop any entry whose prerequisite was not also validated (iterative for chains).
    # Upcoming and completed tasks both satisfy dependencies. reset_due_recurring_tasks()
    # guarantees completed never contains overdue recurring tasks by the time the schedule
    # reaches the advisor, so all of completed is safe to include.
    already_done_names = (
        {e["task"] for e in original_schedule.get("upcoming", [])} |
        {e["task"] for e in original_schedule.get("completed", [])}
    )
    changed = True
    while changed:
        changed = False
        scheduled_names = {e["task"] for e in validated}
        satisfied_names = scheduled_names | already_done_names
        violations = [e for e in validated if e.get("depends_on") and e["depends_on"] not in satisfied_names]
        if violations:
            violation_orig_ids = {id(e["_orig"]) for e in violations}
            for e in violations:
                logger.warning(
                    "AI revised schedule: dropped '%s' — prerequisite '%s' not scheduled",
                    e["task"], e["depends_on"],
                )
            validated = [e for e in validated if id(e["_orig"]) not in violation_orig_ids]
            changed = True

    # Trim lowest-priority entries until total fits within the time budget.
    # Remove by object identity so only the specific dropped instance is affected.
    time_available = owner.time_available_minutes
    total = sum(e["duration"] for e in validated)
    if total > time_available:
        rank = {"high": 0, "medium": 1, "low": 2}
        drop_order = sorted(validated, key=lambda e: (rank[e["priority"]], e["time"]), reverse=True)
        while total > time_available and drop_order:
            dropped = drop_order.pop(0)
            total -= dropped["duration"]
            drop_orig_id = id(dropped["_orig"])
            validated = [e for e in validated if id(e["_orig"]) != drop_orig_id]
            drop_order = [e for e in drop_order if id(e["_orig"]) != drop_orig_id]
            logger.warning("AI revised schedule: dropped '%s' to fit time budget", dropped["task"])

    if not validated:
        return None

    # Skipped = every original not represented in the final validated set (by object identity).
    scheduled_orig_ids = {id(e["_orig"]) for e in validated}
    skipped = [
        {
            "task": e["task"], "pet": e["pet"], "duration": e["duration"],
            "priority": e["priority"], "frequency": e.get("frequency"),
            "preferred_slot": e.get("preferred_slot"), "depends_on": e.get("depends_on"),
        }
        for e in all_original if id(e) not in scheduled_orig_ids
    ]

    # Strip back-references and renumber before returning.
    for i, e in enumerate(validated, 1):
        del e["_orig"]
        e["order"] = i

    # Detect time-overlap conflicts within the validated entries
    conflicts: list[str] = []
    for i in range(len(validated)):
        for j in range(i + 1, len(validated)):
            ea, eb = validated[i], validated[j]
            try:
                ha, ma = map(int, ea["time"].split(":"))
                hb, mb = map(int, eb["time"].split(":"))
            except (ValueError, AttributeError):
                continue
            sa, sb = ha * 60 + ma, hb * 60 + mb
            if sa < sb + eb["duration"] and sb < sa + ea["duration"]:
                conflicts.append(
                    f"Conflict: '{ea['task']}' ({ea['pet']}) at {ea['time']} "
                    f"overlaps with '{eb['task']}' ({eb['pet']}) at {eb['time']}."
                )

    total_scheduled = sum(e["duration"] for e in validated)
    explanation = (
        f"AI-revised schedule based on veterinary knowledge and self-critique. "
        f"{len(validated)} task(s) scheduled using {int(total_scheduled)} of "
        f"{int(time_available)} available minutes."
    )

    return {
        "entries": validated,
        "skipped": skipped,
        "completed": original_schedule.get("completed", []),
        "total_time_scheduled": float(total_scheduled),
        "time_available": time_available,
        "completion_ratio": len(validated) / max(1, len(validated) + len(skipped)),
        "explanation": explanation,
        "conflicts": conflicts,
    }


def get_ai_advice(owner, schedule: dict, status_callback=None) -> dict:
    """Call Gemini with RAG context and a self-critique loop to produce pet care advice.

    Returns a dict with keys: recommendation, concerns, confidence, self_critique,
    final_recommendation, sources_used, error.  Never raises — errors are returned
    as the 'error' key so the caller (Streamlit UI) can display them gracefully.

    status_callback: optional callable(str) invoked at each processing step so the
    caller can surface live progress to the user.
    """
    def _update(msg: str):
        if status_callback:
            status_callback(msg)

    result = {**_EMPTY_RESULT}

    try:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise google_exceptions.Unauthenticated("GOOGLE_API_KEY environment variable is not set.")

        genai.configure(api_key=api_key)

        owner_name = "".join(c for c in owner.name if c.isprintable())[:100]

        species_list = [p.species for p in owner.pets]
        task_names = [e["task"] for e in schedule.get("entries", [])]
        task_names += [s["task"] for s in schedule.get("skipped", [])]

        chunks = retrieve_relevant_chunks(species_list, task_names, max_chunks=5)
        sources_used = [key for key, _ in chunks]
        result["sources_used"] = sources_used
        logger.info("RAG retrieved %d chunks: %s", len(chunks), sources_used)

        knowledge_text = "\n\n".join(f"[{key}]\n{text}" for key, text in chunks)[:MAX_KNOWLEDGE_CHARS]

        system_instruction = (
            "You are Petwise, a knowledgeable and practical pet care advisor. "
            "You help pet owners build safe, realistic daily care schedules. "
            "You are honest about limitations and always prioritize pet welfare. "
            "When giving advice, reference the specific context of the schedule provided.\n\n"
            "=== REFERENCE KNOWLEDGE ===\n"
            + knowledge_text
        )

        model = genai.GenerativeModel(
            model_name=MODEL,
            system_instruction=system_instruction,
        )
        _cfg_advice = genai.GenerationConfig(
            max_output_tokens=MAX_TOKENS_ADVICE,
            response_mime_type="application/json",
        )
        _cfg_schedule = genai.GenerationConfig(
            max_output_tokens=MAX_TOKENS_SCHEDULE,
            response_mime_type="application/json",
        )

        schedule_summary = _build_schedule_summary(owner, schedule)
        schedule_summary = schedule_summary[:MAX_INPUT_CHARS]

        user_message_1 = (
            f"Here is today's pet care schedule for {owner_name}:\n\n"
            f"{schedule_summary}\n\n"
            "Please analyze this schedule and provide:\n"
            "1. RECOMMENDATIONS: 2-3 specific actionable suggestions to improve this schedule (1-2 sentences each)\n"
            "2. CONCERNS: Up to 3 potential issues (animal welfare, timing, missing care needs) — 1 sentence each\n"
            "3. CONFIDENCE: A score from 0-100 indicating how confident you are in this advice\n\n"
            "Respond in this exact JSON format (no markdown, just raw JSON):\n"
            '{"recommendations": "...", "concerns": ["...", "..."], "confidence": 85}'
        )

        logger.info(
            "AI advice request started: owner='%s', pets=%s",
            owner_name,
            [p.name for p in owner.pets],
        )

        chat = model.start_chat()
        _update("Analyzing your pet care schedule...")
        response1 = _retrying_send(chat, user_message_1, _cfg_advice)
        raw1 = response1.text
        logger.debug("First API response: %s", raw1[:200])

        initial_advice = _parse_json_response(raw1)
        logger.info("First API call complete: confidence=%s", initial_advice.get("confidence"))

        result["recommendation"] = str(initial_advice.get("recommendations", ""))
        result["concerns"] = initial_advice.get("concerns", [])
        if not isinstance(result["concerns"], list):
            result["concerns"] = [str(result["concerns"])]
        try:
            result["confidence"] = int(float(initial_advice.get("confidence") or 0))
        except (TypeError, ValueError):
            result["confidence"] = 0

        critique_message = (
            f"You just gave this advice about the pet schedule:\n\n"
            f"Recommendations: {initial_advice.get('recommendations', '')}\n"
            f"Concerns: {initial_advice.get('concerns', [])}\n"
            f"Confidence: {initial_advice.get('confidence', 0)}\n\n"
            "Now critically evaluate your own advice:\n"
            "- Is any recommendation impractical given the owner's actual time constraints?\n"
            "- Did you miss any important pet welfare concerns?\n"
            "- Is your confidence score appropriate given what you know?\n"
            "- What, if anything, would you change?\n\n"
            "Respond in this exact JSON format (no markdown, just raw JSON):\n"
            '{"critique": "...", "revised_recommendation": "...", "adjusted_confidence": 80}'
        )

        time.sleep(3)
        _update("Reviewing and critiquing initial advice...")
        response2 = _retrying_send(chat, critique_message, _cfg_advice)
        raw2 = response2.text
        logger.debug("Self-critique response: %s", raw2[:200])

        critique_data = _parse_json_response(raw2)
        logger.info(
            "Self-critique complete: adjusted_confidence=%s", critique_data.get("adjusted_confidence")
        )

        result["self_critique"] = str(critique_data.get("critique", ""))
        result["final_recommendation"] = str(critique_data.get("revised_recommendation", ""))
        try:
            result["confidence"] = int(float(critique_data.get("adjusted_confidence") or result["confidence"]))
        except (TypeError, ValueError):
            pass  # keep confidence from call 1

        # Third turn: ask Gemini to produce a revised schedule in structured JSON
        all_tasks = schedule.get("entries", []) + schedule.get("skipped", [])
        if not all_tasks:
            logger.warning("No tasks available for revised schedule — skipping third API call")
            result["revised_schedule"] = None
            logger.info("AI advice request finished successfully")
            return result
        task_pool_str = "\n".join(
            f"  - {t['task']} | pet: {t['pet']} | {int(t['duration'])} min | {t['priority']} priority"
            f" | {t.get('frequency') or 'one-time'}"
            + (f" | slot: {t['preferred_slot']}" if t.get("preferred_slot") else "")
            + (f" | requires: {t['depends_on']}" if t.get("depends_on") else "")
            for t in all_tasks
        )
        upcoming_tasks = schedule.get("upcoming", [])
        completed_tasks = schedule.get("completed", [])
        already_done = upcoming_tasks + completed_tasks
        already_done_str = (
            "\n".join(f"  - {t['task']} (already done — satisfies any 'requires' dependency)" for t in already_done)
            if already_done else "  (none)"
        )
        windows_str = ", ".join(f"{s}-{e}" for s, e in owner.time_available)

        revised_schedule_message = (
            "Now produce a revised pet care schedule based on your recommendations and critique.\n\n"
            f"Available tasks (use exact names and pets from this list only):\n{task_pool_str}\n\n"
            f"Already-completed tasks (DO NOT reschedule — these satisfy any 'requires' dependency):\n{already_done_str}\n\n"
            f"Owner time windows: {windows_str} (total: {int(owner.time_available_minutes)} min)\n\n"
            "Rules:\n"
            "- Only use task and pet names exactly as shown above\n"
            f"- Total duration of entries must not exceed {int(owner.time_available_minutes)} minutes\n"
            "- Assign realistic HH:MM start times within the time windows\n"
            "- If a task has 'requires: X', X must either appear in entries OR be listed as already completed above\n"
            "- If a task has a 'slot: X', schedule it within that time window (morning=before 12:00, afternoon=12:00–17:00, evening=after 17:00)\n"
            "- Do not schedule tasks at overlapping times\n"
            "- Tasks you choose not to include go in 'skipped'\n\n"
            "Respond in this exact JSON format (no markdown, just raw JSON):\n"
            '{"entries": [{"time": "HH:MM", "task": "Task Name", "pet": "Pet Name", '
            '"duration": 20, "priority": "high"}], '
            '"skipped": [{"task": "Task Name", "pet": "Pet Name", "duration": 5, "priority": "low"}]}'
        )

        time.sleep(3)
        _update("Building your revised schedule...")
        response3 = _retrying_send(chat, revised_schedule_message, _cfg_schedule)
        raw3 = response3.text
        logger.debug("Revised schedule response: %s", raw3[:200])

        schedule_data = _parse_json_response(raw3)
        raw_entries = schedule_data.get("entries", [])
        if isinstance(raw_entries, list):
            revised = _validate_revised_schedule(owner, schedule, raw_entries)
            result["revised_schedule"] = revised
            if revised is None:
                logger.warning("AI revised schedule: no valid entries after validation")
            else:
                logger.info(
                    "AI revised schedule validated: %d entries, %d skipped",
                    len(revised["entries"]), len(revised["skipped"]),
                )
        else:
            logger.warning("AI revised schedule: 'entries' was not a list — skipped")

        logger.info("AI advice request finished successfully")

    except google_exceptions.Unauthenticated:
        logger.error("Invalid or missing GOOGLE_API_KEY")
        result["error"] = "API key is invalid or missing. Check the GOOGLE_API_KEY environment variable."
    except google_exceptions.ResourceExhausted as e:
        exc_str = str(e)
        if "PerDay" in exc_str or "per_day" in exc_str:
            logger.warning("Daily API quota exhausted")
            result["error"] = "Daily API quota exhausted. The free tier limit has been reached for today — please try again tomorrow."
        else:
            logger.warning("Rate limit hit in get_ai_advice")
            result["error"] = "Rate limit reached. Please wait a moment and try again."
    except google_exceptions.ServiceUnavailable:
        logger.error("Network error connecting to Google AI API")
        result["error"] = "Network error. Check your internet connection and try again."
    except google_exceptions.GoogleAPIError as e:
        logger.error("Google API error: %s", e)
        result["error"] = f"API error: {e}. Please try again."
    except (json.JSONDecodeError, ValueError) as e:
        _raw_for_log = locals().get("raw3") or locals().get("raw2") or locals().get("raw1")
        logger.error("Failed to parse Gemini response: %s | raw text: %r", e, _raw_for_log)
        result["error"] = "Could not parse the AI response. Please try again."
    except Exception:
        logger.exception("Unexpected error in get_ai_advice")
        result["error"] = "An unexpected error occurred. Please try again."

    return result
