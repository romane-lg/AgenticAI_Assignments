# Validation Logs

## Python Compile

Command:

```bash
.venv/bin/python -m py_compile Assignment1/ask_agent.py Assignment1/course_advising_tools.py
```

Output:

```text
success: no output
```

## Eval Fixture JSON Validation

Command:

```bash
.venv/bin/python -m json.tool Assignment1/data/eval_cases.json
```

Output:

```text
success: JSON parsed and pretty-printed without errors
```

## Local Tool Check

Command:

```bash
.venv/bin/python -c "from Assignment1.course_advising_tools import _check_prerequisite_data, _search_course_data, _review_credit_load_data, _calculate_credit_progress_data; assert _check_prerequisite_data('COMP 250')['eligible'] is False; assert _check_prerequisite_data('COMP 202')['eligible'] is True; assert _check_prerequisite_data('COMP 250', ['COMP 202'])['eligible'] is True; assert {c['course_id'] for c in _search_course_data('200 level')} == {'COMP 202','COMP 250','STAT 230','ECON 208'}; load = _review_credit_load_data(['COMP 250','MATH 133','STAT 230','COMP 202','COMP 101','ECON 208']); assert load['total_credits'] == 18 and load['advisor_approval_required'] is True; progress = _calculate_credit_progress_data(['COMP 202']); assert progress['completed_credits'] == 12; assert progress['planned_credits'] == 3; assert progress['projected_credits'] == 15; assert progress['credits_required_to_graduate'] == 120; assert progress['credits_left_to_graduate'] == 105; print('direct behavior checks passed')"
```

Output:

```text
direct behavior checks passed
```

## Agent CLI Check: Credit Overload

Command:

```bash
printf 'Can I take 18 credits next semester with COMP 250, MATH 133, STAT 230, COMP 202, COMP 101, and ECON 208?\nexit\n' | .venv/bin/python -m Assignment1.ask_agent
```

Output:

```text
Agent: Your selected schedule is 18 credits, which exceeds the 15-credit limit. This needs human advisor approval before I can recommend it.
Structured output: {"answer":"Your selected schedule is 18 credits, which exceeds the 15-credit limit. This needs human advisor approval before I can recommend it.","course_ids":["COMP 250","MATH 133","STAT 230","COMP 202","COMP 101","ECON 208"],"approval_status":"needs_advisor","advisor_approval_required":true,"guardrail_triggered":"CREDIT_OVERLOAD_REQUIRES_ADVISOR","approved_course_id":null,"state_notes":["No previously approved courses in chat.","Schedule exceeds credit load limit; advisor approval required."]}
```

## Agent CLI Check: Credits Left

Command:

```bash
printf 'If I take COMP 202 next semester, how many credits will I have left to graduate?\nexit\n' | .venv/bin/python -m Assignment1.ask_agent
```

Output:

```text
Agent: If you take COMP 202 next semester, you would have 105 credits left to graduate.
Structured output: {"answer":"If you take COMP 202 next semester, you would have 105 credits left to graduate.","course_ids":["COMP 202"],"approval_status":"informational","advisor_approval_required":false,"guardrail_triggered":null,"approved_course_id":null,"state_notes":["Projected credits after COMP 202: 15","Credits required to graduate: 120"]}
```
