# APEXGRID

*A Persistent AI Motorsport Simulation Universe*

The full vision is in [`docs/APEXGRID_BIBLE.md`](docs/APEXGRID_BIBLE.md).
This repo currently implements **v0.1 of the simulation kernel**: a
single-race engine with real driver/team AI, tyres, fuel, energy, weather,
incidents, pit stops, and race control. No database, no frontend, no season
loop yet — those are next.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt

# Run one race straight from the console (synthetic grid, no qualifying):
python3 run_demo.py            # seed 42, 55 laps
python3 run_demo.py 7 30       # seed 7, 30 laps

# Run a FULL SEASON — qualifying, races, prize money, R&D, driver market,
# persisted to a real SQLite database:
python3 season_demo.py          # seed 7, all 8 calendar rounds
python3 season_demo.py 3 4      # seed 3, first 4 rounds only

# Run the test suite:
cd backend && python3 -m pytest tests/ -v

# Run the API stub:
cd backend && uvicorn app.main:app --reload
# then: POST http://127.0.0.1:8000/race/run  {"seed": 7, "laps": 30}
```

## Project layout

```
apexgrid/
├── docs/
│   └── APEXGRID_BIBLE.md      # the full spec — every future system's home
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI stub (Part IX/X of the Bible)
│   │   └── simulation/        # the kernel — one module per system
│   │       ├── driver.py          # driver attributes & career
│   │       ├── team.py            # car performance, economy, pit crew
│   │       ├── car.py             # live per-car race state
│   │       ├── tyres.py           # compound & degradation model
│   │       ├── weather.py         # continuous weather simulation
│   │       ├── incidents.py       # lock-ups, spins, crashes, failures
│   │       ├── pit_stop.py        # pit stop execution
│   │       ├── race_control.py    # flags & safety car
│   │       ├── strategy_ai.py     # team pit-wall decisions
│   │       ├── driver_ai.py       # per-lap driver decisions & overtaking
│   │       ├── radio.py           # radio message generation
│   │       ├── grid_generator.py  # default 10-team/20-driver grid
│   │       ├── qualifying.py      # quali session -> real starting grid
│   │       ├── stewards.py        # track limits & unsafe release penalties
│   │       ├── rd.py              # prize money + between-round car development
│   │       ├── driver_market.py   # retirements, rookies, transfers
│   │       ├── newsroom.py        # rule-based race report generation
│   │       ├── season.py          # Season — orchestrates a full calendar
│   │       ├── history.py         # JSON persistence (single-race demo)
│   │       ├── db.py              # SQLite persistence (season demo)
│   │       └── engine.py          # RaceEngine — orchestrates one race
│   ├── data/                  # history.json / apexgrid.db land here
│   └── tests/test_simulation.py
├── run_demo.py                 # single-race console entry point
├── season_demo.py               # full-season console entry point
└── README.md
```

## What's real right now vs. what's a stub

**Actually simulated:** driver attributes affecting pace, team car
performance, tyre compound choice/wear/cliff, fuel weight, a continuously
evolving weather system, probabilistic incidents tied to driver traits *and*
to real component-health degradation (`CarState.degrade`, driven by
`Team.car.reliability` — no longer a placeholder), pit stops with
crew-skill variance and slow-release chance, a steward system that hands
out track-limits and unsafe-release penalties, a strategy AI that reacts to
tyre wear and weather (and occasionally makes a bad call on purpose), safety
car periods triggered by crashes, overtaking based on pace/skill/tyre
deltas *and* on whether the trailing driver's AI actually chose to attack,
a real qualifying session that sets the grid, a season loop across multiple
rounds with prize money funding between-round R&D, a driver market that
retires drivers and generates rookies at season end, a rule-based AI
newsroom report per race, and a real SQLite database for season-scale
persistence (querying most wins / fastest lap ever is in `db.py`).

**Stubs / not yet built:** practice sessions (only qualifying + race exist
per weekend), the 2D live viewer and any frontend, real-time pacing (races
resolve instantly rather than over wall-clock time), user accounts/
notifications, replays, and causing-collision penalties (stewards only
cover track limits and unsafe release so far, since that needs multi-car
contact attribution). All have a defined place in the Bible.

## Known rough edges (v0.2)

- Driver transfers in `driver_market.py` are a random swap, not real
  contract negotiation tied to team performance/budget.
- Qualifying is one simplified session, not a Q1/Q2/Q3 knockout.
- `season_demo.py`'s calendar is fixed; multi-season persistence (a new
  `Season` object per year) works, but nothing yet stitches seasons into
  one continuous "world" object.
