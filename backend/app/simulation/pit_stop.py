"""Pit stop execution: crew skill, reaction time, and human error all matter."""
import random
from dataclasses import dataclass


@dataclass
class PitStopResult:
    total_pit_lane_seconds: float
    stationary_seconds: float
    slow_stop: bool
    description: str


def execute_pit_stop(pit_crew_skill: float, rng: random.Random) -> PitStopResult:
    """pit_crew_skill: 0-100. Base stationary time ~2.2-2.6s for a good crew."""
    skill_factor = (100 - pit_crew_skill) / 100.0
    base_stationary = 2.2 + skill_factor * 1.5
    stationary = max(1.9, rng.gauss(base_stationary, 0.3 + skill_factor * 0.4))

    slow_stop = False
    error_chance = 0.03 + skill_factor * 0.08
    if rng.random() < error_chance:
        stationary += rng.uniform(1.5, 4.0)
        slow_stop = True

    pit_lane_travel = rng.uniform(18.0, 24.0)  # time lost driving through pit lane at limiter speed
    total = stationary + pit_lane_travel

    desc = f"{stationary:.2f}s stop" + (" — slow release!" if slow_stop else "")
    return PitStopResult(
        total_pit_lane_seconds=round(total, 2),
        stationary_seconds=round(stationary, 2),
        slow_stop=slow_stop,
        description=desc,
    )
