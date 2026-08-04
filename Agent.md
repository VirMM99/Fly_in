# Agent.md — Resumen operativo del subject Fly_in (v1.6)

Referencia rápida para trabajar sin releer el PDF. Todo cambio de código debe
respetar esto.

## 1. Objetivo
Enrutar una flota de drones desde un único `start_hub` hasta un único `end_hub`
a través de un grafo de zonas conectadas, minimizando el número total de turnos
de simulación y respetando todas las restricciones de capacidad y movimiento.

## 2. Restricciones técnicas (obligatorias)
- Python **3.10 o posterior**.
- Cumplir el estándar **flake8**.
- **Tipado completo**: mypy sin errores (todos los `def` y `class` tipados).
- Código **100% orientado a objetos** (se debe demostrar en la defensa).
- **Prohibido** cualquier librería de grafos (networkx, graphlib, etc.).
- Excepciones controladas con `try/except`: un crash no controlado = proyecto
  no funcional. Usar context managers (`with`) para ficheros/conexiones.
- `docstrings` en funciones y clases siguiendo PEP 257 (estilo Google/NumPy):
  propósito, parámetros, retorno.

## 3. Makefile (reglas obligatorias)
- `install`: instalar dependencias (pip/uv/pipx...). MODO: venv + requirements.
- `run`: ejecutar el script principal.
- `debug`: ejecutar con `pdb` (`python -m pdb <main> <mapa>`).
- `clean`: eliminar `__pycache__`, `.mypy_cache`, etc.
- `lint`: ejecutar EXACTAMENTE
  - `flake8 .`
  - `mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports
    --disallow-untyped-defs --check-untyped-defs`
- `lint-strict` (opcional): `flake8 .` + `mypy . --strict`.

## 4. Formato de entrada (mapa)
Líneas `clave: valor`, comentarios desde `#`, líneas vacías ignoradas.

- `nb_drones: <positivo>` — **primera línea**. Número de drones (cualquiera).
- `start_hub: <nombre> <x> <y> [metadata]` — único punto de salida.
- `end_hub: <nombre> <x> <y> [metadata]` — único destino.
- `hub: <nombre> <x> <y> [metadata]` — zona normal.
- `connection: <nombre1>-<nombre2> [metadata]` — conexión BIDIRECCIONAL entre
  zonas ya definidas.

### Metadata de zonas (opcional, entre `[...]`, cualquier orden)
- `zone=<tipo>`: `normal` (1 turno, default) · `blocked` (inaccesible) ·
  `restricted` (2 turnos) · `priority` (1 turno, preferido en pathfinding).
- `color=<cualquier palabra>` (sin lista fija; debe haber feedback visual).
- `max_drones=<positivo>` (default 1) — capacidad simultánea de la zona.

### Metadata de conexiones
- `max_link_capacity=<positivo>` (default 1) — drones simultáneos en el enlace.

### Restricciones de parseo
- Exactamente un `start_hub` y un `end_hub`.
- Nombres únicos; coordenadas enteras; **sin guiones ni espacios** en nombres.
- Conexiones solo entre zonas ya definidas; sin duplicados (a-b ≡ b-a).
- Metadata sintácticamente válida; sin duplicar claves; un solo bloque `[]`.
- Tipos de zona válidos; capacidades enteras positivas.
- `max_drones` en start/end se **ignora** (capacidad infinita), no es error.
- Cualquier otro error: detener el programa con mensaje claro indicando
  **línea y causa**.

## 5. Reglas de ocupación y movimiento
- Por defecto 1 drone por zona/turno; `max_drones=N` permite N.
- Start y end: sin límite (todos empiezan juntos; llegan y se entregan).
- Dos drones no pueden entrar en la misma zona el mismo turno si no hay capacidad.
- No mover a una zona que excedería su capacidad.
- Capacidad de conexión: limita cruces simultáneos del enlace.
- Movimientos simultáneos permitidos si se respetan las capacidades.
- Los drones que **salen** de una zona liberan capacidad ese mismo turno.
- En cada turno un drone puede: moverse a zona adyacente, moverse hacia zona
  restricted (tarda 2 turnos y DEBE aterrizar al siguiente turno, sin esperar
  en el enlace), o quedarse (espera estratégica permitida).
- Coste de movimiento = según el tipo de la zona DESTINO.

## 6. Formato de salida
- Cada turno = una línea con los movimientos de ese turno, separados por espacio.
- Movimiento: `D<ID>-<zona>` o `D<ID>-<conexion>` si está en vuelo hacia
  restricted (la conexión se representa como `hub1-hub2`).
- Drones que no se mueven en ese turno: omitidos.
- Drones que llegan al end: se dan por entregados (dejan de aparecer).
- La simulación termina cuando todos llegan al end.
- Ejemplo del subject: `D1-roof1 D2-corridorA` / `D1-roof2 D2-tunnelB` /
  `D1-goal D2-goal`.
- DECISIÓN DEL PROYECTO: dos modos — visual por defecto (color + `T{n}:` +
  banners + flechas `->`) y modo `--raw` con el formato exacto del subject.

## 7. Representación visual (obligatoria)
Salida de terminal en color mostrando movimientos y estados de zona, y/o
interfaz gráfica. Se evalúa calidad/utilidad en la defensa.

## 8. Algoritmo y rendimiento (benchmarks de referencia)
Debe: distribuir drones entre rutas, esperar estratégicamente, evitar conflictos
y deadlocks, tener en cuenta costes por tipo de zona, capacidades de zona y
enlace, y turnos. Debe adaptarse a mapas distintos.

| Nivel | Mapa | Drones | Objetivo turnos |
|---|---|---|---|
| Easy | 01_linear_path | 2 | ≤6 |
| Easy | 02_simple_fork | 4 | ≤8 |
| Easy | 03_basic_capacity | 4 | ≤6 |
| Medium | 01_dead_end_trap | 5 | ≤12 |
| Medium | 02_circular_loop | 6 | ≤15 |
| Medium | 03_priority_puzzle | 5 | ≤12 |
| Hard | 01_maze_nightmare | 8 | ≤30 |
| Hard | 02_capacity_hell | 12 | ≤35 |
| Hard | 03_ultimate_challenge | 15 | ≤45 |
| Challenger | 01_the_impossible_dream | 25 | record 45 (opcional) |

## 9. README.md (obligatorio, en inglés, en la raíz del repo)
- Primera línea en cursiva: "This project has been created as part of the 42
  curriculum by <login>".
- Sección Description (objetivo + visión general).
- Sección Instructions (compilación, instalación, ejecución).
- Sección Resources (referencias clásicas + cómo se usó IA y en qué partes).
- Descripción detallada del algoritmo y la estrategia de implementación.
- Documentación de la representación visual.
- Ejemplo de entrada y salida esperada.

## 10. Bonus (solo si lo obligatorio está completo)
- Cumplir (igualar o batir) todos los objetivos de turnos de los mapas.
- Batir el record de 45 turnos del Challenger.

## 11. Evaluación (estructura de la hoja)
Intro · Guidelines · Attachments · Preliminaries · README · Project Structure
& Requirements (type-safe, OOP/clean) · Parser · Zone & Movement Mechanics
(occupancy, capacity) · Visual Representation · Basic Functionality Tests
(simple scenarios, simulation & capacity) · Pathfinding (valid paths, method) ·
Performance & Optimization (test performance, algorithm explanations) ·
Performance Benchmarks (easy/medium/hard, reference targets) · Edge Cases &
Error Handling · Code Quality & Documentation · **Quick Live Coding
modifications** · Bonus (expert performance, challenger) · Ratings · Conclusion.

Preguntas típicas que el subject anticipa (se espera poder responderlas):
eficiencia, nº grande de drones, complejidad, recálculo vs caché de rutas,
memoria, utilidad de la visualización, comparación con objetivos de turnos,
optimizaciones, challenger.

## 12. Mapas oficiales
`easy/`, `medium/`, `hard/`, `challenger/` (adjuntos al subject). Durante la
evaluación pueden usar mapas distintos.
