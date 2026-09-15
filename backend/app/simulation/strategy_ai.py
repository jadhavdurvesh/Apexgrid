"""Team Strategy AI — the pit wall. Allowed to make bad calls on purpose."""
import random
from dataclasses import dataclass
from .car import CarState
from .weather import Weather
from .tyres import Compound


@dataclass
class StrategyDecision:
    action: str  # "STAY_OUT" or "BOX"
    target_compound: Compound = None


def decide(car: CarState, weather: Weather, current_lap: int, total_laps: int,
           rng: random.Random, team_aggression: float = 0.5) -> StrategyDecision:
    laps_remaining = total_laps - current_lap

    # Weather-forced call: track wetness has crossed the usable threshold for current tyre.
    is_wet_tyre = car.tyres.compound in (Compound.INTERMEDIATE, Compound.WET)
    if weather.recommended_compound_is_wet() and not is_wet_tyre and laps_remaining > 1:
        target = Compound.WET if weather.track_wetness > 55 else Compound.INTERMEDIATE
        return StrategyDecision(action="BOX", target_compound=target)
    if not weather.recommended_compound_is_wet() and is_wet_tyre and laps_remaining > 1:
        return StrategyDecision(action="BOX", target_compound=Compound.MEDIUM)

    # Tyre-wear-forced call.
    cliff_threshold = 78 - (team_aggression * 10)  # aggressive strategies push tyres further
    if car.tyres.wear > cliff_threshold and laps_remaining > 2:
        # Bad-strategy chance: pit wall occasionally makes a suboptimal or mistimed call.
        if rng.random() < 0.12:
            return StrategyDecision(action="STAY_OUT")  # a call that will age badly
        next_compound = Compound.HARD if laps_remaining > total_laps * 0.35 else Compound.MEDIUM
        return StrategyDecision(action="BOX", target_compound=next_compound)

    # Occasional undercut attempt even without a forced tyre issue.
    if car.tyres.wear > 45 and laps_remaining > total_laps * 0.25 and rng.random() < 0.02 * team_aggression:
        return StrategyDecision(action="BOX", target_compound=Compound.MEDIUM)

    return StrategyDecision(action="STAY_OUT")
