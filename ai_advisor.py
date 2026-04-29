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
MAX_TOKENS_ADVICE = 600    # calls 1 & 2: short JSON (recommendations, critique)
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
        lines.append(
            f"  - {time_str} {e['task']} ({e['pet']}/{_species_for(owner, e['pet'])}, "
            f"{int(e['duration'])} min, {e['priority']}, {e.get('frequency') or 'one-time'})"
        )

    skipped = schedule.get("skipped", [])
    lines.append(f"Skipped tasks ({len(skipped)}):")
    for s in skipped:
        lines.append(
            f"  - {s['task']} ({s['pet']}, {int(s['duration'])} min, {s['priority']}) — not enough time"
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
    task_by_name = {e["task"]: e for e in all_original}
    valid_pets = {p.name for p in owner.pets}
    valid_priorities = {"low", "medium", "high"}

    validated: list[dict] = []
    seen: set[str] = set()

    for raw in raw_entries:
        if not isinstance(raw, dict):
            continue
        task_name = raw.get("task", "")
        pet_name = raw.get("pet", "")

        if task_name not in task_by_name:
            logger.warning("AI revised schedule: unknown task '%s' — dropped", task_name)
            continue
        if pet_name not in valid_pets:
            logger.warning("AI revised schedule: unknown pet '%s' for task '%s' — dropped", pet_name, task_name)
            continue
        if task_name in seen:
            logger.warning("AI revised schedule: duplicate task '%s' — dropped", task_name)
            continue
        if not _valid_hhmm(raw.get("time")):
            logger.warning("AI revised schedule: invalid time '%s' for task '%s' — dropped", raw.get("time"), task_name)
            continue

        original = task_by_name[task_name]
        priority = raw.get("priority", "")
        if priority not in valid_priorities:
            priority = original["priority"]

        seen.add(task_name)
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
        })

    # Trim lowest-priority entries until total fits within the time budget
    time_available = owner.time_available_minutes
    total = sum(e["duration"] for e in validated)
    if total > time_available:
        rank = {"high": 0, "medium": 1, "low": 2}
        drop_order = sorted(validated, key=lambda e: (rank[e["priority"]], e["time"]), reverse=True)
        while total > time_available and drop_order:
            dropped = drop_order.pop(0)
            total -= dropped["duration"]
            validated = [e for e in validated if e["task"] != dropped["task"]]
            logger.warning("AI revised schedule: dropped '%s' to fit time budget", dropped["task"])

    if not validated:
        return None

    scheduled_names = {e["task"] for e in validated}
    skipped = [
        {
            "task": e["task"], "pet": e["pet"], "duration": e["duration"],
            "priority": e["priority"], "frequency": e.get("frequency"),
            "preferred_slot": e.get("preferred_slot"), "depends_on": e.get("depends_on"),
        }
        for e in all_original if e["task"] not in scheduled_names
    ]

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
            "1. RECOMMENDATIONS: 2-3 specific actionable suggestions to improve this schedule\n"
            "2. CONCERNS: List any potential issues (animal welfare, timing, missing care needs)\n"
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
            for t in all_tasks
        )
        windows_str = ", ".join(f"{s}-{e}" for s, e in owner.time_available)

        revised_schedule_message = (
            "Now produce a revised pet care schedule based on your recommendations and critique.\n\n"
            f"Available tasks (use exact names and pets from this list only):\n{task_pool_str}\n\n"
            f"Owner time windows: {windows_str} (total: {int(owner.time_available_minutes)} min)\n\n"
            "Rules:\n"
            "- Only use task and pet names exactly as shown above\n"
            f"- Total duration of entries must not exceed {int(owner.time_available_minutes)} minutes\n"
            "- Assign realistic HH:MM start times within the time windows\n"
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
