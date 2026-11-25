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

S7. **Nada constante sobre los trazos.** Los anchos cambian entre trazos de una misma imagen y
entre imágenes: el número de trazos, sus anchos y su separación son datos, no supuestos. Prohibido
cualquier valor fijo en px, cualquier cantidad esperada de trazos y cualquier igualdad entre ellos.
La ventana de pertenencia sale del propio pico (su semianchura a media altura), con un piso de un
bin del acumulador, que es la resolución del dato y no una cota elegida.

S8. **Trazo principal = par de mayor evidencia.** Se mide el par con más votos sumados, que es el
mismo criterio relativo de Hough. Anclar en la candidata principal de `hough_lineas` es incorrecto:
esa candidata puede ser el borde exterior de la zona clara y no una orilla de trazo.

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

L6. **T5 validado con la verdad de terreno de la imagen.** El perfil de intensidad por columna
confirma que los picos de Hough **son** las orillas reales: los saltos fuertes de intensidad caen
exactamente en 168, 276, 335, 432, 491 y 587. La imagen tiene tres bandas claras separadas por
huecos oscuros:

| Banda | Columnas | Ancho |
|---|---|---|
| 1 | 168 → 276 | 108 px |
| 2 | 335 → 432 | 97 px |
| 3 | 491 → 587 | 96 px |

Huecos: 276→335 y 432→491 (59 px cada uno). Por tanto **el par (491, 587) sí es un trazo** y su
ancho verdadero es **96 px**, no 42. La baseline de 41.80/44.03 px del operador no corresponde al
ancho de banda: mide otra magnitud (probablemente el rim brillante interno, con un pico local de
188.6 en x=170 contra ~135 del resto de la banda).

**El defecto restante no es el emparejamiento sino la pertenencia.** Con el par correcto, las
máscaras reparten los puntos en el punto medio (539): orilla A cubre x∈[462, 539] (693 puntos, de
los cuales 474 sí están en el borde 491) y orilla B x∈[539, 587.5] (596 puntos, de los cuales 189
sí están en 587). El resto son bordes espurios de textura **dentro** de la banda, que la partición
de Voronoi no puede rechazar porque no hay otro pico cerca. `medir_trazo` ajusta entonces en
511.6 y 557.9 en lugar de 491 y 587, y reporta 49.390 px en vez de 96.

**Corrección propuesta (pendiente de autorización):** acotar la pertenencia al ancho del propio
pico — la semianchura a media altura (HWHM) del perfil de rho que sostiene a esa orilla. Es
s data-driven, no un número en px: un borde nítido tiene HWHM de 1-2 px y uno inclinado se ensancha
solo; cumple S1 sin introducir una cota fija.

L7. **Verdad de terreno corregida por el usuario (autoritativa).** Los trazos son las franjas
**oscuras**; el fondo claro lo confundí con el trazo en L6. Anchos reales, medidos a ojo sobre la
imagen a resolución de píxel:

| Trazo | Orilla izquierda | Orilla derecha | Ancho |
|---|---|---|---|
| 1.º | 276 px | 334 px | 58 px |
| 2.º | 432 px | 490 px | 58 px |

Los picos 168 y 587/588 **no son orillas de trazo**: son los bordes exteriores de las zonas claras.
El "rim" de L6 queda retirado como explicación.

L8. **El defecto es anterior a esta feature.** Con el par correcto (276, 335) —el de mayor
evidencia, 457— `medir_trazo` devuelve 41.97 px y ajusta las orillas en 303.6 y 322.3, o sea dentro
de la franja. La baseline de 41.80 px está a 0.17 px de ese valor: el pipeline ya venía midiendo
~42 px donde el trazo mide 58. La ventana de `separar_orillas`/`medir_trazo` nunca llegó al borde.

L9. **Dos correcciones necesarias, en este orden:** (1) elegir el par por evidencia y no anclando
en la candidata principal de `hough_lineas`, que puede ser un borde exterior; (2) acotar la
pertenencia al ancho del pico (HWHM) para que cada máscara sea una orilla fina y no media franja.
Sin (2), `medir_trazo` converge al centro de masa de la media franja.

L10. **Hipótesis abierta del usuario:** analizar la inversión de tonos de la imagen. Relevante
porque `separar_orillas` separa por signo del gradiente y los trazos oscuros sobre fondo claro
pueden invertir qué orilla cae en cada grupo; conviene verificarlo antes de tocar la ventana.

L11. **Corregido y medido.** (1) El par se elige por evidencia; (2) la pertenencia se acota con la
semianchura a media altura de cada pico (`picos_de_rho` la devuelve, `asignar_puntos_a_orillas` la
aplica). No hay bug de polaridad: en el trazo oscuro la orilla 276 cae en el grupo B y la 335 en el
A, que es el orden esperado y simétrico para el ancho.

| Par (rho) | Ancho medido | Orillas ajustadas | Verdad de terreno |
|---|---|---|---|
| (276, 335) — 1.º | **58.77 px** | 276.0 / 334.7 | 276 / 334 (58 px) |
| (432, 491) — 2.º | **58.91 px** | 432.1 / 491.0 | 432 / 490 (58 px) |
| (433, 491) | 58.02 px | 432.9 / 491.0 | 432 / 490 |
| nube completa (antes) | 114.878 px | 352.4 / 389.0 | — |

Las ocho semianchuras medidas son de un bin (0.50 px) porque las orillas de esta imagen son nítidas
de un solo píxel; en un borde inclinado o desenfocado crecen solas, y hay test que lo fija.

**Retirado:** la hipótesis de invertir los tonos no hace falta. Verificado sobre `separar_orillas`:
la separación por signo del gradiente ya asigna correctamente las dos orillas de un trazo oscuro
sobre fondo claro.
