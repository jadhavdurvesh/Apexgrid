"""Qualifying — sets the grid from an actual simulated session instead of a
synthetic pace estimate.

v0.1 simplification: one flying-lap-style session per driver rather than a
full Q1/Q2/Q3 knockout structure (that's a fine next step once this is
tuned — the elimination structure doesn't change the underlying lap-time
model, just how many attempts each driver gets).
"""
import random
from dataclasses import dataclass
from typing import Dict, List
from .driver import Driver
from .team import Team
from .tyres import TyreSet, Compound
from .weather import Weather


@dataclass
class QualifyingResult:
    grid_order: List[str]  # driver_ids, best to worst
    best_laps: Dict[str, float]


def run_qualifying(teams: Dict[str, Team], drivers: Dict[str, Driver],
                    weather: Weather, rng: random.Random, base_lap_time: float = 90.0,
                    attempts: int = 3) -> QualifyingResult:
    best_laps: Dict[str, float] = {}

    for did, driver in drivers.items():
        team = teams[driver.team_id]
        best = None
        tyres = TyreSet(compound=Compound.SOFT)

        for attempt in range(attempts):
            a = driver.attributes
            skill_time = base_lap_time - (a.qualifying - 65) * 0.06
            car_time = -(team.car.performance_score() - 65) * 0.055
            tyre_time = tyres.compound_advantage_seconds() + tyres.cold_penalty_seconds()

            wet_penalty = 0.0
            if weather.track_wetness > 5:
                wet_penalty = (weather.track_wetness / 100.0) * (100 - a.wet_performance) / 100.0 * 2.5

            # Pressure and reaction matter more on a qualifying lap than a race lap.
            pressure_noise = rng.gauss(0, 0.35 + (100 - a.pressure_handling) / 250.0)
            mistake_chance = 0.05 + max(0.0, 70 - a.reaction) / 500.0
            mistake_penalty = rng.uniform(0.4, 1.8) if rng.random() < mistake_chance else 0.0

            lap_time = skill_time + car_time + tyre_time + wet_penalty + pressure_noise + mistake_penalty
            tyres.step_lap(a.aggression, a.tyre_management, weather.track_temp)

            if best is None or lap_time < best:
                best = lap_time

        best_laps[did] = round(best, 3)

    grid_order = sorted(best_laps.keys(), key=lambda d: best_laps[d])
    return QualifyingResult(grid_order=grid_order, best_laps=best_laps)
