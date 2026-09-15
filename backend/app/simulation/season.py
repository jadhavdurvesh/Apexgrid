"""Season — orchestrates a full calendar of race weekends, the next layer up
from the single-race kernel (Bible Part X, build-order step after
persistence/API).

One Season run: for each round -> qualifying -> race -> prize money -> a
little R&D -> persist to the database -> generate a report. At the end of
the season, the driver market runs (retirements, rookies, transfers) so the
next Season object starts with a grid that has actually evolved.
"""
import random
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .team import Team
from .driver import Driver
from .weather import Weather
from .qualifying import run_qualifying
from .engine import RaceEngine
from . import db
from . import newsroom
from . import rd
from . import driver_market


@dataclass
class RoundResult:
    round_number: int
    track_name: str
    report: str
    classification: list


@dataclass
class SeasonSummary:
    season_name: str
    rounds: List[RoundResult] = field(default_factory=list)
    market_events: list = field(default_factory=list)


class Season:
    def __init__(self, season_name: str, calendar: List[Tuple[str, int]],
                 teams: Dict[str, Team], drivers: Dict[str, Driver],
                 seed: int = None, db_path: str = None):
        self.season_name = season_name
        self.calendar = calendar
        self.teams = teams
        self.drivers = drivers
        self.rng = random.Random(seed)
        self.db_path = db_path or db.DEFAULT_DB_PATH
        db.init_db(self.db_path)

    def run(self, verbose: bool = True) -> SeasonSummary:
        summary = SeasonSummary(season_name=self.season_name)

        for round_number, (track_name, laps) in enumerate(self.calendar, start=1):
            weather = Weather.generate(self.rng, rain_chance=0.2)
            quali = run_qualifying(self.teams, self.drivers, weather, self.rng)

            engine = RaceEngine(
                self.teams, self.drivers, total_laps=laps, track_name=track_name,
                seed=self.rng.randint(0, 10**9), grid_order=quali.grid_order, weather=weather,
            )
            result = engine.run()

            standings = db.season_standings(self.season_name, self.db_path)
            leader = standings[0]["driver_name"] if standings else None

            report = newsroom.generate_report(
                track_name, result.classification, result.events, result.fastest_lap,
                result.penalties, season_name=self.season_name, standings_leader=leader,
            )

            db.save_race(self.season_name, round_number, track_name, laps,
                          result.classification, result.fastest_lap, report=report, path=self.db_path)

            rd.award_prize_money(self.teams, result.classification)
            rd.run_rd_cycle(self.teams, self.rng, spend_fraction=0.10)

            round_result = RoundResult(round_number=round_number, track_name=track_name,
                                        report=report, classification=result.classification)
            summary.rounds.append(round_result)

            if verbose:
                print(f"\n--- Round {round_number}: {track_name} ({laps} laps) ---")
                print(report)
                print(f"Winner: {result.classification[0]['driver_name']} "
                      f"({result.classification[0]['team']})")

        summary.market_events = driver_market.run_offseason_market(
            list(self.teams.keys()), self.drivers, self.rng,
        )
        if verbose and summary.market_events:
            print(f"\n--- {self.season_name} off-season ---")
            for e in summary.market_events:
                print(f"[{e.kind}] {e.description}")

        return summary

    def final_standings(self) -> list:
        return db.season_standings(self.season_name, self.db_path)
