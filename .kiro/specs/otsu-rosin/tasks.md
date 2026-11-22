<!-- ESTADO:INICIO -->
> **Estado del documento** — veredicto: `ABSORBIDO` · versión ODD: `odd/specs/otsu-rosin.md` · fecha: 2026-11-21
>
> | Requisito | Estado | Evidencia |
> |---|---|---|
> | R1 | IMPLEMENTADO | `otsu_rosin.py:19-21,43`: `IG > 0`, 256 bins; vacío → `0.0`; tests `tests/unit/Procesamiento/test_etapa4_otsu_rosin.py:91,105` |
> | R2 | IMPLEMENTADO | `otsu_rosin.py:57-100`: argmax de `vB`; tests `test_etapa4_otsu_rosin.py:33,57` |
> | R3 | IMPLEMENTADO | `otsu_rosin.py:98`: argmax determinista dentro de la meseta; test `test_etapa4_otsu_rosin.py:43` (meseta plana) |
> | R4 | IMPLEMENTADO | `otsu_rosin.py:102-161`: Rosin pico→cola, respaldo a Otsu (`:159`); test `test_etapa4_otsu_rosin.py:114` |
> | R5 | IMPLEMENTADO | `otsu_rosin.py:29-40,45-52`: un solo bin centrado en el valor real y rescate del caso casi-constante; tests `test_etapa4_otsu_rosin.py:68,76` |
> | R6 | IMPLEMENTADO | `otsu_rosin.py:9`: solo `numpy`; sin `gi`/`GLib`/matplotlib |
>
> **Pendientes:** ninguno.
> **Divergencias verificadas:** R6.1 está desactualizado: describe la deuda D3 (`GLib.idle_add(dibujar_en_hilo_principal, ...)`) como vigente; el módulo ya no invoca UI (`design.md:14,63` lo repite).
> **Inciertos:** ninguno.
<!-- ESTADO:FIN -->

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
