# Requirements Document — circulo-simple (etapa ⑨)

## Introduction

Etapa ⑨ (`odin/Preprocesamiento/circuloSimple.py`) ajusta un círculo a un conjunto
de puntos borde mediante mínimos cuadrados algebraicos (método de Kåsa). Es el
último ajuste geométrico del pipeline de ODIN: recibe los puntos del anillo
entregados por ⑧ (`findCircle`) y devuelve el centro $(x_c, y_c)$ y el radio $r$
en coordenadas de imagen, más una métrica de error pico a valle (`pv`).

**Contexto que motiva la etapa**: `Circulo_simple` es mínimos cuadrados algebraicos
sin robustez. Con puntos casi colineales o menos de 3 puntos, el sistema es
subdeterminado o degenerado y puede devolver un círculo absurdo con `pv = 0.0`
indistinguible de un ajuste perfecto (medido en `test_etapa8_find_circle.py`).
El contrato debe prevenir ajustes silenciosos de basura y explicar el rechazo
con un motivo claro al usuario.

---

## Glossary

- **Kåsa fit**: mínimos cuadrados algebraicos que resuelve $A \mathbf{w} = \mathbf{b}$ con
  $A = [2x_i,\ 2y_i,\ -1]$ y $\mathbf{b} = x_i^2 + y_i^2$.
- **Radio subdeterminado**: resultado de $< 3$ puntos o puntos colineales;
  el radio tiende a infinito o es geométricamente insignificante.
- **Radicando**: $x_c^2 + y_c^2 - s$, que si es negativo hace que $\sqrt{}$ produzca
  `NaN` o un `RuntimeWarning`.
- **PV (pico a valle)**: $\max(|d_i - r|) - \min(|d_i - r|)$, diferencia entre el error
  máximo y mínimo de distancia punto-centro respecto al radio ajustado.

---

## Requirements

### Requirement 1: Contrato de `Circulo_simple`

**User Story:** Como etapa ⑨ del pipeline, quiero un ajuste de círculo
geométricamente válido o un rechazo explícito cuando los datos no lo permiten.

#### Acceptance Criteria

1. `Circulo_simple` SHALL recibir una matriz NumPy de forma $(N, 2)$ con
   coordenadas $(x, y)$ de los puntos.
2. WHEN $N \ge 3$ y los puntos no son colineales, THEN SHALL devolver
   $(x_c, y_c, r, pv)$ con $r > 0$ y $pv \ge 0$.
3. WHEN $N < 3$, THEN SHALL rechazar con `ValueError` y mensaje descriptivo
   ("menos de 3 puntos: ajuste subdeterminado").
4. WHEN los puntos son colineales (o casi), THEN SHALL rechazar con
   `ValueError` ("puntos colineales: no se puede ajustar un círculo").
5. WHEN el radicando $x_c^2 + y_c^2 - s \le 0$, THEN SHALL rechazar con
   `ValueError` ("radicando no positivo: radio indefinido").
6. WHEN la entrada es `None` o no es un array $(N, 2)$, THEN SHALL rechazar con
   `ValueError`.
7. El orden de los puntos SHALL NOT influir en el resultado del ajuste.

### Requirement 2: Métrica de error

**User Story:** Como consumidor del resultado, quiero saber qué tan ajustado
está el círculo a los puntos, no solo un número sin contexto.

#### Acceptance Criteria

1. `pv` SHALL ser el pico a valle de los errores de distancia
   $\max(|d_i - r|) - \min(|d_i - r|)$.
2. $pv$ SHALL ser $0.0$ para un círculo perfecto (todos los puntos exactamente
   sobre la circunferencia).

### Requirement 3: Integración con la etapa ⑧

**User Story:** Como etapa ⑧ (`findCircle`), quiero confiar en que ⑨ valida
geométricamente lo que recibe antes de ajustar.

#### Acceptance Criteria

1. `main.py` SHALL seguir llamando a `LSC.Circulo_simple(puntosFiltrados)`
   tras `validar_anillo`.
2. WHEN `Circulo_simple` rechaza por $< 3$ puntos o colinealidad, THEN
   `main.py` SHALL mostrar el motivo en el diálogo de error en vez de fallar
   silenciosamente.
