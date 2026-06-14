from __future__ import annotations


def reorder_point_policy(state: tuple[int, int, int, int]) -> int:
    """Baseline: if inventory is below 10, order 15 units; otherwise order 0."""
    today_inventory = state[0]
    if today_inventory < 10:
        return 2
    return 0


def random_policy(state: tuple[int, int, int, int], rng) -> int:
    return rng.choice([0, 1, 2])
