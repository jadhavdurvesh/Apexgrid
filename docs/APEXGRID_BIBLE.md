# APEXGRID — Simulation Bible

*A Persistent AI Motorsport Simulation Universe*
*Working document — v0.1*

This is the contract for the project. Every system described here has a defined
place, a defined data model, and a defined relationship to the rest of the
world. Nothing here needs to be built immediately — the simulation kernel
comes first, and everything else attaches to it over time.

---

## Part I — Universe

**World model.** The world is a single continuously-running state machine, not
a session that resets. It owns the calendar, the grid, every team, every
driver, every car, and the full historical record.

**Season loop.**

```
WORLD CREATED → SEASON N → RACE WEEKENDS → CHAMPIONSHIP DECIDED
→ OFF-SEASON (driver market, car development, regulation changes)
→ SEASON N+1 → ...
```

**Calendar compression.** Real-world F1-style calendars run one season a year.
APEXGRID compresses this: a full season (all races) can run in a
configurable window (e.g. 2–4 weeks of wall-clock time), so the world visibly
advances instead of taking a year per title.

**Grid size.** Launch: 10 teams × 2 drivers = 20 drivers. Data model supports
12+ teams, reserve/rookie drivers, and mid-season driver changes without a
schema change.

---

## Part II — Physics & Car Model

**Driver attributes** (0–100 scale, drive simulation outcomes, not just
displayed): Pace, Consistency, Racecraft, Overtaking, Defending, Qualifying,
Wet Performance, Aggression, Reaction, Tyre Management, Pressure Handling,
Fitness, Potential, Experience, Morale.

**Car performance model:** Aerodynamics (downforce/drag balance), Engine
Power, Energy Recovery, Braking, Suspension, Cooling, Tyre Management,
Reliability. Teams can introduce discrete upgrades mid-season (e.g. "Floor
Upgrade: +0.14s/lap") that shift the competitive order over time.

**Tyres.** Five compounds — Soft, Medium, Hard, Intermediate, Wet — each with
Grip, Operating Temperature Window, Wear Rate, Degradation Curve, and Warm-up
Rate. Grip is a function of compound, wear, track temp, and driving style.

**Fuel.** Fuel Level, Consumption Rate, and a Save/Push decision the strategy
AI makes each lap. Fuel load affects car weight and therefore lap time.

**Energy (ERS-style).** Battery state, harvesting rate, deployment rate.
Drivers spend energy tactically: Attack, Defend, Qualifying push, or Save.

**Overtaking model.** A function of speed delta, track position, slipstream,
aero, energy deployment, driver Racecraft/Overtaking attributes, and relative
tyre state — producing a pass probability per opportunity, not a guaranteed
pass.

**Weather.** A continuous environment, not a boolean: Air Temp, Track Temp,
Wind, Humidity, Cloud Cover, Rain Intensity, Track Wetness. States include
Clear, Cloudy, Light Rain, Heavy Rain, Storm, Drying Track, Wet Track. Feeds
directly into tyre grip and car balance.

---

## Part III — AI Systems

**Driver AI.** Every driver observes Position, Gap, Tyre state, Fuel, Weather,
Car health, Opponent behavior, and Traffic each simulated tick, then chooses
an action: Attack, Defend, Push, Save, Pit, Overtake, Yield, Manage Tyres,
Manage Energy. Personality (from the attribute set) makes two drivers behave
differently in the same situation.

**Team Strategy AI (the "pit wall").** Evaluates Pit Window, Weather, Tyre
Degradation, Safety Car Probability, Opponent Strategy, and Remaining Laps,
then decides: Box, Stay Out, Undercut, Overcut, Push, Save. Critically, this
AI is allowed to make a bad call — that's a feature, not a bug, since it's
what produces variance and storylines.

**Race Director / Stewards** are separate systems — see Part IV.

---

## Part IV — Racing Systems

**Pit stops.** Modeled as a pipeline: Entry → Pit Lane → Stop → Tyre Change →
Repairs → Release → Exit. Variables: Pit Crew Skill, Reaction Time, Tyre
Change Time, Equipment Reliability, Release Delay, Human Error — producing
everything from a 2.1s stop to a 5.7s "slow stop."

**Damage & mechanical failures.** Components (Engine, Gearbox, Battery,
Brakes, Suspension, Aero, Cooling) each have a health value. Failure
probability rises with health degradation, age, and reliability rating.

**Incidents.** Lock-ups, running wide, spins, collisions, crashes — probability
driven by driver attributes (Aggression, Pressure Handling, Fitness) and
circumstance (traffic, tyre state, weather).

**Race Control.** Observes the whole race and can trigger Yellow Flag, Double
Yellow, Virtual Safety Car, Safety Car, Red Flag, Restart — in response to
incidents or hazards.

**Stewards / penalties.** Investigates Track Limits, Unsafe Release, Pit Lane
Speeding, Causing a Collision, Ignoring Flags, Illegal Overtakes, Jump
Starts. Outcomes: No Further Action, Warning, +5s, +10s, Drive-Through,
Stop-and-Go, Grid Penalty, Disqualification.

**Radio.** Short driver/engineer exchanges generated directly from simulation
events (tyre state, weather changes, strategy calls) — text first, TTS voice
later.

---

## Part V — Teams

Teams have a Budget, Sponsors, Prize Money, Development Cost, and Staff Cost.
R&D flows Research → Prototype → Testing → Upgrade → Performance Change, and
teams make real tradeoffs (e.g. trade reliability for pace). This economy is
what lets teams rise and fall across seasons instead of the grid order being
static forever.

---

## Part VI — Drivers

Drivers have full careers: Rookie debut → results → title contention →
retirement, with a driver market between seasons (contract ends →
negotiation → offers → decision → transfer, or a team-initiated release).
Retiring drivers are replaced by generated rookies, so the world produces
generations rather than a fixed 20 names forever.

---

## Part VII — World / Presentation Layer

**Race weekend structure:** Practice → Practice → Practice → Qualifying →
Race. Key sessions (Qualifying, Race) run in simulated real time — if the
engine says the race takes 1h32m, it takes 1h32m to watch, not an instant
teleport through 78 laps.

**2D live viewer.** No 3D rendering needed — a top-down circuit map with
team-colored dots/markers, clickable for a driver's live telemetry card
(position, speed, tyres, fuel, ERS, gap).

**Live telemetry.** Position, Speed, Lap/Sector times, Gap, Tyres + wear,
Fuel, Energy, Engine health, Brake temp, Tyre temp, DRS state, current
strategy — followable per-driver.

**Broadcast/spectator mode.** Auto-highlights important live moments:
Overtake, Pit Stop, Crash, Battle, Fastest Lap, Penalty.

**AI Newsroom.** After notable events, auto-generates a race report, top
moments, strategy analysis, and championship implications.

**Championships.** Standard Drivers' and Constructors' tables, updated after
every race.

**Persistent history.** Every season, every result, every record is retained
permanently and queryable ("who has the most wins", "who won Season 73",
"fastest lap ever recorded").

**Replays.** Every meaningful simulation state is logged so a full race can
be replayed after the fact, with auto-generated highlight reels.

---

## Part VIII — Platform

User accounts with a profile, favorite driver/team, notification
preferences (race start/finish, major incidents, championship changes,
driver transfers, own driver/team events), and race history. Notifications
via a free-tier email provider while within its limits.

---

## Part IX — Infrastructure

```
        WEB CLIENT (React/Vite)
                 │
           API / WebSocket
                 │
        BACKEND (FastAPI)
                 │
        SIMULATION ENGINE
     (Physics · AI · Strategy · Weather · Race Control)
                 │
           DATABASE
   (Drivers · Teams · Races · Seasons · History)
```

The frontend never runs the world — it only observes and controls a
continuously-running backend simulation engine.

---

## Part X — Build Order (this is the part that actually matters right now)

We are **not** building all of the above at once. The build order is:

1. **Simulation kernel (v0.1 — being built now):** Driver, Team, Car, Tyres,
   Fuel, Weather, a single-race lap loop, basic overtaking, pit stops,
   incidents, a minimal Race Control, and a season points table, all
   runnable from the console with no frontend or database yet.
2. **Persistence:** move race/season results from an in-memory run into a
   real database (start with SQLite) so history actually accumulates.
3. **API layer:** wrap the kernel in FastAPI so a session can be triggered
   and observed over HTTP/WebSocket instead of only from a script.
4. **Frontend:** the 2D live viewer and standings pages, consuming the API.
5. **Everything else in this document** — stewards detail, driver market,
   R&D economy, newsroom, notifications, replays — layered on afterward,
   in whatever order actually matters to you once the kernel is fun to
   watch.

Each part of this document already has a home in the codebase (see
`backend/app/simulation/`) even where today's implementation is a
simplified first pass.
