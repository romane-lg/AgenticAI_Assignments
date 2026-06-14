from __future__ import annotations

import random
from dataclasses import dataclass


ACTION_ORDER_QUANTITY = {
    0: 0,
    1: 5,
    2: 15,
}

ACTION_NAMES = {
    0: "order_none",
    1: "order_less",
    2: "order_more",
}


@dataclass(frozen=True)
class EnvConfig:
    horizon_days: int = 14
    max_inventory: int = 30
    initial_inventory: int = 12
    selling_price: float = 12.0
    unit_purchase_cost: float = 5.0
    holding_cost_per_unit: float = 0.50
    stockout_penalty_per_unit: float = 3.0
    order_lead_time_days: int = 1


class InventoryReplenishmentEnv:
    """Small 14-day inventory replenishment simulator for one retail product."""

    def __init__(self, config: EnvConfig | None = None, seed: int = 7) -> None:
        self.config = config or EnvConfig()
        self.random = random.Random(seed)
        self.reset()

    def reset(self) -> tuple[int, int, int, int]:
        self.day = 0
        self.inventory = self.config.initial_inventory
        self.inventory_history = [self.config.initial_inventory]
        return self._state()

    def step(self, action: int) -> tuple[tuple[int, int, int, int], float, bool, dict]:
        if action not in ACTION_ORDER_QUANTITY:
            raise ValueError(f"Unknown action {action}. Expected 0, 1, or 2.")

        starting_inventory = self.inventory
        order_quantity = ACTION_ORDER_QUANTITY[action]

        demand = self._sample_demand(day_of_week=self.day % 7)
        units_sold = min(starting_inventory, demand)
        unmet_demand = max(demand - starting_inventory, 0)
        ending_inventory_before_receipt = starting_inventory - units_sold
        received_units = min(
            order_quantity,
            self.config.max_inventory - ending_inventory_before_receipt,
        )
        next_day_inventory = ending_inventory_before_receipt + received_units

        revenue = units_sold * self.config.selling_price
        order_cost = received_units * self.config.unit_purchase_cost
        holding_cost = next_day_inventory * self.config.holding_cost_per_unit
        stockout_penalty = unmet_demand * self.config.stockout_penalty_per_unit
        reward = revenue - order_cost - holding_cost - stockout_penalty

        self.inventory = next_day_inventory
        self.inventory_history.append(next_day_inventory)
        self.day += 1
        done = self.day >= self.config.horizon_days

        info = {
            "day": self.day,
            "day_of_week": (self.day - 1) % 7,
            "starting_inventory": starting_inventory,
            "order_quantity": order_quantity,
            "received_units_next_day": received_units,
            "demand": demand,
            "units_sold": units_sold,
            "ending_inventory_before_receipt": ending_inventory_before_receipt,
            "next_day_inventory": next_day_inventory,
            "unmet_demand": unmet_demand,
            "revenue": revenue,
            "order_cost": order_cost,
            "holding_cost": holding_cost,
            "stockout_penalty": stockout_penalty,
            "reward": reward,
        }
        return self._state(), reward, done, info

    def _state(self) -> tuple[int, int, int, int]:
        today_inventory = self.inventory
        yesterday_inventory = (
            self.inventory_history[-2]
            if len(self.inventory_history) >= 2
            else self.inventory
        )
        same_day_last_week_inventory = (
            self.inventory_history[self.day - 7]
            if self.day >= 7
            else self.config.initial_inventory
        )
        return (
            today_inventory,
            yesterday_inventory,
            self.day % 7,
            same_day_last_week_inventory,
        )

    def _sample_demand(self, day_of_week: int) -> int:
        base_demand_by_day = [7, 8, 7, 8, 10, 12, 9]
        base = base_demand_by_day[day_of_week]
        noise = self.random.choice([-4, -3, -2, -1, 0, 1, 2, 3, 4])
        return max(base + noise, 0)
