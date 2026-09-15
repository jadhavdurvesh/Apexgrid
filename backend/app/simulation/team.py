"""Team model — car performance, reliability, and simple economy."""
from dataclasses import dataclass, field
import random


@dataclass
class CarPerformance:
    aero: float
    engine_power: float
    energy_recovery: float
    braking: float
    suspension: float
    cooling: float
    tyre_management: float
    reliability: float  # 0-100, higher = fewer failures

    @classmethod
    def random(cls, rng: random.Random, tier: float = 1.0) -> "CarPerformance":
        """tier scales the whole car up/down — used to spread the grid out."""
        def r(lo, hi):
            return round(min(99, max(30, rng.uniform(lo, hi) * tier)), 1)

        return cls(
            aero=r(55, 90),
            engine_power=r(55, 90),
            energy_recovery=r(55, 90),
            braking=r(55, 90),
            suspension=r(55, 90),
            cooling=r(55, 90),
            tyre_management=r(55, 90),
            reliability=r(60, 95),
        )

    def performance_score(self) -> float:
        return (
            self.aero * 0.25
            + self.engine_power * 0.25
            + self.energy_recovery * 0.10
            + self.braking * 0.10
            + self.suspension * 0.10
            + self.cooling * 0.05
            + self.tyre_management * 0.15
        )


@dataclass
class Upgrade:
    name: str
    lap_time_delta: float  # negative = faster
    reliability_delta: float = 0.0


@dataclass
class Team:
    team_id: str
    name: str
    car: CarPerformance
    budget: float = 100_000_000.0
    prize_money_last_season: float = 0.0
    upgrades_applied: list = field(default_factory=list)
    constructors_points: float = 0.0
    pit_crew_skill: float = 70.0  # affects pit stop time/consistency

    def apply_upgrade(self, upgrade: Upgrade):
        self.upgrades_applied.append(upgrade)
        self.car.reliability = min(99.0, self.car.reliability + upgrade.reliability_delta)
