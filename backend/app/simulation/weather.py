"""Weather — a continuous environment, not a boolean flag."""
from dataclasses import dataclass
import random


@dataclass
class Weather:
    air_temp: float
    track_temp: float
    humidity: float
    wind_kph: float
    cloud_cover: float  # 0-100
    rain_intensity: float  # 0-100
    track_wetness: float  # 0-100, lags behind rain_intensity

    @classmethod
    def generate(cls, rng: random.Random, rain_chance: float = 0.15) -> "Weather":
        raining = rng.random() < rain_chance
        rain = round(rng.uniform(20, 90), 1) if raining else 0.0
        return cls(
            air_temp=round(rng.uniform(14, 34), 1),
            track_temp=round(rng.uniform(20, 50), 1),
            humidity=round(rng.uniform(30, 90), 1),
            wind_kph=round(rng.uniform(2, 35), 1),
            cloud_cover=round(rng.uniform(0, 100), 1),
            rain_intensity=rain,
            track_wetness=rain * 0.6,
        )

    def step(self, rng: random.Random):
        """Evolve weather by one lap/tick. Simple random walk with inertia."""
        self.cloud_cover = min(100, max(0, self.cloud_cover + rng.uniform(-4, 4)))
        if self.cloud_cover > 70 and rng.random() < 0.08:
            self.rain_intensity = min(100, self.rain_intensity + rng.uniform(5, 25))
        else:
            self.rain_intensity = max(0, self.rain_intensity - rng.uniform(0, 6))
        # track wetness lags rain intensity
        self.track_wetness += (self.rain_intensity - self.track_wetness) * 0.15
        self.track_wetness = min(100, max(0, self.track_wetness))
        self.track_temp = max(10, self.track_temp - self.rain_intensity * 0.02 + rng.uniform(-0.3, 0.3))

    def state_label(self) -> str:
        if self.track_wetness > 60:
            return "WET_TRACK"
        if self.rain_intensity > 50:
            return "HEAVY_RAIN"
        if self.rain_intensity > 15:
            return "LIGHT_RAIN"
        if self.track_wetness > 15:
            return "DRYING_TRACK"
        if self.cloud_cover > 60:
            return "CLOUDY"
        return "CLEAR"

    def recommended_compound_is_wet(self) -> bool:
        return self.track_wetness > 25
