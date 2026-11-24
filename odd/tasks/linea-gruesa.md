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
| T1 | S1 | `Procesamiento/models/geometria.py` + `tests/unit/Procesamiento/test_geometria.py` | hecho | `18d2d1f` |
| T2 | S2, S3, S5 | `Ajustes/models/trazo_linea.py` + `tests/unit/Ajustes/test_trazo_linea.py` (+ prop) | hecho | `93d9ba7` |
| T3 | S2, S4 | `main_controller.py` (`_rama_recta`), alias en `Ajustes/__init__.py` + `models/__init__.py`, vista, test de integración | hecho | `e0ab4f3` |
| T4 | verificación | `bootstrap.py` (`_resolve_base_path`) + `tests/integration/test_bootstrap_arranque.py` | hecho | `d584740` |

**Estado: cerrada** (2026-11-23). Verificación funcional en contenedor completada; ver L10-L12.

## Log
**L1** (usuario): "Tarea 1: corregir el criterio de línea del clasificador. Causa en src/odin/Procesamiento/models/geometria.py: residual_recta = median(|centrado @ normal|) mide distancia al eje principal, y una línea gruesa tiene DOS orillas, así que da ≈ medio ancho. Medido: 26.848px en recorte limpio contra 8.028px reales del ajuste forzado. Arreglo propuesto: medir contra una banda, no contra una recta de grosor cero: median(||signed| - median(|signed|)|). Ojo: un test con dos líneas paralelas perfectas YA pasa en verde (el círculo resulta inadmisible y el residual va a inf). El caso que falla necesita orillas imperfectas. Pedime los puntos reales o acordamos una banda sintética con ruido antes de escribir el test."

**L2** (usuario): "antes de lanzar nada. debemos aclarar algo. La tarea del detector es buscar bordes para en ellos encontrar rectas, despues con el par de rectas que correspondan a la línea gruesa se estima el ancho y centro del trazo (Línea gruesa). Espero haberme explicado"

**L3** (usuario): "Habria que verificar en el codiogo de matlab que se hacia. Si no me equivoco se usaba separa puntos para tratar de identificar las nubes de puntos correspondientes a cada lado del trazo (sus dos orillas) y con dibuja y anchos busca las lineas con Hough y ajusta con linea1 y luego el if (anchos). Asi se hacia aunque se aceptan sugerencias para optimizarlo"

**L4** (decisión del usuario): alcance **A + B** — (A) fix del criterio de banda para el ruteo; (B) port optimizado de `separaPuntos` con dos rectas y ancho/centro.

**L5** (duda del usuario y resolución): "solo me queda la duda de si con los puntos obtenidos de la linea central ajustas una tercer recta?" — No: no hay puntos en la línea central; el centro es la recta media de las dos orillas (S4).

**L6** (alcance, usuario): "Estas considerando que si proceso la imagen completa en el caso de la 600mm_imag hay 2 trazos viables por encontrar" → "Puede ser ahora por recorte, sin embargo, si se procesa la imagen completa no es solo un trazo." Decisión: **esta tarea mide UN trazo por recorte** (como MATLAB `rta='r'`). `medir_trazo` separa sobre los puntos cercanos a la línea candidata (ρ, θ), dejándolo preparado para iterar sobre todas las candidatas de `candidatas_lineas`. **Multi-trazo en imagen completa queda como tarea aparte.**

**L7** (cierre de T1, 2026-11-23): criterio de banda implementado en `geometria.py`. RED observado: 2 fallas (`test_residual_recta_es_la_mediana_no_la_media` y `test_linea_gruesa_de_dos_orillas_clasifica_recta`). GREEN: suite completa `358 passed, 1 skipped`. Commit `18d2d1f`.

**L8** (T2, 2026-11-23): `trazo_linea.py` entregado por `gentle-ai-worker` (`separar_orillas`, `medir_trazo`, `MedicionTrazo`) con 19 tests (17 unit + 2 Hypothesis). Endurecimiento del orquestador: alinear el signo de las direcciones SVD antes de promediar el centro, para que no se cancelen a (0,0) si salen opuestas. Commit `93d9ba7`.

**L9** (T3, 2026-11-23): `medir_trazo` integrado en `_rama_recta` (mide ancho+centro del trazo grueso; fallback a línea única si `medir_trazo` devuelve `None`). Corrección del worker detectada por el orquestador: (1) el import de `medir_trazo` estaba dentro del método y el test mockeaba `src.odin.Ajustes` en vez de `main_controller`, por el doble import `odin` vs `src.odin` → los tests pasaban en vacío; (2) la conversión rho/theta del centro usaba convención de dirección en vez de Hough. Ambos corregidos: import a nivel de módulo, `rho = x0*dy − y0*dx` y `theta = atan2(−dx, dy)`, y aserciones firmes. Suite completa: 379 passed, 1 skipped. Commit `e0ab4f3`.

**L10** (verificación en contenedor, 2026-11-23): la app se ejecutó en el contenedor `vsc-odin` vía WSLg (backend `GdkWaylandDisplay`, 11 módulos OK). Bloqueo encontrado: `open_dialog` abría en `/root` porque `_resolve_base_path` no conocía el montaje del devcontainer. Fix **T4**: `/workspaces/ODIN` se agrega como segundo candidato de la cascada, antes de `/home/<usuario>`. RED con `test_base_path_prefiere_workspace_odin_cuando_existe`; GREEN `tests/integration/test_bootstrap_arranque.py` 32 passed, suite completa 380 passed, 1 skipped. Commit `d584740`. Log verificado en vivo: `Entorno: DOCKER, base_path: /workspaces/ODIN`.

**L11** (resultado funcional sobre imagen real, 2026-11-23): imagen `600mm_Imag0000.bmp`, dos trazos verticales del mismo patrón medidos por recorte.

| Trazo | Modo | Ancho | Centro (ρ, θ) | Residual recta | Residual círculo | Confianza |
|---|---|---|---|---|---|---|
| 1º | automático | 41.80 px | 59.6 px, −0.030 rad | 4.384 px | `inf` | 1.000 |
| 2º | recta forzada | 44.03 px | 87.0 px, 0.102 rad | — | — | — |

Lectura correcta de la convención: `theta` es el ángulo de la **normal**; la dirección de la recta es `(−sin θ, cos θ)`, así que `θ ≈ 0` ⇒ trazo **vertical**. El ancho es la separación entre las dos orillas (izquierda/derecha). Ambos trazos verticales, anchos coherentes entre sí (41.80 vs 44.03 px) y centros separados ~27.4 px. La S1 y la S2 quedan verificadas de punta a punta.

**L12** (deuda y forma de entrega, 2026-11-23): la rama `feat/linea-gruesa` arrastra ~7889 líneas autoradas en 36 commits desde `origin/main`, muy por encima del slice de ~400 líneas, porque nace sobre `feat/fase1-d-selector` (fase 1 aún no mergeada). Al publicar hay que decidir la forma: plegar el fix del clasificador en el PR #27 existente o abrir un PR nuevo apuntado a la rama de fase 1. **Pendiente de decisión del usuario.**

**L13** (defecto colateral observado, 2026-11-23): el `print` de `handleImage.py:196` reporta dimensiones del recorte que no coinciden con la imagen efectivamente procesada (recorte pedido 15×38 px, imagen procesada 396×157). Es deuda preexistente, ajena a esta tarea; no se tocó.

**L14** (entrega, 2026-11-23): publicada como **4º eslabón de la cadena**, no como PR contra `main`. Forma elegida y por qué: plegar en #27 es inválido (su head es `feat/fase1-c-clasificador` y la integración de T3 depende del selector de `fase1-d`) y un PR contra `main` mostraría los ~7907 líneas duplicando #27/#28. Diff real del slice contra su base: **867 inserciones / 20 borrados en 13 archivos**. RDD `assess` del rango commiteado: riesgo `medium`, `reviewDue: false` (under_budget), plan de autoverificación del escritor + readback estructural (ejecutado: los 6 commits contienen solo los archivos esperados). **PR #30** (GitHub) y **PR #17** (Azure), ambos con base `feat/fase1-d-selector`. Orden de merge de la cadena: #27 → re-apuntar #28 a `main` → #28 → re-apuntar #30 a `main` → #30, **sin borrar ramas**.
