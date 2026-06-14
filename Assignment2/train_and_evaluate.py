from __future__ import annotations

import json
import random
from pathlib import Path
from statistics import mean

from inventory_env import ACTION_NAMES, EnvConfig, InventoryReplenishmentEnv
from policies import random_policy, reorder_point_policy
from q_learning_agent import QLearningAgent


OUTPUT_DIR = Path(__file__).parent / "outputs"
TRAINING_EPISODES = 10000


def bucket_inventory(inventory: int) -> int:
    if inventory < 10:
        return 0
    if inventory < 20:
        return 1
    return 2


def bucket_state(state: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    today_inventory, yesterday_inventory, day_of_week, last_week_inventory = state
    return (
        bucket_inventory(today_inventory),
        bucket_inventory(yesterday_inventory),
        day_of_week,
        bucket_inventory(last_week_inventory),
    )


def run_episode(env: InventoryReplenishmentEnv, policy_fn) -> dict:
    state = env.reset()
    total_reward = 0.0
    total_stockouts = 0
    total_units_sold = 0
    steps = []

    done = False
    while not done:
        action = policy_fn(state)
        next_state, reward, done, info = env.step(action)
        total_reward += reward
        total_stockouts += info["unmet_demand"]
        total_units_sold += info["units_sold"]
        steps.append({**info, "action": ACTION_NAMES[action]})
        state = next_state

    return {
        "total_reward": round(total_reward, 2),
        "total_stockouts": total_stockouts,
        "total_units_sold": total_units_sold,
        "steps": steps,
    }


def train_q_learning(
    episodes: int = TRAINING_EPISODES,
    seed: int = 7,
) -> tuple[QLearningAgent, list[float]]:
    agent = QLearningAgent(actions=[0, 1, 2], seed=seed)
    rewards = []

    for episode in range(episodes):
        env = InventoryReplenishmentEnv(seed=seed + episode)
        state = bucket_state(env.reset())
        total_reward = 0.0
        done = False

        while not done:
            action = agent.choose_action(state, training=True)
            next_raw_state, reward, done, _ = env.step(action)
            next_state = bucket_state(next_raw_state)
            agent.update(state, action, reward, next_state, done)
            total_reward += reward
            state = next_state

        agent.decay_exploration()
        rewards.append(total_reward)

    return agent, rewards


def evaluate_policy(name: str, policy_fn, episodes: int = 200, seed: int = 1000) -> dict:
    results = []
    for episode in range(episodes):
        env = InventoryReplenishmentEnv(seed=seed + episode)
        results.append(run_episode(env, policy_fn))

    rewards = [item["total_reward"] for item in results]
    stockouts = [item["total_stockouts"] for item in results]
    units_sold = [item["total_units_sold"] for item in results]

    return {
        "policy": name,
        "episodes": episodes,
        "average_profit": round(mean(rewards), 2),
        "worst_episode_profit": round(min(rewards), 2),
        "best_episode_profit": round(max(rewards), 2),
        "average_stockout_units": round(mean(stockouts), 2),
        "average_units_sold": round(mean(units_sold), 2),
    }


def save_q_table(agent: QLearningAgent) -> None:
    serializable = {
        ",".join(map(str, state)): values
        for state, values in sorted(agent.q_table.items(), key=lambda item: item[0])
    }
    (OUTPUT_DIR / "q_table.json").write_text(
        json.dumps(serializable, indent=2),
        encoding="utf-8",
    )


def learned_policy(agent: QLearningAgent):
    def policy(state: tuple[int, int, int, int]) -> int:
        return agent.best_action(bucket_state(state))

    return policy


def moving_average(values: list[float], window: int = 100) -> list[float]:
    averaged = []
    for index in range(len(values)):
        start = max(0, index - window + 1)
        averaged.append(mean(values[start : index + 1]))
    return averaged


def write_line_plot(path: Path, title: str, values: list[float]) -> None:
    width, height = 760, 360
    margin = 50
    if not values:
        return
    min_value = min(values)
    max_value = max(values)
    value_range = max(max_value - min_value, 1)
    points = []
    for index, value in enumerate(values):
        x = margin + index * (width - 2 * margin) / max(len(values) - 1, 1)
        y = height - margin - (value - min_value) * (height - 2 * margin) / value_range
        points.append(f"{x:.1f},{y:.1f}")

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="white"/>
  <text x="{margin}" y="30" font-family="Arial" font-size="18">{title}</text>
  <line x1="{margin}" y1="{height - margin}" x2="{width - margin}" y2="{height - margin}" stroke="#333"/>
  <line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height - margin}" stroke="#333"/>
  <polyline fill="none" stroke="#1f77b4" stroke-width="2" points="{' '.join(points)}"/>
  <text x="{margin}" y="{height - 15}" font-family="Arial" font-size="12">episode</text>
  <text x="8" y="{margin}" font-family="Arial" font-size="12">{max_value:.0f}</text>
  <text x="8" y="{height - margin}" font-family="Arial" font-size="12">{min_value:.0f}</text>
</svg>
"""
    path.write_text(svg, encoding="utf-8")


def write_bar_plot(path: Path, title: str, labels: list[str], values: list[float]) -> None:
    width, height = 640, 360
    margin = 60
    max_value = max(values) if values else 1
    bar_width = 90
    gap = 70
    bars = []

    for index, (label, value) in enumerate(zip(labels, values)):
        x = margin + index * (bar_width + gap)
        bar_height = value * (height - 2 * margin) / max(max_value, 1)
        y = height - margin - bar_height
        bars.append(
            f'<rect x="{x}" y="{y:.1f}" width="{bar_width}" height="{bar_height:.1f}" fill="#2a9d8f"/>'
            f'<text x="{x + bar_width / 2}" y="{height - 35}" text-anchor="middle" font-family="Arial" font-size="12">{label}</text>'
            f'<text x="{x + bar_width / 2}" y="{y - 8:.1f}" text-anchor="middle" font-family="Arial" font-size="12">{value:.1f}</text>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="white"/>
  <text x="{margin}" y="30" font-family="Arial" font-size="18">{title}</text>
  <line x1="{margin}" y1="{height - margin}" x2="{width - margin}" y2="{height - margin}" stroke="#333"/>
  <line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height - margin}" stroke="#333"/>
  {''.join(bars)}
</svg>
"""
    path.write_text(svg, encoding="utf-8")


def write_policy_plot(path: Path, agent: QLearningAgent) -> None:
    labels = [str(inventory) for inventory in range(0, 31)]
    action_scores = []
    for inventory in range(0, 31):
        state = (inventory, inventory, 0, inventory)
        action_scores.append(agent.best_action(bucket_state(state)))

    width, height = 820, 260
    margin = 50
    cell_width = (width - 2 * margin) / len(labels)
    colors = {0: "#b8c0ff", 1: "#ffd166", 2: "#ef476f"}
    cells = []
    for index, action in enumerate(action_scores):
        x = margin + index * cell_width
        cells.append(
            f'<rect x="{x:.1f}" y="80" width="{cell_width:.1f}" height="70" fill="{colors[action]}"/>'
            f'<text x="{x + cell_width / 2:.1f}" y="170" text-anchor="middle" font-family="Arial" font-size="10">{labels[index]}</text>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="white"/>
  <text x="{margin}" y="30" font-family="Arial" font-size="18">Learned policy by current inventory, Monday state</text>
  {''.join(cells)}
  <text x="{margin}" y="215" font-family="Arial" font-size="12">blue: order none, yellow: order less, red: order more</text>
</svg>
"""
    path.write_text(svg, encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    seed = 7
    agent, training_rewards = train_q_learning(episodes=TRAINING_EPISODES, seed=seed)
    rng = random.Random(seed)

    q_policy = learned_policy(agent)
    random_result = evaluate_policy(
        "random_policy",
        lambda state: random_policy(state, rng),
    )
    baseline_result = evaluate_policy("reorder_point_policy", reorder_point_policy)
    q_result = evaluate_policy("q_learning_policy", q_policy)

    edge_episodes = {
        "low_start_inventory": run_episode(
            InventoryReplenishmentEnv(config=EnvConfig(initial_inventory=3), seed=301),
            q_policy,
        ),
        "high_start_inventory": run_episode(
            InventoryReplenishmentEnv(config=EnvConfig(initial_inventory=28), seed=302),
            q_policy,
        ),
    }

    summary = {
        "problem": "14-day retail inventory replenishment for one product",
        "state": [
            "today_inventory",
            "yesterday_inventory",
            "day_of_week",
            "same_day_last_week_inventory",
        ],
        "actions": ACTION_NAMES,
        "reward": "revenue - purchase cost - holding cost - stockout penalty",
        "horizon_days": 14,
        "order_lead_time_days": 1,
        "demand_noise_range": [-4, 4],
        "training_episodes": TRAINING_EPISODES,
        "q_learning_state_used_for_training": [
            "today_inventory_bucket",
            "yesterday_inventory_bucket",
            "day_of_week",
            "same_day_last_week_inventory_bucket",
        ],
        "results": [random_result, baseline_result, q_result],
        "edge_episodes": {
            name: {
                "total_reward": episode["total_reward"],
                "total_stockouts": episode["total_stockouts"],
                "total_units_sold": episode["total_units_sold"],
            }
            for name, episode in edge_episodes.items()
        },
    }

    (OUTPUT_DIR / "evaluation_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "edge_episode_details.json").write_text(
        json.dumps(edge_episodes, indent=2),
        encoding="utf-8",
    )
    save_q_table(agent)

    write_line_plot(
        OUTPUT_DIR / "training_reward_curve.svg",
        "Q-learning training reward, 100-episode moving average",
        moving_average(training_rewards, window=100),
    )
    write_bar_plot(
        OUTPUT_DIR / "performance_comparison.svg",
        "Average 14-day profit by policy",
        [item["policy"] for item in summary["results"]],
        [item["average_profit"] for item in summary["results"]],
    )
    write_policy_plot(OUTPUT_DIR / "policy_by_inventory.svg", agent)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
