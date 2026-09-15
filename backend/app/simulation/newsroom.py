"""AI Newsroom — turns a race's raw event log into a short readable report.

v0.1 is rule-based templating over real simulation data (who won, by how
much, what actually happened). Swapping in an LLM call over this same
structured data later is a drop-in upgrade, not a rewrite.
"""
from typing import Optional


def generate_report(track_name: str, classification: list, events: list,
                     fastest_lap: Optional[dict], penalties: list,
                     season_name: str = None, standings_leader: str = None) -> str:
    winner = classification[0]
    runner_up = classification[1] if len(classification) > 1 else None
    lines = []

    if runner_up and winner["total_time"] and runner_up["total_time"]:
        margin = runner_up["total_time"] - winner["total_time"]
        lines.append(
            f"{winner['driver_name']} ({winner['team']}) wins at {track_name}, "
            f"beating {runner_up['driver_name']} by {margin:.3f} seconds."
        )
    else:
        lines.append(f"{winner['driver_name']} ({winner['team']}) wins at {track_name}.")

    crashes = [e for e in events if e.kind == "CRASH"]
    safety_cars = [e for e in events if e.kind == "SAFETY_CAR"]
    overtakes = [e for e in events if e.kind == "OVERTAKE"]
    if safety_cars:
        lines.append(
            f"The race was interrupted by the safety car after "
            f"{crashes[0].text.rstrip('!').lower() if crashes else 'an incident'} on lap {safety_cars[0].lap}."
        )
    if len(overtakes) > 15:
        lines.append(f"A frantic race saw {len(overtakes)} overtakes across the field.")
    elif len(overtakes) > 0:
        lines.append(f"{len(overtakes)} overtakes were recorded on track.")

    dnfs = [row for row in classification if row["status"] != "FINISHED"]
    if dnfs:
        names = ", ".join(row["driver_name"] for row in dnfs[:3])
        extra = f" and {len(dnfs) - 3} more" if len(dnfs) > 3 else ""
        lines.append(f"Retirements: {names}{extra}.")

    if penalties:
        time_penalties = [p for p in penalties if p.seconds > 0]
        if time_penalties:
            lines.append(f"{len(time_penalties)} time penalties were handed out by the stewards.")

    if fastest_lap:
        lines.append(f"Fastest lap went to {fastest_lap['driver_name']}, {fastest_lap['time']}s on lap {fastest_lap['lap']}.")

    if standings_leader and season_name:
        lines.append(f"{standings_leader} leads the {season_name} championship after this round.")

    return " ".join(lines)
