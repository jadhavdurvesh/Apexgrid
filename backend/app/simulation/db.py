"""SQLite persistence — the real database the Bible's Part IX calls for,
replacing the flat JSON file once we're running whole seasons instead of
one-off races. history.py's JSON log still works fine for the single-race
demo; this is what season.py uses.
"""
import sqlite3
import os
import json
from contextlib import contextmanager

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "apexgrid.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS seasons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS races (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season_id INTEGER NOT NULL REFERENCES seasons(id),
    round_number INTEGER NOT NULL,
    track_name TEXT NOT NULL,
    laps INTEGER NOT NULL,
    fastest_lap_driver TEXT,
    fastest_lap_time REAL,
    report TEXT
);

CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id INTEGER NOT NULL REFERENCES races(id),
    driver_id TEXT NOT NULL,
    driver_name TEXT NOT NULL,
    team_name TEXT NOT NULL,
    position INTEGER NOT NULL,
    points INTEGER NOT NULL,
    status TEXT NOT NULL,
    total_time REAL
);

CREATE TABLE IF NOT EXISTS driver_records (
    driver_id TEXT PRIMARY KEY,
    driver_name TEXT NOT NULL,
    wins INTEGER DEFAULT 0,
    podiums INTEGER DEFAULT 0,
    dnfs INTEGER DEFAULT 0,
    races INTEGER DEFAULT 0,
    career_points INTEGER DEFAULT 0
);
"""


@contextmanager
def get_conn(path: str = DEFAULT_DB_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(path: str = DEFAULT_DB_PATH):
    with get_conn(path) as conn:
        conn.executescript(SCHEMA)


def get_or_create_season(conn, name: str) -> int:
    from datetime import datetime, timezone
    row = conn.execute("SELECT id FROM seasons WHERE name = ?", (name,)).fetchone()
    if row:
        return row[0]
    cur = conn.execute("INSERT INTO seasons (name, created_at) VALUES (?, ?)",
                        (name, datetime.now(timezone.utc).isoformat()))
    return cur.lastrowid


def save_race(season_name: str, round_number: int, track_name: str, laps: int,
              classification: list, fastest_lap: dict, report: str = "",
              path: str = DEFAULT_DB_PATH):
    with get_conn(path) as conn:
        season_id = get_or_create_season(conn, season_name)
        cur = conn.execute(
            "INSERT INTO races (season_id, round_number, track_name, laps, "
            "fastest_lap_driver, fastest_lap_time, report) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (season_id, round_number, track_name, laps,
             fastest_lap["driver_name"] if fastest_lap else None,
             fastest_lap["time"] if fastest_lap else None, report),
        )
        race_id = cur.lastrowid
        for row in classification:
            conn.execute(
                "INSERT INTO results (race_id, driver_id, driver_name, team_name, "
                "position, points, status, total_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (race_id, row["driver_id"], row["driver_name"], row["team"],
                 row["position"], row["points"], row["status"], row["total_time"]),
            )
            conn.execute(
                "INSERT INTO driver_records (driver_id, driver_name, wins, podiums, dnfs, races, career_points) "
                "VALUES (?, ?, ?, ?, ?, 1, ?) "
                "ON CONFLICT(driver_id) DO UPDATE SET "
                "wins = wins + excluded.wins, podiums = podiums + excluded.podiums, "
                "dnfs = dnfs + excluded.dnfs, races = races + 1, "
                "career_points = career_points + excluded.career_points",
                (row["driver_id"], row["driver_name"],
                 1 if row["position"] == 1 and row["status"] == "FINISHED" else 0,
                 1 if row["position"] <= 3 and row["status"] == "FINISHED" else 0,
                 1 if row["status"] != "FINISHED" else 0,
                 row["points"]),
            )


def season_standings(season_name: str, path: str = DEFAULT_DB_PATH) -> list:
    with get_conn(path) as conn:
        rows = conn.execute(
            "SELECT r.driver_name, r.team_name, SUM(r.points) as total_points "
            "FROM results r JOIN races ra ON r.race_id = ra.id "
            "JOIN seasons s ON ra.season_id = s.id "
            "WHERE s.name = ? GROUP BY r.driver_id ORDER BY total_points DESC",
            (season_name,),
        ).fetchall()
    return [{"driver_name": r[0], "team_name": r[1], "points": r[2]} for r in rows]


def all_time_records(path: str = DEFAULT_DB_PATH) -> dict:
    with get_conn(path) as conn:
        most_wins = conn.execute(
            "SELECT driver_name, wins FROM driver_records ORDER BY wins DESC LIMIT 1"
        ).fetchone()
        fastest = conn.execute(
            "SELECT fastest_lap_driver, fastest_lap_time, track_name FROM races "
            "WHERE fastest_lap_time IS NOT NULL ORDER BY fastest_lap_time ASC LIMIT 1"
        ).fetchone()
    return {
        "most_wins": {"driver": most_wins[0], "wins": most_wins[1]} if most_wins else None,
        "fastest_lap_ever": (
            {"driver": fastest[0], "time": fastest[1], "track": fastest[2]} if fastest else None
        ),
    }
