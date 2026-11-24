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
| T6 | L6 | `Procesamiento/models/strategies/base_strategy.py` — contrato de estrategia | hecho | `115b3bc` |

### T4 — criterios de diseño del clasificador

Decisión del orquestador (2026-11-21). S4 fija el contrato —geometría propuesta con confianza, evidencia, y falla cerrado bajo el umbral— pero no el criterio de decisión. Sin criterio explícito el worker tendría que inventar el algoritmo, contra la regla de cero adivinación.

Contrato: `Geometria` (enumeración `CIRCULO`/`RECTA`) y `EvidenciaGeometria` (`@dataclass(frozen=True, slots=True)`) con `geometria`, `confianza`, `candidatos`, `residual_recta`, `residual_circulo`, `cobertura_angular`, `radio` y `detalle`. Función `clasificar_geometria(puntos, *, umbral_confianza=0.75, tolerancia_px=2.0, factor_radio_max=4.0) -> EvidenciaGeometria`.

1. **Residuales por mediana.** Recta por PCA/SVD; círculo por ajuste algebraico consumido por el alias público del dominio. La mediana, no la media, para que un puñado de puntos sueltos no decida.
2. **Admisibilidad del círculo.** Si `radio > factor_radio_max · extensión` o el radio no es finito, el residual del círculo pasa a `inf`. Sin este paso toda recta es un círculo de radio enorme y el clasificador elige círculo siempre.
3. **Confianza.** `(peor - mejor) / peor`, con `1.0` cuando `peor` es infinito y `0.0` cuando ambos lo son. Queda en `[0,1]` por construcción, es `0` cuando las dos hipótesis ajustan igual, y crece al mejorar el ganador.
4. **Falla cerrado.** `confianza < umbral` ⇒ `geometria=None` y `candidatos=(CIRCULO, RECTA)`.
5. **Degenerados no lanzan.** Menos de 3 puntos, valores no finitos, duplicados, o una extensión que no supera `tolerancia_px`, devuelven confianza `0` con ambos candidatos. **La colinealidad exacta no es una degeneración:** es la evidencia más limpia de una recta, y el criterio 2 ya la resuelve al dejar el círculo sin radio admisible.

Semántica ratificada tras la implementación (las cuatro cosas que el bloque dejaba abiertas):

- `extensión` es la diagonal de la caja envolvente medida en el marco de componentes principales, para que la admisibilidad del círculo sea invariante ante rotación y reflexión.
- `tolerancia_px` es la **extensión mínima clasificable**: un conjunto confinado a menos de esa distancia no tiene geometría determinable, así que cae en el criterio 5.
- `candidatos` es `(geometria,)` cuando el clasificador decide y `(CIRCULO, RECTA)` cuando falla cerrado. Un operador que lee un solo candidato sabe que hubo decisión.
- `detalle` es un texto en español legible por el operador, no un diccionario de números: los números ya están en los campos tipados.

Propiedades de Hypothesis exigidas: confianza en `[0,1]`; invariancia ante rotación y reflexión rígidas; nunca lanza en entradas degeneradas; monotonicidad del ganador; y falla cerrado como invariante.

### T5 — criterios de diseño del selector

Decisión del orquestador (2026-11-21), con autorización explícita del usuario para modificar código existente. S4 fija la política (selector explícito + autodetección que falla cerrado) pero no el contrato del pipeline ni de la vista.

1. **La geometría es una entrada explícita.** El pipeline recibe `geometria` y, cuando el operador la fija, la obedece sin consultar al clasificador.
2. **Automático consulta, no adivina.** Cuando la geometría no está fijada, se consulta `clasificar_geometria` sobre los puntos de borde ya detectados (etapas ①–⑥) y la propuesta se usa **solo** si el clasificador decidió. El clasificador ya falla cerrado devolviendo `None`.
3. **Sin decisión no hay excepción críptica.** Se retira el `ValueError` de círculo ausente: el pipeline se detiene reportando **ambos** candidatos con la confianza y la evidencia numérica, y la vista los muestra para que el operador elija.
4. **Las dos geometrías son ramas del mismo selector.** Círculo usa ⑦→⑧→⑨; recta usa ⑩→⑪. Ninguna es el camino por defecto.
5. **La vista expone el selector** (círculo / recta / automático) y, en automático, muestra la geometría propuesta con su confianza y detalle; cuando falla cerrado, muestra ambos candidatos.
6. **La decisión es una función pura.** El mapeo «geometría + evidencia → plan de etapas» se aísla en una función sin GTK, para poder probarlo sin UI. El hilo de trabajo no toca GTK; el resultado vuelve por `GLib.idle_add` (AGENTS.md §6.3).

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

**L12** (decisión, 2026-11-21): S4 exige confianza y evidencia pero no fija el criterio de decisión, así que el orquestador lo definió antes de delegar T4 y lo dejó escrito en «T4 — criterios de diseño del clasificador». El punto que no se puede omitir es la admisibilidad del círculo: una recta es un círculo de radio infinito, y sin acotar el radio el clasificador responde círculo ante cualquier conjunto colineal. La confianza se define como separación relativa de residuales para que sea monótona y quede en `[0,1]` por construcción, en vez de un puntaje ad hoc.

**L13** (corrección de la spec, 2026-11-21): el bloque de diseño de T4 se contradecía a sí mismo — el criterio 5 listaba los «colineales exactos» como degenerados mientras la tarea exigía un test que probase que una nube colineal se clasifica como recta. El worker lo detectó y resolvió a favor del test. **La resolución correcta es esa**: la colinealidad exacta no es un dato degenerado, es la evidencia más limpia de una recta, y el criterio 2 ya la cubre porque deja el círculo sin radio admisible. Se reescribió el criterio 5 para sacar la colinealidad de la lista de degenerados y se ratificaron las cuatro semánticas que el bloque dejaba implícitas (`extensión`, `tolerancia_px`, `candidatos`, `detalle`). Lección para el próximo bloque de diseño: si un criterio y una prueba exigida pueden contradecirse, el criterio está mal escrito.

**L14** (hallazgo, 2026-11-21): la suite completa falló **después** de que T4 reportara verde en el foco (`161 passed`). Ese verde fue suerte de semilla: la propiedad de invariancia es aleatoria y su primer ejemplo falsador apareció en la corrida completa. Con `--hypothesis-seed` explícito pasaba 5 de 5 porque eso desactiva el replay de la base de datos de Hypothesis.

El ejemplo falsador era `puntos=[[3.0, 0.0], [1.11253693e-308, 0.0], [0.0, 0.0]]` con `angulo=0.0`, `reflejar=False` y `desplazamiento=[1., 1.]`: la única transformación es una **traslación**, y la decisión cambiaba de `RECTA` a `None` con el detalle «menos de 3 puntos distintos». Causa real: sumar `1.0` vuelve exactamente idénticos dos puntos que difieren en `1e-308`, así que el detector de duplicados —correcto según el criterio 5— los colapsa. **No era una falla del clasificador sino una propiedad insatisfacible**: exigía invariancia para un input cuya distinción destruye la aritmética de punto flotante. Se corrigió el test con `assume(...)` que exige que la transformación conserve cuántos puntos distintos hay, y se fijó la conducta real en dos pruebas deterministas: el colapso se reporta degenerado, y una traslación que conserva los puntos no cambia la decisión.

De paso quedó un defecto real que la investigación destapó: el ajuste algebraico de Kåsa usa coordenadas absolutas, así que ahora se ajusta sobre la nube centrada y el centro se devuelve al marco original. Medido sobre un círculo de radio 50 desplazado `1e6`: el residual pasa de `2.441e-06` a `1.785e-11` y el radio de `49.999998` a `50.000000`. Suite completa: **313 passed, 1 skipped**.

Lección de proceso: un `| tail` me devolvió exit `0` con la suite en rojo. Las verificaciones se corren leyendo el código de salida explícito, nunca a través del pipe.

**L15** (T6, 2026-11-21): se creó `Procesamiento/models/strategies/base_strategy.py` con `DeteccionStrategy` y su `strategies/__init__.py`, cumpliendo L6. Test-first: RED observado como `ModuleNotFoundError: No module named 'src.odin.Procesamiento.models.strategies'` (exit 2, error de colección); GREEN `4 passed`. Cubre que la base y una subclase sin `detectar` no se instancian, que una concreta devuelve la máscara con la forma de la entrada, y que los `kwargs` llegan a la estrategia. Suite completa: **317 passed, 1 skipped**. Commit `115b3bc`.

**L16** (autorización, 2026-11-21): el usuario autorizó explícitamente **T5 completo, controlador y vista**, que es la primera modificación de código existente en esta fase y por eso requería permiso según AGENTS.md. Se escribió el bloque «T5 — criterios de diseño del selector» antes de delegar, por la misma razón que en T4: sin criterio explícito el writer habría inventado el contrato del pipeline y de la UI.
