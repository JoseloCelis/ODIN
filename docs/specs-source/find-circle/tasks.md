<!-- ESTADO:INICIO -->
> **Estado del documento** — veredicto: `ABSORBIDO` · versión ODD: `odd/specs/find-circle.md` · fecha: 2026-11-21
>
> | Requisito | Estado | Evidencia |
> |---|---|---|
> | R1 | IMPLEMENTADO | `find_circle.py:46-105` (salida (N,2), vacío (0,2) en `:92`, orden irrelevante); tests `tests/unit/Ajustes/test_etapa8_find_circle.py:64,74,82` |
> | R2 | IMPLEMENTADO | `tolerancia_anillo` `find_circle.py:31-43` (`min(10, 0.25·re)`), parámetro explícito `:46,98`; tests `:105,116,129,138` |
> | R3 | IMPLEMENTADO | `cobertura_angular` `find_circle.py:187-229`, `validar_anillo:231-262`; umbrales `:26-28`; aborta con motivo en `main_controller.py:321-325`; tests `:151,161,178,188,203` |
> | R4 | IMPLEMENTADO | `validar_anillo:237-260` (<3 puntos y cobertura insuficiente); tests `:237,259` |
> | R5 | IMPLEMENTADO | centro escalar `find_circle.py:64-71`; el orquestador pasa `mejor_centro` (`main_controller.py:298-303,317`); tests `:157,278` |
> | R6 | IMPLEMENTADO | `find_circle.py:75-86` (`re=None`/`re<=0` → `ValueError` con `segmento_mas_largo`), `segmento_mas_largo:107-183`; tests `:289,297,304,311,323` |
>
> **Pendientes:** ninguno.
> **Divergencias verificadas:** ninguna. La banda `[0.6·r0, r0]` no pertenece a este spec (L8, candidata B falsa) y no se registra.
> **Inciertos:** R6.4 (equivalencia contra `b350deb`) no se re-ejecutó en esta reverificación; el comportamiento está cubierto por los tests `:311-343`.
<!-- ESTADO:FIN -->

# Tasks Document — find-circle (etapa ⑧)

## Tarea 1: Especificación — hecha

- [x] `requirements.md` R1-R6.
- [x] `design.md` con el estado del módulo, la evidencia ejecutada (anillo
      frágil lejos del radio, degeneración con `re <= 10`, síntoma del usuario
      reproducido sobre `img100`) y los umbrales con su margen.

## Tarea 2: Tests (TDD) — hecha

- [x] `tests/test_etapa8_find_circle.py`, 27 casos (rojo: 19 fallos / 5 pasados).
- [x] Caracterización de `find_circle` (R1): selección, forma, coordenadas,
      vacío sin excepción, orden irrelevante.
- [x] `tolerancia_anillo` (R2): valores por radio, círculo interno sin
      contaminación, equivalencia con la tolerancia fija para `re >= 40`.
- [x] `cobertura_angular` y `validar_anillo` (R3): anillo completo vs basura,
      umbrales, motivo del rechazo; arco rechazado por cobertura y arco de 290°
      rechazado por hueco.
- [x] Selección insuficiente (R4): 0, 1 y 2 puntos; ajuste subdeterminado con
      `pv = 0`; tres puntos casi colineales.
- [x] Regresión de un solo centro (R5).
- [x] El modo sin radio quedó explícito (R6): `find_circle` exige el radio y
      `segmento_mas_largo` conserva el agrupamiento, probado aislado.

## Tarea 3: Implementación — hecha

- [x] `src/odin/Ajustes/models/find_circle.py`: `tolerancia_anillo`,
      `cobertura_angular`, `validar_anillo`, y `tolerancia` opcional en
      `find_circle`; centro con arreglos rechazado con mensaje explícito.
- [x] `src/main.py`: validar el anillo antes de `Circulo_simple` y abortar con
      el motivo; el diálogo pasó de "Error Matemático" a "No se pudo procesar
      la imagen" con la causa en el mensaje.

## Tarea 4: Verificación con datos reales — hecha

- [x] Recorte holgado de `img100`: el disco se acepta con 100 % de cobertura y
      el ajuste da 427.85 (0.46 px); los radios 126.5, 300 y 550 se rechazan
      con 54.2 % / 27.8 % / 15.3 % de cobertura.
- [x] Sin regresión en la medición de la etapa ⑦: diámetro 855.70, centro a
      0.29–0.32 px.
- [x] Suite completa verde: **126 passed**.

## Tarea 5: Cierre

- [x] `MEMORY.md` y commit.
- [x] R6: el modo sin radio es explícito. Se descartó eliminarlo por ahora
      (capacidad y trazabilidad con el MATLAB original); queda pendiente de
      borrado si tras la refactorización sigue sin llamadores.
- [x] Corrección: la afirmación de que `< 6` y `<= 6` eran umbrales distintos
      era falsa; ambos ejes usan `np.where(l > 6)`, así que son equivalentes.
