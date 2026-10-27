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
