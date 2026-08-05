# Explain.md — Guía de defensa del proyecto Fly_in

Documento para preparar la defensa presencial. Explica cada pieza del código en
términos simples (todo debe poder explicarse en ~30 segundos) y anticipa las
preguntas típicas del evaluador.

## 1. Resumen de arquitectura

```
main.py ──► Parser ──► Pathfinder ──► Simulation ──► salida (visual / --raw)
  │            │            │             │
  │         hub.py      hub.py        hub.py
  │      connection.py  connection.py  connection.py
  │            │            │             │
  └────────────┴────────────┴─────────────┘
        modelos pydantic v2: Hub, Connection
```

**Explicación en 30 segundos:** "El mapa se lee con un parser que valida cada
línea y construye objetos `Hub` y `Connection` (pydantic valida tipos y
capacidades). Con ese grafo, un pathfinder basado en Dijkstra calcula una ruta
por dron repartiendo la carga mediante penalizaciones dinámicas. La simulación
ejecuta los movimientos turno a turno respetando capacidades de zona y enlace,
y detecta deadlocks comparando estados repetidos. `main.py` orquesta todo y
solo se encarga de presentar la salida (colores o formato exacto del subject)."

## 2. Flujo de datos

1. **`main.py`** valida argumentos (`<mapa>` y `--raw` opcional).
2. **Parser** lee el fichero línea a línea y produce: `nb_drones`, `start`,
   `end`, `hubs`, `connections`. Cualquier error aborta con mensaje claro
   indicando línea y causa.
3. **Pathfinder** construye un grafo de adyacencia y calcula una ruta por dron
   (Dijkstra + penalización dinámica de congestión).
4. **Simulation** inicializa los drones con sus rutas y ejecuta turnos hasta
   que todos llegan al `end_hub`.
5. **main.py** imprime el log: visual por defecto, o `--raw` con el formato
   exacto del subject (`D1-goal D2-goal`).

## 3. Explicación módulo a módulo

### `main.py` — Punto de entrada y presentación
- Valida que haya 1 o 2 argumentos y que el segundo sea `--raw`.
- Orquesta: parsear → rutas → simular → imprimir.
- Dos modos de salida:
  - **Visual (default):** colores ANSI por zona, prefijo `T{n}:`, banner de
    inicio/fin, y vuelos a zonas restricted renderizados como `D1-roof1->roof2`.
  - **`--raw`:** exactamente una línea por turno con el formato del subject.
- Captura `ValueError` (parseo/rutas) y `RuntimeError` (deadlock) y sale con
  código 1.

### `hub.py` — Modelo de zona (pydantic v2)
- Campos: `name`, `x`, `y`, `zone`, `color`, `max_drones`.
- Validadores: tipos de zona permitidos y capacidad positiva.
- Sin lógica de negocio: solo datos + validación (principio de responsabilidad
  única).

### `connection.py` — Modelo de enlace (pydantic v2)
- Campos: `hub1`, `hub2`, `max_link_capacity`.
- Un enlace es **bidireccional** (a-b es lo mismo que b-a).

### `parser.py` — Lectura y validación del mapa
- Orquesta `nb_drones` como primera línea significativa (ignora vacías y `#`).
- Funciones `parse_*` por tipo de línea, cada una con mensajes de error
  indicando número de línea.
- Validaciones clave:
  - un único `start_hub` / `end_hub`; nombres únicos.
  - sin guiones en nombres (el guion es el separador de las conexiones).
  - coordenadas y capacidades enteras positivas.
  - conexiones solo entre zonas ya definidas y sin duplicados (a-b ≡ b-a).
  - metadata `[...]`: un solo bloque, cerrado, sintaxis `clave=valor`, sin
    claves duplicadas, claves permitidas según el tipo de línea.
  - `max_drones` en start/end se ignora y se fuerza a 999999 (capacidad
    infinita, según el subject).
- Detalle importante: pydantic v2 hace que `ValidationError` sea subclase de
  `ValueError`, por eso los `except ValidationError` van **antes** de los
  `except ValueError`.

### `pathfinder.py` — Cálculo de rutas (Dijkstra propio)
- Construye un grafo de adyacencia **ignorando zonas blocked**.
- Coste por zona **destino**: `restricted=2.0`, `priority=0.5`, `normal=1.0`.
  Así el algoritmo "prefiere" las zonas priority y "evita" las restricted,
  alineado con el coste real de moverse por ellas.
- **Dijkstra manual** sin heap (extracción del mínimo en O(V) por iteración).
  Justificación: mapas pequeños, simplicidad, cero dependencias; el subject
  prohíbe librerías de grafos.
- **Penalización dinámica:** por cada dron encaminado por un nodo intermedio se
  suma +0.5 a su coste, de modo que los siguientes drones tienden a elegir
  rutas alternativas (evita embudos en la defensa).
- Si el `end_hub` es inalcanzable (mapa desconectado o bloqueado) lanza
  `ValueError` claro en lugar de dejar drones parados.
- Complejidad: O(V²) por dron (manual), O(V²·N) para N drones. Memoria O(V+E)
  para el grafo + O(V) por ruta.

### `simulation.py` — Motor de turnos
- **`Drone`:** guarda su ruta (lista de `Hub`), el índice actual y una bandera
  `in_transit_to_restricted`. Métodos: `get_current_hub`, `get_next_hub`,
  `has_arrived`.
- **`Simulation.run()`**, por turno:
  1. **Pre-ocupación:** los drones que no se moverán este turno ocupan su zona
     (los que vuelan hacia restricted ocupan su zona de destino; los parados
     ocupan su zona actual, salvo el start que tiene capacidad infinita).
  2. **Movimientos:** cada dron que puede moverse comprueba capacidad de zona
     destino (salvo el end) y capacidad del enlace en **ambas direcciones**
     (bidireccional). Si cumple: libera su zona de origen (salvo start),
     reserva el enlace y avanza.
  3. **Zona restricted:** el movimiento tarda 2 turnos. Turno 1 → imprime
     `D1-a-b` y marca `in_transit_to_restricted`. Turno 2 → aterrizaje forzoso
     (sin log, porque la acción ya se imprimió).
  4. Los movimientos del turno se ordenan por ID de dron y se unen con espacio.
- **Turno sin movimientos** = espera estratégica permitida (subject VII.3).
  Solo es deadlock si el **mismo estado** (paso de todos los drones + bandera)
  ya se vio al inicio de un turno vacío anterior: como la simulación es
  determinista, repetir el estado implica bucle infinito. Ahí lanza
  `RuntimeError`.

## 4. Representación visual (obligatoria en el subject)
- Por defecto `main.py` colorea la salida por terminal usando el `color` de
  cada zona (ANSI, sin librerías externas).
- Las zonas restricted en vuelo se dibujan con flecha: `D1-roof1->roof2`.
- Los banners `=== SIMULATION START (N Drones) ===` y
  `==== TARGET REACHED SUCCESSFULLY ====` dan feedback de inicio/fin.

## 5. Rendimiento medido (turnos por mapa)

| Nivel | Mapa | Drones | Objetivo | Resultado | Estado |
|---|---|---|---|---|---|
| Easy | 01_linear_path | 2 | ≤6 | 4 | OK |
| Easy | 02_simple_fork | 4 | ≤8 | 4 | OK |
| Easy | 03_basic_capacity | 4 | ≤6 | 4 | OK |
| Medium | 01_dead_end_trap | 5 | ≤12 | 8 | OK |
| Medium | 02_circular_loop | 6 | ≤15 | 9 | OK |
| Medium | 03_priority_puzzle | 5 | ≤12 | 7 | OK |
| Hard | 01_maze_nightmare | 8 | ≤30 | 13 | OK |
| Hard | 02_capacity_hell | 12 | ≤35 | 16 | OK |
| Hard | 03_ultimate_challenge | 15 | ≤45 | 28 | OK |
| Challenger | 01_the_impossible_dream | 25 | record 45 | 49 | no batido |

Punto honesto para la defensa: los 9 mapas obligatorios se superan con margen;
el record del Challenger (45) no se bate (49). El bonus exige "igualar o batir
los objetivos" → se cumple en los obligatorios; batir el record es opcional.

## 6. Preguntas típicas y respuestas cortas

- **¿Eficiencia / complejidad?** Dijkstra manual O(V²) por dron y O(V²·N)
  total; memoria O(V+E) + O(V) por ruta. Suficiente: los mapas tienen pocas
  decenas de zonas.
- **¿Número grande de drones?** La penalización dinámica reparte las rutas
  entre caminos alternativos, evitando saturar un único camino.
- **¿Recálculo vs caché de rutas?** Las rutas se calculan una vez por dron
  (Dijkstra secuencial con penalizaciones acumuladas). La simulación decide el
  momento real de moverse turno a turno según capacidades: es la estrategia que
  se defiende, no el recálculo continuo.
- **¿Memoria?** Cada dron guarda solo su lista de hubs y un índice; la
  simulación solo mantiene dos diccionarios de ocupación por turno.
- **¿Utilidad de la visualización?** Muestra turno a turno qué drones se mueven
  y a qué zona, coloreada por zona; útil para depurar y demostrar que se
  respetan capacidades.
- **¿Cómo evitas deadlocks?** Con snapshots de estado en turnos vacíos: mismo
  estado dos veces → bucle determinista → `RuntimeError`. Mientras, la espera
  estratégica está permitida.
- **¿Por qué no librerías de grafos?** Prohibido por el subject; el grafo es
  un dict de adyacencia construido a mano.
- **¿Optimizaciones posibles?** Heap de Fibonacci/`heapq` en Dijkstra, poda
  con A*, precomputar rutas alternativas, batch de movimientos. No se hicieron
  porque los mapas son pequeños y la simplicidad es un requisito del proyecto.

## 7. Puntos débiles conocidos (para no pillarte por sorpresa)
- `lint-strict` corre `mypy --strict` desde dentro de `Fly_in/` (los imports
  planos solo se resuelven así; en runtime Python añade el directorio del
  script al `sys.path`).
- El record del Challenger no se bate (49 vs 45).
- La entrega usa un venv `.venv/` porque las instalaciones de Python del campus
  suelen ser "externally managed" (PEP 668) y rechazan `pip install` global.
