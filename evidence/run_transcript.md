# Run Transcript

Command:

```bash
printf 'Can I take COMP 202?\nCan I take COMP 250 now?\nWrite me a poem about unicorns.\nCan I take 18 credits next semester with COMP 250, MATH 133, STAT 230, COMP 202, COMP 101, and ECON 208?\nIf I take COMP 202 next semester, how many credits will I have left to graduate?\nexit\n' | .venv/bin/python ask_agent.py
```

Output:

```text
Ask the course advising agent a question. Type 'exit' to quit.

You:
Agent: Yes — you can take COMP 202 (Data Structures).
Structured output: {"answer":"Yes — you can take COMP 202 (Data Structures).","course_ids":["COMP 202"],"approval_status":"approved","advisor_approval_required":false,"guardrail_triggered":null,"approved_course_id":"COMP 202","state_notes":["Prerequisites satisfied.","No prior approved courses in chat."]}

You:
Agent: Yes — you can take COMP 250 now.
Structured output: {"answer":"Yes — you can take COMP 250 now.","course_ids":["COMP 250"],"approval_status":"approved","advisor_approval_required":false,"guardrail_triggered":null,"approved_course_id":"COMP 250","state_notes":["Prerequisites satisfied with previously approved COMP 202."]}

You:
Agent: Sorry I am a course advising agent, I am unable to fulffil your request
Structured output: {"answer":"Sorry I am a course advising agent, I am unable to fulffil your request","course_ids":[],"approval_status":"out_of_scope","advisor_approval_required":false,"guardrail_triggered":"BLOCK_NON_COURSE_ADVISING_REQUEST","approved_course_id":null,"state_notes":["User request is outside course advising.","No course lookup or prerequisite check needed."]}

You:
Agent: Your selected schedule is 18 credits, which exceeds the 15-credit limit. This needs human advisor approval before I can recommend it.
Structured output: {"answer":"Your selected schedule is 18 credits, which exceeds the 15-credit limit. This needs human advisor approval before I can recommend it.","course_ids":["COMP 250","MATH 133","STAT 230","COMP 202","COMP 101","ECON 208"],"approval_status":"needs_advisor","advisor_approval_required":true,"guardrail_triggered":"CREDIT_OVERLOAD_REQUIRES_ADVISOR","approved_course_id":null,"state_notes":["Schedule exceeds credit load limit; advisor approval required."]}

You:
Agent: If you take COMP 202 next semester, you would have 105 credits left to graduate.
Structured output: {"answer":"If you take COMP 202 next semester, you would have 105 credits left to graduate.","course_ids":["COMP 202"],"approval_status":"informational","advisor_approval_required":false,"guardrail_triggered":null,"approved_course_id":null,"state_notes":["Projected credits after COMP 202: 15","Credits required to graduate: 120"]}

You:
```

This transcript shows:

- one runnable OpenAI Agents SDK app;
- structured output from the SDK agent;
- chat state storing `COMP 202`;
- a stateful follow-up approval for `COMP 250`;
- an off-topic blocking guardrail.
- a credit overload escalation to a human advisor;
- a credits-left recalculation after a planned course.
