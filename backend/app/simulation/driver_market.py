"""Driver market — runs between seasons: retirements, rookie generation,
and a simplified transfer window.

v0.1 simplification: no real contracts or negotiation flow yet (Part VI of
the Bible describes the full pipeline). `experience` doubles as an age
proxy since we don't model literal driver age.
"""
import random
from dataclasses import dataclass
from typing import Dict, List
from .driver import Driver, DriverAttributes


@dataclass
class MarketEvent:
    kind: str  # "RETIREMENT" or "TRANSFER"
    description: str


def age_and_develop(drivers: Dict[str, Driver], rng: random.Random):
    """End-of-season attribute drift: young drivers improve toward potential,
    veterans slowly decline, everyone gains experience."""
    for driver in drivers.values():
        a = driver.attributes
        a.experience = min(100.0, a.experience + rng.uniform(4, 9))
        if a.experience < 60:  # still developing
            growth = rng.uniform(0.5, 2.5) * (a.potential - a.pace) / 100.0
            a.pace = min(a.potential, a.pace + max(0, growth))
            a.consistency = min(95.0, a.consistency + rng.uniform(0, 1.5))
            a.racecraft = min(95.0, a.racecraft + rng.uniform(0, 1.5))
        else:  # veteran decline
            decline = rng.uniform(0, 1.2)
            a.pace = max(40.0, a.pace - decline)
            a.reaction = max(35.0, a.reaction - rng.uniform(0, 0.8))


def run_offseason_market(teams_ids: List[str], drivers: Dict[str, Driver],
                          rng: random.Random, retirement_chance_base: float = 0.05) -> List[MarketEvent]:
    events: List[MarketEvent] = []
    age_and_develop(drivers, rng)

    to_retire = []
    for did, driver in drivers.items():
        a = driver.attributes
        chance = retirement_chance_base
        if a.experience > 75:
            chance += (a.experience - 75) / 100.0
        if a.morale < 40:
            chance += 0.05
        if rng.random() < chance:
            to_retire.append(did)

    for did in to_retire:
        driver = drivers[did]
        events.append(MarketEvent(
            kind="RETIREMENT",
            description=f"{driver.name} retires after {int(driver.career['races'])} races, "
                        f"{driver.career['wins']} wins.",
        ))
        rookie_attrs = DriverAttributes.random_rookie(rng)
        drivers[did] = Driver(
            driver_id=did, name=_generate_rookie_name(rng), number=driver.number,
            team_id=driver.team_id, attributes=rookie_attrs,
        )
        events.append(MarketEvent(
            kind="ROOKIE_DEBUT",
            description=f"{drivers[did].name} joins as a rookie, taking over car #{driver.number}.",
        ))

    # Simplified transfer window: a handful of unhappy or high-morale drivers
    # swap teams at random rather than through full contract negotiation.
    candidates = [d for d in drivers.values() if not d.retired and rng.random() < 0.06]
    rng.shuffle(candidates)
    for i in range(0, len(candidates) - 1, 2):
        d1, d2 = candidates[i], candidates[i + 1]
        if d1.team_id == d2.team_id:
            continue
        d1.team_id, d2.team_id = d2.team_id, d1.team_id
        events.append(MarketEvent(
            kind="TRANSFER",
            description=f"{d1.name} and {d2.name} swap teams in the driver market.",
        ))

    return events


_ROOKIE_FIRST = ["Aidan", "Timo", "Kaio", "Emre", "Noel", "Ilya", "Rian", "Andres", "Jamal", "Otto"]
_ROOKIE_LAST = ["Falk", "Osei", "Brandt", "Ueda", "Villar", "Kowalski", "Dube", "Marsh", "Tanaka", "Reyes"]


def _generate_rookie_name(rng: random.Random) -> str:
    return f"{rng.choice(_ROOKIE_FIRST)} {rng.choice(_ROOKIE_LAST)}"
