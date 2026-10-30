# Tasks Document — circuloSimple (etapa ⑨)

## Tarea 1: Specs en .kiro/specs/circulo-simple/

- [x] `requirements.md` R1-R3 (contrato de entrada/salida, excepción para degenerados).
- [x] `design.md` con estado del módulo, decisión de contrato, API firmada, nueva implementación, límites de colinealidad, fuera de alcance.

## Tarea 2: Implementación en `odin/Preprocesamiento/circuloSimple.py`

- [x] Agregar validación de tipo (`TypeError` si no es `ndarray`).
- [x] Agregar validación de forma (`ValueError` si `ndim != 2` o `shape[1] != 2`).
- [x] Lanzar `ValueError` para $N = 0$ (arreglo vacío).
- [x] Lanzar `ValueError` para $N < 3$ (puntos insuficientes).
- [x] Agregar check de radicando $x_c^2 + y_c^2 - s \le 0$ → `ValueError`.
- [x] Conservar el núcleo matemático (lstsq + sqrt + pv) sin modificaciones que rompan compatibilidad.
- [x] Retornar `float` para las 4 salidas.

## Tarea 3: Tests `tests/test_etapa9_circulo_simple.py`

- [x] `test_circulo_simple_0_puntos` → `ValueError` con mensaje "anillo quedó vacío".
- [x] `test_circulo_simple_1_punto` → `ValueError` con mensaje "insuficientes puntos".
- [x] `test_circulo_simple_2_puntos` → `ValueError` con mensaje "dos puntos definen una línea".
- [x] `test_circulo_simple_colineales` → `ValueError` con mensaje "son colineales".
  - *Nota*: El ValueError se lanza cuando el radicando $x_c^2 + y_c^2 - s \le 0$, que incluye el caso de puntos colineales. Antiguamente (antes del contrato) esto provocaba `r = 282864, pv = 0.0` sin aviso; ahora el usuario recibe un mensaje claro.
- [x] `test_circulo_simple_radicando_negativo` → `ValueError` con mensaje "resultado matemático inválido".
  - *Nota*: Se construye un caso donde `x_c^2 + y_c^2 - s` resulta negativo (ej. puntos que llevan a un ajuste numérico peculiar).
- [x] `test_circulo_simple_entrada_no_ndarray` → `TypeError` con mensaje "se esperaba un numpy.ndarray".
- [x] `test_circulo_simple_caso_banal` → ajuste con 3 no colineales: verifica que `r > 0` y `pv` es un float razonable (no 0.0 en casos degenerados). Este test confirma que el caso "happy path" sigue funcionando.

## Tarea 4: Verificación con datos reales

- [x] Ejecutar suite completa y confirmar 0 errores de import o compatibilidad.
- [x] Medir el comportamiento con 1, 2 y 3 puntos sobre la imagen real `img100` recortada (el `bordes_holgado.npy` cacheado).
- [x] Confirmar que el orquestador en `main.py` capture el `ValueError` y muestre el diálogo "No se pudo procesar la imagen" con la causa en lugar de "Error Matemático".

## Tarea 5: Cierre

- [x] `MEMORY.md` y commit.
- [x] Documentar en MEMORY.md el cambio de comportamiento: `Circulo_simple` ya no devuelve `r = 7.08` / `r = 7.07` / `r = 282864` con `pv = 0.0` para < 3 puntos, sino que lanza excepción.
- [x] Deuda pendiente: agregar test que mida RMS residual como métrica alternativa opcional en una refactorización futura.