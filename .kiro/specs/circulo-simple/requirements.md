# Requirements Document — circuloSimple (etapa ⑨)

## Introduction

`Circulo_simple(puntos0)` ajusta un círculo a una matriz de puntos por mínimos cuadrados algebraicos (Kåsa) y devuelve `(x, y, r, pv)`, donde `pv = max(res) - min(res)` es el pico a valle del residuo.

**Contexto.** Antes de la etapa ⑨ el ajuste no validaba nada: devolvía `r = 7.08` con 1 punto, `r = 7.07` con 2 puntos y `r = 282864` con centro a 200 000 px y `pv = 0.000000` con 3 puntos casi colineales. Los tres casos son indistinguibles de un ajuste perfecto para el usuario, porque `pv` vale 0 en ambos extremos. Con datos reales, 537 de 537 triples horizontales y 4080 de 4080 verticales de un trazo recto producían círculos absurdos sin excepción.

---

## Glossary

- **`pv` (Peak-to-Valley)**: diferencia entre el residuo máximo y mínimo. No es un RMS; colapsa a 0 tanto en un ajuste perfecto como en un ajuste catastrófico con N = 3.
- **Radicando**: `x_c² + y_c² - s`, la expresión cuya raíz da `r`. Si es ≤ 0, el círculo es imaginario.
- **Colinealidad**: los puntos caen sobre (o casi sobre) una recta; la matriz `A = [2x, 2y, -1]` queda mal condicionada y el ajuste no tiene sentido geométrico.
- **`cond` normalizado**: número de condición de `A` calculado sobre los puntos centrados en su centroide y escalados por su RMS radial.

---

## Requirements

### Requirement 1: entrada inválida lanza excepción descriptiva

**User Story:** Como usuario, quiero que `Circulo_simple` me avise cuando no puede hacer el ajuste, en lugar de devolver números que parezcan legítimos.

#### Acceptance Criteria

1. SHALL lanzar `TypeError` cuando `puntos0` no sea un `numpy.ndarray`.
2. SHALL lanzar `ValueError` cuando `puntos0` no tenga forma `(N, 2)`.
3. SHALL lanzar `ValueError` cuando `N = 0`.
4. SHALL lanzar `ValueError` cuando `N = 1`.
5. SHALL lanzar `ValueError` con un mensaje **distinto** cuando `N = 2` ("dos puntos definen una línea, no un círculo único").
6. SHALL lanzar `ValueError` cuando todos los puntos coincidan (`escala ≤ 0`).
7. Cada mensaje SHALL indicar la causa concreta, en español.

### Requirement 2: guard de colinealidad

**User Story:** Como usuario, quiero que un conjunto casi colineal sea rechazado en lugar de producir un círculo de radio absurdo que parezca válido.

#### Acceptance Criteria

1. El guard SHALL calcularse sobre coordenadas normalizadas (centroide + RMS radial), NO sobre `A` cruda.
2. SHALL lanzar `ValueError` cuando el `cond` normalizado supere el umbral (`3.0`).
3. El umbral SHALL justificarse con márgenes medidos a ambos lados: `1.701` peor caso válido, `4.056` recta más benigna.
4. SHALL aceptar un arco de hasta medio círculo (`cond` 2.395).
5. SHALL rechazar los triples reales de trazos rectos (medido: 500/500 horizontales, 500/500 verticales).
6. NO SHALL alterar el resultado numérico de los ajustes válidos: el anillo real de 3150 puntos conserva `r = 428.1769`.
7. El costo del guard SHALL ser despreciable (medido: 1.00 ms con 3150 puntos).

### Requirement 3: salida del ajuste exitoso

#### Acceptance Criteria

1. SHALL retornar cuatro `float`: `x_c`, `y_c`, `r`, `pv`.
2. SHALL cumplir `r > 0` cuando el ajuste converge.
3. `pv` SHALL ser ≥ 0 y depender de la dispersión real de los puntos.

### Requirement 4: documentación del comportamiento degenerado

#### Acceptance Criteria

1. El spec SHALL documentar la tabla completa de excepciones y sus mensajes.
2. SHALL documentar por qué `pv` no discrimina y por qué RMSE tampoco sirve con `N = 3`.
3. SHALL documentar que la rama `radicando ≤ 0` es defensiva e inalcanzable (0 de 200 000 casos aleatorios).
4. SHALL documentar que el orquestador (`main.py:602-606`) captura `Exception` y muestra "No se pudo procesar la imagen" con `str(e)`.
