# Inventory Replenishment Q-Learning Agent

This project trains and evaluates a small tabular Q-learning agent for retail
inventory replenishment. The agent controls one product over a 14-day horizon
and decides whether to order nothing, order a small amount, or order a larger
amount.

## Run It

From the repository root:

```bash
python3 Assignment2/train_and_evaluate.py
```

This trains the Q-learning agent, evaluates it against baselines, and writes
results to `Assignment2/outputs/`.

Expected runtime is under one minute on a normal laptop.

## Project Files

- `inventory_env.py`: the 14-day business simulator.
- `q_learning_agent.py`: tabular Q-learning implementation.
- `policies.py`: baseline and random policies.
- `train_and_evaluate.py`: training, evaluation, saved artifacts, and plots.
- `business_memo.md`: deployment recommendation and risk discussion.
- `outputs/`: generated evaluation results, Q-table, and SVG plots.

## Problem Framing

### State

Each state is a tuple:

```text
(today_inventory, yesterday_inventory, day_of_week, same_day_last_week_inventory)
```

For tabular Q-learning, the inventory values are bucketed before lookup in the
Q-table:

```text
0 = low inventory, below 10 units
1 = medium inventory, 10 to 19 units
2 = high inventory, 20 or more units
```

The learning state is therefore:

```text
(today_inventory_bucket, yesterday_inventory_bucket, day_of_week, same_day_last_week_inventory_bucket)
```

### Action

The action space has three discrete choices:

```text
0 = order_none = order 0 units
1 = order_less = order 5 units
2 = order_more = order 15 units
```

Orders have a one-day lead time: an order placed today is available as part of
tomorrow's starting inventory. Inventory is capped at 30 units so the agent
cannot build unlimited stock.

### Reward

The reward is daily profit:

```text
reward = revenue - purchase cost - holding cost - stockout penalty
```

Where:

- `revenue = units_sold * selling_price`
- `purchase cost = units_received_next_day * unit_purchase_cost`
- `holding cost = ending_inventory * holding_cost_per_unit`
- `stockout penalty = unmet_demand * stockout_penalty_per_unit`

The goal is to maximize total monetary reward over the episode.

### Transition

For each day:

1. The agent observes the current state.
2. The agent chooses an order action.
3. Customer demand is sampled for that day of week with random variation.
4. Inventory decreases by the number of units sold.
5. If demand is higher than inventory, the difference is counted as stockout.
6. The order arrives for the next day, limited by the inventory cap.
7. The next day's state is created from the new inventory history.

### Horizon

Each episode lasts 14 days, so the agent is planning over the next two weeks.

## Baseline

The main baseline is the reorder point policy:

```python
if inventory < 10:
    order 15
else:
    order 0
```

A random policy is also included only as a weak sanity check.

## Learning Agent

The learning agent uses tabular Q-learning:

```text
Q(s, a) <- Q(s, a) + alpha * (reward + gamma * max_a Q(s_next, a) - Q(s, a))
```

Training settings:

- Episodes: 10000
- Learning rate: 0.12
- Discount factor: 0.92
- Exploration: epsilon-greedy
- Initial epsilon: 0.25
- Minimum epsilon: 0.03

When multiple actions have the same Q-value for a state, the agent uses the
reorder point action as a tie-breaker. This avoids arbitrary behavior in rarely
seen states while still allowing Q-learning updates to change the policy when
there is evidence.

## Evaluation

The script evaluates:

- random policy
- reorder point baseline
- trained Q-learning policy

Each policy is evaluated across 200 simulated 14-day episodes using fixed
random seeds for reproducibility.

The evaluation reports:

- average 14-day profit
- worst episode profit
- best episode profit
- average stockout units
- average units sold

It also checks two edge episodes:

- low starting inventory
- high starting inventory

Saved run result:

| Policy | Average profit | Average stockout units | Average units sold |
| --- | ---: | ---: | ---: |
| random policy | 458.25 | 32.79 | 89.38 |
| reorder point policy | 515.95 | 27.67 | 94.50 |
| Q-learning policy | 571.92 | 19.95 | 102.22 |

The exact saved values are in `outputs/evaluation_summary.json`.
In this run, adding one-day lead time and more variable demand gave Q-learning
room to use the day-of-week and inventory-history state better than the simple
reorder point baseline.

## Plots and Artifacts

Generated files:

- `outputs/evaluation_summary.json`
- `outputs/edge_episode_details.json`
- `outputs/q_table.json`
- `outputs/training_reward_curve.svg`
- `outputs/performance_comparison.svg`
- `outputs/policy_by_inventory.svg`

## Validation

From the repository root:

```bash
python3 -m py_compile Assignment2/inventory_env.py Assignment2/q_learning_agent.py Assignment2/policies.py Assignment2/train_and_evaluate.py
python3 Assignment2/train_and_evaluate.py
```
