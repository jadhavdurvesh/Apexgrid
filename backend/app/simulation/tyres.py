"""Tyre compounds and degradation model."""
from dataclasses import dataclass
from enum import Enum


class Compound(str, Enum):
    SOFT = "SOFT"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    INTERMEDIATE = "INTERMEDIATE"
    WET = "WET"


# (grip_index, wear_rate_per_lap, warmup_laps) — grip_index is a lap-time
# advantage in "seconds equivalent" relative to HARD at zero wear.
COMPOUND_BASE = {
    Compound.SOFT: {"grip": 0.9, "wear_rate": 3.2, "warmup_laps": 1},
    Compound.MEDIUM: {"grip": 0.45, "wear_rate": 2.0, "warmup_laps": 2},
    Compound.HARD: {"grip": 0.0, "wear_rate": 1.1, "warmup_laps": 3},
    Compound.INTERMEDIATE: {"grip": 0.2, "wear_rate": 1.6, "warmup_laps": 2},
    Compound.WET: {"grip": -0.3, "wear_rate": 1.0, "warmup_laps": 2},
}


@dataclass
class TyreSet:
    compound: Compound
    wear: float = 0.0  # 0-100, 100 = fully worn / cliff
    laps_on: int = 0

    def step_lap(self, driving_aggression: float, tyre_management_skill: float, track_temp: float):
        base = COMPOUND_BASE[self.compound]["wear_rate"]
        aggression_factor = 1.0 + (driving_aggression - 50) / 100.0
        management_factor = 1.0 - (tyre_management_skill - 50) / 200.0
        temp_factor = 1.0 + max(0.0, (track_temp - 35)) / 100.0
        self.wear = min(100.0, self.wear + base * aggression_factor * management_factor * temp_factor)
        self.laps_on += 1

    def grip_penalty_seconds(self) -> float:
        """Extra seconds per lap from wear. Cliff effect above 80% wear."""
        linear = (self.wear / 100.0) * 1.1
        cliff = 0.0
        if self.wear > 80:
            cliff = (self.wear - 80) * 0.12
        return linear + cliff

    def compound_advantage_seconds(self) -> float:
        return -COMPOUND_BASE[self.compound]["grip"]  # negative wear-free time vs HARD

    def is_warmed_up(self) -> bool:
        return self.laps_on >= COMPOUND_BASE[self.compound]["warmup_laps"]

    def cold_penalty_seconds(self) -> float:
        if self.is_warmed_up():
            return 0.0
        remaining = COMPOUND_BASE[self.compound]["warmup_laps"] - self.laps_on
        return 0.4 * remaining
