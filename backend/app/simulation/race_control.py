"""Race Control: observes the race and issues flags / safety car periods."""
from dataclasses import dataclass


@dataclass
class RaceControlState:
    flag: str = "GREEN"  # GREEN, YELLOW, DOUBLE_YELLOW, VSC, SC, RED
    safety_car_laps_remaining: int = 0

    def trigger_safety_car(self, laps: int = 3):
        self.flag = "SC"
        self.safety_car_laps_remaining = laps

    def trigger_vsc(self, laps: int = 2):
        self.flag = "VSC"
        self.safety_car_laps_remaining = laps

    def step(self):
        if self.safety_car_laps_remaining > 0:
            self.safety_car_laps_remaining -= 1
            if self.safety_car_laps_remaining == 0:
                self.flag = "GREEN"

    def is_caution(self) -> bool:
        return self.flag in ("VSC", "SC", "YELLOW", "DOUBLE_YELLOW")

    def pace_multiplier(self) -> float:
        """Under SC/VSC the whole field is bunched and slowed — model as a lap-time multiplier."""
        if self.flag == "SC":
            return 1.35
        if self.flag == "VSC":
            return 1.2
        return 1.0
