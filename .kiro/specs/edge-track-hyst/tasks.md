# Tasks Document — edge-track-hyst (etapa ⑥)

## Tarea 1: Especificación (hecha)

- [x] `requirements.md` R1-R8.
- [x] `design.md` con la revisión del módulo (dos implementaciones, solo una
  en producción), evidencia ejecutada y divergencias D1-D5.
- [x] Batería previa: radio Chebyshev, comparación vectorizada vs recursiva,
  degenerados, `RecursionError` en 300×300, contrato de salida.

## Tarea 2: Tests (TDD)

- [ ] `tests/test_etapa6_edge_track_hyst.py` con la caracterización de
  `EdgeTrack_Hyst` (R1-R5).
- [ ] Test de entrada vacía **en rojo** (R6.1) antes de tocar el código.

## Tarea 3: Fixes (pendiente de OK del usuario)

- [ ] D1: entrada vacía sin excepción → test en verde.
- [ ] D3: eliminar `DThEdgeTrack` + `FindConnectedWeakEdges` (+ `import sys`).
- [ ] D4: `main.py` imprime `np.sum(DetectedEdges > 0)`.
- [ ] D5: decisión sobre los `print` de diagnóstico.

## Tarea 4: Cierre

- [ ] Suite completa verde (`python3 -m pytest tests -v`).
- [ ] Commit y `MEMORY.md`.
