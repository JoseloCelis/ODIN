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

S9. **Una franja es trazo si su interior se aparta de la intensidad del fondo.** La evidencia de
Hough mide alineación, no intensidad, así que **no** distingue una franja oscura de una clara; en
`600mm` todos los pares consecutivos de orillas son franjas (L14). Criterio: la intensidad mediana
del interior de cada par —muestreada sobre la línea media entre sus dos orillas, en las posiciones
que ocupan los puntos asignados a ese par— se compara con la intensidad mediana de la escena, que
es el fondo. Es trazo la familia de franjas cuyo interior **más** se aparta de ese fondo —la familia
se identifica por su miembro más contrastado— y dentro de ella manda la evidencia (S8).
**La polaridad se deriva de la imagen, no se supone:** «a veces pudiera ser invertido», trazo claro
sobre fondo oscuro, y el criterio debe elegir la franja clara sin intervención del operador. Si
ninguna franja se aparta del fondo el criterio se abstiene y se conserva el par de mayor evidencia,
porque entonces no hay base para descartar a Hough (S5).

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
| T6 | S9 | `intensidad_interior` y `seleccionar_trazo_por_intensidad` en `pares_orillas.py`, cableadas en `_rama_recta`; `intensidad_interior` y `seleccionar_trazo_por_intensidad` como alias públicos |
| T7 | S9 | Tests de la selección por intensidad: franja oscura contra franja de más evidencia, polaridad invertida, abstención y ausencia de pares |
| T8 | S9, S8 | Verificación real en las cuatro imágenes: `600mm` vuelve a 58.4 px y las `HL3` se mantienen |

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

L12. **La semianchura deja de ser solo ventana y pasa a medir el desenfoque.** `picos_de_rho`
devuelve la semianchura a media altura del pico fusionado (regiones contiguas se funden antes de
calcularla). Con eso cumple dos funciones a la vez: ventana de pertenencia (S7) y barra de error del
ancho. Medición sobre cuatro imágenes, rama `feat/trazo-por-picos-hough`, **cambios sin commitear**:

| Imagen | Orillas | Semianchura | Ancho |
|---|---|---|---|
| `500mm` | 1351.96 / 1389.01 | 2.54 / 4.01 px | 36.96 px |
| `600mm` | 276.23 / 334.78 | 0.77 / 0.78 px | 58.37 px |
| `HL3-0000` | — | 1.74 / 1.93 px | 172.33 · 173.13 px |
| `HL3-0047` | — | 1.72 / 1.76 px | 172.28 · 173.17 px |

Efecto sobre el ruido de picos: `500mm` de diez orillas a dos; `HL3-0047` de diez picos a cinco;
`600mm` de ocho a seis.

L13. **El desacuerdo de la 500 mm no era error del algoritmo, era el dato.** Perfil de energía de
gradiente por columna, calculado **independiente de Hough**: hay un lomo centrado en 1352 y el
segundo sube hasta 1389, o sea **37 px entre los puntos de inflexión de las dos rampas**, no los
27 px leídos a ojo. En una rampa sin inflexión única la «orilla» depende del umbral elegido;
semianchuras de 2.5 y 4.01 px son exactamente esa incertidumbre. El resultado correcto es un
número con su barra de error, no un número solo.

L14. **Regresión introducida y no entregada: la fusión de regiones cambia los pesos de evidencia.**
En `600mm` el par `(490.97, 587.53)` sube a **96.69 px** y desplaza al trazo real de **58.37 px**
del primer lugar por evidencia; antes de este cambio el trazo ganaba con **457 votos**. La causa es
estructural: en esa imagen la secuencia de bordes es `276 · 335 · 432 · 491 · 587` y **todos** los
pares consecutivos son franjas — `276/335` y `432/491` son las franjas oscuras (los trazos),
`335/432` y `491/587` las claras intermedias. La evidencia de Hough no las distingue porque **no
mira la intensidad**. Por eso el árbol queda sin commitear: el cambio mejora la detección y empeora
la selección (S8).

L15. **Criterio de selección identificado, NO implementado: franja oscura.** Una franja es trazo si
su interior es más oscuro que su exterior. Exige la imagen dentro del criterio, lo que implica
pasar la imagen a `_rama_recta` (hoy recibe `DetectedEdges, Gx, Gy, MG, puntos_borde, plan`), tocar
el modelo y añadir tests. Debe escribirse como spec nueva (**S9 pendiente de confirmación del
usuario**) antes de tocar código: el criterio es decisión, no implementación.

L16. **Orden de retomada, fijado por el usuario:** (1) selección por franja oscura con la imagen;
(2) verificar que la `600mm` vuelve a 58.4 px y que las `HL3` se mantienen; (3) commit y
actualización de los PR. Estado de verificación al detenerse: **194 tests verdes en `Procesamiento`**
y solo la falla preexistente del punto 3 (`test_geometria_prop.py`).

L17. **Decisión del usuario (autoritativa): la imagen entra en el criterio.** «A veces pudiera ser
invertido». Retira la propuesta de derivar la polaridad solo de `Gx`/`Gy`: el signo del gradiente
separa las dos familias de franjas (proyecciones convergentes = franja oscura, divergentes = franja
clara) pero **no dice cuál familia es el trazo** cuando la imagen llega con polaridad invertida
(trazo claro sobre fondo oscuro). Por eso `_rama_recta` recibe la imagen y el criterio se evalúa
sobre intensidades, no sobre signos. Orden de retomada confirmado por el usuario:
(1) selección por franja oscura con la imagen; (2) verificar que `600mm` vuelve a 58.4 px y que las
`HL3` se mantienen; (3) commit y actualización de los PR.

L18. **S9 implementada, verificada y con la firma intacta.** Decisión del usuario (3 opciones
ofrecidas): **polaridad derivada de la imagen**, no supuesta ni declarada por el operador. Corrige L15
en un punto importante: **no hizo falta cambiar la firma de `_rama_recta`** — la imagen en escala de
gris ya está en `self.current_image`, la misma matriz de la que salen `Gx`, `Gy` y `MG`, así que el
criterio la lee de ahí y no se toca ningún contrato compartido.

Implementación: `intensidad_interior` mide la mediana de la intensidad sobre la **línea media** del
par (`rho` promedio), muestreada bilinealmente en las posiciones `t` de los puntos que el par tiene
asignados — el muestreo no inventa posiciones ni cotas, usa las del dato. `seleccionar_trazo_por_intensidad`
compara esa mediana con la mediana de la escena (el fondo), agrupa las franjas por el lado del fondo en
que caen, identifica cada familia por su miembro más contrastado y gana la que más se aparta; dentro de
ella manda la evidencia (S8). Si ninguna franja se aparta del fondo, se abstiene y el llamador conserva
el par de mayor evidencia: no hay base para descartar Hough.

TDD: 4 tests en `tests/unit/Procesamiento/test_trazo_por_picos.py`, RED observado primero como
`ImportError` del símbolo inexistente. Suite: **438 passed, 1 skipped, 1 falla preexistente**
(`test_geometria_prop.py`, punto 3).

Verificación real (paso 2 del orden), medición headless sobre las cuatro imágenes:

| Imagen | Antes (evidencia) | Ahora (S9) | Veredicto |
|---|---|---|---|
| `600mm` | par (490.97, 587.53) → **96.69 px** | par (432.49, 490.97) → **58.37 px** | arreglado |
| `500mm` | par (1351.96, 1389.01) → 36.96 px | idéntico | se mantiene |
| `HL3-0000` | par (70.28, 242.29) → 172.33 px | idéntico | se mantiene |
| `HL3-0047` | par (1815.78, 1988.74) → 173.17 px | idéntico | se mantiene |

En `600mm` la familia elegida es la oscura y dentro de ella gana el segundo trazo por evidencia
(1030 contra 819 del primero): mide **58.37 px**, el mismo ancho que el par (276.23, 334.78) de la
tabla de L12 porque los dos trazos son simétricos. Las orillas ajustadas caen en 432.49 y 490.97,
contra la verdad de terreno 432 y 490.

L19. **Entrega elegida por el usuario: PRs encadenados, no un PR de 1600 líneas.** Tres eslabones, cada
uno verde y revisable por separado; los cortes se hicieron sobre commits ya existentes, sin reescribir
historia publicada:

| Eslabón | Rama | Cabeza | Contenido | Tamaño |
|---|---|---|---|---|
| L1 | `feat/trazo-orillas-picos` | `e9b705a` | orillas por picos + medición real + validación (T1-T5) | 779 líneas |
| L2 | `feat/trazo-propiedades` | `815d2d6` | propiedades de Hypothesis (T2) | 191 líneas |
| L3 | `feat/trazo-por-picos-hough` | `87acfa9` | semianchura + selección por intensidad (T6-T8) | 476 líneas |

`e9b705a` va en L1 y no en L2 a propósito: corrige el cableado que hacía que la feature **nunca se
ejecutara** (`max_dist_px=5.0` lanzaba `ValueError` y el `except` lo convertía en «sin candidatas»).
Un eslabón que pasa tests sin ejecutar la feature no es revisable, y era el riesgo real de cortar por
fecha de commit en vez de por unidad de comportamiento.

Estado por remoto: **Azure completo** — PR **27** (`feat/trazo-orillas-picos` → `main`), PR **28**
(`feat/trazo-propiedades` → `feat/trazo-orillas-picos`), PR **26** re-apuntado a
`feat/trazo-propiedades` y retitulado. **GitHub pendiente**: la creación y el re-apuntado de PR están
caídos por una indisponibilidad mayor del servicio (`Pull Requests major_outage` en la status page),
no por permisos ni por contenido. Pendiente allí: crear los PR de L1 (base `main`) y L2 (base
`feat/trazo-orillas-picos`) y re-apuntar el **#41** a `feat/trazo-propiedades`.

L20. **Segunda falla preexistente descubierta al verificar los cortes.** Además de
`test_geometria_prop.py::test_prop_invariancia_rotacion_y_reflexion`, falla
`tests/integration/test_bootstrap_arranque.py::TestPropiedadesCorreccion::test_propiedad_1_formato_canonico_log`:
`bootstrap.py:97` trunca los mensajes de nivel `WARNING` a `MAX_WARN_LEN = 200` y la propiedad P1 exige
la forma exacta `[ODIN] fase | nivel | mensaje`. La propiedad y el truncado de R5.3 se contradicen.
Verificado que falla igual en `azure/main` (`1793861`), así que no viene de esta rama. Apareció al
repetir la suite porque Hypothesis guarda el ejemplo falsador en su base de datos: desde entonces falla
siempre en esta máquina. Deuda abierta, ajena a los tres eslabones.

L21. **Cadena mergeada en Azure (2026-11-25), en orden y sin borrar ramas.** PR **27** (`6f7fdd0`), luego
PR **28** re-apuntado a `main` (`3d18075`), luego PR **26** re-apuntado a `main` (`21cf36a`). Cada hijo se
re-apuntó **después** de que su base entrara: sin eso el merge aterriza en la rama intermedia y `main` no
recibe el contenido (lección ya pagada en esta cadena, ahora aplicada a propósito). Ninguna rama borrada.

Verificación por contenido, no por estado del PR: en un worktree limpio de `azure/main` (`21cf36a`) la
suite da **435 passed, 5 skipped, 0 fallas**, `pares_orillas.py` contiene `seleccionar_trazo_por_intensidad`,
`test_pares_orillas_prop.py` está presente y el log llega hasta L21.

L22. **Refinamiento de L20: las dos fallas no son deterministas, dependen de la base de ejemplos de
Hypothesis.** En el worktree limpio **no fallan**; en el repo local sí, porque Hypothesis guarda el ejemplo
falsador en `.hypothesis/` y lo reproduce al inicio de cada corrida. No es «una falla de `main`» en sentido
estricto: es una violación de propiedad real que solo se manifiesta cuando el generador produce el caso. La
del log es la más sólida de las dos y **volverá a aparecer** en cuanto se genere un mensaje `WARNING` de más
de 200 caracteres, porque la propiedad P1 exige la forma exacta y `bootstrap.py:97` trunca. Consignar
«1 falla preexistente» o «2» sin decir en qué entorno se midió es impreciso; decir el entorno es parte del dato.
