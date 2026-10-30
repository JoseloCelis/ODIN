# Tasks Document — circuloSimple (etapa ⑨)

## Tarea 1: specs en `.kiro/specs/circulo-simple/`

- [x] `requirements.md` — R1 entrada inválida, R2 guard de colinealidad, R3 salida, R4 documentación.
- [x] `design.md` — estado, contrato, guard (por qué no el cond crudo, normalización, umbral con márgenes, costo, verificación real), rama defensiva, fuera de alcance.
- [x] `tasks.md` — este documento.

## Tarea 2: validación de entrada

- [x] `TypeError` si `puntos0` no es `ndarray`.
- [x] `ValueError` si la forma no es `(N, 2)`.
- [x] `ValueError` si `N = 0` ("anillo quedó vacío").
- [x] `ValueError` si `N = 1` ("insuficientes puntos").
- [x] `ValueError` con mensaje propio si `N = 2` ("dos puntos definen una línea").
- [x] Contrato de retorno: cuatro `float`.

## Tarea 3: guard de colinealidad

- [x] Medir por qué el `cond(A)` crudo NO sirve: anillo válido `6.86e3` contra recta `9.3e3` (rangos solapados).
- [x] Elegir normalización: centroide + RMS radial (escalar). Descartar desvío por eje por margen 1.11× contra 2.38×.
- [x] Medir márgenes: válidos ≤ `1.701`, rectas ≥ `4.056`, semicírculo `2.395`, hueco 240° `3.672`.
- [x] Fijar `UMBRAL_CONDICION_NORMALIZADA = 3.0`.
- [x] Implementar el guard antes del `lstsq`, con mensaje "los puntos son colineales".
- [x] Guardar `escala ≤ 0` con mensaje propio ("todos los puntos coinciden").
- [x] Mantener el ajuste sobre coordenadas originales para no alterar el resultado.

## Tarea 4: tests `tests/test_etapa9_circulo_simple.py`

- [x] 0 / 1 / 2 puntos → `ValueError` (el de 2 con mensaje propio).
- [x] Entrada no `ndarray` → `TypeError`; forma 1D y 3 columnas → `ValueError`.
- [x] 3 puntos colineales exactos → `ValueError` "colineales".
- [x] 3 puntos casi colineales (`[[0,0],[10,10],[20,20.001]]`) → `ValueError` "colineales".
- [x] Recta de 50 puntos con ruido perpendicular (el caso 537/537) → `ValueError` "colineales".
- [x] Puntos idénticos → `ValueError` "coinciden".
- [x] Triángulo rectángulo bien conformado → `r ≈ 7.071`, sin excepción.
- [x] Anillo completo, anillo con hueco de 60° y arco de 240° → sin excepción, `r` correcto.
- [x] Caso banal: `r`, centro y `pv ≥ 0`.

## Tarea 5: tests de etapa 8 ajustados al nuevo contrato

- [x] `test_el_ortodoxo_con_menos_de_tres_puntos_lanza_valueerror`: parametrizado con el mensaje propio de `N = 2`.
- [x] `test_tres_puntos_casi_colineales_son_rechazados_por_ambas_capas`: `validar_anillo` devuelve `False` y `Circulo_simple` lanza.

## Tarea 6: verificación con datos reales

- [x] Regenerar los bordes desde `img100.bmp` (el caché `/tmp/opencode/bordes_holgado.npy` no existía): 10 100 bordes, 3150 puntos de anillo.
- [x] Camino real completo: `validar_anillo = True`, `r = 428.1769` (error 0.13 px contra el radio real 428.31).
- [x] Guard no altera el ajuste válido: diferencia `1.2e-05` px contra el valor previo al guard.
- [x] Triples reales de trazos rectos: **500/500 horizontales y 500/500 verticales** lanzan `ValueError`.
- [x] `cond` normalizado del anillo real: `1.4179`, muy por debajo del umbral `3.0`.
- [x] `main.py:602-606` confirmado: `except Exception` → "No se pudo procesar la imagen" con `str(e)`.

## Tarea 7: cierre

- [x] Suite completa: **147 passed**.
- [x] `MEMORY.md` actualizado.
- [x] Deuda anotada: `pv` sigue siendo una métrica pobre (RMSE estaría mejor calibrado) pero cambiarla rompe `main.py:597`; pertenece a una refactorización mayor.
