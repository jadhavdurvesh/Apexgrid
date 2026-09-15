"""Stewards — investigates violations and hands out penalties.

v0.1 covers two violation types that don't require full multi-car contact
modeling: track limits (escalating warnings -> time penalty) and unsafe
pit release (tied to the pit_stop module's slow-stop roll). Causing a
collision, pit lane speeding, and grid penalties are natural next additions
once the incident model tracks which car caused contact with which.
"""
import random
from dataclasses import dataclass
from typing import Dict, Optional

from .driver import Driver
from .pit_stop import PitStopResult


@dataclass
class PenaltyEvent:
    driver_id: str
    violation: str
    outcome: str
    seconds: float
    description: str


class Stewards:
    def __init__(self):
        self.track_limit_warnings: Dict[str, int] = {}
        self.log: list = []

    def check_track_limits(self, driver: Driver, rng: random.Random) -> Optional[PenaltyEvent]:
        a = driver.attributes
        chance = 0.012 + max(0.0, a.aggression - 60) / 1000.0 - max(0.0, a.consistency - 50) / 2000.0
        chance = max(0.002, chance)
        if rng.random() >= chance:
            return None

        count = self.track_limit_warnings.get(driver.driver_id, 0) + 1
        self.track_limit_warnings[driver.driver_id] = count

        if count % 3 == 0:
            event = PenaltyEvent(
                driver_id=driver.driver_id, violation="TRACK_LIMITS", outcome="5_SECONDS", seconds=5.0,
                description=f"{driver.name}: third track limits infringement — 5 second penalty.",
            )
        else:
            event = PenaltyEvent(
                driver_id=driver.driver_id, violation="TRACK_LIMITS", outcome="WARNING", seconds=0.0,
                description=f"{driver.name} warned for exceeding track limits ({count}/3 this race).",
            )
        self.log.append(event)
        return event

    def check_unsafe_release(self, driver: Driver, pit_result: PitStopResult,
                              rng: random.Random) -> Optional[PenaltyEvent]:
        if not pit_result.slow_stop or rng.random() >= 0.15:
            return None
        event = PenaltyEvent(
            driver_id=driver.driver_id, violation="UNSAFE_RELEASE", outcome="10_SECONDS", seconds=10.0,
            description=f"{driver.name}'s team under investigation for unsafe release — 10 second penalty.",
        )
        self.log.append(event)
        return event
