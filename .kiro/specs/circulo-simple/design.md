# Design Document — circuloSimple (etapa ⑨)

## 1. Estado del módulo

`Circulo_simple(puntos0)` ajusta un círculo por mínimos cuadrados algebraicos (Kåsa): resuelve `A @ [x_c, y_c, s] = x² + y²` con `A = [2x, 2y, -1]` y devuelve `(x_c, y_c, r, pv)` con `r = sqrt(x_c² + y_c² - s)`.

| Símbolo | Rol | Llamadores |
|---|---|---|
| `Circulo_simple(puntos0)` | ajuste de círculo con validación y guard de colinealidad | `main.py:597`, `tests/test_etapa7_hough_circles.py`, `tests/test_etapa8_find_circle.py`, `tests/test_etapa9_circulo_simple.py` |

**Historial del contrato.** Antes de la etapa ⑨ no había validación: con 1 punto devolvía `r = 7.08`, con 2 puntos `r = 7.07`, y con 3 casi colineales `r = 282864` con centro a 200 000 px y `pv = 0.000000`. Ninguno de esos números se distinguía de un ajuste perfecto, porque `pv` colapsa a 0 en ambos casos.

## 2. Contrato

### Mensajes de excepción

| Caso | Excepción | Mensaje |
|---|---|---|
| `puntos0` no es `ndarray` | `TypeError` | `circuloSimple: se esperaba un numpy.ndarray de forma (N, 2)` |
| Shape distinta a `(N, 2)` | `ValueError` | `circuloSimple: el arreglo debe tener forma (N, 2) con coordenadas (x, y); recibido shape {shape}` |
| `N = 0` | `ValueError` | `circuloSimple: el anillo quedó vacío; revise la detección de bordes o el radio` |
| `N = 1` | `ValueError` | `circuloSimple: insuficientes puntos para ajuste; se necesitan al menos 3` |
| `N = 2` | `ValueError` | `circuloSimple: dos puntos definen una línea, no un círculo único; se necesitan al menos 3` |
| Todos los puntos coinciden | `ValueError` | `circuloSimple: todos los puntos coinciden; no hay círculo determinable` |
| Puntos colineales | `ValueError` | `circuloSimple: los puntos son colineales; no hay círculo único determinable` |
| Radicando ≤ 0 | `ValueError` | `circuloSimple: resultado matemático inválido; los puntos no definen un círculo real` |

### Salida

`(float, float, float, float)` → `x_c`, `y_c`, `r`, `pv`. Se ajusta sobre las **coordenadas originales**, igual que antes del guard, para no alterar el resultado numérico histórico.

## 3. Guard de colinealidad

### 3.1 El número de condición crudo no sirve

Medido sobre `A = [2x, 2y, -1]` sin transformar:

- un anillo **válido** de `r = 428` centrado en `(1150, 1000)` da `cond(A) = 6.86e3`;
- una recta con ruido que produce `r = 1.4e5` puede dar `9.3e3`.

Los rangos se solapan. Cualquier umbral sobre el `cond` crudo rechaza anillos buenos o acepta basura. La causa es que la columna `-1` no escala con `x` e `y`, así que el cond depende del centro y del radio.

### 3.2 Normalización

Se centran los puntos en su centroide y se dividen por su RMS radial (un escalar, no por eje, para no deformar la geometría):

```python
desplazados = puntos0 - puntos0.mean(axis=0)
escala = np.sqrt(np.mean(np.sum(desplazados**2, axis=1)))
normalizados = desplazados / escala
A_norm = np.column_stack(
    (2.0 * normalizados[:, 0], 2.0 * normalizados[:, 1], -np.ones(nr))
)
condicion = np.linalg.cond(A_norm)
```

Dividir por la desviación estándar **por eje** se descartó: mide 1.11× de margen entre válidos y rectas (`2.323` contra `2.578`), mientras el escalar da 2.38×.

### 3.3 Umbral y márgenes medidos

`UMBRAL_CONDICION_NORMALIZADA = 3.0`

| Geometría | `cond` normalizado |
|---|---|
| Anillo real de 3150 puntos (img100, r ≈ 428) | **1.418** |
| Peor caso válido del contrato (hueco 60°, sigma 2, 216 casos) | **1.701** |
| Arco de 240° (hueco 120°) | 1.718 |
| Semicírculo (hueco 180°) | 2.395 |
| Arco con hueco 240° | 3.672 |
| Mínimo de 960 rectas (N 3–59, ruido 0 a 10 % del largo) | **4.056** |

El umbral deja 1.76× de margen por debajo del peor válido y 1.35× por encima de la recta más benigna, y todavía deja pasar un semicírculo.

### 3.4 Costo

`np.linalg.cond` sobre una matriz `N×3` (SVD) cuesta **1.00 ms** con 3150 puntos, medido de punta a punta en la función. Es despreciable frente a las etapas ①–⑥ (decenas de segundos).

### 3.5 Verificación con datos reales

Sobre los bordes reales de img100 (recorte 2288×2000, 10 100 bordes):

| Prueba | Resultado |
|---|---|
| Anillo real completo | `r = 428.1769`, idéntico al valor previo al guard (diferencia `1.2e-05` px) |
| Triples horizontales de trazos rectos | **500/500 lanzan `ValueError`** |
| Triples verticales de trazos rectos | **500/500 lanzan `ValueError`** |
| Triángulo rectángulo `(0,0) (10,0) (0,10)` | `r = 7.0710678`, sin excepción |

Antes del guard, los mismos triples devolvían círculos de hasta 39 010 px de radio con `pv ≈ 4e-6`, sin excepción.

## 4. Rama defensiva del radicando

`radicando <= 0` se conserva como red de seguridad, pero es **inalcanzable en la práctica**: 0 casos en 200 000 conjuntos aleatorios de 3 a 11 puntos en el rango de coordenadas real. No tiene test propio porque no existe una entrada que lo dispare; se documenta aquí en lugar de escribir un test vacuo.

## 5. Fuera de alcance

- **RANSAC / ajuste robusto**: etapa futura.
- **Cambiar `pv` por RMSE**: `pv` se mantiene en el retorno para no romper `main.py:597`. Medido, RMSE está mejor calibrado (`≈ sigma`) que `pv` (`≈ 3.4 σ` con dispersión 1.43–2.40), pero **ninguna de las dos sirve como guard con N = 3**: 3 puntos se interpolan exactos, 111 de 200 rectas dan `pv == 0` y 110 además `r > 1e4`.
- **Regularización Tikhonov**: fuera de alcance.
- **Guard por cantidad de puntos**: un triángulo bien conformado es un ajuste legítimo; el criterio geométrico (cond normalizado) es el correcto, no `N`.
