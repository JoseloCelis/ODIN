# Tasks Document — otsu-rosin

## Tarea 1: Escribir la especificación

- [x] `requirements.md` R1-R6 estilo ODD (caracterización + divergencia D1).
- [x] `design.md` con revisión de símbolos, tablas de evidencia ejecutada y
  divergencias D1-D5.
- [x] Batería previa: referencia Otsu independiente, prueba de meseta, escala,
  degenerados, geometría de Rosin.

## Tarea 2: Fixes

- [x] D1: guarda de un solo bin — `_preparar_histograma` devuelve un histograma
  de un bin centrado en el valor exacto (+ guarda defensiva en `_umbral_otsu`).
- [x] D1: umbral ≥ 0 con entrada ≥ 0 (verificado hasta 1e-12).
- [x] D3: se mantiene como deuda para el refactor `src/odin/`.
- [x] D4: `umbralOtsu` se conserva (API pública legítima).

## Tarea 3: Commit y memoria

- [x] Commit del spec.
- [x] Commit del fix D1 (batería completa reejecutada).
- [x] Actualizar `MEMORY.md`.
