# otsu-rosin — Etapa ④: umbrales de Otsu y Rosin

> Absorbido de `.kiro/specs/otsu-rosin/` el 2026-11-21. Original conservado sin
> modificar (S1). Estado verificado contra el código en esa fecha.

## Requisitos absorbidos

### R1 — Histograma de píxeles activos

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Procesamiento/models/otsu_rosin.py:19-21,43`

> ### Requirement 1: Histograma de píxeles activos
>
> **User Story:** Como usuario de ODIN, quiero que los umbrales se calculen solo
> sobre el gradiente real, para que el fondo negro no arrastre el histograma.
>
> #### Acceptance Criteria
>
> 1. THE histograma SHALL construirse con 256 bins uniformes sobre el rango de
>    los píxeles con `IG > 0`.
> 2. WHEN no hay píxeles activos (todo cero, todo negativo, arreglo vacío), THEN
>    ambas funciones SHALL devolver `0.0` sin lanzar excepción.
> 3. WHEN hay `NaN` en la entrada, THEN SHALL excluirse del histograma (el filtro
>    `IG > 0` los descarta) sin propagar `NaN` al umbral.

`pixeles_validos = IG[IG > 0]` (`:19`), `np.histogram(..., bins=256)` (`:43`) y
retorno `(0.0, 0.0)` cuando no hay píxeles (`:121`). Verificado: vacío,
negativos y `NaN` se comportan según el requisito. Tests:
`tests/unit/Procesamiento/test_etapa4_otsu_rosin.py:91,105`.

### R2 — Umbral de Otsu

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Procesamiento/models/otsu_rosin.py:57-100`

> ### Requirement 2: Umbral de Otsu
>
> **User Story:** Como etapa ⑤, quiero el umbral que maximiza la separación
> interclase, para particionar los bordes en fuertes y débiles.
>
> #### Acceptance Criteria
>
> 1. THE umbral SHALL ser el centro de bin que maximiza `vB`.
> 2. WHEN el óptimo es agudo (clusters de varianza amplia), THEN el umbral SHALL
>    coincidir con una referencia independiente por barrido sobre valores reales
>    dentro de **1 ancho de bin** (verificado: sigma 0.12 → 0.4 bins; sigma 0.20
>    → 0.6 bins).
> 3. THE resultado SHALL ser invariante a usar índices de bin (1..L) en lugar de
>    `xcenters` reales: es una transformación afín monótona, y el argmax de `vB`
>    no cambia (verificado: valores idénticos).
> 4. THE umbral SHALL escalar proporcionalmente con la entrada (verificado:
>    `IG × 10` → umbral ×10.0000).

`_umbral_otsu` calcula `vB = (w0*w1)*((u1-u0)**2)` vectorizado y devuelve
`xcenters[np.argmax(vB)]` (`:98`). Tests:
`tests/unit/Procesamiento/test_etapa4_otsu_rosin.py:33,57`.

### R3 — Meseta de Otsu (contrato de unicidad)

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Procesamiento/models/otsu_rosin.py:98`

> ### Requirement 3: Meseta de Otsu (contrato de unicidad)
>
> **User Story:** Como consumidor del umbral, quiero saber cuándo el valor es
> único y cuándo no, para no perseguir diferencias que no significan nada.
>
> #### Acceptance Criteria
>
> 1. WHEN los clusters son compactos y bien separados, THEN `vB` SHALL ser
>    prácticamente constante en una región amplia y **cualquier punto de la
>    meseta SHALL considerarse un umbral válido**.
> 2. Evidencia vinculante: en datos bimodales (σ=0.05), `vB(0.45321) =
>    vB(0.51478) = 0.062669804206` — idénticos a 12 decimales. Una diferencia de
>    umbral de 0.06 en esa región **no es un defecto**.

`np.argmax(vB)` es determinista dentro de la meseta (primer índice del máximo).
Test: `tests/unit/Procesamiento/test_etapa4_otsu_rosin.py:43`.

### R4 — Umbral de Rosin (diagnóstico)

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Procesamiento/models/otsu_rosin.py:102-161`

> ### Requirement 4: Umbral de Rosin (diagnóstico)
>
> **User Story:** Como usuario, quiero ver en el histograma dónde cae el criterio
> de Rosin, para compararlo con Otsu.
>
> #### Acceptance Criteria
>
> 1. THE umbral Rosin SHALL ser el punto de máxima distancia perpendicular a la
>    recta pico→cola, evaluado en la zona `[pico, último bin no vacío]`.
> 2. THE umbral Rosin SHALL ser **solo diagnóstico**: `main.py` lo descarta y el
>    pipeline no lo usa para decidir nada.
> 3. WHEN la geometría es indefinida (un solo bin no vacío, recta de longitud 0),
>    THEN SHALL caer al respaldo `umbral_rosin = umbral_otsu`.
> 4. (Comportamiento documentado) En histogramas bimodales, Rosin cae en el
>    **flanco del pico dominante** (verificado: pico en 0.100 → Rosin 0.1417), no
>    en el valle entre clusters: el criterio es para histogramas unimodales.

`umbralRosinYOtsu` evalúa las distancias perpendiculares en
`zona_busqueda = np.arange(idx_pico, idx_cola + 1)` (`:143`) y cae al respaldo
`umbral_rosin = umbral_otsu` (`:159`) cuando la geometría es indefinida. Test:
`tests/unit/Procesamiento/test_etapa4_otsu_rosin.py:114`.

### R5 — Casos degenerados (divergencia D1)

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Procesamiento/models/otsu_rosin.py:29-40,45-52`

> ### Requirement 5: Casos degenerados (divergencia D1)
>
> **User Story:** Como llamador (librería o pipeline con una imagen degenerada),
> quiero un umbral con sentido cuando no hay separación posible, no un valor
> arbitrario del borde artificial del histograma.
>
> #### Acceptance Criteria
>
> 1. WHEN todos los píxeles activos tienen el mismo valor (un solo bin no
>    vacío), THEN el umbral SHALL ser exactamente ese valor. **(Resuelto:
>    `_preparar_histograma` devuelve un histograma de un solo bin centrado en el
>    valor real; verificado 1e-6, 0.001, 0.005, 0.05, 0.5, 0.7, 1.0 y 3.7 → el
>    umbral es idéntico al valor.)**
> 2. THE umbral devuelto SHALL ser siempre ≥ 0 cuando la entrada es ≥ 0.
>    **(Resuelto; verificado con valores diminutos: 1e-12 y 1e-6 incluidos.)**

`_preparar_histograma` devuelve un solo bin centrado en el valor cuando
`vmin == vmax` (`:29-40`) y rescata el caso casi-constante con `except ValueError`
(`:45-52`). Verificado en esta ejecución con 1e-6, 0.001, 0.005, 0.05, 0.5, 0.7,
1.0 y 3.7: el umbral es idéntico al valor. Tests:
`tests/unit/Procesamiento/test_etapa4_otsu_rosin.py:68,76`.

### R6 — Función pura respecto de la UI (deuda)

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Procesamiento/models/otsu_rosin.py:9`

> ### Requirement 6: Función pura respecto de la UI (deuda)
>
> **User Story:** Como capa de modelos, quiero que el cálculo no dependa de GTK,
> para poder testearlo y reutilizarlo.
>
> #### Acceptance Criteria
>
> 1. THE funciones de umbralizado SHALL NOT invocar la UI. **(Deuda D3: hoy
>    llaman `GLib.idle_add(dibujar_en_hilo_principal, ...)` de forma
>    incondicional, incluso con `histo=False`; el módulo importa `gi`. La deuda
>    se resuelve en el refactor `src/odin/` inyectando un callback de dibujo.)**

El módulo tiene un único import: `import numpy as np` (`:9`); no importa `gi`,
`GLib` ni matplotlib y no invoca UI. La cita del AC 1 queda registrada como
desactualizada en Divergencias.

## Divergencias

- **R6.1** — el requisito describe la deuda D3 (`GLib.idle_add(dibujar_en_hilo_principal, ...)`
  incondicional y `import gi`) como vigente; el módulo solo importa `numpy` y no
  invoca UI. · `src/odin/Procesamiento/models/otsu_rosin.py:9`
- **R6.1 (bloque de estado)** — el bloque de estado del original cita
  `design.md:14,63` como repetición de la deuda D3; la línea 14 es el propio bloque
  de estado y la 63 pertenece al texto de D1, no a D3 (la deuda D3 está en
  `design.md:80-81` y `design.md:94`). La divergencia de fondo (el módulo ya no
  invoca UI) se verifica. · `.kiro/specs/otsu-rosin/design.md:80`

## Pendientes

- Ninguno.
