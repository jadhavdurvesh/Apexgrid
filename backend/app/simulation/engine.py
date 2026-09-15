"""RaceEngine — the simulation kernel.

Runs a single race weekend's race session lap-by-lap, wiring together every
subsystem described in the Bible (docs/APEXGRID_BIBLE.md): driver/team AI,
tyres, fuel, energy, weather, incidents, pit stops, race control, and radio.

This is v0.1 of the kernel: everything runs in memory for one race. Season
orchestration, qualifying, practice sessions, and persistence beyond a flat
JSON log are the next layers (see Bible Part X — Build Order).
"""
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .driver import Driver
from .team import Team
from .car import CarState
from .tyres import TyreSet, Compound
from .weather import Weather
from .race_control import RaceControlState
from .incidents import check_incident
from .pit_stop import execute_pit_stop
from .stewards import Stewards
from . import strategy_ai
from . import driver_ai
from . import radio

POINTS_TABLE = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]


@dataclass
class LapEvent:
    lap: int
    kind: str
    text: str


@dataclass
class RaceResult:
    classification: List[dict]
    fastest_lap: Optional[dict]
    events: List[LapEvent]
    points_awarded: Dict[str, int]
    penalties: List = field(default_factory=list)


class RaceEngine:
    def __init__(self, teams: Dict[str, Team], drivers: Dict[str, Driver],
                 total_laps: int = 55, track_name: str = "Meridian Circuit",
                 seed: int = None, base_lap_time: float = 92.0,
                 grid_order: Optional[List[str]] = None, weather: Optional[Weather] = None,
                 on_lap=None):
        self.teams = teams
        self.drivers = drivers
        self.total_laps = total_laps
        self.track_name = track_name
        self.base_lap_time = base_lap_time
        self.rng = random.Random(seed)
        # If qualifying already produced a weather reading, carry the same
        # conditions into the race instead of re-rolling a fresh, unrelated sky.
        self.weather = weather if weather is not None else Weather.generate(self.rng, rain_chance=0.2)
        self.race_control = RaceControlState()
        self.stewards = Stewards()
        self.events: List[LapEvent] = []
        self.fastest_lap = None  # {"driver_id", "driver_name", "lap", "time"}
        self.on_lap = on_lap

        self.cars: Dict[str, CarState] = {}
        fuel_per_lap = 92.0 / total_laps  # roughly burns full tank across race distance
        for did, driver in drivers.items():
            starting_compound = Compound.MEDIUM
            self.cars[did] = CarState(
                driver_id=did, team_id=driver.team_id,
                tyres=TyreSet(compound=starting_compound),
                fuel_consumption_per_lap=fuel_per_lap,
            )

        if grid_order is not None:
            self._apply_grid_order(grid_order)
        else:
            self._set_grid_order()  # fallback: synthetic pace estimate, no real qualifying run

    # ---- setup -----------------------------------------------------
    def _apply_grid_order(self, grid_order: List[str]):
        for grid_pos, did in enumerate(grid_order, start=1):
            self.cars[did].position = grid_pos

    def _set_grid_order(self):
        """Fallback only: rough starting order from a one-shot pace score, no
        qualifying session actually run. Prefer passing grid_order= from
        qualifying.run_qualifying()."""
        scores = []
        for did, driver in self.drivers.items():
            team = self.teams[driver.team_id]
            score = driver.base_pace_score() * 0.5 + team.car.performance_score() * 0.5
            score += self.rng.uniform(-3, 3)
            scores.append((score, did))
        scores.sort(reverse=True)
        for grid_pos, (_, did) in enumerate(scores, start=1):
            self.cars[did].position = grid_pos

    def _log(self, lap: int, kind: str, text: str):
        self.events.append(LapEvent(lap=lap, kind=kind, text=text))

    # ---- core lap loop ----------------------------------------------
    def _lap_time_for(self, driver: Driver, team: Team, car: CarState) -> float:
        pace_score = driver.base_pace_score()
        car_score = team.car.performance_score()
        # Convert 0-100 scores into seconds relative to base_lap_time: higher = faster.
        skill_time = self.base_lap_time - (pace_score - 65) * 0.045
        car_time = -(car_score - 65) * 0.05

        tyre_time = car.tyres.grip_penalty_seconds() + car.tyres.cold_penalty_seconds()
        tyre_time += car.tyres.compound_advantage_seconds()
        fuel_time = car.fuel_weight_penalty_seconds()

        wet_penalty = 0.0
        wetness = self.weather.track_wetness
        if wetness > 5:
            is_wet_tyre = car.tyres.compound in (Compound.INTERMEDIATE, Compound.WET)
            mismatch = 0.0 if is_wet_tyre else (wetness / 100.0) * 6.0
            skill_offset = (100 - driver.attributes.wet_performance) / 100.0 * (wetness / 100.0) * 2.0
            wet_penalty = mismatch + skill_offset

        noise = self.rng.gauss(0, 0.25 + (100 - driver.attributes.consistency) / 300.0)

        lap_time = skill_time + car_time + tyre_time + fuel_time + wet_penalty + noise
        lap_time *= self.race_control.pace_multiplier()
        return max(60.0, lap_time)

    def run(self) -> RaceResult:
        order = sorted(self.cars.values(), key=lambda c: c.position)
        cumulative: Dict[str, float] = {c.driver_id: 0.0 for c in order}

        for lap in range(1, self.total_laps + 1):
            self.weather.step(self.rng)
            self.race_control.step()

            if lap == 1:
                self._log(lap, "WEATHER", f"Conditions: {self.weather.state_label()}")

            active_ids = [did for did, c in self.cars.items() if not c.dnf]
            ranking = sorted(active_ids, key=lambda d: cumulative[d])
            gaps = {}
            for i, did in enumerate(ranking):
                ahead = cumulative[ranking[i - 1]] if i > 0 else None
                behind = cumulative[ranking[i + 1]] if i < len(ranking) - 1 else None
                gaps[did] = (
                    (cumulative[did] - ahead) if ahead is not None else None,
                    (behind - cumulative[did]) if behind is not None else None,
                )

            lap_times = {}
            decisions = {}
            for did in active_ids:
                driver = self.drivers[did]
                team = self.teams[driver.team_id]
                car = self.cars[did]

                gap_ahead, gap_behind = gaps[did]
                decision = driver_ai.decide(driver, car, gap_ahead, gap_behind,
                                             self.total_laps - lap, self.rng)
                decisions[did] = decision
                strat = strategy_ai.decide(car, self.weather, lap, self.total_laps,
                                            self.rng, team_aggression=0.5)

                lt = self._lap_time_for(driver, team, car)
                if decision.mode == "PUSH":
                    lt -= 0.15
                elif decision.mode == "SAVE":
                    lt += 0.2
                energy_delta = car.energy_step(decision.deploy_energy)
                lt += energy_delta

                if strat.action == "BOX":
                    pit = execute_pit_stop(team.pit_crew_skill, self.rng)
                    lt += pit.total_pit_lane_seconds
                    car.change_tyres(strat.target_compound)
                    self._log(lap, "PIT", f"{driver.name} pits: {pit.description} -> {strat.target_compound.value}")
                    self._log(lap, "RADIO", "; ".join(f"{s}: {t}" for s, t in radio.pit_call(driver.name)))

                    penalty = self.stewards.check_unsafe_release(driver, pit, self.rng)
                    if penalty:
                        lt += penalty.seconds
                        self._log(lap, "PENALTY", penalty.description)
                else:
                    car.tyres.step_lap(driver.attributes.aggression, driver.attributes.tyre_management,
                                        self.weather.track_temp)

                track_limits_penalty = self.stewards.check_track_limits(driver, self.rng)
                if track_limits_penalty:
                    lt += track_limits_penalty.seconds
                    self._log(lap, "STEWARDS", track_limits_penalty.description)

                car.burn_fuel()
                aggression_factor = 1.0 + max(0.0, (driver.attributes.aggression - 60)) / 100.0
                car.degrade(team.car.reliability, self.rng, aggression_factor=aggression_factor)
                car.laps_completed = lap

                incident = check_incident(driver, car, self.weather, self.rng,
                                           under_pressure=(gap_behind is not None and gap_behind < 1.0))
                if incident:
                    lt += incident.time_penalty_seconds
                    self._log(lap, incident.kind, incident.description)
                    if incident.dnf:
                        car.dnf = True
                        car.dnf_reason = incident.kind
                    if incident.triggers_safety_car:
                        self.race_control.trigger_safety_car()
                        self._log(lap, "SAFETY_CAR", "; ".join(t for _, t in radio.safety_car_call()))

                lap_times[did] = lt

            # Apply lap times and check for overtakes on tight gaps.
            for did in active_ids:
                cumulative[did] += lap_times[did]

            ranking_after = sorted(active_ids, key=lambda d: cumulative[d])
            for i in range(1, len(ranking_after)):
                ahead_id, behind_id = ranking_after[i - 1], ranking_after[i]
                gap = cumulative[behind_id] - cumulative[ahead_id]
                attacker_decision = decisions.get(behind_id)
                if 0 < gap < 1.0 and attacker_decision is not None and attacker_decision.attack_gap:
                    attacker, defender = self.drivers[behind_id], self.drivers[ahead_id]
                    attacker_car, defender_car = self.cars[behind_id], self.cars[ahead_id]
                    pace_delta = lap_times[ahead_id] - lap_times[behind_id]
                    prob = driver_ai.overtake_probability(attacker, attacker_car, defender, defender_car,
                                                           pace_delta, self.rng)
                    if self.rng.random() < prob:
                        cumulative[behind_id] = cumulative[ahead_id] - 0.1
                        self._log(lap, "OVERTAKE", f"{attacker.name} passes {defender.name}!")

            for did in active_ids:
                driver = self.drivers[did]
                if self.fastest_lap is None or lap_times[did] < self.fastest_lap["time"]:
                    self.fastest_lap = {"driver_id": did, "driver_name": driver.name,
                                         "lap": lap, "time": round(lap_times[did], 3)}
                self.cars[did].last_lap_time = lap_times[did]
                self.cars[did].total_time = cumulative[did]

            if self.on_lap is not None:
                self.on_lap(self, lap, cumulative, lap_times)

        return self._finalize(cumulative)

    # ---- finish -------------------------------------------------------
    def _finalize(self, cumulative: Dict[str, float]) -> RaceResult:
        finishers = sorted(
            [did for did, c in self.cars.items() if not c.dnf],
            key=lambda d: cumulative[d],
        )
        dnfs = sorted(
            [did for did, c in self.cars.items() if c.dnf],
            key=lambda d: -self.cars[d].laps_completed,
        )
        final_order = finishers + dnfs

        classification = []
        points_awarded = {}
        for pos, did in enumerate(final_order, start=1):
            driver = self.drivers[did]
            car = self.cars[did]
            points = POINTS_TABLE[pos - 1] if pos <= len(POINTS_TABLE) and not car.dnf else 0
            points_awarded[did] = points

            driver.career["races"] += 1
            driver.career["points"] += points
            if pos == 1 and not car.dnf:
                driver.career["wins"] += 1
            if pos <= 3 and not car.dnf:
                driver.career["podiums"] += 1
            if car.dnf:
                driver.career["dnfs"] += 1
            self.teams[driver.team_id].constructors_points += points

            classification.append({
                "position": pos,
                "driver_id": did,
                "driver_name": driver.name,
                "team": self.teams[driver.team_id].name,
                "total_time": None if car.dnf else round(cumulative[did], 3),
                "status": car.dnf_reason if car.dnf else "FINISHED",
                "pit_stops": car.pit_stops,
                "points": points,
            })

        return RaceResult(
            classification=classification,
            fastest_lap=self.fastest_lap,
            events=self.events,
            points_awarded=points_awarded,
            penalties=self.stewards.log,
        )
