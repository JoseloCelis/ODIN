# Tasks Document — non-max-sup

## Tarea 1: Escribir la especificación

- [x] `requirements.md` R1-R5 estilo ODD con divergencias D1-D3 marcadas en sus ACs.
- [x] `design.md` con revisión de las 5 funciones, divergencias probadas y
  comportamientos correctos verificados.
- [x] Batería de caracterización: delta, cuchilla ancha, meseta 3×3, espejo
  80°/100°, partición de umbrales.

## Tarea 2: Fixes (pendiente de usuario)

- [ ] D2: tie-breaking consistente (`>=` en los 4 sectores) + reejecución de B'.
- [ ] D1: selección de vecinos por cuadrante (signo de Gx/Gy) + simetría de C'.
- [ ] D3: decisión sobre el parámetro muerto `angle` de `DobleThreshold`.
- [ ] D4: limpieza de código muerto (propio commit).

## Tarea 3: Commit y memoria

- [ ] Commit del spec.
- [ ] Commit de fixes.
- [ ] Actualizar `MEMORY.md`.
