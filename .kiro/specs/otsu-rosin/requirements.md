# Requirements Document

## Introduction

Este documento captura los requerimientos de la **etapa ④ del pipeline de ODIN**
(`otsu-rosin`): el cálculo de los umbrales de Otsu y Rosin sobre la magnitud de
gradiente ya suprimida (etapa ③).

Corresponde a `umbralRosinYOtsu(IG, histo=False)` y `umbralOtsu(IG, histo=False)`
en `src/odin/Procesamiento/models/otsu_rosin.py` (legacy `odin/Preprocesamiento/MtoOtsu.py`), con los helpers privados
`_preparar_histograma` y `_umbral_otsu`.

Contrato aguas arriba: `IG` es la magnitud de gradiente tras NMS (etapa ③),
normalizada a `[0, 1]` por la etapa ②. Aguas abajo: `main.py` usa **solo el
umbral de Otsu** (`uOtsu, _uRosin = Otsu.umbralRosinYOtsu(...)`) y lo pasa a
`DobleThreshold` (etapa ⑤). El umbral Rosin se calcula únicamente para el
histograma de diagnóstico (`histo=True`).

Es un spec **mixto**: caracterización de lo correcto + una divergencia real
(D1) en un caso degenerado.

---

## Glossary

- **Píxeles activos**: los que cumplen `IG > 0`. El fondo (gradiente nulo) se
  excluye del histograma.
- **Histograma**: 256 bins uniformes sobre el rango observado de los píxeles
  activos, con centros `xcenters`.
- **Varianza interclase** (`vB`): `w0·w1·(u1−u0)²`, el criterio que Otsu
  maximiza.
- **Meseta de Otsu**: región de umbrales donde `vB` es prácticamente constante
  (clusters compactos y bien separados).
- **Criterio de Rosin**: umbral = punto del histograma con máxima distancia
  perpendicular a la recta que une el pico con el final de la cola.

---

## Requirements

### Requirement 1: Histograma de píxeles activos

**User Story:** Como usuario de ODIN, quiero que los umbrales se calculen solo
sobre el gradiente real, para que el fondo negro no arrastre el histograma.

#### Acceptance Criteria

1. THE histograma SHALL construirse con 256 bins uniformes sobre el rango de
   los píxeles con `IG > 0`.
2. WHEN no hay píxeles activos (todo cero, todo negativo, arreglo vacío), THEN
   ambas funciones SHALL devolver `0.0` sin lanzar excepción.
3. WHEN hay `NaN` en la entrada, THEN SHALL excluirse del histograma (el filtro
   `IG > 0` los descarta) sin propagar `NaN` al umbral.

### Requirement 2: Umbral de Otsu

**User Story:** Como etapa ⑤, quiero el umbral que maximiza la separación
interclase, para particionar los bordes en fuertes y débiles.

#### Acceptance Criteria

1. THE umbral SHALL ser el centro de bin que maximiza `vB`.
2. WHEN el óptimo es agudo (clusters de varianza amplia), THEN el umbral SHALL
   coincidir con una referencia independiente por barrido sobre valores reales
   dentro de **1 ancho de bin** (verificado: sigma 0.12 → 0.4 bins; sigma 0.20
   → 0.6 bins).
3. THE resultado SHALL ser invariante a usar índices de bin (1..L) en lugar de
   `xcenters` reales: es una transformación afín monótona, y el argmax de `vB`
   no cambia (verificado: valores idénticos).
4. THE umbral SHALL escalar proporcionalmente con la entrada (verificado:
   `IG × 10` → umbral ×10.0000).

### Requirement 3: Meseta de Otsu (contrato de unicidad)

**User Story:** Como consumidor del umbral, quiero saber cuándo el valor es
único y cuándo no, para no perseguir diferencias que no significan nada.

#### Acceptance Criteria

1. WHEN los clusters son compactos y bien separados, THEN `vB` SHALL ser
   prácticamente constante en una región amplia y **cualquier punto de la
   meseta SHALL considerarse un umbral válido**.
2. Evidencia vinculante: en datos bimodales (σ=0.05), `vB(0.45321) =
   vB(0.51478) = 0.062669804206` — idénticos a 12 decimales. Una diferencia de
   umbral de 0.06 en esa región **no es un defecto**.

### Requirement 4: Umbral de Rosin (diagnóstico)

**User Story:** Como usuario, quiero ver en el histograma dónde cae el criterio
de Rosin, para compararlo con Otsu.

#### Acceptance Criteria

1. THE umbral Rosin SHALL ser el punto de máxima distancia perpendicular a la
   recta pico→cola, evaluado en la zona `[pico, último bin no vacío]`.
2. THE umbral Rosin SHALL ser **solo diagnóstico**: `main.py` lo descarta y el
   pipeline no lo usa para decidir nada.
3. WHEN la geometría es indefinida (un solo bin no vacío, recta de longitud 0),
   THEN SHALL caer al respaldo `umbral_rosin = umbral_otsu`.
4. (Comportamiento documentado) En histogramas bimodales, Rosin cae en el
   **flanco del pico dominante** (verificado: pico en 0.100 → Rosin 0.1417), no
   en el valle entre clusters: el criterio es para histogramas unimodales.

### Requirement 5: Casos degenerados (divergencia D1)

**User Story:** Como llamador (librería o pipeline con una imagen degenerada),
quiero un umbral con sentido cuando no hay separación posible, no un valor
arbitrario del borde artificial del histograma.

#### Acceptance Criteria

1. WHEN todos los píxeles activos tienen el mismo valor (un solo bin no
   vacío), THEN el umbral SHALL ser exactamente ese valor. **(Resuelto:
   `_preparar_histograma` devuelve un histograma de un solo bin centrado en el
   valor real; verificado 1e-6, 0.001, 0.005, 0.05, 0.5, 0.7, 1.0 y 3.7 → el
   umbral es idéntico al valor.)**
2. THE umbral devuelto SHALL ser siempre ≥ 0 cuando la entrada es ≥ 0.
   **(Resuelto; verificado con valores diminutos: 1e-12 y 1e-6 incluidos.)**

### Requirement 6: Función pura respecto de la UI (deuda)

**User Story:** Como capa de modelos, quiero que el cálculo no dependa de GTK,
para poder testearlo y reutilizarlo.

#### Acceptance Criteria

1. THE funciones de umbralizado SHALL NOT invocar la UI. **(Deuda D3: hoy
   llaman `GLib.idle_add(dibujar_en_hilo_principal, ...)` de forma
   incondicional, incluso con `histo=False`; el módulo importa `gi`. La deuda
   se resuelve en el refactor `src/odin/` inyectando un callback de dibujo.)**
