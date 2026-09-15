"""Driver AI — per-lap racing decisions: push, save, defend, attack."""
import random
from dataclasses import dataclass
from .driver import Driver
from .car import CarState


@dataclass
class DriverLapDecision:
    mode: str  # "PUSH", "BALANCED", "SAVE"
    deploy_energy: bool
    attack_gap: bool  # whether they'll attempt an overtake this lap if gap allows


def decide(driver: Driver, car: CarState, gap_ahead: float, gap_behind: float,
           laps_remaining: int, rng: random.Random) -> DriverLapDecision:
    a = driver.attributes

    # Fuel/tyre management overrides aggression late in a stint.
    if car.fuel_level < 8 and laps_remaining > 3:
        mode = "SAVE"
    elif car.tyres.wear > 85:
        mode = "SAVE" if a.tyre_management < 60 else "BALANCED"
    elif gap_ahead is not None and gap_ahead < 1.0:
        mode = "PUSH"
    elif gap_behind is not None and gap_behind < 1.0:
        mode = "PUSH"
    else:
        # baseline tendency from aggression
        roll = rng.random() * 100
        mode = "PUSH" if roll < a.aggression * 0.4 else "BALANCED"

    deploy_energy = mode == "PUSH" and car.energy_battery > 15
    attack_gap = gap_ahead is not None and gap_ahead < 1.0 and mode in ("PUSH", "BALANCED")

    return DriverLapDecision(mode=mode, deploy_energy=deploy_energy, attack_gap=attack_gap)


def overtake_probability(attacker: Driver, attacker_car: CarState,
                          defender: Driver, defender_car: CarState,
                          pace_delta: float, rng: random.Random) -> float:
    """pace_delta: attacker lap-pace advantage in seconds (positive = attacker faster)."""
    base = 0.05 + max(0.0, pace_delta) * 0.30
    skill_term = (attacker.attributes.overtaking - defender.attributes.defending) / 250.0
    tyre_term = (defender_car.tyres.wear - attacker_car.tyres.wear) / 350.0
    return max(0.0, min(0.85, base + skill_term + tyre_term))
