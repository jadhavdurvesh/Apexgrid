"""Live per-car state during a race: fuel, energy, damage, current tyre set."""
from dataclasses import dataclass, field
from .tyres import TyreSet, Compound


@dataclass
class ComponentHealth:
    engine: float = 100.0
    gearbox: float = 100.0
    battery: float = 100.0
    brakes: float = 100.0
    suspension: float = 100.0
    aero: float = 100.0
    cooling: float = 100.0

    def worst(self) -> float:
        return min(self.engine, self.gearbox, self.battery, self.brakes,
                    self.suspension, self.aero, self.cooling)

    def degrade(self, reliability: float, rng, aggression_factor: float = 1.0):
        """One lap of wear-and-tear. Lower `reliability` (0-100) degrades faster,
        with an occasional larger spike on a random component — this is what makes
        `worst()` eventually drop low enough for incidents.check_incident's
        mechanical-failure roll to actually mean something."""
        base_wear = (100 - reliability) / 100.0 * 0.35 * aggression_factor
        for field_name in ("engine", "gearbox", "battery", "brakes", "suspension", "aero", "cooling"):
            current = getattr(self, field_name)
            wear = base_wear * rng.uniform(0.4, 1.3)
            if rng.random() < (100 - reliability) / 100.0 * 0.01:
                wear += rng.uniform(3, 9)  # a rough lap / kerb strike on that component
            setattr(self, field_name, max(0.0, current - wear))


@dataclass
class CarState:
    driver_id: str
    team_id: str
    tyres: TyreSet
    fuel_level: float = 100.0  # percent of race fuel load
    fuel_consumption_per_lap: float = 1.4  # percent per lap, tuned to total_laps
    energy_battery: float = 100.0  # percent
    health: ComponentHealth = field(default_factory=ComponentHealth)
    position: int = 0
    gap_to_leader: float = 0.0
    last_lap_time: float = 0.0
    total_time: float = 0.0
    pit_stops: int = 0
    dnf: bool = False
    dnf_reason: str = ""
    laps_completed: int = 0

    def burn_fuel(self):
        self.fuel_level = max(0.0, self.fuel_level - self.fuel_consumption_per_lap)

    def fuel_weight_penalty_seconds(self) -> float:
        """Heavier car early in the race = slower. ~0.03s per % fuel above empty."""
        return self.fuel_level * 0.03

    def energy_step(self, deploy: bool):
        if deploy:
            self.energy_battery = max(0.0, self.energy_battery - 12.0)
            return -0.25  # seconds gained from deployment
        else:
            self.energy_battery = min(100.0, self.energy_battery + 8.0)
            return 0.0

    def change_tyres(self, compound: Compound):
        self.tyres = TyreSet(compound=compound)
        self.pit_stops += 1

    def degrade(self, reliability: float, rng, aggression_factor: float = 1.0):
        self.health.degrade(reliability, rng, aggression_factor=aggression_factor)
