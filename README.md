# Petwise

**Smart Pet Care, Optimized Daily**

## Summary

Petwise helps pet owners build optimized daily care schedules by combining a constraint-based task engine with an AI advisor powered by veterinary knowledge. It matters because pet care is time-sensitive and easy to deprioritize — most tools treat it like a generic to-do list rather than an optimization problem with real trade-offs.

---

## Original Project

**PawPal**

PawPal was originally built to help pet owners organize and prioritize their daily care routines. It featured a rule-based scheduler that assigned tasks to time windows based on priority and duration, with support for multiple pets and recurring tasks. The goal was to reduce missed care routines and make scheduling feel effortless for busy owners.

However, the original system had no AI component and several clear limitations: it could not ground its recommendations in veterinary knowledge (any advice would be speculative), it had no mechanism for evaluating the quality or reliability of its own output, and it applied no guardrails to prevent invalid or harmful schedule suggestions from reaching the user. These gaps motivated four targeted extensions in Petwise: a RAG layer to anchor advice in curated veterinary knowledge, an agentic self-critique loop to iteratively improve recommendations, a confidence scoring system to surface output reliability, and logging with validation guardrails to prevent bad AI output from being shown to the user.

---

## New Features

The following four AI features were added to Petwise beyond the original PawPal system:

**1. Retrieval-Augmented Generation (RAG)**

A static veterinary knowledge base (`knowledge_base.py`) of 26 hand-curated chunks is keyword-matched to the owner's pets and scheduled tasks on every AI call. Relevant chunks are injected into the model's system prompt so advice is grounded in real veterinary guidance rather than free recall.

**2. Agentic Self-Critique Loop**

The AI advisor calls Gemini three times in a single session. Turn 1 produces initial recommendations and a confidence score. Turn 2 forces the model to critically evaluate its own output against the owner's actual time constraints and adjust its confidence accordingly. Turn 3 generates a revised schedule based on the critique.

**3. Confidence Scoring**

Every AI advice run returns a 0–100 confidence score, surfaced in the UI as green (≥75), orange (≥50), or red (<50). The score is updated after self-critique, giving the user a visible reliability signal before acting on any recommendation.

**4. Logging and Guardrails**

All AI-generated schedule entries are validated before display: unknown tasks, unknown pets, malformed times, and duplicates are dropped; entries that exceed the time budget are trimmed lowest-priority-first; task durations from the AI are always overridden with the original values. API failures (missing key, rate limit, network error) degrade gracefully with informative error messages rather than crashes. All advisor activity is written to `petwise.log`.

---

## Architecture Overview

Petwise is organized as a six-layer pipeline: user input flows into a deterministic scheduling engine, which passes its results to an AI advisor backed by a veterinary knowledge base. The AI advisor's raw output passes through a guardrails/validation layer before the final result is displayed in the Streamlit UI for the owner to review and act on.

### System Diagram

```
┌──────────────────────────────────────────────┐
│          USER INPUT  (Streamlit UI)          │
│   Owner info · Time windows · Pets · Tasks   │
└─────────────────────┬────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────┐
│      CORE SCHEDULER  (pawpal_system.py)      │
│  1. Filter incomplete tasks                  │
│  2. 0/1 Knapsack — select optimal task set   │
│  3. Sort by priority + pet grouping          │
│  4. Topological sort (dependency ordering)   │
│  5. Pack tasks into time windows → HH:MM     │
│  6. Detect conflicts                         │
└─────────────────────┬────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────┐  ┌──────────────────────────────┐
│          AI ADVISOR  (ai_advisor.py)         │  │        KNOWLEDGE BASE        │
│                                              │  │  (knowledge_base.py)         │
│  Turn 1: Recommendations + confidence score  │◄─┤  26 vet-curated chunks       │
│  Turn 2: Self-critique → adjusted confidence │  │  Keyword-matched to species  │
│  Turn 3: Produces revised schedule (raw)     │  │  and task type (RAG)         │
└─────────────────────┬────────────────────────┘  └──────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────┐
│    GUARDRAILS / VALIDATOR  (ai_advisor.py)   │
│  · Drop unknown tasks or pets                │
│  · Drop invalid / malformed HH:MM times      │
│  · Drop duplicate tasks                      │
│  · Trim entries that exceed time budget      │
│  · Always use original task durations        │
│  · Detect conflicts in revised schedule      │
└─────────────────────┬────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────┐
│            OUTPUT  (Streamlit UI)            │
│  Scheduled tasks (color-coded by priority)   │
│  Skipped tasks · Completed tasks             │
│  Conflicts · AI advice · Revised schedule    │
│  Confidence score · Self-critique            │
│                                              │
│  ← Human reviews and acts here               │
└──────────────────────────────────────────────┘

  Testing:  pytest tests/test_pawpal.py
  (129 unit tests covering all layers above)
```

---

## Setup Instructions

1. **Clone the repository**
   ```
   git clone <repo-url>
   cd <repo-folder>
   ```

2. **Create a virtual environment**
   ```
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`

4. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

5. **Add your Gemini API key**
   Create a `.env` file in the project root:
   ```
   GOOGLE_API_KEY=your_key_here
   ```
   Get a key from [Google AI Studio](https://aistudio.google.com/app/apikey). The app reads this variable at startup — without it, the AI Advisor will display an error and scheduling will still work but AI advice will be unavailable.

6. **Run the app**
   ```
   streamlit run app.py
   ```

7. **Run the test suite**
   ```
   pytest tests/test_pawpal.py
   ```
   129 unit tests cover all layers: input validation, scheduling algorithms, conflict detection, task recurrence, knowledge base retrieval, and AI advisor guardrail utilities.

---

## Sample Interactions

*The AI advisor was not successfully run end-to-end during development, so no live AI output samples are available. The core scheduler (input → optimized task schedule) functions correctly and can be demonstrated independently.*

<video src="assets/Petwise End-to-End.mp4" controls="controls" style="max-width: 100%;"></video>

---

## Design Decisions

**Knapsack over greedy selection:** The scheduler uses 0/1 dynamic programming rather than a greedy approach. Greedy would pick the highest-priority tasks one at a time, potentially filling the time budget with several low-value tasks and crowding out a single high-value one. Knapsack finds the globally optimal subset — the trade-off is slightly more complexity in the scheduling logic.

**3-turn multi-turn prompting:** The AI advisor is designed to call Gemini three times: initial recommendations, self-critique, and a revised schedule. The self-critique step is intended to improve output quality by forcing the model to evaluate its own reasoning against the owner's actual constraints. The trade-off is 3× the API calls and added latency per session.

**RAG from a static knowledge base:** Retrieval is grounded in 10 hand-curated veterinary knowledge chunks rather than letting the model recall freely. This eliminates hallucinated advice and makes the system's knowledge auditable. The trade-off is that the knowledge base must be updated manually as best practices evolve.

**Streamlit for the UI:** Streamlit allowed rapid iteration with minimal boilerplate and native session state support. It is not suited for concurrent production users, but it was the right call for a single-owner tool at this stage.

**Topological sort with silent cycle fallback:** Task dependencies are enforced via topological sort. If a dependency cycle is detected, the scheduler silently falls back to the original task order rather than crashing. This keeps the app stable, but the user is not notified when a cycle exists — a known limitation worth addressing in a future iteration.

---

## Testing Summary

**What was tested and how:**

- **129 automated unit tests** via `pytest` covering `Task`, `Pet`, `Owner`, `Scheduler`, knowledge base retrieval, and all AI advisor helper utilities
- **Confidence scoring** — the AI advisor is designed to return a 0–100 confidence score on every run; the Turn 2 self-critique is intended to adjust it downward when the model identifies weaknesses in its own recommendations
- **Logging and error handling** — API failures degrade gracefully with informative messages; AI-generated schedules that fail validation are filtered out entirely rather than displayed to the user
- **Human evaluation** — the UI is designed to show the AI-revised schedule side-by-side with the original so the owner can compare and decide what to act on; this could not be verified as the advisor did not produce output

### Reliability Highlights

**What worked:** The knapsack correctly deprioritized lower-value tasks when the time budget was tight, and the dependency ordering held up across all tested scenarios.

**What didn't:** The AI advisor could not be run end-to-end, so live AI output could not be evaluated.

**Lessons learned:**
- Iterating on individual features in small, testable increments — rather than building the full system overhaul before validating any of it — would have allowed for earlier detection of API compatibility and quota issues, potentially leaving enough runway to resolve them before hitting request limits.
- Over-relying on AI assistance throughout development created a dependency that made it harder to course-correct independently when things broke. Pulling back earlier and working through problems manually would have built a clearer understanding of where the system was actually failing.
- Recognizing scope creep sooner and reverting to a simpler, working state would have been the better call. Continuing to build on top of an unstable foundation compounded the issues rather than resolving them, and an earlier revert could have salvaged a functional end-to-end result.

---

## Reflection

**What this project taught about AI and problem-solving:** AI is most useful when it has structured context to reason over. The combination of RAG retrieval and explicit JSON formatting constraints is theoretically well-suited to producing reliable outputs — grounding the model in curated knowledge and constraining its response format should reduce hallucination and parsing failures compared to open-ended prompting.

**Limitations and biases:** The knowledge base covers dogs, cats, rabbits, birds, guinea pigs, hamsters, reptiles, and fish — advice for species outside this list falls back to generic scheduling rules. The urgency multiplier can also over-schedule long-overdue recurring tasks, crowding out other important care items.

**Could the AI be misused?:** AI-generated advice could be mistaken for licensed veterinary guidance. All outputs are clearly labeled as suggestions, not medical advice, to mitigate this risk.

**What was surprising during development:** The scope of the system overhaul — building RAG, agentic self-critique, confidence scoring, and guardrails simultaneously — made it difficult to isolate where API issues originated before request limits were hit. Smaller, staged feature rollouts would have made debugging far more tractable.

**Future Improvements**
- *Expand the knowledge base further:* The knowledge base now covers 8 species (dogs, cats, rabbits, birds, guinea pigs, hamsters, reptiles, and fish). Adding chunks for additional species and deepening coverage for existing ones — particularly condition-specific care (e.g., dental disease, obesity management) — would improve RAG relevance for edge cases.
- *Fix the urgency multiplier:* The current urgency calculation can over-weight long-overdue recurring tasks, crowding out other high-priority items. Capping the multiplier or applying it only when the time budget is not already exhausted would produce more balanced schedules.
- *Notify users of dependency cycles:* The topological sort silently falls back to the original task order when a cycle is detected. Surfacing a warning in the UI would make this behavior visible rather than invisible to the user.
- *Replace keyword matching with embedding-based retrieval:* The current RAG retrieval is sensitive to exact task name phrasing. Switching to vector embeddings would make retrieval more robust to paraphrasing and improve chunk relevance for edge cases.
- *Add multi-model agreement:* A second model pass or a separate evaluator model could cross-check the AI advisor's revised schedule against the original, flagging large deviations for the user to review rather than accepting the revision silently.

**Collaboration with AI during this project**

*Design*
- **Implementation planning:** AI mapped the full codebase before any code was written, then produced a detailed implementation plan covering architecture (RAG + agentic self-critique + confidence scoring + logging/guardrails), file structure, prompt design, and API call sequencing. The plan was reviewed and approved before implementation began.
- **Read-only advisor:** AI proposed that the advisor suggest a revised schedule alongside the original rather than overwrite it, reasoning that silently rewriting the scheduler's output risked violating hard constraints (time windows, dependencies, knapsack) with no visible indication to the user.
- **Prompt caching:** AI identified prompt caching as a cost-reduction opportunity for the static system prompt knowledge base block, incorporated from the start.

*Prompting*
- **JSON output format:** The `"Respond in this exact JSON format (no markdown, just raw JSON)"` constraint was arrived at iteratively — early drafts produced markdown-wrapped code blocks that broke `_parse_json_response`, and AI diagnosed and resolved it.
- **Self-critique grounding:** The Turn 2 self-critique message was designed with AI to include four specific grounding questions intended to produce schedule-specific, actionable critiques rather than generic outputs.

*Debugging*
- **Time input normalization:** Time windows only accepted `HH:MM` — AI helped build `_normalize_time_input` to handle digit-only strings, 12-hour am/pm formats, and out-of-range values via modulo. Streamlit's restriction on writing session state post-render was resolved by switching to an `on_change` callback (which also fixed a bypass edge case). Two separate callbacks were later collapsed into one using `args=`.
- **Dependency enforcement:** `Scheduler.complete_task()` had no guard against completing a task before its prerequisite. A pre-check raising a `ValueError` was added, surfaced through the existing `st.error()` handler. Two unit tests confirm the block and its resolution.
- **Rate limiting & status feedback:** Rate limiting was identified as a risk given 3 sequential API calls per request; the model was set to `gemini-1.5-flash-8b` (higher RPM) and exponential backoff retry logic was added via `google.api_core.retry.Retry`. A `status_callback` parameter was also added to surface live step updates via `st.status` in place of a plain spinner. The advisor ultimately could not be run end-to-end due to API issues.
- **Conflict detection & recurring tasks:** Completed tasks retained stale `time` values from prior runs, causing false conflict warnings — fixed by adding `not task.completed` to the `detect_conflicts()` filter. Separately, completing a recurring task immediately re-scheduled its new instance in the same session; a `_is_due()` guard now excludes recently completed tasks, and upcoming instances appear in a distinct "Coming Up" section.

*AI Duality*
- **Helpful suggestion:** AI recommended keeping the advisor as a read-only layer, preserving the integrity of the deterministic scheduler while still contributing a validated side-by-side revision for the user to accept or reject.
- **Flawed suggestion:** AI initially proposed a single `dominant_slot` derived from availability windows, which collapsed multiple time periods into one label and didn't correctly route tasks into matching windows. The correct fix tracked covered slots as a frozenset and reworked `_assign_start_times` to prefer `preferred_slot`-matching windows before falling back.

---