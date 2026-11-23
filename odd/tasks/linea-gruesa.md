# Línea gruesa: criterio del clasificador y medición de ancho/centro

Corrige el criterio de línea del clasificador de geometría (`geometria.py`) y migra `separaPuntos.m` para medir el ancho y el centro de un trazo (línea gruesa) como el par de rectas de sus dos orillas. Revive la S3 de `migracion-lineas-geometria.md`, que había postergado `separaPuntos.m`.

## Specs

**S1 — Criterio de banda para el residual de recta.**
El usuario describió: "residual_recta = median(|centrado @ normal|) mide distancia al eje principal, y una línea gruesa tiene DOS orillas, así que da ≈ medio ancho. Medido: 26.848px en recorte limpio contra 8.028px reales del ajuste forzado. Arreglo propuesto: medir contra una banda, no contra una recta de grosor cero: median(||signed| - median(|signed|)|)."

Con `signed = centrado @ normal`, el residual de recta pasa a `median(||signed| - median(|signed|)|)`: mide la desviación respecto de la banda de medio-ancho uniforme. Da ~0 en dos orillas paralelas (o con ruido de orilla) y se mantiene alto en un círculo, donde `|signed|` recorre un rango ancho.

**S2 — Modelo del trazo: dos orillas, no una recta de grosor cero.**
El usuario aclaró: "La tarea del detector es buscar bordes para en ellos encontrar rectas, despues con el par de rectas que correspondan a la línea gruesa se estima el ancho y centro del trazo (Línea gruesa)."

Una línea gruesa (trazo) son DOS rectas: sus dos orillas. El ancho es la separación perpendicular entre ambas y el centro es la recta media.

**S3 — Flujo de MATLAB a migrar.**
El usuario recordó: "se usaba separa puntos para tratar de identificar las nubes de puntos correspondientes a cada lado del trazo (sus dos orillas) y con dibuja y anchos busca las lineas con Hough y ajusta con linea1 y luego el if (anchos)."

Verificado en `CodigoMatlab/circle_detector.m` (rama `geometria==1`): `separaPuntos` (`:138`) parte por el signo del gradiente (Izq/Der por Gx, Arriba/Abajo por Gy); cada orilla se ajusta con `houghLines`+`Linea1` (`:276-285`, `:291-302`); el ancho es la media por fila/columna de `dist_p_recta` entre las dos rectas (`:321-345`).

**S4 — Centro derivado, no ajustado a puntos.**
Ante la duda "si con los puntos obtenidos de la linea central ajustas una tercer recta?", la resolución es: no hay puntos sobre la línea central —el detector de bordes (NMS + histéresis) solo emite puntos donde el gradiente es máximo, o sea sobre las dos orillas—. El centro se calcula como la recta media de las dos orillas ajustadas: en forma normal (ρ, θ) con θ compartido, `centro = ((ρ_a + ρ_b)/2, θ)` y `ancho = |ρ_a - ρ_b|` (o la distancia perpendicular media si no son exactamente paralelas). No existe una tercera recta ajustada a puntos.

**S5 — Optimización de `separaPuntos` (orquestador).**
En vez de las 4 cubetas por signo de Gx/Gy (que asumen trazo casi horizontal o vertical y necesitan el flag `anchos`), se separa por `signo(gradiente · normal)`, donde `normal` sale de la dirección θ del Hough: da exactamente dos orillas para cualquier inclinación. El ancho se calcula como distancia perpendicular media entre las dos rectas, no por barrido 1D de filas/columnas.

## Tasks

| ID | Specs | Ruta | Estado | Commit |
|----|-------|------|--------|--------|
| T1 | S1 | `Procesamiento/models/geometria.py` + `tests/unit/Procesamiento/test_geometria.py` | pendiente | — |
| T2 | S2, S3, S5 | `Ajustes/models/trazo_linea.py` + `tests/unit/Ajustes/test_trazo_linea.py` (+ prop) | pendiente | — |
| T3 | S2, S4 | `main_controller.py` (`_rama_recta`), alias en `Ajustes/__init__.py`, registro en `bootstrap.py`, test de integración | pendiente | — |

## Log
**L1** (usuario): "Tarea 1: corregir el criterio de línea del clasificador. Causa en src/odin/Procesamiento/models/geometria.py: residual_recta = median(|centrado @ normal|) mide distancia al eje principal, y una línea gruesa tiene DOS orillas, así que da ≈ medio ancho. Medido: 26.848px en recorte limpio contra 8.028px reales del ajuste forzado. Arreglo propuesto: medir contra una banda, no contra una recta de grosor cero: median(||signed| - median(|signed|)|). Ojo: un test con dos líneas paralelas perfectas YA pasa en verde (el círculo resulta inadmisible y el residual va a inf). El caso que falla necesita orillas imperfectas. Pedime los puntos reales o acordamos una banda sintética con ruido antes de escribir el test."

**L2** (usuario): "antes de lanzar nada. debemos aclarar algo. La tarea del detector es buscar bordes para en ellos encontrar rectas, despues con el par de rectas que correspondan a la línea gruesa se estima el ancho y centro del trazo (Línea gruesa). Espero haberme explicado"

**L3** (usuario): "Habria que verificar en el codiogo de matlab que se hacia. Si no me equivoco se usaba separa puntos para tratar de identificar las nubes de puntos correspondientes a cada lado del trazo (sus dos orillas) y con dibuja y anchos busca las lineas con Hough y ajusta con linea1 y luego el if (anchos). Asi se hacia aunque se aceptan sugerencias para optimizarlo"

**L4** (decisión del usuario): alcance **A + B** — (A) fix del criterio de banda para el ruteo; (B) port optimizado de `separaPuntos` con dos rectas y ancho/centro.

**L5** (duda del usuario y resolución): "solo me queda la duda de si con los puntos obtenidos de la linea central ajustas una tercer recta?" — No: no hay puntos en la línea central; el centro es la recta media de las dos orillas (S4).

**L6** (alcance, usuario): "Estas considerando que si proceso la imagen completa en el caso de la 600mm_imag hay 2 trazos viables por encontrar" → "Puede ser ahora por recorte, sin embargo, si se procesa la imagen completa no es solo un trazo." Decisión: **esta tarea mide UN trazo por recorte** (como MATLAB `rta='r'`). `medir_trazo` separa sobre los puntos cercanos a la línea candidata (ρ, θ), dejándolo preparado para iterar sobre todas las candidatas de `candidatas_lineas`. **Multi-trazo en imagen completa queda como tarea aparte.**
