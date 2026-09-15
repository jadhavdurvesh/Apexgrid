"""Generate short radio exchanges from concrete simulation events."""


def pit_call(driver_name: str) -> list:
    return [
        (driver_name, "Box, box, box, copy?"),
        ("ENGINEER", "Copy, box this lap."),
    ]


def tyre_warning(driver_name: str, wear: float) -> list:
    return [
        (driver_name, "These tyres are gone."),
        ("ENGINEER", f"Copy, wear is at {wear:.0f} percent. Working on it."),
    ]


def weather_update(rain_intensity: float, laps_out: int = 3) -> list:
    if rain_intensity > 40:
        return [("ENGINEER", f"Heavy rain expected in {laps_out} laps, stand by.")]
    if rain_intensity > 10:
        return [("ENGINEER", f"Light rain forecast in {laps_out} laps.")]
    return [("ENGINEER", "Track drying out, stay out for now.")]


def safety_car_call() -> list:
    return [("RACE CONTROL", "Safety car, safety car, safety car.")]
