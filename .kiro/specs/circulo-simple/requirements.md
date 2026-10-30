# Requirements Document — circuloSimple (etapa ⑨)

## Introduction

`Circulo_simple(puntos0)` ajusta un círculo a una matriz de puntos usando mínimos cuadrados (método Kåsa / Taubin sin regularizar). La salida son `x, y, r, pv` donde `pv = max(res) - min(res)` es la métrica pico-a-valle del residuo.

**Contexto que motiva la etapa**: antes de agregar validación, `Circulo_simple` devolvía resultados silenciosos para entradas degeneradas: `r = 7.08` con 1 punto, `r = 7.07` con 2 puntos colineales, `r = 282864` con 3 casi colineales y `pv = 0.000000` en todos estos casos. Ningún usuario interpretaría esos números como "ajuste perfecto". Además, el `pv` actual no distingue un ajuste bueno de uno catastrófico (mismo pv = 0 en ambos casos). Se agregó un contrato de entrada que lanza `ValueError` descriptivo en lugar de devolver números sin sentido.

---\n\n## Glossary

- **`pv` (Peak-to-Valley)**: diferencia entre el residuo máximo y mínimo después del ajuste. No es un RMS ni un desvío estándar; no distingue un ajuste bueno de uno catastrófico. Con el contrato actual, `pv = 0.0` sólo ocurre cuando los residuos son idénticos (casos degenerados controlados), no como antes cuando ocultaba ajustes erróneos.
- **Radicando**: la expresión $x_c^2 + y_c^2 - s$ que se raíz para obtener `r`. Si es negativa, `r` es imaginario y `np.sqrt` lanza o devuelve `nan`; la implementación actual lanza `ValueError` antes que eso suceda.
- **Colinealidad**: cuando los puntos caen sobre (o casi sobre) una línea recta; la matriz `A` queda mal condicionada. Con el contrato actual, 3 puntos colineales hacen que la función lance `ValueError` (por radicando ≤ 0) en lugar de devolver `r = 282864, pv = 0.0` sin aviso.

---\n\n## Requirements

### Requirement 1: Entrada inválida lanza ValueError

**User Story:** Como usuario, quiero que `Circulo_simple` me avise cuando no puede hacer el ajuste, en lugar de devolver números que parezcan legítimos pero no significan nada.

#### Acceptance Criteria

1. `Circulo_simple` SHALL lanzar `ValueError` cuando `puntos0` no sea un `numpy.ndarray`.
2. SHALL lanzar `ValueError` cuando `puntos0` no tenga forma `(N, 2)`.
3. SHALL lanzar `ValueError` cuando $N = 0$ (arreglo vacío).
4. SHALL lanzar `ValueError` cuando $N = 1$ (un solo punto no define un círculo).
5. SHALL lanzar `ValueError` cuando $N = 2$ (dos puntos definen una línea, no un círculo único).
6. SHALL lanzar `ValueError` cuando el radicando $x_c^2 + y_c^2 - s \le 0$ (radio imaginario). Esto incluye el caso de puntos colineales, que antiguamente provocaban `r = 282864, pv = 0.0` sin aviso.
7. SHALL lanzar `ValueError` con un mensaje descriptivo que indique la causa (pocos puntos, tipo incorrecto, forma incorrecta, radicando negativo).

### Requirement 2: Salida cuando el ajuste es exitoso

**User Story:** Como usuario, quiero recibir `x, y, r, pv` con tipos y rangos esperables.

#### Acceptance Criteria

1. SHALL retornar `x_c` y `y_c` como `float64` (coordenadas del centro).
2. SHALL retornar `r` como `float64` (radio positivo, siempre cuando el ajuste converge).
3. SHALL retornar `pv` como `float64` (pico a valle del residuo).
4. SHALL que `r > 0` cuando el ajuste converge.
5. El valor de `pv` depende de la dispersión de los puntos alrededor del círculo ajustado; no hay un valor fijo "correcto". Con puntos bien distribuidos, `pv > 0`; con puntos idénticos, `pv = 0.0` (caso permitido después de la validación).

### Requirement 3: Documentación del comportamiento degenerado

**User Story:** Como mantenedor, quiero que el contrato quede escrito para que futuros desarrolladores sepan por qué lanzamos excepciones en ciertos casos.

#### Acceptance Criteria

1. El spec SHALL documentar que, con el contrato actual, `Circulo_simple` lanza `ValueError` para:
   - $N = 0$ (arreglo vacío) → mensaje "el anillo quedó vacío"
   - $N = 1$ (un solo punto) → mensaje "insuficientes puntos para ajuste; se necesitan al menos 3"
   - $N = 2$ (dos puntos) → mensaje "dos puntos definen una línea, no un círculo único; se necesitan al menos 3"
   - Tipo incorrecto (no ndarray) → `TypeError` → mensaje "se esperaba un numpy.ndarray de forma (N, 2)"
   - Forma incorrecta (ndim ≠ 2 o shape[1] ≠ 2) → `ValueError` → mensaje que indica el shape recibido
   - Radicando ≤ 0 → `ValueError` → mensaje "resultado matemático inválido; los puntos no definen un círculo real"
2. SHALL documentar por qué `pv` no es un discriminador confiable en el diseño antiguo y cómo el nuevo contrato resuelve eso (lanzando excepción antes que un resultado ambiguo).
3. SHALL documentar que el orquestador (`main.py`) captura el `ValueError` y muestra el diálogo "No se pudo procesar la imagen" con la causa, en lugar de mostrar "Error Matemático".