# Agentic AI Assignments

This repository contains my Agentic AI assignment projects.

## Assignment 1: McGill Course Advising Agent

Assignment 1 is a course advising agent that helps a fake McGill-style student
search courses, check prerequisites, review credit load, and calculate credit
progress.

Main files:

- `Assignment1/ask_agent.py`
- `Assignment1/course_advising_tools.py`
- `Assignment1/data/`
- `Assignment1/evidence/`

See the full Assignment 1 README here:

```text
Assignment1/README.md
```

## Assignment 2: Inventory Replenishment Q-Learning Agent

Assignment 2 is a retail inventory replenishment simulator with one tabular
Q-learning agent. The agent decides whether to order nothing, order less, or
order more over a 14-day horizon.

The project includes:

- problem framing for state, action, reward, transition, and horizon
- reorder-point baseline policy
- tabular Q-learning agent
- evaluation against baseline
- edge episode checks
- plots and saved outputs
- failure analysis and deployment recommendation

See the full Assignment 2 README here:

```text
Assignment2/README.md
```

Run Assignment 2 from the repository root:

```bash
python3 Assignment2/train_and_evaluate.py
```
