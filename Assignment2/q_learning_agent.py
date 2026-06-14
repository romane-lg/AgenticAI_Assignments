from __future__ import annotations

import random


class QLearningAgent:
    def __init__(
        self,
        actions: list[int],
        learning_rate: float = 0.12,
        discount_factor: float = 0.92,
        epsilon: float = 0.25,
        epsilon_decay: float = 0.997,
        min_epsilon: float = 0.03,
        seed: int = 7,
    ) -> None:
        self.actions = actions
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = min_epsilon
        self.random = random.Random(seed)
        self.q_table: dict[tuple[int, int, int, int], dict[int, float]] = {}

    def choose_action(self, state: tuple[int, int, int, int], training: bool = True) -> int:
        self._ensure_state(state)
        if training and self.random.random() < self.epsilon:
            return self.random.choice(self.actions)
        return self.best_action(state)

    def best_action(self, state: tuple[int, int, int, int]) -> int:
        self._ensure_state(state)
        values = self.q_table[state]
        best_value = max(values.values())
        tied_actions = [
            action for action in self.actions if values[action] == best_value
        ]
        if len(tied_actions) == 1:
            return tied_actions[0]

        today_inventory_bucket = state[0]
        baseline_action = 2 if today_inventory_bucket == 0 else 0
        if baseline_action in tied_actions:
            return baseline_action
        return tied_actions[0]

    def update(
        self,
        state: tuple[int, int, int, int],
        action: int,
        reward: float,
        next_state: tuple[int, int, int, int],
        done: bool,
    ) -> None:
        self._ensure_state(state)
        self._ensure_state(next_state)
        current_value = self.q_table[state][action]
        next_value = 0.0 if done else max(self.q_table[next_state].values())
        target = reward + self.discount_factor * next_value
        self.q_table[state][action] = current_value + self.learning_rate * (
            target - current_value
        )

    def decay_exploration(self) -> None:
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)

    def _ensure_state(self, state: tuple[int, int, int, int]) -> None:
        if state not in self.q_table:
            self.q_table[state] = {action: 0.0 for action in self.actions}
