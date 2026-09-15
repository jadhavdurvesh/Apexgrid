"""Driver model — attributes that actually feed the simulation, not just a profile."""
from dataclasses import dataclass, field
import random


@dataclass
class DriverAttributes:
    pace: float
    consistency: float
    racecraft: float
    overtaking: float
    defending: float
    qualifying: float
    wet_performance: float
    aggression: float
    reaction: float
    tyre_management: float
    pressure_handling: float
    fitness: float
    potential: float
    experience: float
    morale: float = 75.0

    @classmethod
    def random_rookie(cls, rng: random.Random) -> "DriverAttributes":
        """Generate a plausible rookie: high potential, everything else mid/low."""
        def r(lo, hi):
            return round(rng.uniform(lo, hi), 1)

        return cls(
            pace=r(55, 78),
            consistency=r(40, 65),
            racecraft=r(40, 65),
            overtaking=r(45, 70),
            defending=r(40, 65),
            qualifying=r(50, 75),
            wet_performance=r(35, 70),
            aggression=r(50, 90),
            reaction=r(60, 90),
            tyre_management=r(35, 60),
            pressure_handling=r(35, 65),
            fitness=r(70, 95),
            potential=r(65, 98),
            experience=r(0, 15),
            morale=75.0,
        )

    @classmethod
    def random_veteran(cls, rng: random.Random) -> "DriverAttributes":
        def r(lo, hi):
            return round(rng.uniform(lo, hi), 1)

        return cls(
            pace=r(65, 96),
            consistency=r(60, 95),
            racecraft=r(60, 96),
            overtaking=r(55, 92),
            defending=r(55, 92),
            qualifying=r(60, 95),
            wet_performance=r(45, 92),
            aggression=r(30, 80),
            reaction=r(55, 90),
            tyre_management=r(55, 92),
            pressure_handling=r(55, 92),
            fitness=r(55, 90),
            potential=r(40, 85),
            experience=r(30, 95),
            morale=75.0,
        )


@dataclass
class Driver:
    driver_id: str
    name: str
    number: int
    team_id: str
    attributes: DriverAttributes
    career: dict = field(default_factory=lambda: {
        "wins": 0, "podiums": 0, "poles": 0, "points": 0,
        "races": 0, "championships": 0, "dnfs": 0,
    })
    retired: bool = False

    def base_pace_score(self) -> float:
        """Rough single-number pace used before car/tyre/weather modifiers."""
        a = self.attributes
        return (
            a.pace * 0.35
            + a.consistency * 0.15
            + a.racecraft * 0.15
            + a.reaction * 0.10
            + a.tyre_management * 0.10
            + a.pressure_handling * 0.10
            + (a.morale - 50) * 0.05
        )
