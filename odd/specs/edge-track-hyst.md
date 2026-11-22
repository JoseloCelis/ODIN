# edge-track-hyst (etapa ⑥)

> Absorbido de `.kiro/specs/edge-track-hyst/` el 2026-11-21. Original conservado sin
> modificar (S1). Estado verificado contra el código en esa fecha.

## Requisitos absorbidos

### R1 — Contrato de entrada y salida

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Procesamiento/models/edge_track_hyst.py:22-34,41,45-46,55,76-89`

> ### Requirement 1: Contrato de entrada y salida
>
> **User Story:** Como etapa aguas abajo (Hough, círculos), quiero una imagen
> binaria con la misma geometría que la entrada.
>
> #### Acceptance Criteria
>
> 1. THE función SHALL recibir dos arreglos de igual forma (`strong`, `weaks`)
>    tratados como máscaras: cualquier valor `> 0` significa "presente".
> 2. THE salida SHALL tener la misma forma que la entrada, `dtype=uint8` y
>    valores en `{0, 255}`.
> 3. THE función SHALL NOT modificar sus argumentos.

`np.asarray` no muta los argumentos y la salida es `uint8` de la forma de `strong` con valores 0/255; tests `tests/unit/Procesamiento/test_etapa6_edge_track_hyst.py:122,134`.

### R2 — Los bordes fuertes se conservan siempre

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Procesamiento/models/edge_track_hyst.py:76,84`

> ### Requirement 2: Los bordes fuertes se conservan siempre
>
> #### Acceptance Criteria
>
> 1. WHEN `strong[i, j] > 0`, THEN la salida SHALL ser 255 en `(i, j)`.
> 2. WHEN no hay fuertes, THEN la salida SHALL ser toda cero, aunque haya
>    débiles (no hay nada a lo que conectarse).

`output[strong_mask] = 255` en `:76,84`; sin fuertes `connected_ids` queda vacío y la salida es cero; tests `:94,104,112`.

### R3 — Alcance desde un borde fuerte

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Procesamiento/models/edge_track_hyst.py:60-61`

> ### Requirement 3: Alcance desde un borde fuerte
>
> **User Story:** Como detector, quiero tolerar el pequeño hueco entre el
> núcleo del borde y su cola débil.
>
> #### Acceptance Criteria
>
> 1. A weak pixel SHALL conservarse si está a **distancia Chebyshev ≤ 2** de un
>    fuerte (dilatación con kernel 5×5).
> 2. Evidencia vinculante: horizontal `d=1,2` conservado, `d=3,4,5` descartado;
>    diagonal `d=1,2` conservado, `d=3` descartado.
> 3. **Enmienda de contrato (decisión del usuario)**: el valor anterior era
>    Chebyshev ≤ 3 (kernel 7×7). Se reduce a 5×5 porque el 7×7 se juzgó
>    exagerado para el hueco real entre núcleo y cola del borde. Medición que
>    respalda el cambio: sobre `img100.bmp` real, 3×3, 5×5 y 7×7 producen los
>    mismos 10 028 bordes (0 px de diferencia), y en imágenes sintéticas con
>    ruido, 5×5 es indistinguible de 3×3 mientras 7×7 agrega entre 45 y 380
>    píxeles espurios con σ ≥ 0.10. El 5×5 conserva el comportamiento útil y
>    recorta el alcance innecesario.

El kernel `np.ones((5, 5))` de `:60` dilata con Chebyshev ≤ 2; tests `:39,50`.

### R4 — Isla débil se conserva completa o se descarta completa

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Procesamiento/models/edge_track_hyst.py:66-70,86-89`

> ### Requirement 4: Isla débil se conserva completa o se descarta completa
>
> #### Acceptance Criteria
>
> 1. WHEN una isla débil (8-vecinos) toca la zona dilatada de un fuerte, THEN
>    **todos** sus píxeles SHALL conservarse (propagación transitiva dentro de
>    la isla). Evidencia: línea continua de 12 débiles → 1 fuerte + 12.
> 2. WHEN ninguna parte de la isla toca la zona dilatada, THEN la isla entera
>    SHALL descartarse.

`cv2.connectedComponents(..., connectivity=8)` (`:66-70`) etiqueta la isla y `np.isin` (`:86-89`) la conserva entera; tests `:60,70`.

### R5 — Semántica de unión entre islas

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Procesamiento/models/edge_track_hyst.py:66-89`

> ### Requirement 5: Semántica de unión entre islas (contrato, no defecto)
>
> #### Acceptance Criteria
>
> 1. Dos islas débiles separadas por píxeles vacíos SHALL NOT unirse aunque el
>    hueco sea ≤ 3 px. La propagación transitiva ocurre **solo dentro** de una
>    isla 8-conexa.
> 2. Evidencia: fuerte en (20,20), débil en (20,23) y (20,26) → solo sobrevive
>    (20,23). La implementación recursiva salvaba ambas (propagaba saltos ≤3),
>    pero **no es la que corre en producción**.
> 3. La implementación vectorizada es **subconjunto estricto** de la recursiva
>    (`solo_vec = 0` en todos los casos medidos).

La propagación ocurre solo dentro de cada componente 8-conexo (`:66-89`); test `:82`. El ejemplo de R5.2 está desactualizado: ver Divergencias.

### R6 — Robustez (entrada vacía)

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Procesamiento/models/edge_track_hyst.py:40-47`

> ### Requirement 6: Robustez (divergencia D1)
>
> **User Story:** Como llamador, quiero que una entrada vacía devuelva una
> salida vacía, no una excepción.
>
> #### Acceptance Criteria
>
> 1. WHEN la entrada es un arreglo vacío, THEN la función SHALL devolver un
>    arreglo vacío `uint8` sin lanzar excepción. **(NO CUMPLE hoy:
>    `ValueError: zero-size array to reduction operation maximum`.)**
> 2. WHEN una de las dos máscaras está vacía, THEN la salida SHALL respetar
>    R2.2 y R2.1.

La guarda `strong.size == 0` (`:40-41`) devuelve vacío `uint8` sin excepción y `weaks.size == 0` (`:44-47`) conserva solo los fuertes; test `:147`. El texto de R6.1 está desactualizado: ver Divergencias.

### R7 — Sin recursión ni efectos globales

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Procesamiento/models/edge_track_hyst.py:22-91`

> ### Requirement 7: Sin recursión ni efectos globales
>
> #### Acceptance Criteria
>
> 1. THE función SHALL NOT usar recursión.
> 2. THE módulo SHALL NOT llamar `sys.setrecursionlimit` en el camino de
>    producción (hoy lo hace `DThEdgeTrack`, que no se usa).

Implementación iterativa; 0 ocurrencias de `setrecursionlimit` en `src/`.

### R8 — Diagnóstico por consola

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Procesamiento/models/edge_track_hyst.py:22-91`, `src/odin/controllers/main_controller.py:227-231`

> ### Requirement 8: Diagnóstico por consola
>
> **User Story:** Como lector de la consola, quiero una sola línea de resumen del
> pipeline, no ocho líneas de diagnóstico por cada procesamiento.
>
> #### Acceptance Criteria
>
> 1. THE función SHALL NOT escribir en consola. Era el único módulo del pipeline
>    con prints por llamada; el modelo queda libre de salida, como el resto.
> 2. THE orquestador (`main.py`) SHALL reportar el resumen de la etapa en una
>    sola línea: fuertes, débiles y píxeles conservados tras la histéresis.

El módulo no imprime; el resumen de una línea está en `main_controller.py:227-231` (el spec lo atribuye a `main.py`, renombrado durante la refactorización).

## Divergencias

- **R5.2** — El spec afirma que con un fuerte en (20,20) sobrevive el débil en (20,23); el código dilata con kernel 5×5 (Chebyshev ≤ 2), por lo que (20,23) queda a distancia 3 y no sobrevive (verificado ejecutando `EdgeTrack_Hyst`: salida 0 en (20,23) y (20,26)). El ejemplo quedó del contrato anterior 7×7. · `src/odin/Procesamiento/models/edge_track_hyst.py:60-61`
- **R6.1** — El criterio afirma «(NO CUMPLE hoy: `ValueError: zero-size array to reduction operation maximum`)»; el código resuelve el caso vacío con una guarda temprana y devuelve un arreglo vacío `uint8` sin excepción. · `src/odin/Procesamiento/models/edge_track_hyst.py:40-41`

## Pendientes

- Ninguna obligación pendiente.
