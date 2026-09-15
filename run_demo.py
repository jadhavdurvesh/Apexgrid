#!/usr/bin/env python3
"""Run one APEXGRID race from the console and print the result.

Usage:
    python run_demo.py [seed] [laps]
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.simulation.grid_generator import generate_grid
from app.simulation.engine import RaceEngine
from app.simulation import history


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42
    laps = int(sys.argv[2]) if len(sys.argv) > 2 else 55

    teams, drivers = generate_grid(seed=seed)
    engine = RaceEngine(teams, drivers, total_laps=laps, seed=seed)

    print(f"\n=== APEXGRID — {engine.track_name} ({laps} laps) — seed {seed} ===\n")
    result = engine.run()

    key_events = [e for e in result.events if e.kind in
                  ("OVERTAKE", "CRASH", "SAFETY_CAR", "PIT", "SPIN", "MECH_FAILURE", "WEATHER")]
    print("--- Key moments ---")
    for e in key_events[:40]:
        print(f"Lap {e.lap:>2} | {e.kind:<12} | {e.text}")
    if len(key_events) > 40:
        print(f"... and {len(key_events) - 40} more events")

    print("\n--- Classification ---")
    for row in result.classification:
        time_str = f"{row['total_time']:.3f}s" if row["total_time"] is not None else row["status"]
        print(f"P{row['position']:<2} {row['driver_name']:<20} {row['team']:<20} "
              f"{time_str:<14} pit:{row['pit_stops']} pts:{row['points']}")

    if result.fastest_lap:
        fl = result.fastest_lap
        print(f"\nFastest lap: {fl['driver_name']} — {fl['time']}s (lap {fl['lap']})")

    history.save_race_result({
        "track": engine.track_name,
        "seed": seed,
        "laps": laps,
        "classification": result.classification,
        "fastest_lap": result.fastest_lap,
    })
    print(f"\nResult logged to backend/data/history.json")


if __name__ == "__main__":
    main()
