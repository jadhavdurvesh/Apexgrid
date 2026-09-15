"""Generate a default launch grid: 10 teams, 20 drivers."""
import random
from .team import Team, CarPerformance
from .driver import Driver, DriverAttributes

TEAM_NAMES = [
    "Apex GP", "Vantage Racing", "Ironclad Motorsport", "Solstice F1 Team",
    "Kestrel Grand Prix", "Meridian Racing", "Voltage Sport", "Obsidian GP",
    "Halcyon Motorsport", "Zenith Racing",
]

FIRST_NAMES = ["Marco", "Kenji", "Lucas", "Erik", "Diego", "Nikolai", "Rafael", "Theo",
               "Milo", "Aksel", "Ravi", "Bruno", "Felix", "Ines", "Owen", "Sami",
               "Adrian", "Kaito", "Leo", "Mateus"]
LAST_NAMES = ["Ferraro", "Nakata", "Silva", "Voss", "Reyes", "Petrov", "Cardoso", "Lindqvist",
              "Costa", "Berg", "Menon", "Alves", "Krause", "Duarte", "Whitfield", "Hassan",
              "Moreau", "Sato", "Novak", "Rocha"]


def generate_grid(seed: int = None):
    rng = random.Random(seed)
    names = list(zip(FIRST_NAMES, LAST_NAMES))
    rng.shuffle(names)

    teams = {}
    drivers = {}
    number = 1
    for i, team_name in enumerate(TEAM_NAMES):
        tier = rng.uniform(0.82, 1.08)  # spreads the grid competitively
        team_id = f"team_{i+1:02d}"
        car = CarPerformance.random(rng, tier=tier)
        teams[team_id] = Team(team_id=team_id, name=team_name, car=car,
                               pit_crew_skill=round(rng.uniform(55, 92), 1))

        for seat in range(2):
            first, last = names.pop()
            driver_id = f"drv_{number:02d}"
            is_rookie = rng.random() < 0.25
            attrs = (DriverAttributes.random_rookie(rng) if is_rookie
                     else DriverAttributes.random_veteran(rng))
            drivers[driver_id] = Driver(
                driver_id=driver_id, name=f"{first} {last}", number=number,
                team_id=team_id, attributes=attrs,
            )
            number += 1

    return teams, drivers
