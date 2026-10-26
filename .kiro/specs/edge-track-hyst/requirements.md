# Requirements Document — edge-track-hyst (etapa ⑥)

## Introduction

Histéresis de bordes: recibe las máscaras de bordes fuertes y débiles de la
etapa ⑤ (`DobleThreshold`) y decide qué débiles sobreviven por estar
conectados a un fuerte.

**Hallazgo que redefine la etapa**: `main.py` llama a
`EdgeTrack_Hyst(HighE, LowE)` — la implementación **vectorizada con OpenCV**,
no recursiva. `DThEdgeTrack` + `FindConnectedWeakEdges` (la traducción
recursiva de MATLAB) tienen **cero llamadores**. La deuda de recursión está
en código muerto; el riesgo real es otro (ver R6).

---

## Glossary

- **Fuerte**: píxel con `strong > 0` (la máscara viene de `DobleThreshold`).
- **Débil**: píxel con `weaks > 0`.
- **Distancia Chebyshev**: `max(|Δfila|, |Δcol|)`; radio 3 = ventana 7×7.
- **Isla débil**: componente conexa de la máscara débil (8-vecinos).

---

## Requirements

### Requirement 1: Contrato de entrada y salida

**User Story:** Como etapa aguas abajo (Hough, círculos), quiero una imagen
binaria con la misma geometría que la entrada.

#### Acceptance Criteria

1. THE función SHALL recibir dos arreglos de igual forma (`strong`, `weaks`)
   tratados como máscaras: cualquier valor `> 0` significa "presente".
2. THE salida SHALL tener la misma forma que la entrada, `dtype=uint8` y
   valores en `{0, 255}`.
3. THE función SHALL NOT modificar sus argumentos.

### Requirement 2: Los bordes fuertes se conservan siempre

#### Acceptance Criteria

1. WHEN `strong[i, j] > 0`, THEN la salida SHALL ser 255 en `(i, j)`.
2. WHEN no hay fuertes, THEN la salida SHALL ser toda cero, aunque haya
   débiles (no hay nada a lo que conectarse).

### Requirement 3: Alcance desde un borde fuerte

**User Story:** Como detector, quiero tolerar el pequeño hueco entre el
núcleo del borde y su cola débil.

#### Acceptance Criteria

1. A weak pixel SHALL conservarse si está a **distancia Chebyshev ≤ 3** de un
   fuerte (dilatación con kernel 7×7).
2. Evidencia vinculante: horizontal `d=1,2,3` conservado, `d=4,5` descartado;
   diagonal `d=2,3` conservado, `d=4` descartado.

### Requirement 4: Isla débil se conserva completa o se descarta completa

#### Acceptance Criteria

1. WHEN una isla débil (8-vecinos) toca la zona dilatada de un fuerte, THEN
   **todos** sus píxeles SHALL conservarse (propagación transitiva dentro de
   la isla). Evidencia: línea continua de 12 débiles → 1 fuerte + 12.
2. WHEN ninguna parte de la isla toca la zona dilatada, THEN la isla entera
   SHALL descartarse.

### Requirement 5: Semántica de unión entre islas (contrato, no defecto)

#### Acceptance Criteria

1. Dos islas débiles separadas por píxeles vacíos SHALL NOT unirse aunque el
   hueco sea ≤ 3 px. La propagación transitiva ocurre **solo dentro** de una
   isla 8-conexa.
2. Evidencia: fuerte en (20,20), débil en (20,23) y (20,26) → solo sobrevive
   (20,23). La implementación recursiva salvaba ambas (propagaba saltos ≤3),
   pero **no es la que corre en producción**.
3. La implementación vectorizada es **subconjunto estricto** de la recursiva
   (`solo_vec = 0` en todos los casos medidos).

### Requirement 6: Robustez (divergencia D1)

**User Story:** Como llamador, quiero que una entrada vacía devuelva una
salida vacía, no una excepción.

#### Acceptance Criteria

1. WHEN la entrada es un arreglo vacío, THEN la función SHALL devolver un
   arreglo vacío `uint8` sin lanzar excepción. **(NO CUMPLE hoy:
   `ValueError: zero-size array to reduction operation maximum`.)**
2. WHEN una de las dos máscaras está vacía, THEN la salida SHALL respetar
   R2.2 y R2.1.

### Requirement 7: Sin recursión ni efectos globales

#### Acceptance Criteria

1. THE función SHALL NOT usar recursión.
2. THE módulo SHALL NOT llamar `sys.setrecursionlimit` en el camino de
   producción (hoy lo hace `DThEdgeTrack`, que no se usa).

### Requirement 8: Diagnóstico por consola

**User Story:** Como lector de la consola, quiero una sola línea de resumen del
pipeline, no ocho líneas de diagnóstico por cada procesamiento.

#### Acceptance Criteria

1. THE función SHALL NOT escribir en consola. Era el único módulo del pipeline
   con prints por llamada; el modelo queda libre de salida, como el resto.
2. THE orquestador (`main.py`) SHALL reportar el resumen de la etapa en una
   sola línea: fuertes, débiles y píxeles conservados tras la histéresis.
