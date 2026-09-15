"""Incidents: lock-ups, spins, crashes, and mechanical failures."""
import random
from dataclasses import dataclass
from typing import Optional
from .driver import Driver
from .car import CarState
from .weather import Weather


@dataclass
class IncidentResult:
    kind: str  # "LOCKUP", "SPIN", "CRASH", "MECH_FAILURE", or "" for none
    driver_id: str
    time_penalty_seconds: float = 0.0
    dnf: bool = False
    triggers_safety_car: bool = False
    description: str = ""


def check_incident(driver: Driver, car: CarState, weather: Weather,
                    rng: random.Random, under_pressure: bool = False) -> Optional[IncidentResult]:
    a = driver.attributes
    wet_factor = 1.0 + (weather.track_wetness / 100.0) * (1.0 - a.wet_performance / 100.0)
    tyre_cliff_factor = 1.0 + max(0.0, (car.tyres.wear - 85)) / 30.0
    pressure_factor = 1.3 if under_pressure and a.pressure_handling < 55 else 1.0
    aggression_factor = 1.0 + max(0.0, (a.aggression - 70)) / 100.0

    base_incident_chance = 0.006  # per lap baseline
    chance = base_incident_chance * wet_factor * tyre_cliff_factor * pressure_factor * aggression_factor

    if rng.random() < chance:
        roll = rng.random()
        if roll < 0.55:
            return IncidentResult(
                kind="LOCKUP", driver_id=driver.driver_id, time_penalty_seconds=rng.uniform(0.8, 2.5),
                description=f"{driver.name} locks up and runs wide.",
            )
        elif roll < 0.85:
            return IncidentResult(
                kind="SPIN", driver_id=driver.driver_id, time_penalty_seconds=rng.uniform(4, 12),
                description=f"{driver.name} spins!",
            )
        else:
            return IncidentResult(
                kind="CRASH", driver_id=driver.driver_id, dnf=True, triggers_safety_car=True,
                description=f"{driver.name} has crashed out of the race!",
            )

    # Mechanical failure check, independent of driving. `car.health` is degraded
    # lap-by-lap in the engine via CarState.degrade(team.car.reliability), so a
    # low-reliability car actually accumulates real failure risk over a race.
    worst = car.health.worst()
    failure_chance = ((max(0.0, 100 - worst)) / 100.0) ** 1.6 * 0.05
    if rng.random() < failure_chance:
        return IncidentResult(
            kind="MECH_FAILURE", driver_id=driver.driver_id, dnf=True,
            description=f"{driver.name} pulls over — mechanical failure.",
        )

    return None
