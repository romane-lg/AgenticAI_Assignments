# McGill Course Advising Agent

A small single-agent project using the OpenAI Agents SDK. The agent helps one
fake McGill-style student search courses, check prerequisites, surface simple
approval risks, and decide when a human advisor is needed.

This is intentionally small: one agent, two tools, no deployment, no real
McGill data, and no autonomous side effects.

## Run It

Create a `.env` file with:

```text
OPENAI_API_KEY=your_key_here
```

Then ask the agent questions:

```bash
.venv/bin/python -m Assignment1.ask_agent
```

Example questions:

```text
Can I take COMP 250?
Can I take COMP 202?
What 200 level classes are available?
Can I take COMP 250 now?
Can I take 18 credits next semester with COMP 250, MATH 133, STAT 230, COMP 202, COMP 101, and ECON 208?
If I take COMP 202 next semester, how many credits will I have left to graduate?
Write me a poem.
```

Type `exit` to quit.

## Project Files

- `ask_agent.py`: the runnable OpenAI Agents SDK app.
- `course_advising_tools.py`: typed tools, structured output models, and
  blocking guardrail helper logic.
- `data/course_catalog.json`: fake catalog with 10 courses.
- `data/prerequisites.json`: prerequisite rules.
- `data/student_profile.json`: one fake student profile.
- `data/policy_rules.json`: small policy/risk rules.
- `data/eval_cases.json`: seven eval cases.
- `evidence/`: transcripts, trace-style summaries, validation logs, and notes.

## Agent Design

The project has one agent: `McGill Course Advising Agent`.

The agent has two typed tools:

- `search_course(query: str)`: searches course ID, title, department, level, and
  tags in the small fake catalog.
- `check_prerequisite(course_id: str, additional_completed_courses:
  list[str] | None)`: checks whether the fixture student satisfies a course's
  prerequisites.
- `review_credit_load(course_ids: list[str])`: totals a proposed term schedule
  and flags schedules above 15 credits for human advisor approval.
- `calculate_credit_progress(planned_course_ids: list[str] | None)`: recalculates
  projected completed credits and credits left to graduate after planned courses.

The agent returns structured output through the SDK using `AdvisorResponse`:

```python
class AdvisorResponse(BaseModel):
    answer: str
    course_ids: list[str]
    approval_status: Literal[
        "approved", "blocked", "informational", "out_of_scope", "needs_advisor"
    ]
    advisor_approval_required: bool
    guardrail_triggered: str | None
    approved_course_id: str | None
    state_notes: list[str]
```

The CLI prints the human answer and the JSON structured output.

## Guardrail

The main blocking guardrail is:

```text
BLOCK_MISSING_PREREQUISITE_APPROVAL
```

If the student is missing a prerequisite, the agent must not approve the course.
It should explain the missing course and mark the structured output as blocked.

There is also an off-topic scope refusal:

```text
BLOCK_NON_COURSE_ADVISING_REQUEST
```

For non-course requests, the required answer is:

```text
Sorry I am a course advising agent, I am unable to fulffil your request
```

Schedules above 15 credits are not approved automatically. They are marked as:

```text
CREDIT_OVERLOAD_REQUIRES_ADVISOR
```

For these cases, the agent should explain that a human advisor needs to approve
the overload request before the schedule can be recommended.

## State Strategy

Stored during the local chat:

- Approved courses from previous turns.

Passed:

- Approved courses are passed back to the agent as context.
- The agent passes them into `check_prerequisite` as
  `additional_completed_courses`.

Recomputed:

- Course search results.
- Prerequisite eligibility.
- Approval or blocking decision.
- Credits left to graduate after planned or approved courses.

Not stored:

- Informational searches.
- Off-topic requests.
- Temporary recommendations.

Example: if the student first asks for `COMP 202` and it is approved, the CLI
stores `COMP 202`. If the student later asks for `COMP 250`, the agent can pass
`COMP 202` into the prerequisite check.

## Eval Cases

The seven cases in `data/eval_cases.json` cover:

1. Missing prerequisite: `COMP 250` should be blocked.
2. Passing prerequisite: `COMP 202` should be approved.
3. Course search: 200-level classes should be listed without updating state.
4. Off-topic request: poem request should be refused.
5. Stateful follow-up: `COMP 250` can pass after `COMP 202` was approved.
6. Credit overload: an 18-credit schedule should require human advisor approval.
7. Credit progress: planned `COMP 202` recalculates credits left to graduate.

## Validation

Run local validation:

```bash
.venv/bin/python -m py_compile Assignment1/ask_agent.py Assignment1/course_advising_tools.py
.venv/bin/python -m json.tool Assignment1/data/eval_cases.json
.venv/bin/python -m json.tool Assignment1/evidence/trace_summary.json
```

The evidence packet is in `evidence/`.
