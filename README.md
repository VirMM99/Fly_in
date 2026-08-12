# Fly_in

_This project has been created as part of the 42 curriculum by vimirand_

## Description

Fly_in routes a fleet of drones from a single `start_hub` to a single `end_hub`
through a graph of connected zones. Each drone follows a path computed with a
Dijkstra-based algorithm while a turn-by-turn simulation enforces every
constraint: zone occupancy, link capacity, restricted (2-turn) transits and
strategic waiting. The goal is to minimize the total number of simulation turns.

The project is written in Python 3.10+ (100% object-oriented, fully typed and
flake8/mypy clean) with no graph libraries: the graph, the pathfinding and the
simulation engine are all implemented from scratch.

## Features

- Custom parser with clear, line-numbered error messages.
- Dijkstra pathfinding with per-zone costs and dynamic congestion penalties.
- Turn-based simulation respecting hub occupancy, link capacity and zone types
  (`normal`, `blocked`, `restricted`, `priority`).
- Real deadlock detection (state snapshots) while still allowing legal
  strategic waiting.
- Two output modes: colored visual representation and `--raw` with the exact
  subject format.

## Instructions

### Requirements

- Python 3.10 or later
- `make`

### Installation

```sh
make install
```

This creates a virtual environment in `.venv/` and installs the dependencies
from `requirements.txt` (pydantic, mypy, flake8). A virtual environment is used
because campus Python installations are often "externally managed" (PEP 668)
and reject global `pip install`.

### Execution

```sh
make run                        # runs the default map (visual mode)
make run MAP=maps/hard/01_maze_nightmare.txt
make run MAP=maps/easy/01_linear_path.txt --raw   # exact subject format
python3 Fly_in/main.py <map_file> [--raw]
```

### Other targets

```sh
make debug      # run under pdb
make clean      # remove .venv, caches and __pycache__
make lint       # flake8 . + mypy with the subject-required flags
make lint-strict # flake8 . + mypy --strict
```

## Input format

A map is a text file with `key: value` lines. Comments start with `#` and empty
lines are ignored. The first meaningful line must define the number of drones.

| Line | Meaning |
|---|---|
| `nb_drones: <positive>` | Number of drones to route |
| `start_hub: <name> <x> <y> [metadata]` | Single departure zone |
| `end_hub: <name> <x> <y> [metadata]` | Single destination zone |
| `hub: <name> <x> <y> [metadata]` | A normal zone |
| `connection: <hub1>-<hub2> [metadata]` | Bidirectional link between existing zones |

Zone metadata (optional, order-independent, between `[...]`):

- `zone=normal|blocked|restricted|priority` (`normal` by default)
- `color=<any word>` (used by the visual mode)
- `max_drones=<positive>` (simultaneous capacity, `1` by default; ignored on
  start/end, which have infinite capacity)

Connection metadata:

- `max_link_capacity=<positive>` (simultaneous drones on the link, `1` by
  default)

## Example

Input (`maps/easy/01_linear_path.txt`):

```
# Easy Level 1: Simple linear path
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

Raw output (`python3 Fly_in/main.py maps/easy/01_linear_path.txt --raw`):

```
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

Visual output (default mode):

```
=== SIMULATION START (2 Drones) ===
T1: D1-waypoint1
T2: D1-waypoint2 D2-waypoint1
T3: D1-goal D2-waypoint2
T4: D2-goal
==== TARGET REACHED SUCCESSFULLY ===
```

## Algorithm and implementation strategy

**Pathfinding** (`pathfinder.py`). A graph is built as an adjacency list that
excludes `blocked` zones. For every connection, the cost is based on the
**destination** zone type: `restricted = 2.0`, `priority = 0.5`,
`normal = 1.0`, so the algorithm naturally prefers priority zones and avoids
restricted ones. Each drone gets its path from a Dijkstra run; after each
routing, every intermediate hub of the chosen path receives a +0.5 congestion
penalty, pushing subsequent drones toward alternative routes and preventing
single-path bottlenecks. If the destination is unreachable, a clear error is
raised instead of a confusing simulation hang.

**Simulation engine** (`simulation.py`). Each turn performs three steps:

1. **Pre-occupation**: drones that will not move this turn occupy a hub
   (in-flight drones occupy their restricted destination; parked drones occupy
   their current hub, except the start, which has infinite capacity).
2. **Movements**: each drone checks the destination hub capacity (unless it is
   the end) and the link capacity in both directions. If allowed, it frees its
   origin hub (same turn), reserves the link and advances.
3. **Restricted zones**: crossing one takes two turns. The first turn logs the
   move as `D<ID>-<hub1>-<hub2>` and marks the drone as in transit; the next
   turn the landing is forced (no extra log line, since the action was already
   reported).

A turn with no movements is legal strategic waiting. A true deadlock is
detected by storing a snapshot of every drone's state (path step + transit
flag) at the start of each empty turn: because the simulation is deterministic,
seeing the exact same state twice means the loop would repeat forever, so a
`RuntimeError` is raised.

## Visual representation

By default the output is rendered in color using each zone's `color` metadata
(ANSI escapes, no external libraries). Each line is prefixed with the turn
number (`T{n}:`), flights toward restricted zones are drawn with an arrow
(`D1-roof1->roof2`), and start/end banners give clear feedback. The `--raw`
flag switches to the exact subject format: one line per turn, no colors, no
prefixes, no banners — useful for automated checking and benchmarks.

## Project structure

```
Fly_in/
  main.py        entry point, argument handling and output rendering
  parser.py      map reading and validation
  pathfinder.py  Dijkstra + congestion penalties
  simulation.py  turn engine, Drone and deadlock detection
  hub.py         Hub model (pydantic v2)
  connection.py  Connection model (pydantic v2)
maps/            official maps (easy, medium, hard, challenger)
Makefile         install / run / debug / clean / lint / lint-strict
```

## Resources

- Python documentation: https://docs.python.org/3/
- pydantic v2: https://docs.pydantic.dev/
- Dijkstra's algorithm: E. W. Dijkstra, "A note on two problems in connexion
  with graphs", 1959.
- The 42 Fly_in subject (v1.6).

**Use of AI.** This project was developed with the assistance of an AI coding
assistant. AI was used to audit and clean the existing codebase. All algorithms and data
structures (Dijkstra, capacity handling, turn engine) are original
implementations written for this project; AI did not generate the core
simulation or pathfinding logic from scratch.
