#!/usr/bin/env python3
"""Run a full APEXGRID season: qualifying + race for each round, prize money,
R&D between rounds, persisted to a real SQLite database, then the driver
market runs at season end.

Usage:
    python season_demo.py [seed] [num_rounds]
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.simulation.grid_generator import generate_grid
from app.simulation.season import Season

CALENDAR = [
    ("Meridian Circuit", 55), ("Solstice Street Course", 48), ("Halcyon Ring", 60),
    ("Obsidian Grand Prix Circuit", 52), ("Voltage Speedway", 44), ("Zenith Highlands", 58),
    ("Ironclad Docklands", 50), ("Kestrel Coastal Loop", 56),
]


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    num_rounds = int(sys.argv[2]) if len(sys.argv) > 2 else len(CALENDAR)

    teams, drivers = generate_grid(seed=seed)
    season = Season("Season 001", CALENDAR[:num_rounds], teams, drivers, seed=seed)
    summary = season.run(verbose=True)

    print(f"\n=== {season.season_name} — Final Championship ===")
    for i, row in enumerate(season.final_standings()[:10], start=1):
        print(f"P{i:<2} {row['driver_name']:<20} {row['team_name']:<22} {row['points']} pts")

    print(f"\nFull results persisted to backend/data/apexgrid.db")


if __name__ == "__main__":
    main()
