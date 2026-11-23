# Migración Fase 1: detección de líneas y geometría explícita

Extiende el port Python de ODIN con la capacidad de líneas heredada de `CodigoMatlab/`, y sustituye el selector `geometria` hardcodeado por una decisión explícita con autodetección que falla cerrado.

## Specs

**S1 — Hough de líneas migrado de `houghLines.m`.**
El usuario pidió "iniciaría con la transformada de Hough para líneas". Debe existir un modelo puro que, a partir de un conjunto de puntos de borde, estime rectas candidatas mediante acumulador de Hough en el espacio (ρ, θ) con θ∈[-π/2, π/2] en paso π/360 y ρ cuantizado a 0.5 px. Debe rechazar `percent` fuera del rango [0.6, 0.9] y `maxDistPx` menor a 30, igual que el original.

Cada candidata expone **dos métricas distintas**, porque el original las usa con propósitos distintos y confundirlas cambia el resultado:
- el **conteo de picos agrupados** (`houghLines.m:92,105` → `respuesta(i,3)=p`, con `p=p+1` por pico), que es el criterio de selección del original;
- la **masa del acumulador** sumada sobre las celdas del grupo, que es información de fuerza de evidencia.

Antes de seleccionar, las candidatas se fusionan con `reduce(respuesta, sigma)` donde `sigma = 2.7 · max(DesvStd)` (`houghLines.m:113,115`), tal como hace el original. La función devuelve la candidata con **más picos agrupados**, y ante empate la de mayor masa del acumulador.

`reduce` no es un archivo: es una función anidada dentro de `houghLines.m:153`. El port la reproduce con **dos diferencias**, documentadas bajo el criterio de S7:

- El original ordena por conteo de picos descendente (`:158`) y fusiona *entradas consecutivas en ese orden*, comparando `abs(abs(rho_i) - abs(rho_{i-1})) <= sigma` (`:170`). Ese doble valor absoluto fusiona rectas de `rho` opuesto, que son rectas **distintas** (están en lados opuestos del origen). El port ordena por `rho` y aplica single-linkage sobre `|rho_i - rho_j| <= sigma`, de modo que la partición no depende del orden de las candidatas y no une rectas de signo contrario. Una sola pasada basta porque el single-linkage es transitivo sobre un eje.
- `desviaciones`: el original no la recalcula al fusionar. El port conserva la original cuando el grupo tiene una candidata y usa la desviación muestral de las `rho` fusionadas cuando el grupo tiene varias.

**S2 — Ajuste robusto de recta migrado de `Linea_robusta.m`.**
El usuario pidió "el ajustes robusto de rectas". Debe existir un modelo puro que reciba una recta inicial (punto y cosenos directores) y un conjunto de puntos, y refine la recta podando iterativamente los puntos cuya distancia a la recta supera una cota decreciente desde 20 px hasta 8 px en pasos de 0.1, mientras la fracción de inliers se mantenga por encima de 0.2. Cuando quedan más de 3 inliers, el refit se hace por descomposición en valores singulares (centroide + dirección principal). Devuelve los parámetros de la recta, la dispersión del residual y los puntos conservados.

El **flujo de control del bucle se preserva literalmente**, pero las tres funciones del original contienen defectos de expresión que no se preservan (criterio en S7):

- `EucSpace.m` fijaba `param(1,4) = 1 - param(1,3)^2`, que solo es un coseno director cuando la recta es horizontal o vertical. Para θ intermedio devuelve `cos²θ` en lugar de `cos θ`, y la distancia calculada con ese valor es falsa. El port devuelve `(-sin θ, cos θ)`, unitario y perpendicular a la normal.
- `Linea_robusta.m` calculaba `r` con una partición por coordenada X y `max(pi)`/`max(pd)`, que no mide dispersión. El port define `r` como pico a valle de los residuales de los puntos conservados contra la recta final. **Los valores de `r` de este port no son comparables con los que producía MATLAB.**
- `Linea1.m` devolvía la última candidata repetida, porque `EucSpace` sobrescribía su salida en cada iteración. El port produce un resultado por fila de entrada.

**S3 — `separaPuntos.m` queda postergado.**
El usuario dijo "esperaria con separaPunos.m para ver si realmente es necesario". No se migra en esta fase. Solo se migra cuando exista una tarea que requiera medir ancho en una dirección preferida, porque su único consumidor en `circle_detector.m` es la rama `anchos`.

**S4 — La geometría no se hardcodea.**
El usuario dijo "en el codigo matlab lo hacia hardcodeando la variable geometria. pero no es lo mas correcto" y "hay que considerar que ya sea en la UI o en algun momento como decidir si la imagen corresponde a un circulo o a una linea". La geometría es una entrada explícita del pipeline. La autodetección es un asistente que devuelve la geometría propuesta junto con su confianza y la evidencia que la sustenta, y que por debajo del umbral de confianza no elige: expone ambos candidatos para que el operador decida.

**S5 — `linea.m` no se migra.**
Es código muerto: no se invoca desde ningún punto de `CodigoMatlab/`. No aporta comportamiento que preservar.

**S6 — Aislamiento de la capa de modelo y convenciones del repo.**
Todo modelo nuevo vive en `src/odin/<dominio>/models/` sin importar `gi`, `Gtk`, `Gdk`, `Adw` ni `cairo`, recibe y devuelve `numpy.ndarray` o tipos numéricos nativos, y usa vectorización de NumPy en lugar de bucles por píxel. Identificadores, comentarios y mensajes en español. La exposición al resto del sistema se hace exclusivamente por el alias público del `__init__.py` del dominio.

**S7 — Política de fidelidad: se preserva la conducta, se corrige el defecto demostrable.**
La migración distingue dos casos y no los confunde:

1. **Conducta** — flujo de control, criterios de selección y desempate, orden de salida, tolerancias y cardinalidad de los resultados — se preserva tal cual, aunque parezca arbitraria. Así se resolvió L7: el original ordena por conteo de picos y no por masa del acumulador, y se replicó.
2. **Defecto demostrable** — una expresión que no hace lo que su nombre o su variable declara, o cuya salida se destruye por aliasing — se corrige, se documenta en la `S#` que la contiene y se asume que sus números dejan de ser comparables con MATLAB.

Toda corrección del caso 2 debe venir acompañada de la prueba de que el caso 1 se conservó: la verificación de fidelidad cubre el flujo de control, no los valores corregidos.

## Tasks

| ID | Specs | Ruta | Estado | Commit |
|----|-------|------|--------|--------|
| T1 | S1, S6, S7 | `src/odin/Procesamiento/models/hough_lineas.py` + tests | hecho | `be90572` |
| T2 | S2, S5, S6, S7 | `src/odin/Ajustes/models/linea_robusta.py` + tests | hecho | `aac7292` |
| T3 | S6 | Aliases en `Procesamiento/__init__.py`, `Ajustes/__init__.py` y registro en `bootstrap.py` | hecho | `f4f4c8a` |
| T4 | S4 | `Procesamiento/models/geometria.py` — clasificador puro con evidencia | pendiente | — |
| T5 | S4 | Selector explícito en controlador y vista; retiro del supuesto círculo-only | pendiente | — |

## Log
**L1** (usuario, 2026-11-20): "Este proyecto es la migración de un antiguo codigo que tenia de Matlab a Python. Agregue al repo la carpeta CodigoMatlab. Ya hemos realizado la migración y optimizacion de varias etapas de ese codigo. como siguiente paso quiero que analices lo que hay en la carpeta CodigoMatlab para ver que falta de migrar. Circle_detector era mi codigo principal. vamos a proponer como continuar con la migración"

**L2** (usuario, 2026-11-20): "vamos con la Fase 1. Sin embargo, esperaria con separaPunos.m para ver si realmente es necesario e iniciaria con la transformada de Hough para líneas y el ajustes robusto de rectas." — la sesión se interrumpió leyendo `houghLines.m` y `Linea_robusta.m` sin producir plan ni código.

**L3** (usuario, 2026-11-21): "Revisala y analizala de nuevo. creo que no termino en su momento. y hay que considerar que ya sea en la UI o en algun momento como decidir si la imagen corresponde a un circulo o a una linea, en el codigo matlab lo hacia hardcodeando la variable geometria. pero no es lo mas correcto. Propon delega si es necesario"

**L4** (usuario, 2026-11-21): "No olvides TDD, ODD, RDD, si es necesario"

**L5** (decisión del usuario, 2026-11-21): ante las cuatro alternativas de decisión de geometría, eligió "Híbrido: selector explícito + autodetección sugerida que falla cerrado" — el operador elige la geometría; el clasificador propone con confianza y evidencia; bajo el umbral no adivina y muestra ambos candidatos.

**L6** (hallazgo, 2026-11-21): `AGENTS.md` §4 y §8 documentan `Procesamiento/models/strategies/base_strategy.py`, que no existe en el repositorio. **Decisión del usuario (2026-11-21): el archivo debe existir; no se modifica `AGENTS.md`.** Su propósito inicial es alojar otros métodos de detección como Zernike. Las tareas T1/T2 no lo necesitan: operan aguas abajo de la detección de bordes y consumen puntos ya detectados.

**L7** (corrección de fidelidad, 2026-11-21): al cerrar T1 se detectó que `houghLines.m:114` aplica `reduce(respuesta, sigma)` con `sigma=2.7·max(DesvStd)` antes de elegir el máximo, y que `houghLines.m:117` (`[M,I]=max(detected0(:,3))`) ordena por el **conteo de picos** `p`, no por la masa del acumulador. S1 se reescribió para nombrar ambas métricas, exigir la fusión `reduce` y fijar el criterio de orden. El código de T1 se ajustó en consecuencia.

**L8** (reporte de T2, 2026-11-21): T2 entregó `linea_robusta.py` con `dist_p_recta`, `euc_space`, `linea_mc`, `linea_robusta` y el wrapper `linea1`, más 47 tests (39 de comportamiento + 8 suites Hypothesis). RED observado: `ModuleNotFoundError` (exit 2). GREEN: `47 passed in 0.60s`. La suite `tests/unit/Ajustes` queda en `100 passed, 1 skipped`; el skip es preexistente (`test_etapa9_imagen_real.py:80`, requiere `ODIN_TEST_LENTO=1`). Fidelidad del bucle verificada contra una transcripción literal de `Linea_robusta.m` sobre 5.359 configuraciones aleatorias, 0 discrepancias en `param` y sobrevivientes.

T2 introduce **tres desviaciones deliberadas** de `EucSpace.m`, `Linea_robusta.m` y `Linea1.m` (ver S2). Verificadas por el orquestador: `(-sin θ, cos θ)` es unitario y perpendicular a la normal, mientras que `1 - cos²θ` solo coincide con `cos θ` en θ=0 y θ=±π/2, es decir en rectas horizontales y verticales — el caso que aparece en cualquier imagen de prueba de Hough. Al chocar con el criterio de fidelidad con que se reabrió T1, se añade **S7** para dejar explícito cuándo se preserva la conducta y cuándo se corrige un defecto, de modo que la migración no acumule dos políticas contradictorias.

**L9** (reporte de T1, cierre, 2026-11-21): T1 cerró las dos brechas de L7 y convirtió el retorno múltiple a `CandidatasLineas`, un `@dataclass(frozen=True, slots=True)` con campos `rhos, thetas, conteos, masas, desviaciones`. RED observado en ambos bloques: el primero por `ImportError: cannot import name 'reducir_candidatas'` (2 errores de colección), el segundo por la ausencia de la API nueva. GREEN: `41 passed` en los tests de la etapa ⑩ y `128 passed` en `tests/unit/Procesamiento`. Verificado por el orquestador: `228 passed, 1 skipped` en `Procesamiento` + `Ajustes`; el dataclass es frozen y slotted, rechaza asignación con `FrozenInstanceError`, y la ruta de retorno anticipado de `reducir_candidatas` también devuelve el dataclass.

Hallazgo del worker que corrige la lectura anterior: **`CodigoMatlab/reduce.m` no existe**; `reduce` es una función anidada en `houghLines.m:153`. Confirmado en el fuente: `sigma=max(DesvStd)*2.7` en `:113`, el orden por `detected0(:,3)` (conteo de picos) en `:158`, y la condición `abs(abs(...)-abs(...)) <= DistPx` en `:170`. S1 se amplió con las **dos desviaciones deliberadas** de la fusión (criterio de proximidad sobre `rho` firmado, y recálculo de `desviaciones`), que el worker había documentado solo en el docstring del módulo.

**L10** (cierre de T1 y T2, 2026-11-21): ambos ports commiteados en `feat/migracion-lineas-geometria` — `be90572` (Hough de líneas, 1069 líneas), `aac7292` (ajuste robusto, 833 líneas) y `3927e82` (este documento y `.gitignore`). **Las rebanadas superan el presupuesto de ~400 líneas**: quedan como dos slices de trabajo autocontenidos (modelo + sus tests, sin mezclar dominios); la forma de entrega se decide al publicar.

GGA actúa como pre-commit hook y en T2 rechazó cuatro hallazgos. Se corrigieron dos, de anotaciones faltantes en helpers de test (`_recta`, `_inliers_con_outliers`, `_param_de_recta`). Se **rechazaron con evidencia** los otros dos, que exigían importar por el alias del dominio en vez de por el módulo: todos los tests preexistentes del repo importan directo (`from src.odin.Procesamiento.models import non_max_sup as NMS`, `from src.odin.Ajustes.models.circulo_simple import Circulo_simple`), GGA aprobó T1 con ese mismo patrón, y el alias que exige recién lo crea T3. Además `.gga` vive gitignorado: su fix es configuración local y no entra al repositorio.

**L11** (cierre de T3, 2026-11-21): las etapas ⑩ y ⑪ se exponen por la cadena `models/__init__.py` → `dominio/__init__.py` y entran en `PREPROCESAMIENTO_SUITE_ORDER` de `bootstrap.py` como `HoughLineas` y `LineaRobusta`. RED observado con tres fallas: `ImportError: cannot import name 'CandidatasLineas' from 'src.odin.Procesamiento'`, lo mismo con `dist_p_recta` en `Ajustes`, y `AssertionError` del registro de arranque. GREEN: `3 passed`.

Tocar el registro **rompió 3 tests de integración** de `tests/integration/test_bootstrap_arranque.py`, que fijan `ALIASES_ESPERADOS` con las 8 etapas originales. La lista es escrita a mano a propósito — derivarla del código haría que el test se comparara contra sí mismo. Se amplió a 10 entradas conservando la igualdad y el orden exactos; no se debilitó ningún assert. Suite completa: **278 passed, 1 skipped**.
