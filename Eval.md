# Eval.md — Hoja de evaluación resuelta

Mapeo 1:1 de la hoja de evaluación oficial (versión en texto proporcionada) a
nuestro proyecto: estado, cómo demostrarlo y referencia al código. Todo
verificado sobre el repositorio.

## Leyenda
- ✅ requisito cumplido y verificado
- ⚠️ parcial / requiere explicación en la defensa
- ❌ no cumplido

## Preliminaries
- ✅ Repositorio Git del alumno: `origin git@github.com:VirMM99/Fly_in.git`.
- ✅ Solo los ficheros solicitados en el repo (código, mapas, Makefile, docs).
- ✅ `git clone` en carpeta vacía; sin aliases maliciosos.

## README.md (raíz)
La hoja pide 5 apartados:
- ✅ **Description** (objetivo + visión general).
- ✅ **Instructions** (instalación y ejecución).
- ✅ **Algorithm explanation** (pathfinding + decisiones de diseño).
- ✅ **Visual representation** (documentación + cómo mejora la UX).
- ✅ **Example input and expected output** (mapa real + salida raw y visual).

## Project Structure and Requirements
- ✅ **OOP:** clases `Hub`, `Connection`, `Parser`, `Pathfinder`, `Simulation`,
      `Drone`; separación clara de responsabilidades (datos/validación,
      parseo, rutas, simulación, presentación).
- ✅ **Type safe:** `mypy .` (comando exacto del evaluador, desde la raíz) →
      `Success: no issues found in 6 source files`. También `mypy --strict`
      (`make lint-strict`).
- ✅ **Graph implementation:** grafo propio como `dict[name, list[(Hub, cost)]]`
      (`pathfinder.py:_build_graph`). Sin networkx/graphlib ni similares.
      Explicable en 30s.

## Parser Implementation
**Input files** (≥4/5):
- ✅ `nb_drones: <number>` (obligatorio en primera línea significativa).
- ✅ Prefijos `start_hub:` / `end_hub:` / `hub:`.
- ✅ `connection: <zone1>-<zone2>`.
- ✅ Metadata con defaults (`zone=normal`, `max_drones=1`,
      `max_link_capacity=1`).
- ✅ Comentarios `#` ignorados.

**Error handling** (≥4/5):
- ✅ Ficheros malformados (sin nb_drones → `Line 1: The first line must define
      nb_drones`; formato inválido → `Line N: Unknown line`).
- ✅ Tipos de zona inválidos → `Line N: Invalid zone type: 'bogus'`.
- ✅ Falta start/end → `Parsing Error: Missing start_hub zone`.
- ✅ Capacidades no positivas → `Line N: max_drones capacity must be positive
      integer`.
- ✅ Zonas/conexiones duplicadas → `Line N: Duplicate hub: X` / `Duplicate
      connection between a and b`.

## Zone and Movements Mechanics
- ✅ **Occupancy:** `max_drones` respetado (default 1); no se entra en zona
      llena; start/end compartidos sin límite; capacidad liberada al salir en
      el mismo turno. Ver `simulation.py`, bloque "Capacity checks".
- ✅ **Movement costs:** normal 1 turno, restricted 2 turnos (`D1-a-b` +
      aterrizaje forzoso), priority 1 turno y preferida en pathfinding,
      blocked inaccesible (fuera del grafo).
- ✅ **Connection capacity:** `max_link_capacity` (default 1) contabiliza cruces
      simultáneos en ambas direcciones del enlace.

## Visual Representation
- ✅ Feedback visual coloreado (ANSI) por zona usando el `color` del mapa.
- ✅ Los `color=` de la metadata se usan en la salida.
- ✅ Mejora la comprensión: banners, prefijo `T{n}:`, flecha `->` para vuelos
      a restricted.
- ✅ Muestra posiciones/movimientos de los drones (qué drone va a qué zona
      cada turno).

## Basic Functionality Tests
**Simple scenarios** (≥4/5):
- ✅ Un dron en ruta lineal.
- ✅ Varios drones con rutas distintas (fork, capacity).
- ✅ Mapas de ejemplo adjuntos (los 9 obligatorios + challenger funcionan).
- ✅ Formato de salida: una línea por turno, `D<ID>-<zone>` /
      `D<ID>-<connection>` (modo `--raw`).
- ✅ Drones estacionarios omitidos (solo aparecen los que se mueven).

**Simulation ends correctly:**
- ✅ Para de producir salida cuando todos llegan al `end_hub`
      (`TARGET REACHED SUCCESSFULLY`).

## Pathfinding Algorithm
- ✅ **Valid path:** resuelve mapas lineales, con rutas múltiples, con cuellos
      de botella/capacidad y con distintos tipos de zona (9/9 obligatorios).
- ✅ **Conflict resolution:** penalización dinámica (+0.5 por dron por nodo
      intermedio) reparte los drones; capacidad de zona y enlace evitan
      conflictos; restricted de 2 turnos gestionada con bandera
      `in_transit_to_restricted`.

## Performance and Optimization
- ✅ **Efficiency:** mapas con 12–15 drones resueltos en 16–28 turnos;
      topología compleja (maze, capacity hell, ultimate challenge) sin
      problemas de rendimiento.
- ✅ **Algorithm explanation:** complejidad O(V²) por dron (Dijkstra manual),
      decisiones de diseño y trade-offs documentados en `README.md` y
      `Explain.md`.

## Performance Benchmarks
| Categoría | Pregunta eval | Nuestros turnos | Media | Estado |
|---|---|---|---|---|
| Easy | ¿< 10 de media? | 4, 4, 4 | 4 | ✅ |
| Medium | ¿10–30 de media? | 8, 9, 7 | 8 | ✅ |
| Hard | ¿< 60 de media? | 13, 16, 28 | 19 | ✅ |

Nota de defensa: la franja "10–30" de Medium es orientativa; los targets de
referencia reales son ≤12/≤15/≤12 y los batimos con margen (8/9/7). Si el
evaluador cuestiona la media 8 < 10, se explica: más rápido que el mínimo de la
franja = mejor; los objetivos de referencia se cumplen.

## Edge Cases and Error Handling
**Edge cases** (≥4/5):
- ✅ Un solo dron (mapas fáciles; funciona).
- ✅ Cuellos de botella / capacidad limitada (capacity hell, basic_capacity).
- ✅ Grafo desconectado → `No path found from start to end for drone N: the map
      is unreachable or blocked` (sin cuelgue).
- ✅ Conexiones inválidas → `Line N: Hub 'X' is not defined`.
- ✅ Capacidades cero o muy altas → cero rechazada (`must be positive integer`),
      muy altas aceptadas.

**Error handling:**
- ✅ Mensajes claros e informativos con línea y causa para ficheros malformados,
      falta de start/end, capacidades inválidas, grafo desconectado y tipos de
      zona/conexión inválidos.

## Code Quality and Documentation
- ✅ Código estructurado y legible; OOP correcta; comentarios QUÉ/POR QUÉ;
      estilo consistente (flake8 0); visualización bien integrada (solo en
      `main.py`, sin contaminar el motor).

## Quick Live Coding modifications
**Tarea oficial:** añadir el flag `--capacity-info` que muestre por turno
"Zone X: Y/Z drones" y "Connection A-B: Y/Z capacity used", junto a la salida
normal. Máximo 10 minutos.

⚠️ **Preparado para hacerse EN VIVO** (el repo no lo contiene a propósito,
para poder demostrar el cambio en directo). El plan exacto está en
`Defensa.md` §3 (LC0), con los 4 pasos (2 en `simulation.py`, 2 en `main.py`)
probados y verificados. Clave: los datos de capacidad ya se calculan en el
motor (`hub_occupancy`/`link_occupancy`); solo hay que exponerlos turno a
turno, no recalcular nada.

Verificación tras hacerlo:
```
python3 Fly_in/main.py maps/easy/01_linear_path.txt --capacity-info
python3 Fly_in/main.py --capacity-info maps/easy/01_linear_path.txt --raw
```


## Bonus Features
- ✅ **Exceptional Performance:** los 9 mapas obligatorios cumplen o superan
      sus targets de referencia:
  - Easy: 4≤6 · 4≤8 · 4≤6
  - Medium: 8≤12 · 9≤15 · 7≤12
  - Hard: 13≤30 · 16≤35 · 28≤45
- ⚠️ **Challenger Map:** 01_the_impossible_dream se resuelve en 49 turnos, pero
      no bate el record de 45 → este bonus NO se logra. Aceptado como limitación
      honesta en la defensa.
