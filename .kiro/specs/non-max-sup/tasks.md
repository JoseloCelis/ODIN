<!-- ESTADO:INICIO -->
> **Estado del documento** — veredicto: `ABSORBIDO` · versión ODD: `odd/specs/non-max-sup.md` · fecha: 2026-11-21
>
> | Requisito | Estado | Evidencia |
> |---|---|---|
> | R1 | CONTRADICHO | el requisito exige sectores con `np.mod(angle, 360)` y cortes en 22.5° (`requirements.md:46`); el código compara sobre el eje `mod 180` con fracción angular: `non_max_sup.py:64-66,72-78,85`. R1.2/R1.3 se cumplen (borde de 1 px en 0; adelgazamiento) |
> | R2 | CONTRADICHO | el requisito exige pesos `w_x=|Gx|/max(|Gx|,|Gy|)`, `w_y=|Gy|/max(...)` (`requirements.md:64`); el código interpola con la fracción angular `f` y no usa Gx/Gy (`non_max_sup.py:36-38,66,81-82`) |
> | R3 | IMPLEMENTADO | simetría por construcción sobre el eje mod 180 (`non_max_sup.py:61-66`); test `tests/unit/Procesamiento/test_etapa3_non_max_sup.py:50` |
> | R4 | IMPLEMENTADO | `keep = (C >= v_este) & (C >= v_opuesto)` (`non_max_sup.py:85`); test `:40` |
> | R5 | IMPLEMENTADO | `DobleThreshold` `non_max_sup.py:268-297` (gnh=1.0 si M≥thresh; gnl magnitud en [thresh², thresh); thresh>1→1.0; sin parámetro `angle`); tests `:77,88` |
>
> **Pendientes:** ninguno.
> **Divergencias verificadas:** R1.1 — `requirements.md:46` exige `np.mod(angle, 360)` con límites 22.5°/67.5°/…; `non_max_sup.py:64-66` usa `np.mod(angle, 180.0)` y `sector = floor(phi/45)`. R2.1 — `requirements.md:64` exige los pesos `|Gx|/max`; `non_max_sup.py:36-38` declara Gx/Gy sin uso y `:66,81-82` interpola con `f=(phi−45·sector)/45`. La referencia `tests/utilidades.py:nms_referencia_escalar` implementa el mismo esquema mod-180: su test valida coherencia interna, no el spec.
> **Inciertos:** ninguno.
<!-- ESTADO:FIN -->

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
- [x] D4: revisión con verificación de utilidad (corregido tras decisión del
  usuario — sin referencias ≠ sin utilidad) — `NMS_Parabolic` y
  `NMS_Gaussian` **recuperados** (subpíxel exacto, simetría 20/20);
  `Interpolation_old` y `NMS_Migrado.py` descartados **tras verificar** que
  fallan simetría 20/20 (el primero es la D1 superada; el segundo suma 0/0).

## Tarea 3: Commit y memoria

- [x] Commit del spec.
- [x] Commit de fixes (+ referencia escalar 100 casos + integración 1→2→3).
- [x] Actualizar `MEMORY.md`.
