# Tarea: pertenencia de puntos al trazo por picos de Hough

Repo: `/home/jolopez/proyectos/ODIN`. Rama base `main` (`1793861` en Azure, `e452f13` en GitHub).

## Problema

`_rama_recta` entrega a `medir_trazo` **todos** los puntos de borde (51 424 en
`600mm_Imag0000.bmp`), sin relación con la candidata que encontró Hough. `separar_orillas` los
parte por signo del gradiente y mide entre los dos montones, así que el ancho mide la escena,
no el trazo. Evidencia medida (`600mm_Imag0000.bmp`): nube completa 112.70 px; cota 15 px
7.51 px; cota 10 px 2.34 px; recortes manuales 13.79 y 25.24 px. El ancho lo decidía la ventana.

## Specs

S1. **Pertenencia sin número mágico.** Cada punto de borde se asigna a la orilla cuyo pico de
Hough le queda más cerca en la dirección normal, midiendo distancia perpendicular
`|x·cosθ + y·sinθ − ρ|`. Es una partición por vecino más cercano (Voronoi) entre las orillas del
par. **Prohibido** introducir una cota de distancia fija en px.

S2. **Las orillas de un trazo son dos picos paralelos.** Dos candidatas de Hough forman par si su
`θ` difiere en menos de `TOLERANCIA_THETA` y sus `ρ` difieren al menos `SEPARACION_MINIMA`. El par
es un trazo; otros picos de la misma θ y `ρ` lejano pertenecen a otro trazo.

S3. **`medir_trazo` no cambia.** Conserva firma y lógica: recibe los puntos de cada orilla del par
y devuelve `MedicionTrazo`. La corrección de signo de las direcciones SVD antes de promediar el
centro se mantiene intacta.

S4. **Test de aceptación.** Imagen sintética con un trazo de orillas a 20.5 px y un segundo trazo
a ~200 px: el ancho reportado es `20.5 ± 0.2` px. Hoy el pipeline devolvería un valor global entre
ambos.

S5. **No regresión.** `hough_lineas` conserva firma y resultado. Si no hay par válido, el camino
actual sigue funcionando sin excepción.

S6. **Modelo puro.** Sin `gi`, `Gtk`, `Gdk`, `Adw` ni `cairo`; sin bucles anidados por píxel.
Identificadores, comentarios y docstrings en español. Tipado en todas las firmas.

## Tasks

| ID | Specs | Qué |
|----|-------|-----|
| T1 | S1, S2, S6 | `Procesamiento/models/pares_orillas.py`: `emparejar_orillas` y `asignar_puntos_a_orillas`, con alias público en `Procesamiento/__init__.py` |
| T2 | S1, S2 | Tests unitarios de emparejamiento y de partición |
| T3 | S3, S5 | Cableado en `main_controller._rama_recta` sobre `puntos_borde`, sin tocar `medir_trazo` |
| T4 | S4 | Test de aceptación con dos trazos sintéticos, tolerancia ±0.2 px |
| T5 | — | Medición real sobre `600mm_Imag0000.bmp` y reporte antes/después |

## Log

L1 (pedido del usuario, verbatim):
> dale del 1 al 4, uno a uno

L2. Punto 1 elegido por el usuario entre cuatro criterios de pertenencia, con los números de
sensibilidad a la ventana a la vista: **«Picos de Hough como orillas (sin número mágico)»** —
«Cada candidata de Hough ya trae sus picos: las dos líneas más fuertes son las orillas. Sin número
mágico y sin recorte. Es la spec de multi-trazo que MEMORY tiene pendiente.»

L3. Referencia MATLAB: `CodigoMatlab/circle_detector.m:138` separa con `separaPuntos` y ajusta cada
orilla con `Linea1` por separado, siempre sobre un recorte (`Xizq(ll)`, `yTop(ll)`). El original no
resuelve la pertenencia: la delega al recorte del operador.

L4. **Hallazgo que cambió el diseño.** `candidatas_lineas` exige `max_dist_px >= 30`
(`_validar_parametros`), así que su agrupamiento **funde las dos orillas** de un trazo de 20.5 px
en una sola candidata (rho 10.25, verificado). El `max_dist_px=5.0` que había puesto el worker
lanzaba `ValueError`, que su `except Exception` convertía en `candidatas = None`: la feature nunca
se ejecutaba. Además su cableado medía con `mas_cercana == i`, o sea una sola orilla. Corregido:
la evidencia de orillas se toma del **perfil de rho** a `theta` fijo (`picos_de_rho`), que es la
columna del acumulador, cuesta O(N) y no depende del agrupamiento. La pertenencia se expresa con
**máscaras booleanas** para no perder la alineación con `gx`/`gy`.

L5. **T5, medición sobre `600mm_Imag0000.bmp` (480×616, 5 684 puntos de borde):**

| | ancho | orillas ajustadas | puntos |
|---|---|---|---|
| Antes (nube completa) | 114.878 px | (352.4, 389.0) | 5 684 |
| Después (par de picos) | 49.390 px | (511.6, 557.9) | 1 289 |
| Baseline del operador (recorte) | 41.80 / 44.03 px | — | — |

Picos de rho medidos: 168, 276, 335, 432, 433, 491, 587, 588. El par elegido para la candidata
principal (`rho=587.5`) fue (491, 587), a **96 px**: implausible como un solo trazo con baseline
~42 px. El mecanismo está validado en el sintético (20.5 px exactos, ±0.2), pero **la elección del
par en la imagen real no está validada** contra la verdad de terreno. Esa es la tarea abierta.
