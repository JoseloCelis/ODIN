<!-- ESTADO:INICIO -->
> **Estado del documento** — veredicto: `ABSORBIDO` · versión ODD: `odd/specs/edge-track-hyst.md` · fecha: 2026-11-21
>
> | Requisito | Estado | Evidencia |
> |---|---|---|
> | R1 | IMPLEMENTADO | `edge_track_hyst.py:22-34,45,55,76-89`: `uint8` en `{0,255}`, misma forma, no muta los argumentos; tests `tests/unit/Procesamiento/test_etapa6_edge_track_hyst.py:122,134` |
> | R2 | IMPLEMENTADO | `edge_track_hyst.py:76,84`: los fuertes se conservan; sin fuertes la salida es cero; tests `:94,104,112` |
> | R3 | IMPLEMENTADO | `edge_track_hyst.py:60`: kernel 5×5 → Chebyshev ≤ 2; tests `:39,50` |
> | R4 | IMPLEMENTADO | `edge_track_hyst.py:66-89`: componentes 8-conexas, isla entera; tests `:60,70` |
> | R5 | IMPLEMENTADO | `edge_track_hyst.py:66-89`: solo propaga dentro de la isla; los huecos no unen; test `:82` |
> | R6 | IMPLEMENTADO | `edge_track_hyst.py:40-48`: entrada vacía → vacía `uint8` sin excepción; test `:147` |
> | R7 | IMPLEMENTADO | `edge_track_hyst.py:22-89` iterativo; 0 hits de `setrecursionlimit` en `src/` |
> | R8 | IMPLEMENTADO | sin prints en el módulo; el orquestador reporta una línea en `main_controller.py:227-232` |
>
> **Pendientes:** ninguno.
> **Divergencias verificadas:** R6.1 está desactualizado: afirma «NO CUMPLE hoy» con el `ValueError` de NumPy; el caso vacío ya está resuelto (`edge_track_hyst.py:40-48`, `requirements.md:100`).
> **Inciertos:** ninguno.
<!-- ESTADO:FIN -->

# Tasks Document — edge-track-hyst (etapa ⑥)

## Tarea 1: Especificación (hecha)

- [x] `requirements.md` R1-R8.
- [x] `design.md` con la revisión del módulo (dos implementaciones, solo una
  en producción), evidencia ejecutada y divergencias D1-D5.
- [x] Batería previa: radio Chebyshev, comparación vectorizada vs recursiva,
  degenerados, `RecursionError` en 300×300, contrato de salida.

## Tarea 2: Tests (TDD) — hecha

- [x] `tests/test_etapa6_edge_track_hyst.py` con la caracterización de
  `EdgeTrack_Hyst` (R1-R5): 17 casos.
- [x] Test de entrada vacía **en rojo** (R6.1) antes de tocar el código
  (falló con `ValueError: zero-size array to reduction operation maximum`).

## Tarea 3: Fixes — hechos

- [x] D1: guarda temprana en `EdgeTrack_Hyst` (`strong.size == 0` → salida
  vacía; `weaks.size == 0` → solo fuertes) → test en verde.
- [x] D3: eliminados `DThEdgeTrack` + `FindConnectedWeakEdges` + `import sys`
  (152 → 79 líneas), tras verificar en §2.2/§2.3 del design que el código
  muerto está superado y revienta a 300×300.
- [x] D4: `main.py` imprime `np.sum(DetectedEdges > 0)`.
- [x] D5: los 8 `print` por llamada salieron del modelo; en `main.py` queda
  una línea con fuertes, débiles y total. Comentario obsoleto del kernel
  corregido (3×3 → 5×5).

## Tarea 4: Cierre — hecha

- [x] Suite completa verde: `python3 -m pytest tests -q` → **62 passed**.
- [x] Import smoke (`python3 -c "import odin.main"`).
- [x] `MEMORY.md` actualizado y commit.

## Tarea 5: Enmienda de contrato 7×7 → 5×5 — hecha

- [x] R3 enmendado (Chebyshev ≤ 3 → ≤ 2) con la justificación medida.
- [x] Tests de radio actualizados **antes** de tocar el kernel (2 sí / 3 no).
- [x] `np.ones((7, 7))` → `np.ones((5, 5))` en `DThEdgeTrackHyst.py`.
- [x] Suite completa verde tras el cambio.
