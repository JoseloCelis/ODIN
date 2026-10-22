# Tasks Document — non-max-sup

## Tarea 1: Escribir la especificación

- [x] `requirements.md` R1-R5 estilo ODD con divergencias D1-D3 marcadas en sus ACs.
- [x] `design.md` con revisión de las 5 funciones, divergencias probadas y
  comportamientos correctos verificados.
- [x] Batería de caracterización: delta, cuchilla ancha, meseta 3×3, espejo
  80°/100°, partición de umbrales.

## Tarea 2: Fixes

- [x] D2: tie-breaking consistente (`>=` en los 4 sectores) + reejecución de B' (9/9 ambos).
- [x] D1: selección de vecinos por eje mod 180° (cuadrante-correcta) + simetría de C' (exacta).
- [x] D3: parámetro muerto `angle` eliminado de `DobleThreshold`; `main.py` actualizado.
- [x] D4: revisión y descarte — `NMS_Parabolic`, `NMS_Gaussian`, `Interpolation_old`,
  bloques comentados y `NMS_Migrado.py` (cero referencias verificadas).

## Tarea 3: Commit y memoria

- [x] Commit del spec.
- [x] Commit de fixes (+ referencia escalar 100 casos + integración 1→2→3).
- [x] Actualizar `MEMORY.md`.
