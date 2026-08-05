# Defensa.md — Checklist de defensa y preparación de Live Coding

Checklist de auditoría: cada requisito evaluable del subject mapeado al código
concreto. Última sección: modificaciones típicas de Live Coding, listas para
hacer en directo.

## 1. Checklist requisito → código

### Preliminares / entorno
- [x] `make install` crea `.venv/` e instala pydantic, mypy, flake8.
- [x] `make run` ejecuta el mapa por defecto; `make run MAP=<mapa>` un mapa dado.
- [x] `make debug` lanza `python -m pdb Fly_in/main.py <mapa>`.
- [x] `make clean` borra `.venv/`, caches y `__pycache__`.
- [x] `make lint` = `flake8 .` + `mypy .` con los flags exactos del subject.
- [x] `make lint-strict` = `flake8 .` + `mypy . --strict` (pasa).

### Project Structure & Requirements
- [x] **Type-safe:** todos los `def`/`class` tipados; mypy 0 errores.
- [x] **100% OOP:** `Hub`, `Connection`, `Parser`, `Pathfinder`, `Simulation`,
      `Drone`. No hay funciones sueltas con lógica de negocio.
- [x] **Python 3.10+:** union types (`Hub | None`), `dict[str, ...]`,
      `str.removeprefix`.
- [x] **flake8 limpio.**
- [x] **Sin librerías de grafos:** grafo propio = `dict[name, list[(Hub, cost)]]`.
- [x] **try/except + context managers:** `open()` con `with`; todos los errores
      esperados se capturan y se convierten en mensajes claros.
- [x] **Docstrings PEP 257** en clases y métodos.

### Parser (`parser.py`)
- [x] `nb_drones` obligatorio en la primera línea significativa.
- [x] Un único `start_hub` / `end_hub`; nombres de hub únicos.
- [x] Coordenadas y capacidades enteras positivas.
- [x] Conexiones solo entre zonas definidas; sin duplicados (a-b ≡ b-a).
- [x] Metadata `[...]`: bloque único, cerrado, `clave=valor`, sin duplicados.
- [x] Errores con **línea y causa** (p. ej. `Line 4: Coordinates must be integers`).
- [x] `max_drones` en start/end ignorado (se fuerza 999999).
- [x] Comentarios `#` y líneas vacías ignoradas.

### Zone & Movement Mechanics (`simulation.py`)
- [x] Capacidad de zona: default 1, `max_drones=N` permite N.
- [x] Start y end con capacidad infinita.
- [x] Capacidad de enlace `max_link_capacity` respetada en ambas direcciones.
- [x] Salir de una zona libera capacidad en el mismo turno.
- [x] `restricted`: tarda 2 turnos y el aterrizaje es forzoso (sin esperar en el
      enlace); formato `D<ID>-<hub1>-<hub2>`.
- [x] `blocked`: excluido del grafo (inalcanzable).
- [x] `priority`: coste menor en pathfinding.
- [x] Espera estratégica permitida (subject VII.3); deadlock solo si el estado
      se repite.

### Visual Representation (`main.py`)
- [x] Colores ANSI por zona (campo `color` del mapa).
- [x] Vuelos a restricted con flecha: `D1-roof1->roof2`.
- [x] Banners de inicio/fin y prefijo de turno `T{n}:`.
- [x] Modo `--raw` con el formato exacto del subject (`D1-goal D2-goal`).

### Pathfinding (`pathfinder.py`)
- [x] Dijkstra propio (sin librerías), parada temprana al llegar a end.
- [x] Costes por zona destino: restricted 2.0, priority 0.5, normal 1.0.
- [x] Penalización dinámica de congestión (+0.5 por dron) reparte rutas.
- [x] Error claro si el end es inalcanzable (no deadlock confuso).

### Performance & Benchmarks
- [x] 9 mapas obligatorios superados con margen (ver tabla en `Explain.md`).
- [x] Challenger: 49 turnos (record 45 no batido — se admite en la defensa).

### Edge Cases & Error Handling
- [x] Fichero inexistente → `Cannot open file '<name>'`.
- [x] Deadlock real → `RuntimeError` con turno; espera legal → sin error.
- [x] `main.py` captura `ValueError`/`RuntimeError` y sale con código 1.

### Documentación
- [x] `Agent.md` (resumen del subject), `Explain.md` (guía de defensa),
      `Defensa.md` (este), `README.md` (H6, en inglés).

## 2. Demo sugerida (en directo, ~5 min)

1. `make lint` y `make lint-strict` → mostrar 0 issues.
2. `make run` → salida visual del mapa easy.
3. `make run MAP=maps/medium/02_circular_loop.txt` → ejemplo de deadlock
   resuelto y de zonas restricted en el log.
4. `make run MAP="maps/hard/03_ultimate_challenge.txt --raw"` → formato exacto
   del subject y cuenta de turnos (28 ≤ 45).
5. Mapa inventado con zona `blocked`/`restricted` para demostrar parseo y
   errores (`Line N: ...`).

## 3. Quick Live Coding — modificaciones preparadas

Técnica general: cambiar lo mínimo, una sola responsabilidad, comentar el
cambio y re-ejecutar con `make run MAP=...`. Después, `make lint` para
confirmar que sigue limpio.

### LC0 — TAREA OFICIAL de la hoja: flag `--capacity-info` (hacerlo en vivo)
La hoja de evaluación pide: añadir `--capacity-info` para mostrar por turno
"Zone X: Y/Z drones" y "Connection A-B: Y/Z capacity used" junto a la salida
normal. Ejemplo de la hoja: `./main.py --capacity-info map.txt`.

**El repo NO lo contiene a propósito** (para poder hacerlo en directo en
<10 min). Plan probado y verificado en un borrador; reproducirlo:

**Paso 1 — `simulation.py`, en `__init__`** (tras `self.log_output = []`):
```python
# Ordered unique list of all hubs (start, end, then connection
# endpoints). Used to report capacity info per turn.
seen_names = {start_hub.name, end_hub.name}
self.hubs: list[Hub] = [start_hub, end_hub]
for conn in connections:
    for hub in (conn.hub1, conn.hub2):
        if hub.name not in seen_names:
            seen_names.add(hub.name)
            self.hubs.append(hub)
# Per-turn capacity report: one list of info lines per turn.
self.capacity_log: list[list[str]] = []
```

**Paso 2 — `simulation.py`, final del bucle de `run()`** (justo antes del
`return self.log_output`, al nivel del `if turn_moves: ... else: ...`):
```python
# Snapshot the capacity state of this turn for reporting: zones with
# current occupancy vs max_drones; links with simultaneous crossings
# (both directions) vs max_link_capacity.
capacity_lines: list[str] = []
for hub in self.hubs:
    occupancy = hub_occupancy.get(hub.name, 0)
    capacity_lines.append(
        f"Zone {hub.name}: {occupancy}/{hub.max_drones} drones"
    )
for conn in self.connections:
    used = link_occupancy.get(
        (conn.hub1.name, conn.hub2.name), 0
    ) + link_occupancy.get((conn.hub2.name, conn.hub1.name), 0)
    capacity_lines.append(
        f"Connection {conn.hub1.name}-{conn.hub2.name}: "
        f"{used}/{conn.max_link_capacity} capacity used"
    )
self.capacity_log.append(capacity_lines)
```

**Paso 3 — `main.py`, sustituir la validación de argumentos** (el `if len(...)`
actual) por parsing flexible que acepta el flag antes o después del mapa:
```python
flags: set[str] = set()
map_filename: str | None = None
for arg in sys.argv[1:]:
    if arg.startswith("--"):
        flags.add(arg)
    elif map_filename is None:
        map_filename = arg
    else:
        # A second positional argument is invalid
        map_filename = None
        break

if (
    map_filename is None
    or not flags.issubset({"--raw", "--capacity-info"})
):
    print(
        "Usage: Python main.py <map_file> [--raw] [--capacity-info]",
        file=sys.stderr,
    )
    sys.exit(1)

raw_mode = "--raw" in flags
capacity_info_mode = "--capacity-info" in flags
```

**Paso 4 — `main.py`, en el render**: imprimir la línea normal y, debajo, la
info de capacidad de ese turno (estructura que sustituye al `if raw_mode: ...
else: ...`):
```python
if not raw_mode:
    print(
        f"\n{ANSI_COLORS['cyan']}=== SIMULATION START "
        f"({parser.nb_drones} Drones) ==={ANSI_RESET}"
        )
for turn_number, turn_log in enumerate(log_output, start=1):
    if raw_mode:
        print(turn_log)
    else:
        colored_line = (
            f"T{turn_number}: "
            f"{colorize_log(turn_log, parser.hubs_by_name)}"
        )
        print(colored_line)
    if capacity_info_mode:
        for info in simulation.capacity_log[turn_number - 1]:
            print(f"  {info}")
if not raw_mode:
    print(
        f"{ANSI_COLORS['cyan']}==== TARGET REACHED SUCCESSFULLY "
        f"==={ANSI_RESET}\n"
        )
```

Verificar: `python3 Fly_in/main.py maps/easy/01_linear_path.txt --capacity-info`
y `python3 Fly_in/main.py --capacity-info maps/easy/01_linear_path.txt --raw`.
Después `make lint` (debe seguir a 0). Detalle clave para la defensa: los datos
de capacidad ya se calculan en el motor (`hub_occupancy`/`link_occupancy`); solo
hay que exponerlos, no recalcular nada.

### LC1 — Cambiar el coste de una zona en pathfinding
Fichero: `pathfinder.py`, bloque `if h2.zone == "restricted"` (≈ líneas 41-53
del método `_build_graph`). Cambiar `2.0`/`0.5`/`1.0`.
Ejemplo: hacer `restricted = 1.5` para penalizarla menos. Re-run y observar
cómo cambian las rutas (menos turnos, más uso de restricted).

### LC2 — Cambiar la capacidad global por defecto de las zonas
Fichero: `hub.py`, línea 12: `max_drones: int = 1` → `2`. Afecta a toda zona
sin `max_drones` explícito. Nota: start/end siguen siendo 999999 (se fijan en
`parser.py`).

### LC3 — Cambiar la capacidad global por defecto de los enlaces
Fichero: `connection.py`, línea 9: `max_link_capacity: int = 1` → `3`.
Efecto: más drones cruzando el mismo enlace por turno → menos turnos.

### LC4 — Salida exacta del subject por defecto (quitar el modo visual)
Fichero: `main.py`. Opción mínima: en `main()`, cambiar
`raw_mode = len(sys.argv) == 3 and sys.argv[2] == "--raw"` por
`raw_mode = True` (o invertir el `if raw_mode:` de la impresión).
Mejor opción de defensa: mantener ambos y explicar la elección de diseño.

### LC5 — Añadir un nuevo tipo de zona (ej. "express", coste 0.25)
Pasos:
1. `hub.py` → añadir `"express"` al set `valid` (línea 18).
2. `pathfinder.py` → añadir `elif h2.zone == "express": cost_to_h2 = 0.25`
   (y lo mismo para `h1`).
3. `simulation.py` → si "express" debe mover en 1 turno, no hay que tocar nada
   (ya es el caso por defecto para zonas no-restricted).
Re-parsear y re-run con un mapa que tenga `zone=express`.

### LC6 — Límite de turnos (evitar simulación infinita)
Fichero: `simulation.py`, en el bucle `while not all(...)` (línea 71), añadir:
```python
if self.current_turn > MAX_TURNS:
    raise RuntimeError(f"Turn limit exceeded: {MAX_TURNS}")
```
Sirve como red de seguridad y demuestra control de errores.

### LC7 — Devolver el número de turnos
Trivial: `len(log_output)` (cada turno sin movimiento también se cuentan; si se
quiere solo turnos con movimiento, contar líneas no vacías). En la demo se
obtiene con `--raw | wc -l`.

### LC8 — Ruta para un dron concreto
Fichero: `pathfinder.py`, método `find_all_paths` (línea 118): por cada
`drone_id` llama a `self._dijkstr(dynamic_penalties)`. Mostrar que llamar una
vez devuelve `list[Hub]` y que las penalizaciones se acumulan entre drones.
Si piden "recalcular en caliente": re-ejecutar `_dijkstr` con penalizaciones
actualizadas de la simulación.

## 4. Trampas típicas a evitar en directo
- Cambiar `hub.py` y olvidar `pathfinder.py`: el nuevo tipo de zona no tendría
  coste asociado (caería en `else` = normal) → comportamiento silencioso raro.
- Poner un `except` de `ValueError` antes que `ValidationError` en pydantic v2
  (subclase) → el mensaje saldría con el prefijo "Value error, ".
- Olvidar que `start`/`end` tienen capacidad infinita fijada en el parser, no
  en el modelo.
