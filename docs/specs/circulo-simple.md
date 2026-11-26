# circulo-simple

> Absorbido de `.kiro/specs/circulo-simple/` el 2026-11-21. Original conservado sin
> modificar (S1). Estado verificado contra el código en esa fecha.

## Requisitos absorbidos

### R1 — Contrato de `Circulo_simple`

**Estado:** CONTRADICHO · **Evidencia:** `src/odin/Ajustes/models/circulo_simple.py:55-57,61-103,132-135`

> **User Story:** Como etapa ⑨ del pipeline, quiero un ajuste de círculo
> geométricamente válido o un rechazo explícito cuando los datos no lo permiten.
>
> #### Acceptance Criteria
>
> 1. `Circulo_simple` SHALL recibir una matriz NumPy de forma $(N, 2)$ con
>    coordenadas $(x, y)$ de los puntos.
> 2. WHEN $N \ge 3$ y los puntos no son colineales, THEN SHALL devolver
>    $(x_c, y_c, r, pv)$ con $r > 0$ y $pv \ge 0$.
> 3. WHEN $N < 3$, THEN SHALL rechazar con `ValueError` y mensaje descriptivo
>    ("menos de 3 puntos: ajuste subdeterminado").
> 4. WHEN los puntos son colineales (o casi), THEN SHALL rechazar con
>    `ValueError` ("puntos colineales: no se puede ajustar un círculo").
> 5. WHEN el radicando $x_c^2 + y_c^2 - s \le 0$, THEN SHALL rechazar con
>    `ValueError` ("radicando no positivo: radio indefinido").
> 6. WHEN la entrada es `None` o no es un array $(N, 2)$, THEN SHALL rechazar con
>    `ValueError`.
> 7. El orden de los puntos SHALL NOT influir en el resultado del ajuste.

El código valida forma, `N < 3`, colinealidad y radicando con `ValueError`, pero para `None` o entrada no `ndarray` lanza `TypeError` (`circulo_simple.py:55-57`), no `ValueError`; el orden es irrelevante por `np.linalg.lstsq`.

### R2 — Métrica de error

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Ajustes/models/circulo_simple.py:138-145`; test `tests/unit/Ajustes/test_etapa9_circulo_simple.py:132`

> **User Story:** Como consumidor del resultado, quiero saber qué tan ajustado
> está el círculo a los puntos, no solo un número sin contexto.
>
> #### Acceptance Criteria
>
> 1. `pv` SHALL ser el pico a valle de los errores de distancia
>    $\max(|d_i - r|) - \min(|d_i - r|)$.
> 2. $pv$ SHALL ser $0.0$ para un círculo perfecto (todos los puntos exactamente
>    sobre la circunferencia).

`pv = float(np.max(res) - np.min(res))` con `res = |distancias - r|`; un círculo perfecto da `pv = 0.0`.

### R3 — Integración con la etapa ⑧

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/controllers/main_controller.py:321-338`

> **User Story:** Como etapa ⑧ (`findCircle`), quiero confiar en que ⑨ valida
> geométricamente lo que recibe antes de ajustar.
>
> #### Acceptance Criteria
>
> 1. `main.py` SHALL seguir llamando a `LSC.Circulo_simple(puntosFiltrados)`
>    tras `validar_anillo`.
> 2. WHEN `Circulo_simple` rechaza por $< 3$ puntos o colinealidad, THEN
>    `main.py` SHALL mostrar el motivo en el diálogo de error en vez de fallar
>    silenciosamente.

`main_controller.py:321-327` llama a `validar_anillo` y luego a `self.LSC.Circulo_simple(puntosFiltrados)`; el `except` de `:333-339` muestra `str(e)` en `mostrar_alerta`.

## Divergencias

- **R1.6** — el spec exige `ValueError` para entrada `None` o no array `(N, 2)`; el código lanza `TypeError` · `src/odin/Ajustes/models/circulo_simple.py:55`

## Pendientes

- Ninguno.
