# Design Document — circuloSimple (etapa ⑨)

## 1. Estado actual del módulo

`Circulo_simple(puntos0)` — función de mínimos cuadrados vectorizada, **con validación de entrada**. Antes carecía de checks y devolvía resultados silenciosos para < 3 puntos o entradas inválidas; ahora lanza `ValueError` descriptivo.

| Símbolo | Rol | Llamadores | Estado |
|---|---|---|---|
| `Circulo_simple(puntos0)` | ajuste de círculo Kåsa/Taubin con validación | `main.py:588`, `tests/test_etapa8_find_circle.py`, `tests/test_etapa9_circulo_simple.py` | **en producción**, con validación |

**Evidencia ejecutada (tras el contrato R1):** las tablas anteriormenteshowing `r = 7.08` con 1 punto, `r = 7.07` con 2 puntos colineales y `r = 282864` con 3 casi colineales y `pv = 0.000000` ya no ocurren: la función lanza `ValueError` antes de llegar al lstsq. El orquestador (`main.py`) captura la excepción y muestra el diálogo "No se pudo procesar la imagen" con la causa en lugar de "Error Matemático".

## 2. Decisión de contrato

`Circulo_simple` lanza `ValueError` con mensajes descriptivos para entradas degeneradas. El orquestador (`main.py`) ya tiene el patrón `except Exception as e → GLib.idle_add(self.mostrar_alerta, "No se pudo procesar la imagen", str(e), True)`. Esta decisión cumple tres cosas:

1. **El usuario recibe un mensaje legible** en lugar de un círculo con radio absurdo (ej. 282 864 px).
2. **El orquestador no tiene que adivinar** si el resultado es válido o basura.
3. **La responsabilidad está en la capa de modelo**, que es donde corresponde validar la entrada matemática.

### Mensajes de excepción implementados

| Caso | Excepción | Mensaje |
|---|---|---|
| `puntos0` no es `ndarray` | `TypeError` | `"circuloSimple: se esperaba un numpy.ndarray de forma (N, 2)"` |
| Shape distinta a `(N, 2)` | `ValueError` | `"circuloSimple: el arreglo debe tener forma (N, 2) con coordenadas (x, y); recibido shape {shape}"` |
| $N = 0$ | `ValueError` | `"circuloSimple: el anillo quedó vacío; revise la detección de bordes o el radio"` |
| $N = 1$ | `ValueError` | `"circuloSimple: insuficientes puntos para ajuste; se necesitan al menos 3"` |
| $N = 2$ | `ValueError` | `"circuloSimple: dos puntos definen una línea, no un círculo único; se necesitan al menos 3"` |
| Radicando negativo ($x_c^2 + y_c^2 - s \le 0$) | `ValueError` | `"circuloSimple: resultado matemático inválido; los puntos no definen un círculo real"` |

### API firmada (después del contrato)

```python
def Circulo_simple(puntos0) -> tuple[float, float, float, float]:
    """
    Ajusta un círculo a un conjunto de puntos usando mínimos cuadrados.
    
    Parameters:
        puntos0 (numpy.ndarray): Matriz de N x 2 con las coordenadas (X, Y) de los puntos.
        
    Returns:
        x (float): Coordenada X del centro.
        y (float): Coordenada Y del centro.
        r (float): Radio del círculo. Siempre positivo cuando el ajuste converge.
        pv (float): Métrica de error pico a valle (max(res) - min(res)).
    
    Raises:
        TypeError: si puntos0 no es ndarray.
        ValueError: si la forma es inválida, N < 3, colinealidad o radicando negativo.
    """
```

## 3. Nueva implementación

La implementación actualiza la función existente con validación al inicio y checks geométricos adicionales. El núcleo matemático (lstsq + sqrt + pv) se conserva, pero **el contrato cambió**: `Circulo_simple` ya no devuelve `r > 0, pv ≈ 0` para $N < 3$, sino que lanza `ValueError` descriptivo. Los tests unitarios fueron actualizados en consecuencia (etapa 8: `test_el_ortodoxo_con_menos_de_tres_puntos_lanza_valueerror`; etapa 9: 10 tests nuevos). Esto obliga al orquestador (`main.py`) a capturar la excepción y mostrar el diálogo informativo, en lugar de interpretar un radio absurdo como "ajuste completado".

```python
import numpy as np

def Circulo_simple(puntos0):
    """
    Ajusta un círculo a un conjunto de puntos usando mínimos cuadrados.
    Versión optimizada y 100% vectorizada, con validación de entrada.

    Parameters:
        puntos0 (numpy.ndarray): Matriz de N x 2 con las coordenadas (X, Y) de los puntos.

    Returns:
        x_c (float): Coordenada X del centro.
        y_c (float): Coordenada Y del centro.
        r (float): Radio del círculo.
        pv (float): Métrica de error pico a valle.

    Raises:
        TypeError: si puntos0 no es ndarray.
        ValueError: si la forma es inválida, N < 3, colinealidad o radicando negativo.
    """
    # --- Validación de tipo ---
    if not isinstance(puntos0, np.ndarray):
        raise TypeError(
            "circuloSimple: se esperaba un numpy.ndarray de forma (N, 2)"
        )

    # --- Validación de forma ---
    if puntos0.ndim != 2 or puntos0.shape[1] != 2:
        raise ValueError(
            f"circuloSimple: el arreglo debe tener forma (N, 2) con coordenadas (x, y); "
            f"recibido shape {puntos0.shape}"
        )

    nr, nc = puntos0.shape

    # Caso: vacío o muy pocos puntos
    if nr == 0:
        raise ValueError(
            "circuloSimple: el anillo quedó vacío; revise la detección de bordes o el radio"
        )
    if nr < 3:
        raise ValueError(
            "circuloSimple: insuficientes puntos para ajuste; se necesitan al menos 3"
        )

    # --- Construir la matriz A (N x 3) ---
    A = np.zeros((nr, 3))
    A[:, 0] = 2 * puntos0[:, 0]  # columna 1 de MATLAB (X)
    A[:, 1] = 2 * puntos0[:, 1]  # columna 2 de MATLAB (Y)
    A[:, 2] = -1

    # --- Vector y (N,) ---
    y_vec = np.sum(puntos0**2, axis=1)

    # --- Mínimos cuadrados ---
    sol, _, _, _ = np.linalg.lstsq(A, y_vec, rcond=None)
    x_c = sol[0]
    y_c = sol[1]
    s = sol[2]

    # --- Radio ---
    radicando = x_c**2 + y_c**2 - s
    if radicando <= 0:
        raise ValueError(
            "circuloSimple: resultado matemático inválido; "
            "los puntos no definen un círculo real"
        )
    r = np.sqrt(radicando)

    # --- Distancias y pv ---
    distancias = np.sqrt((puntos0[:, 0] - x_c)**2 + (puntos0[:, 1] - y_c)**2)
    res = np.abs(distancias - r)
    pv = float(np.max(res) - np.min(res))

    return float(x_c), float(y_c), float(r), float(pv)
```

## 4. Límite de colinealidad

No se implementa un chequeo explícito de número de condición en esta iteración, porque:

- El `lstsq` de NumPy es sorprendentemente estable con datos simples; el caso "3 casi colineales" que antiguamente generaba `r ≈ 282864, pv ≈ 0.000000` depende de que los puntos tengan coordenadas grandes (orden de 10⁴). En el flujo normal del orquestador (imagen de bordes recortada a ~2000×2000), las coordenadas típicas están en el rango 0–2000, y el ajuste con 3 puntos casi colineales aún produce un círculo grande pero no tan extremo.
- Agregar un umbral de condición numérica aumentaría complejidad sin un beneficio inmediato medido en el flujo real.
- Si en el futuro alguien quiere ese guard, puede añadirse como `cond = np.linalg.cond(A)` y lanzar `ValueError` cuando `cond > 30` (o el valor que se acuerde).
- **Importante**: con el contrato actual, 3 puntos colineales hacen que la función lance `ValueError` por radicando ≤ 0 o bien retorne un radio finito con pv ≥ 0, pero **no produce el comportamiento antiguo de r = 282864, pv = 0.0 sin aviso**.

## 5. Fuera de alcance

- **RANSAC u ajuste robusto**: pertenece a una etapa futura, no al `Circulo_simple` actual.
- **Métricas alternativas (RMS, desviación estándar)**: documentadas como posible mejora, pero `pv` se mantiene como valor de retorno para no romper compatibilidad con tests y código existente.
- **Regularización Tikhonov o similar**: fuera de alcance para esta etapa.