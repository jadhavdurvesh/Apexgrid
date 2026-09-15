import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.simulation.grid_generator import generate_grid
from app.simulation.engine import RaceEngine


def test_full_race_produces_full_classification():
    teams, drivers = generate_grid(seed=1)
    engine = RaceEngine(teams, drivers, total_laps=10, seed=1)
    result = engine.run()

    assert len(result.classification) == len(drivers)
    positions = [row["position"] for row in result.classification]
    assert positions == list(range(1, len(drivers) + 1))

    # Points should only be awarded to non-DNF top 10.
    total_points = sum(row["points"] for row in result.classification)
    assert total_points <= 25 + 18 + 15 + 12 + 10 + 8 + 6 + 4 + 2 + 1


def test_fastest_lap_is_recorded():
    teams, drivers = generate_grid(seed=2)
    engine = RaceEngine(teams, drivers, total_laps=8, seed=2)
    result = engine.run()
    assert result.fastest_lap is not None
    assert result.fastest_lap["time"] > 0


def test_deterministic_with_same_seed():
    teams1, drivers1 = generate_grid(seed=99)
    result1 = RaceEngine(teams1, drivers1, total_laps=6, seed=99).run()

    teams2, drivers2 = generate_grid(seed=99)
    result2 = RaceEngine(teams2, drivers2, total_laps=6, seed=99).run()

    order1 = [row["driver_name"] for row in result1.classification]
    order2 = [row["driver_name"] for row in result2.classification]
    assert order1 == order2
