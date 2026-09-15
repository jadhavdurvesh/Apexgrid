"""Persist race/season results so history actually accumulates across runs.

v0.1: flat JSON file. Swap for a real database (Part IX of the Bible) once
the kernel is doing something worth persisting properly.
"""
import json
import os
from datetime import datetime, timezone

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "history.json")


def _load(path: str = DEFAULT_PATH) -> dict:
    if not os.path.exists(path):
        return {"races": [], "records": {"fastest_lap": None}}
    with open(path, "r") as f:
        return json.load(f)


def save_race_result(race_summary: dict, path: str = DEFAULT_PATH):
    data = _load(path)
    race_summary["logged_at"] = datetime.now(timezone.utc).isoformat()
    data["races"].append(race_summary)

    fastest = data["records"].get("fastest_lap")
    if race_summary.get("fastest_lap") and (
        fastest is None or race_summary["fastest_lap"]["time"] < fastest["time"]
    ):
        data["records"]["fastest_lap"] = race_summary["fastest_lap"]

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_history(path: str = DEFAULT_PATH) -> dict:
    return _load(path)
