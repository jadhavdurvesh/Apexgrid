"""R&D and team economy — Part V/VII of the Bible.

Teams earn prize money from a race, then spend part of their budget
developing the car between rounds, with a real pace/reliability tradeoff.
"""
import random
from dataclasses import dataclass
from typing import Dict, List
from .team import Team

DEVELOPABLE_AREAS = [
    "aero", "engine_power", "energy_recovery", "braking",
    "suspension", "cooling", "tyre_management",
]

PRIZE_MONEY_BY_POSITION = {
    1: 8_000_000, 2: 6_500_000, 3: 5_500_000, 4: 4_500_000, 5: 4_000_000,
    6: 3_500_000, 7: 3_000_000, 8: 2_500_000, 9: 2_000_000, 10: 1_500_000,
}
BASE_PAYMENT = 800_000


@dataclass
class RDEvent:
    team_id: str
    description: str


def award_prize_money(teams: Dict[str, Team], classification: list):
    """Split constructor prize money across a team's two cars' finishing positions."""
    for row in classification:
        team_id = None
        for tid, team in teams.items():
            if team.name == row["team"]:
                team_id = tid
                break
        if team_id is None:
            continue
        teams[team_id].budget += BASE_PAYMENT + PRIZE_MONEY_BY_POSITION.get(row["position"], 0)


def run_rd_cycle(teams: Dict[str, Team], rng: random.Random,
                  spend_fraction: float = 0.15) -> List[RDEvent]:
    events = []
    for team in teams.values():
        spend = team.budget * spend_fraction
        if spend < 500_000:
            continue
        team.budget -= spend

        area = rng.choice(DEVELOPABLE_AREAS)
        gain = min(4.0, spend / 3_000_000) * rng.uniform(0.6, 1.3)
        current = getattr(team.car, area)
        setattr(team.car, area, round(min(99.0, current + gain), 1))

        # Aggressive development sometimes costs reliability; conservative gains it back slowly.
        if rng.random() < 0.3:
            reliability_delta = -rng.uniform(0.5, 2.0)
        else:
            reliability_delta = rng.uniform(0.0, 0.6)
        team.car.reliability = round(min(99.0, max(35.0, team.car.reliability + reliability_delta)), 1)

        events.append(RDEvent(
            team_id=team.team_id,
            description=(
                f"{team.name} invests ${spend/1_000_000:.1f}M into {area.replace('_', ' ')} "
                f"(+{gain:.2f}), reliability {'+' if reliability_delta >= 0 else ''}{reliability_delta:.2f}."
            ),
        ))
    return events
